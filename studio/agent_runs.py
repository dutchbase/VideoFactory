"""User-started agent work on a Studio request: unattended `claude -p`, or a guided terminal.

Not a jobs.py job on purpose: a job holds the workspace lock for its whole process, and the
agent must itself mark its output ready.
"""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from pathlib import Path

from studio.jobs import _KEY, _now, _process_start, _read, _record_path, _save, _secret_values, _valid, claim_request, finish_request
from studio.jobs import validate_request_output
from studio.workspace import WorkspaceError
from studio.production import production_lock, lease_fds, child_environment

# Approved gate -> agent request kind for the next stage. The kind's input gate matches claim_request.
AGENT_NEXT = {"brief": "script", "transcript": "cues", "cues": "scene"}
TASK = {"script": "Write the script from the approved brief.",
        "cues": "Author the storyboard cues from the approved transcript.",
        "scene": "Author the scene from the approved storyboard cues."}
GUARD_ENV = {"WAYLAND_DISPLAY": "omabox-guard", "DISPLAY": "", "HYPRLAND_INSTANCE_SIGNATURE": "omabox-guard"}
AGENT_TOOLS = ["Read", "Edit", "Write", "Glob", "Grep", "Bash(.venv/bin/python anim.py:*)", "Bash(omabox:*)"]
# Deny rules win over the allow list: no paid voice, no second studio (its recovery would kill runs), no jobs.
DENIED_TOOLS = ["Bash(.venv/bin/python anim.py speak:*)", "Bash(.venv/bin/python anim.py studio:*)", "Bash(.venv/bin/python anim.py studio-job:*)"]
_LOG_LIMIT = 1_048_576
_LOCK = threading.Lock()
_PROCS: dict[tuple[str, str], subprocess.Popen] = {}

AUTO_PROMPT = """You are running unattended. The user started you from the VideoFactory Studio.
Studio request {id} is already claimed for you: {kind} for videos/{slug}.
User instructions: {instructions}

Read AGENTS.md, then _shared/dashboard-review.md and the CONTEXT.md of the {gate} stage.
Do the work without asking questions. Where a choice is open, take the documented default and name it in your final note.
Run the stage's checks. When the output is complete, read the current fingerprint with `.venv/bin/python anim.py review {slug} {gate}` and mark it ready with `.venv/bin/python anim.py review {slug} {gate} --ready --expected <fingerprint>`.
Then run `.venv/bin/python anim.py studio-request {id} --finish succeeded --note '<one line>'`, or `--finish failed` with the reason.
Never approve a gate, never generate paid voice, never publish. Do not open a browser: the Studio shows the review.
"""

GUIDED_PROMPT = """The user asked you from the VideoFactory Studio to guide them through Studio request {id}: {kind} for videos/{slug}.
User instructions: {instructions}

Claim it first with `.venv/bin/python anim.py studio-request {id} --claim claude`.
Read AGENTS.md, then _shared/dashboard-review.md and the CONTEXT.md of the {gate} stage.
Walk the user through the stage's open choices before you write. When the output is complete, read the fingerprint with `.venv/bin/python anim.py review {slug} {gate}`, mark it ready with `--ready --expected <fingerprint>`, and finish the request with `.venv/bin/python anim.py studio-request {id} --finish succeeded --note '<one line>'`.
Never approve a gate yourself.
"""


def _key(root, request_id):
    return (str(Path(root).resolve()), request_id)


def _log_path(root, request_id):
    return _record_path(root, "requests", request_id).with_suffix(".log")


def agent_argv(root: Path, record: dict, mode: str) -> list[str]:
    fields = {"id": record["id"], "kind": record["kind"], "slug": record.get("slug", ""),
              "instructions": record.get("instructions", ""), "gate": record["kind"]}
    if mode == "auto":
        return ["claude", "-p", AUTO_PROMPT.format(**fields), "--permission-mode", "acceptEdits",
                "--allowedTools", *AGENT_TOOLS, "--disallowedTools", *DENIED_TOOLS]
    return ["uwsm-app", "--", "xdg-terminal-exec", f"--dir={Path(root).resolve()}", "claude", GUIDED_PROMPT.format(**fields)]


def _finish_if_running(root, request_id, state, note):
    with _LOCK:
        if _read(_record_path(root, "requests", request_id)).get("state") == "running":
            finish_request(root, request_id, {"state": state, "note": note})


def _copy_log(root, request_id, stream):
    secrets = _secret_values(root)
    size = 0
    try:
        with _log_path(root, request_id).open("w", encoding="utf-8") as log:
            for line in stream:
                for secret in secrets: line = line.replace(secret, "[redacted]")
                line = line.replace(str(root), "<workspace>")
                if size < _LOG_LIMIT:
                    log.write(line[:_LOG_LIMIT - size]); log.flush()
                    size += len(line)
    except (OSError, ValueError):
        pass


def _watch(root, request_id, process):
    # Finish on process exit, not stdout EOF: a leftover grandchild may hold the pipe open.
    root = Path(root)
    code = None
    try:
        reader = threading.Thread(target=_copy_log, args=(root, request_id, process.stdout), daemon=True)
        reader.start()
        code = process.wait()
        try: os.killpg(process.pid, signal.SIGTERM)  # leftovers in the agent's group
        except ProcessLookupError: pass
        reader.join(timeout=5)
        if not reader.is_alive():
            process.stdout.close()
    finally:
        _PROCS.pop(_key(root, request_id), None)
        note = log_tail(root, request_id, 200)[-300:].strip() or f"Agent exited with status {code}."
        record = _read(_record_path(root, "requests", request_id))
        if record.get("state") == "succeeded":
            try:
                validate_request_output(root, record)
            except WorkspaceError as exc:
                record.update(state="failed", note=str(exc), finished_at=_now())
                _save(_record_path(root, "requests", request_id), record)

        try:
            _finish_if_running(root, request_id, "succeeded" if code == 0 else "failed", note)
        except WorkspaceError as exc:
            _finish_if_running(root, request_id, "failed", str(exc))


def _start_run(root, request_id: str, mode: str) -> dict:
    root = Path(root)
    _valid(request_id, "request id", _KEY)
    if mode not in ("auto", "guided"):
        raise WorkspaceError("invalid", "Run mode must be auto or guided.")
    path = _record_path(root, "requests", request_id)
    if not path.exists(): raise WorkspaceError("missing", "Agent request not found.")
    with _LOCK:
        record = _read(path)
        if record.get("run"): return record
        if record.get("subject") or record.get("kind") not in TASK:
            raise WorkspaceError("invalid", "Only script, cues and scene requests can be run from the studio.")
        argv = agent_argv(root, record, mode)
        if mode == "guided":
            try:
                process = subprocess.Popen(argv, cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL, start_new_session=True)
            except OSError:
                raise WorkspaceError("blocked", "Could not open a terminal for the agent.") from None
            threading.Thread(target=process.wait, daemon=True).start()
            record["run"] = {"mode": "guided", "started_at": _now()}
            _save(path, record)
            return record
        record = claim_request(root, request_id, "claude (studio)")
        try:
            process = subprocess.Popen(argv, cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, errors="replace", start_new_session=True,
                                       env=os.environ | GUARD_ENV | child_environment(root), pass_fds=lease_fds())
        except OSError:
            finish_request(root, request_id, {"state": "failed", "note": "Claude Code could not be started."})
            raise WorkspaceError("blocked", "Claude Code could not be started from the studio.") from None
        _PROCS[_key(root, request_id)] = process
        record["run"] = {"mode": "auto", "pid": process.pid, "process_start": _process_start(process.pid),
                         "started_at": _now(), "log": str(_log_path(root, request_id).relative_to(root)),
                         "server": {"pid": os.getpid(), "start": _process_start(os.getpid())}}
        _save(path, record)
    return record


def start_run(root, request_id: str, mode: str) -> dict:
    _valid(request_id, "request id", _KEY)
    existing = _read(_record_path(root, "requests", request_id))
    if existing.get("run"):
        return existing
    if mode == "guided":
        raise WorkspaceError("blocked", "Use saved run controls or copy the handoff. Terminal agents cannot share the production lock.")
    ready = threading.Event()
    result = {}
    def worker():
        try:
            with production_lock(root, "studio-agent:" + request_id):
                result["record"] = _start_run(root, request_id, mode)
                ready.set()
                process = _PROCS.get(_key(root, request_id))
                if process is not None:
                    _watch(root, request_id, process)
        except Exception as exc:
            result["error"] = exc
        finally:
            ready.set()
    threading.Thread(target=worker, daemon=True).start()
    ready.wait()
    if "error" in result:
        exc = result["error"]
        if isinstance(exc, ValueError):
            raise WorkspaceError("busy", str(exc)) from None
        raise exc
    return result["record"]


def _kill_group(pid, process_start, process=None):
    try: os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError: return
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None: break
        if process is None and _process_start(pid) != process_start: break
        time.sleep(.05)
    try: os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError: pass


def cancel_run(root, request_id: str) -> dict:
    root = Path(root)
    _valid(request_id, "request id", _KEY)
    path = _record_path(root, "requests", request_id)
    if not path.exists(): raise WorkspaceError("missing", "Agent request not found.")
    record = _read(path)
    run = record.get("run") or {}
    if record.get("state") != "running" or run.get("mode") != "auto":
        raise WorkspaceError("conflict", "No studio agent run is active for this request.")
    # Record the stop first so the watcher does not report the killed process as failed.
    _finish_if_running(root, request_id, "cancelled", "Stopped by you; partial files may remain.")
    process = _PROCS.get(_key(root, request_id))
    if process is not None or _process_start(run["pid"]) == run.get("process_start"):
        _kill_group(run["pid"], run.get("process_start"), process)
    return _read(path)


def recover(root) -> None:
    from studio.jobs import list_requests
    for record in list_requests(root):
        run = record.get("run") or {}
        if record.get("state") != "running" or run.get("mode") != "auto": continue
        process = _PROCS.get(_key(root, record["id"]))
        if process is not None and process.poll() is None: continue
        server = run.get("server") or {}
        # Another studio process (a test server, a CLI start) still owns and watches this run.
        if server.get("pid") != os.getpid() and isinstance(server.get("pid"), int) and _process_start(server["pid"]) == server.get("start"): continue
        if isinstance(run.get("pid"), int) and _process_start(run["pid"]) == run.get("process_start"):
            _kill_group(run["pid"], run["process_start"])
        _finish_if_running(root, record["id"], "failed", "Interrupted when the studio restarted.")


def log_tail(root, request_id: str, lines: int = 40) -> str:
    _valid(request_id, "request id", _KEY)
    log = _log_path(root, request_id)
    if not log.exists(): return ""
    return "\n".join(log.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:])


def run_status(root, request_id: str) -> dict:
    path = _record_path(root, "requests", _valid(request_id, "request id", _KEY))
    if not path.exists(): raise WorkspaceError("missing", "Agent request not found.")
    record = _read(path)
    return {"state": record.get("state"), "note": record.get("note", ""), "log": log_tail(root, request_id)}
