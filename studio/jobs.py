"""Durable, guarded local production jobs and agent handoffs."""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import socket
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from studio.production import production_lock, lease_fds, child_environment
from studio.project_paths import resolve_project, project_id
from studio.workspace import WorkspaceError, gate_fingerprint, review_state, mark_ready, workspace_lock, safe_path

GATE_PASSED = {"approved"}

_ID = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
_KEY = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
_ACTIVE = {"queued", "running", "cancelling"}
_GUARD = threading.Lock()
_PROCESSES: dict[tuple[str, str], subprocess.Popen] = {}
_THREADS: dict[tuple[str, str], threading.Thread] = {}
_BOXES: dict[tuple[str, str], str] = {}
_BROWSER_ACTIONS = {"check", "stills", "render", "thumbnail", "capture", "record"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _valid(value, label, pattern=_ID):
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise WorkspaceError("invalid", f"Invalid {label}.")
    return value


def _options(options, allowed):
    if not isinstance(options, dict) or set(options) - set(allowed):
        raise WorkspaceError("invalid", "Unsupported action options.")


def _project(root, slug):
    try:
        return resolve_project(root, slug)
    except ValueError as exc:
        raise WorkspaceError("invalid", str(exc)) from None


def _existing_video(root, slug):
    if not _project(root, slug).is_dir():
        raise WorkspaceError("missing", f"Video {slug} does not exist.")


def build_argv(root, action, slug, options):
    root = Path(root)
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9_][a-z0-9_-]*(?:/[a-z0-9_][a-z0-9_-]*)?", slug):
        raise WorkspaceError("invalid", "Invalid video id.")
    if action in {"new", "native-render"}:
        _valid(slug, "video slug")
    if action == "native-render":
        _options(options, {"variant", "view", "action", "expression"})
        variant = _valid(options.get("variant"), "variant")
        view = options.get("view")
        if view not in ("front", "three-quarter-right"):
            raise WorkspaceError("invalid", "Unknown native view.")
        motion = _valid(options.get("action"), "native action")
        expression = _valid(options.get("expression"), "native expression")
        return [str(root / ".venv/bin/python"), "-m", "studio.native_pipeline", "render",
                str(root), slug, variant, view, motion, expression]
    _options(options, {
        "brand", "format", "style", "style_id", "brief", "confirmation_fingerprint", "language", "model", "replace",
        "provider", "query", "ref", "type", "orientation", "limit", "name", "start", "end",
        "url", "breakpoint", "steps",
    })
    python = [str(root / ".venv/bin/python"), str(root / "anim.py")]
    if action == "new":
        _options(options, {"brand", "format", "style", "style_id", "brief"})
        from studio.workspace import check_brand
        brand = check_brand(root, options.get("brand"), options.get("style", "modern"))
        fmt, style = options.get("format", "wide"), options.get("style", "modern")
        if fmt not in ("wide", "tall") or style != "modern":
            raise WorkspaceError("invalid", "Unknown video format or base style.")
        if options.get("style_id") is not None: _valid(options["style_id"], "style id")
        brief = options.get("brief")
        if not isinstance(brief, dict) or any(not str(brief.get(k, "")).strip() for k in ("audience", "video_type", "language", "outcome")):
            raise WorkspaceError("invalid", "Audience, video type, language and outcome are required.")
        return python + ["new", slug, "--brand", brand, "--format", fmt, "--style", style]
    simple = {"research-init": ["research", slug], "voice-check": ["speak", slug, "--check"],
              "voice-test": ["speak", slug, "--chunk", "1"], "voice": ["speak", slug],
              "cues": ["cues", slug], "check": ["check", slug], "stills": ["stills", slug],
              "render": ["render", slug, "--workers", "1"], "thumbnail": ["thumbnail", slug]}
    if action in simple:
        allowed = {"voice-test": {"confirmation_fingerprint"}, "voice": {"confirmation_fingerprint"},
                   "transcribe": {"language", "model", "replace"}}.get(action, set())
        _options(options, allowed)
        args = python + simple[action]
        if action in {"voice", "voice-test"}:
            confirmation = options.get("confirmation_fingerprint")
            if not isinstance(confirmation, str) or not re.fullmatch(r"[0-9a-f]{64}", confirmation):
                raise WorkspaceError("invalid", "Paid voice needs the current confirmation fingerprint.")
            args += ["--confirm-script", confirmation]
        return args
    if action == "transcribe":
        _options(options, {"language", "model", "replace"})
        language, model = options.get("language", "en"), options.get("model", "large-v3")
        if language not in ("en", "nl") or model not in ("tiny", "base", "small", "medium", "large-v3", "large-v3-turbo") or type(options.get("replace", False)) is not bool:
            raise WorkspaceError("invalid", "Unsupported transcription language or model.")
        return python + ["transcribe", slug, "--language", language, "--model", model] + (["--force"] if options.get("replace") is True else [])
    if action == "stock-search":
        _options(options, {"provider", "query", "type", "orientation", "limit"})
        provider, query = options.get("provider"), options.get("query")
        if provider not in ("pexels", "pixabay", "unsplash", "openverse", "all") or not isinstance(query, str) or not query.strip() or len(query) > 200:
            raise WorkspaceError("invalid", "Choose a provider and short search query.")
        args = python + ["stock", "search", provider, query]
        if options.get("type"):
            if options["type"] not in ("video", "photo", "audio"): raise WorkspaceError("invalid", "Unsupported stock type.")
            args += ["--type", options["type"]]
        if options.get("orientation"):
            if options["orientation"] not in ("landscape", "portrait"): raise WorkspaceError("invalid", "Unsupported orientation.")
            args += ["--orientation", options["orientation"]]
        if "limit" in options:
            if type(options["limit"]) is not int or not 1 <= options["limit"] <= 50:
                raise WorkspaceError("invalid", "Stock search limit must be 1–50.")
            args += ["--limit", str(options["limit"])]
        return args
    if action == "stock-get":
        _options(options, {"ref"})
        ref = options.get("ref", "")
        if not isinstance(ref, str) or not re.fullmatch(r"stock:(pexels|pixabay|unsplash|openverse)/(video|photo|audio)/[A-Za-z0-9_-]+", ref):
            raise WorkspaceError("invalid", "Invalid stock reference.")
        return python + ["stock", "get", ref]
    if action == "use":
        _options(options, {"ref", "name", "start", "end"})
        ref = options.get("ref", "")
        if not isinstance(ref, str) or not re.fullmatch(r"(?:icon|graphic|lottie|stock):[A-Za-z0-9_./-]+", ref):
            raise WorkspaceError("invalid", "Invalid library reference.")
        args = python + ["use", slug, ref]
        if options.get("name"):
            args += ["--as", _valid(options["name"], "asset name")]
        if ref.startswith("stock:") and "/video/" in ref:
            if "start" not in options or "end" not in options: raise WorkspaceError("invalid", "Footage needs start and end times.")
            try: start, end = float(options["start"]), float(options["end"])
            except (TypeError, ValueError): raise WorkspaceError("invalid", "Invalid footage interval.") from None
            if not (0 <= start < end <= 36000): raise WorkspaceError("invalid", "Invalid footage interval.")
            args += ["--start", str(start), "--end", str(end)]
        return args
    if action in ("capture", "record"):
        _options(options, {"url", "name", "breakpoint"} if action == "capture" else {"name", "breakpoint", "steps"})
        name = _valid(options.get("name"), "capture name")
        bp = options.get("breakpoint", "laptop")
        if bp not in ("mobile", "tablet", "laptop", "desktop"):
            raise WorkspaceError("invalid", "Unknown breakpoint.")
        if action == "capture":
            from urllib.parse import urlsplit
            url = options.get("url", "")
            parsed = urlsplit(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password:
                raise WorkspaceError("invalid", "Capture URL must be public HTTP or HTTPS.")
            return python + ["grab", slug, url, name, "--bp", bp]
        steps = options.get("steps", "")
        if not isinstance(steps, str) or not steps.startswith(f"videos/{slug}/") or not re.fullmatch(r"videos/[a-z0-9-]+/[A-Za-z0-9_./-]+", steps) or ".." in steps:
            raise WorkspaceError("invalid", "Invalid steps file.")
        if not safe_path(root, steps).is_file():
            raise WorkspaceError("missing", "Capture steps file is missing.")
        return python + ["record", slug, name, steps, "--bp", bp]
    raise WorkspaceError("invalid", "Unsupported production action.")


def _record_path(root, shelf, key):
    _valid(key, "record id", _KEY)
    return Path(root) / ".studio" / shelf / f"{key}.json"


def _save(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temp.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _read(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or value.get("id") != path.stem:
            raise ValueError("record mismatch")
        return value
    except (OSError, ValueError, TypeError):
        raise WorkspaceError("io", "Stored studio record is unreadable.")


def _secret_values(root):
    values = []
    env = Path(root) / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                value = line.split("=", 1)[1].strip().strip('"\'')
                if len(value) >= 6: values.append(value)
    return values


def _voice_ready(root, slug):
    try:
        snapshot = json.loads((_project(root, slug) / "settings.json").read_text(encoding="utf-8"))
        fields = snapshot.get("voice", {})
    except (OSError, ValueError):
        return False
    if any(not fields.get(key) or fields[key].startswith("YOUR_") for key in ("voice_id", "model")):
        return False
    if os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("ELEVEN_API_KEY"):
        return True
    env = Path(root) / ".env"
    if not env.is_file(): return False
    return any(re.match(r"\s*(?:ELEVENLABS_API_KEY|ELEVEN_API_KEY)\s*=\s*\S+", line) for line in env.read_text(encoding="utf-8").splitlines())


def _omabox_env():
    env = os.environ.copy()
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    return env


def _contained_browser():
    """Start a private browser box; the host renderer writes the actual project outputs."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = _omabox_env()
    launched = subprocess.run(["omabox", "up", "--new", "--idle", "0"], env=env,
                              capture_output=True, text=True, timeout=45)
    if launched.returncode:
        raise WorkspaceError("blocked", "Contained browser could not start. Check omabox availability.")
    name = launched.stdout.strip().splitlines()[-1]
    if not re.fullmatch(r"box-[0-9]+", name):
        raise WorkspaceError("io", "Contained browser returned an invalid box id.")
    try:
        started = subprocess.run(["omabox", "run", "-b", name, "-d", "--", "chromium", "--no-first-run",
                                  "--no-default-browser-check", "--remote-debugging-address=127.0.0.1",
                                  f"--remote-debugging-port={port}", "--user-data-dir=/home/sbx/studio-cdp", "about:blank"],
                                 env=env, capture_output=True, text=True, timeout=20)
        if started.returncode:
            raise WorkspaceError("blocked", "Chromium could not start in the contained desktop.")
        from urllib.request import urlopen
        endpoint = f"http://127.0.0.1:{port}"
        for _ in range(50):
            try:
                with urlopen(endpoint + "/json/version", timeout=1) as response:
                    if json.load(response).get("webSocketDebuggerUrl"):
                        return name, endpoint
            except (OSError, ValueError):
                time.sleep(0.1)
        raise WorkspaceError("blocked", "Contained Chromium debugging endpoint did not become ready.")
    except Exception:
        _stop_box(name)
        raise


def _stop_box(name):
    subprocess.run(["omabox", "down", "-b", name], env=_omabox_env(),
                   capture_output=True, text=True, timeout=20)


def _run_job(root, job_id):
    try:
        with production_lock(root, "studio-job:" + job_id):
            return _run_job_locked(root, job_id)
    except ValueError as exc:
        path = _record_path(root, "jobs", job_id)
        record = _read(path)
        record.update(state="failed", error=str(exc), finished_at=_now())
        _save(path, record)


def _run_job_locked(root, job_id):
    root = Path(root)
    path = _record_path(root, "jobs", job_id)
    record = _read(path)
    slug, action = record["slug"], record["action"]
    process = None
    gate_to_ready = None
    ready_fingerprint = None
    box = None
    backup = None
    try:
        if record.get("cancel_requested"):
            record.update(state="cancelled", error="Cancelled before start.")
            return
        if action == "new":
            from studio.workspace import create_video
            create_video(root, slug, record["options"]["brief"], record["options"].get("format", "wide"),
                         record["options"].get("style", "modern"), record["options"].get("style_id"), brand=record["options"]["brand"])
            record.update(state="succeeded", exit_code=0, outputs=[f"videos/{record['options']['brand']}/{slug}/01_voice/brief.md"])
            return
        with production_lock(root, "studio-job:" + job_id), workspace_lock(root, blocking=False):
            current = _read(path)
            if current.get("state") not in ("queued", "running", "cancelling"):
                return
            if current.get("cancel_requested"):
                record.update(state="cancelled", cancel_requested=True, error="Cancelled before start.")
                return
            if action == "native-render":
                from studio.creative import creative_review_state
                native_gate = creative_review_state(root, "character", slug, "rig:" + record["options"]["variant"])
                if native_gate["state"] != "approved":
                    raise WorkspaceError("blocked", "Current native rig review is not approved.")
                if native_gate["fingerprint"] != record.get("expected_fingerprint"):
                    raise WorkspaceError("conflict", "Native rig inputs changed after this job was queued.")
            gate = {"voice": "script", "voice-test": "script", "transcribe": "voice", "cues": "transcript",
                    "check": "cues", "stills": "cues", "render": "scene"}.get(action)
            if gate and review_state(root, slug, gate)["state"] not in GATE_PASSED:
                raise WorkspaceError("blocked", f"Current {gate} review is no longer approved.")
            if gate and record.get("expected_fingerprint") and gate_fingerprint(root, slug, gate) != record["expected_fingerprint"]:
                raise WorkspaceError("conflict", "Production inputs changed after this job was queued.")
            if action in ("voice", "voice-test") and record["options"].get("confirmation_fingerprint") != gate_fingerprint(root, slug, "script"):
                raise WorkspaceError("blocked", "Paid voice confirmation no longer matches the current script.")
            with _GUARD:
                if _read(path).get("cancel_requested"):
                    record.update(state="cancelled", cancel_requested=True, error="Cancelled before start.")
                    return
                record.update(state="running", started_at=_now())
                _save(path, record)
            argv = build_argv(root, action, slug, record["options"])
            started_ns = time.time_ns()
            if action == "render":
                prior = _project(root, slug) / "05_render" / f"{Path(slug).name}.mp4"
                if prior.is_file():
                    backup = path.with_suffix(".previous.mp4")
                    shutil.copy2(prior, backup)
            env = os.environ | child_environment(root)
            if action in _BROWSER_ACTIONS:
                box, endpoint = _contained_browser()
                _BOXES[(str(root.resolve()), job_id)] = box
                record["box"] = box
                _save(path, record)
                env["ANIM_CDP_URL"] = endpoint
            if _read(path).get("cancel_requested"):
                record.update(state="cancelled", cancel_requested=True, error="Cancelled before process start.")
                return
            process = subprocess.Popen(argv, cwd=root, shell=False, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, start_new_session=True, text=True, env=env, pass_fds=lease_fds())
            record["pid"] = process.pid
            record["process_start"] = _process_start(process.pid)
            with _GUARD:
                _PROCESSES[(str(root.resolve()), job_id)] = process
                if _read(path).get("cancel_requested"):
                    record["cancel_requested"] = True
                _save(path, record)
            if record.get("cancel_requested"):
                _terminate(process)
            log = path.with_suffix(".log")
            secrets = _secret_values(root)
            size = 0
            with log.open("w", encoding="utf-8") as stream:
                for line in process.stdout:
                    for secret in secrets: line = line.replace(secret, "[redacted]")
                    line = line.replace(str(root), "<workspace>")
                    data = line.encode("utf-8")
                    if size < 1_048_576:
                        stream.write(data[:1_048_576 - size].decode("utf-8", errors="ignore"))
                        size += min(len(data), 1_048_576 - size)
                    record["progress"] = line.strip()[:300]
                    with _GUARD:
                        if not _read(path).get("cancel_requested"):
                            _save(path, record)
                    if _read(path).get("cancel_requested"):
                        _terminate(process)
                        break
            code = process.wait()
            process.stdout.close()
            record["cancel_requested"] = _read(path).get("cancel_requested", False)
            record["exit_code"] = code
            if record.get("cancel_requested"):
                record.update(state="cancelled", error="Cancelled; partial outputs are incomplete.")
            elif code:
                record.update(state="failed", error=f"{action} exited with status {code}; partial outputs are incomplete.")
            else:
                outputs = _job_outputs(root, slug, action, record["options"], started_ns, log=path.with_suffix(".log"))
                if outputs is None:
                    record.update(state="failed", error=f"{action} exited successfully but required output is missing or incomplete.")
                else:
                    record.update(state="succeeded", outputs=outputs)
                    gate_to_ready = {"voice-test": "voice-test", "voice": "voice", "transcribe": "transcript",
                                     "cues": "cues", "stills": "scene", "render": "render"}.get(action)
                    if gate_to_ready and action not in ("voice-test", "voice"):
                        ready_fingerprint = gate_fingerprint(root, slug, gate_to_ready)
        if record["state"] == "succeeded" and action in ("voice-test", "voice"):
            from studio.workspace import set_voice_selection
            key = "voice_test" if action == "voice-test" else "voice"
            voice_path = "01_voice/takes/01.mp3" if action == "voice-test" else "01_voice/voice.mp3"
            if not (_project(root, slug) / voice_path).is_file():
                record.update(state="failed", error=f"{action} exited successfully but expected audio is missing.")
            else:
                set_voice_selection(root, slug, key, voice_path, gate_fingerprint(root, slug, "script"))
        if gate_to_ready and record["state"] == "succeeded":
            try:
                if ready_fingerprint is None:
                    ready_fingerprint = gate_fingerprint(root, slug, gate_to_ready)
                mark_ready(root, slug, gate_to_ready, ready_fingerprint)
            except WorkspaceError as error:
                record.update(state="failed", error=f"Output needs review preparation: {error}")
    except WorkspaceError as error:
        record.update(state="failed", error=str(error))
    except Exception:
        record.update(state="failed", error=f"Could not complete {action}; partial outputs are incomplete.")
    finally:
        if backup:
            prior = _project(root, slug) / "05_render" / f"{Path(slug).name}.mp4"
            try:
                if record["state"] != "succeeded": os.replace(backup, prior)
                else: backup.unlink(missing_ok=True)
            except OSError:
                record["error"] = (record.get("error") or "") + " Previous export could not be restored."
        if box:
            try: _stop_box(box)
            except (OSError, subprocess.TimeoutExpired): pass
        with _GUARD:
            if _read(path).get("cancel_requested") and record["state"] not in {"cancelled", "interrupted"}:
                record.update(state="cancelled", cancel_requested=True, error="Cancelled; partial outputs are incomplete.")
            record["finished_at"] = _now()
            _save(path, record)
            _PROCESSES.pop((str(root.resolve()), job_id), None)
            _THREADS.pop((str(root.resolve()), job_id), None)
            _BOXES.pop((str(root.resolve()), job_id), None)


def _job_outputs(root, slug, action, options, started_ns, log=None):
    if action == "native-render":
        from studio.native_pipeline import render_status
        result = render_status(root, slug, options["variant"], options["view"], options["action"], options["expression"])
        clip = result.get("clip")
        if not result["current"] or not clip:
            return None
        return [clip["preview"], clip["path"] + "/render.json"]
    video = _project(root, slug)
    exact = {
        "research-init": [video / "00_research/research.md", video / "00_research/sources.md"],
        "voice-test": [video / "01_voice/takes/01.mp3", video / "01_voice/takes/01.txt", video / "01_voice/takes/01.json"],
        "voice": [video / "01_voice/voice.mp3"],
        "transcribe": [video / "02_transcript/words.json", video / "02_transcript/transcript.md"],
        "cues": [video / "03_cues/cues.json", video / "03_cues/cues.js"],
        "check": [video / "05_render/check.md"],
        "stills": [video / "05_render/contact.html", video / "05_render/contact.png"],
        "render": [video / "05_render" / f"{Path(slug).name}.mp4", video / "05_render/check-video.md"],
        "use": [video / "04_scene/assets/library.md"],
    }
    paths = exact.get(action, [])
    if action == "thumbnail": paths = list((video / "05_render").glob("thumbnail-*.png"))
    if action == "capture": paths = [video / "04_scene/assets" / (options["name"] + ".png")]
    if action == "record": paths = [video / "04_scene/assets/real.js"]
    if action == "stills" and not list((video / "05_render/stills").glob("*.png")):
        return None
    if action in ("thumbnail", "record") and not paths:
        return None
    if any(not p.is_file() or p.stat().st_size == 0 or (action != "research-init" and p.stat().st_mtime_ns < started_ns) for p in paths):
        return None
    return [p.relative_to(root).as_posix() for p in paths]


def _terminate(process):
    try: os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError: return
    try: process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try: os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        process.wait()


def _process_start(pid):
    try: return Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()[19]
    except (OSError, IndexError): return None


def start_job(root, action, slug, options, expected_fingerprint, request_id):
    root = Path(root)
    _valid(request_id, "request id", _KEY)
    if action not in {"new", "native-render"}:
        slug = project_id(root, _project(root, slug))
    path = _record_path(root, "jobs", request_id)
    if path.exists():
        old = _read(path)
        if (old.get("action"), old.get("slug"), old.get("options"), old.get("expected_fingerprint")) != (action, slug, options, expected_fingerprint):
            raise WorkspaceError("conflict", "Request id was already used for another job.")
        return old
    build_argv(root, action, slug, options)
    if action == "native-render":
        from studio.creative import creative_review_state
        from studio.native_pipeline import render_status
        native_gate = creative_review_state(root, "character", slug, "rig:" + options["variant"])
        if native_gate["state"] != "approved":
            raise WorkspaceError("blocked", "Approve the current native rig before rendering actions.")
        if expected_fingerprint != native_gate["fingerprint"]:
            raise WorkspaceError("conflict", "Native rig revision changed; reload the page.")
        status = render_status(root, slug, options["variant"], options["view"], options["action"], options["expression"])
        if status["error"]:
            raise WorkspaceError("blocked", status["error"])
    elif action != "new":
        slug = project_id(root, _project(root, slug))
        _existing_video(root, slug)
    if action in ("voice", "voice-test"):
        current = gate_fingerprint(root, slug, "script")
        if options.get("confirmation_fingerprint") != current or expected_fingerprint != current:
            raise WorkspaceError("blocked", "Paid voice generation needs confirmation for the current script.")
    gate = {"voice": "script", "voice-test": "script", "transcribe": "voice", "cues": "transcript",
            "check": "cues", "stills": "cues", "render": "scene"}.get(action)
    if gate and review_state(root, slug, gate)["state"] not in GATE_PASSED:
        raise WorkspaceError("blocked", f"Approve the current {gate} review before {action}.")
    if action == "voice" and review_state(root, slug, "voice-test")["state"] not in {"approved", "not-applicable"}:
        raise WorkspaceError("blocked", "Approve the test take before full voice generation.")
    if action in ("cues",) and not (_project(root, slug) / "03_cues" / "cues.md").is_file():
        raise WorkspaceError("blocked", "Write cues.md before compiling cues.")
    if action in ("check", "stills", "render") and not (_project(root, slug) / "04_scene" / "scene.js").is_file():
        raise WorkspaceError("blocked", "Write scene.js before this action.")
    if action == "thumbnail" and not (_project(root, slug) / "04_scene" / "thumbnail.js").is_file():
        raise WorkspaceError("blocked", "Write thumbnail.js first.")
    if action == "render" and not (_project(root, slug) / "05_render" / "check.md").is_file():
        raise WorkspaceError("blocked", "Run scene checks before render.")
    if action == "transcribe" and (_project(root, slug) / "02_transcript" / "words.json").exists() and options.get("replace") is not True:
        raise WorkspaceError("blocked", "Existing timings need explicit replacement confirmation.")
    if action != "new" and not (root / ".venv/bin/python").is_file():
        raise WorkspaceError("blocked", "Workspace virtualenv is unavailable.")
    if action in ("voice-check", "voice-test", "voice") and not _voice_ready(root, slug):
        raise WorkspaceError("blocked", "Configure the voice model and ElevenLabs key before this action.")
    if action in _BROWSER_ACTIONS and (not shutil.which("omabox") or not shutil.which("chromium")):
        raise WorkspaceError("blocked", "Contained browser tools are unavailable.")
    if action in ("render", "record", "transcribe", "voice", "voice-test", "native-render") and not shutil.which("ffmpeg"):
        raise WorkspaceError("blocked", "FFmpeg is unavailable.")
    with _GUARD:
        with workspace_lock(root, blocking=False):
            if path.exists():
                old = _read(path)
                if (old.get("action"), old.get("slug"), old.get("options"), old.get("expected_fingerprint")) != (action, slug, options, expected_fingerprint):
                    raise WorkspaceError("conflict", "Request id was already used for another job.")
                return old
            for old in list_jobs(root):
                if old.get("state") in _ACTIVE:
                    raise WorkspaceError("busy", f"Production is active for {old.get('slug', 'another video')}.")
            if any(r.get("state") == "running" for r in list_requests(root)):
                raise WorkspaceError("busy", "An agent is already working on a video.")
            record = {"id": request_id, "slug": slug, "action": action, "options": options,
                      "expected_fingerprint": expected_fingerprint,
                      "state": "queued", "created_at": _now(), "pid": None, "exit_code": None,
                      "outputs": [], "error": None, "progress": None}
            _save(path, record)
        thread = threading.Thread(target=_run_job, args=(root, request_id), daemon=True)
        _THREADS[(str(root.resolve()), request_id)] = thread
        thread.start()
        return record


def list_jobs(root):
    directory = Path(root) / ".studio/jobs"
    records = []
    for path in sorted(directory.glob("*.json")):
        try: records.append(_read(path))
        except WorkspaceError: continue
    return sorted(records, key=lambda r: r.get("created_at", ""), reverse=True)


def job_detail(root, job_id):
    path = _record_path(root, "jobs", job_id)
    if not path.exists(): raise WorkspaceError("missing", "Job not found.")
    record = _read(path)
    log = path.with_suffix(".log")
    record["log"] = log.read_text(encoding="utf-8", errors="replace")[-1_048_576:] if log.exists() else ""
    return record


def cancel_job(root, job_id):
    root = Path(root)
    path = _record_path(root, "jobs", job_id)
    with _GUARD:
        if not path.exists(): raise WorkspaceError("missing", "Job not found.")
        record = _read(path)
        if record["state"] not in _ACTIVE: return record
        record["cancel_requested"] = True
        record["state"] = "cancelling"
        _save(path, record)
        process = _PROCESSES.get((str(root.resolve()), job_id))
    if process: _terminate(process)
    elif isinstance(record.get("pid"), int) and record.get("process_start") and _process_start(record["pid"]) == record["process_start"]:
        try: os.killpg(record["pid"], signal.SIGTERM)
        except ProcessLookupError: pass
        deadline = time.monotonic() + 5
        while _process_start(record["pid"]) == record["process_start"] and time.monotonic() < deadline:
            time.sleep(.05)
        if _process_start(record["pid"]) == record["process_start"]:
            try: os.killpg(record["pid"], signal.SIGKILL)
            except ProcessLookupError: pass
    return job_detail(root, job_id)


def recover_jobs(root):
    try:
        with workspace_lock(root, blocking=False):
            for record in list_jobs(root):
                if record.get("state") not in _ACTIVE: continue
                local = _THREADS.get((str(Path(root).resolve()), record["id"]))
                if local and local.is_alive(): continue
                pid = record.get("pid")
                owned = isinstance(pid, int) and record.get("process_start") and _process_start(pid) == record["process_start"]
                if owned:
                    try: os.killpg(pid, signal.SIGTERM)
                    except ProcessLookupError: pass
                    deadline = time.monotonic() + 5
                    while _process_start(pid) == record["process_start"] and time.monotonic() < deadline:
                        time.sleep(.05)
                    if _process_start(pid) == record["process_start"]:
                        try: os.killpg(pid, signal.SIGKILL)
                        except ProcessLookupError: pass
                if owned and isinstance(record.get("box"), str) and re.fullmatch(r"box-[0-9]+", record["box"]):
                    try: _stop_box(record["box"])
                    except (OSError, subprocess.TimeoutExpired): pass
                record.update(state="interrupted", error="Server stopped; partial outputs are incomplete.", finished_at=_now())
                _save(_record_path(root, "jobs", record["id"]), record)
    except WorkspaceError as error:
        if error.code != "busy": raise


def create_request(root, slug, kind, instructions, fingerprint, request_id, *, subject=None, input_revision=None):
    root = Path(root)
    _valid(request_id, "request id", _KEY)
    creative_kinds = {"style-discovery": "style", "style-development": "style", "website-reference": "style",
                      "creative-material": None, "character-discovery": "character", "character-concepts": "character",
                      "character-identity": "character", "character-animation": "character"}
    if kind not in ("research", "script", "cues", "scene", "review-checks", "style-template", "material") and kind not in creative_kinds:
        raise WorkspaceError("invalid", "Unsupported agent request.")
    if not isinstance(instructions, str) or not instructions.strip() or len(instructions) > 20000:
        raise WorkspaceError("invalid", "Agent instructions are required.")
    if kind in creative_kinds:
        if not isinstance(subject, dict) or subject.get("type") not in ({"style", "character"} if kind == "creative-material" else {creative_kinds[kind]}) or set(subject) != {"type", "id"}:
            raise WorkspaceError("invalid", "Creative request needs a typed subject.")
        _valid(subject["id"], "creative id")
        from studio.creative import creative_fingerprint
        gate = {"style-discovery": "brief", "style-development": "brief", "website-reference": "materials",
                "creative-material": "brief", "character-discovery": "brief", "character-concepts": "brief",
                "character-identity": "design", "character-animation": "identity"}[kind]
        if kind == "creative-material" and subject["type"] == "style": gate = "materials"
        if input_revision != creative_fingerprint(root, subject["type"], subject["id"], gate):
            raise WorkspaceError("conflict", "Creative request inputs changed.")
    else:
        if kind not in ("style-template", "material"):
            slug = project_id(root, _project(root, slug))
        else:
            _valid(slug, "video slug")
        if subject is not None or input_revision is not None: raise WorkspaceError("invalid", "Legacy request does not use a creative subject.")
        if kind not in ("style-template", "material"): _existing_video(root, slug)
    path = _record_path(root, "requests", request_id)
    if path.exists():
        old = _read(path)
        if (old.get("slug"), old.get("kind"), old.get("instructions"), old.get("fingerprint"), old.get("subject"), old.get("input_revision")) != (slug, kind, instructions, fingerprint, subject, input_revision):
            raise WorkspaceError("conflict", "Request id was already used.")
        return old
    record = {"id": request_id, "kind": kind, "instructions": instructions,
              "state": "waiting-for-agent", "created_at": _now(),
              "handoff": "Waiting for a workspace agent to claim this request."}
    if subject is None: record.update(slug=slug, fingerprint=fingerprint)
    else: record.update(subject=subject, input_revision=input_revision)
    _save(path, record)
    return record


def list_requests(root):
    records = []
    for path in sorted((Path(root) / ".studio/requests").glob("*.json")):
        try: records.append(_read(path))
        except WorkspaceError: continue
    return sorted(records, key=lambda r: r.get("created_at", ""), reverse=True)


def claim_request(root, request_id, agent):
    path = _record_path(root, "requests", request_id)
    if not path.exists(): raise WorkspaceError("missing", "Agent request not found.")
    record = _read(path)
    if record["state"] != "waiting-for-agent": raise WorkspaceError("conflict", "Request is already claimed or finished.")
    if not isinstance(agent, str) or not agent.strip(): raise WorkspaceError("invalid", "Agent name is required.")
    if record.get("subject"):
        from studio.creative import creative_fingerprint
        kind = record["kind"]
        gate = {"style-discovery": "brief", "style-development": "brief", "website-reference": "materials",
                "creative-material": "brief", "character-discovery": "brief", "character-concepts": "brief",
                "character-identity": "design", "character-animation": "identity"}[kind]
        subject = record["subject"]
        if kind == "creative-material" and subject["type"] == "style": gate = "materials"
        if record["input_revision"] != creative_fingerprint(root, subject["type"], subject["id"], gate):
            raise WorkspaceError("conflict", "Request inputs changed before claim.")
    if record.get("fingerprint"):
        gate = {"research": "research", "script": "brief", "cues": "transcript", "scene": "cues"}.get(record["kind"])
        if gate and record["fingerprint"] != gate_fingerprint(root, record["slug"], gate):
            raise WorkspaceError("conflict", "Request inputs changed before claim.")
    with _GUARD:
        with workspace_lock(root, blocking=False):
            if any(r.get("state") in _ACTIVE for r in list_jobs(root)) or any(r.get("state") == "running" for r in list_requests(root)):
                raise WorkspaceError("busy", "Another video is under active production work.")
            record.update(state="running", agent=agent.strip(), claimed_at=_now(), handoff="Claimed by a workspace agent.")
            _save(path, record)
    return record


def validate_request_output(root, record):
    if not record.get("subject") and record.get("kind") in {"script", "cues", "scene"}:
        kind = record["kind"]
        input_gate = {"script": "brief", "cues": "transcript", "scene": "cues"}[kind]
        if record.get("fingerprint") != gate_fingerprint(root, record["slug"], input_gate):
            raise WorkspaceError("conflict", "Request inputs changed while the agent worked.")
        output = review_state(root, record["slug"], kind)
        if not output.get("ready") or output.get("state") not in {"awaiting-review", "approved"}:
            raise WorkspaceError("blocked", "The current output must pass its checks and be marked ready.")


def finish_request(root, request_id, result):
    path = _record_path(root, "requests", request_id)
    if not path.exists(): raise WorkspaceError("missing", "Agent request not found.")
    record = _read(path)
    if record["state"] != "running": raise WorkspaceError("conflict", "Request is not claimed.")
    if isinstance(result, str): result = {"state": result}
    if not isinstance(result, dict) or result.get("state") not in ("succeeded", "failed", "cancelled"):
        raise WorkspaceError("invalid", "Request result must be succeeded, failed or cancelled.")
    if result["state"] == "succeeded":
        validate_request_output(root, record)
    outputs = result.get("outputs", [])
    if not isinstance(outputs, list) or len(outputs) > 100 or any(not isinstance(item, str) for item in outputs):
        raise WorkspaceError("invalid", "Request outputs must be workspace paths.")
    for item in outputs: safe_path(root, item)
    record.update(state=result["state"], note=str(result.get("note", ""))[:2000],
                  outputs=outputs, finished_at=_now())
    _save(path, record)
    return record


_MANAGED = {}

def managed_runs(root, video_id):
    video_id = project_id(root, _project(root, video_id))
    records = []
    for path in (Path(root) / ".studio/runs").glob("*.json"):
        record = _read(path)
        if record.get("video_id") == video_id:
            records.append(record)
    return records


def start_managed_run(root, video_id, settings=None, resume=None):
    """Save explicit choices before any unattended work starts."""
    from studio.autonomous import run_video, validate_settings
    root = Path(root)
    project = _project(root, video_id)
    video_id = project_id(root, project)
    try:
        if resume:
            _valid(resume, "run id", re.compile(r"[a-f0-9]{32}\Z"))
            prior = _read(root / ".studio/runs" / (resume + ".json"))
            if prior.get("video_id") != video_id:
                raise WorkspaceError("invalid", "This run belongs to another video.")
            saved = validate_settings(prior["settings"])
        else:
            saved = validate_settings(settings)
        if saved["brand"] != json.loads((project / "project.json").read_text())["brand"]:
            raise WorkspaceError("invalid", "Run brand differs from project brand.")
    except ValueError as exc:
        raise WorkspaceError("invalid", str(exc)) from None
    with _GUARD:
        key = str(root.resolve())
        active = _MANAGED.get(key)
        if active and active.is_alive():
            raise WorkspaceError("busy", "A managed run is already active.")
        ready, result = threading.Event(), {}
        def worker():
            try:
                with production_lock(root, "studio-managed:" + video_id):
                    _save(project / "run_settings.json", saved)
                    ready.set()
                    result["run"] = run_video(root, video_id, settings=saved, resume=resume)
            except Exception as exc:
                result["error"] = str(exc)
                ident = uuid.uuid4().hex
                _save(root / ".studio/runs" / (ident + ".json"), {"id": ident, "video_id": video_id,
                      "settings": saved, "status": "failed", "error": str(exc), "stages": {}, "builder_id": "builder-" + ident, "repair_rounds": 0, "created_at": _now()})
            finally:
                ready.set()
        thread = threading.Thread(target=worker, daemon=True)
        _MANAGED[key] = thread
        thread.start()
    ready.wait()
    if result.get("error"):
        raise WorkspaceError("blocked", result["error"])
    return {"video_id": video_id, "state": "started", "settings": saved}
