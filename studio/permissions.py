"""Human permission for work within one Studio or chat session."""
from __future__ import annotations

import json
import fcntl
import contextvars
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path

from studio.project_paths import resolve_project

SESSION_QUESTION = "Do I have full permission for this session?"
SESSION_CHOICES = ("full", "each-stage", "selected-stages")
MODES = SESSION_CHOICES
STAGES = ("research", "brief", "script", "voice", "voice-test", "transcript", "cues",
          "scene", "checks", "render", "critic", "package", "concepts", "rig", "variant",
          "materials", "sample", "design", "identity", "animation")
REVIEWABLE_STAGES = ("research", "brief", "script", "voice-test", "voice", "transcript",
                     "cues", "scene", "render", "materials", "sample", "design",
                     "identity", "rig", "animation")
_SESSION_ID = uuid.uuid4().hex
_REQUEST_SESSION = contextvars.ContextVar("vf_permission_session", default=None)
_LOCK = threading.RLock()
_PART = re.compile(r"[a-z0-9_][a-z0-9_-]*\Z")


def current_session(root: Path) -> str:
    """Return the inherited chat ID or this process's stable Studio ID."""
    value = _REQUEST_SESSION.get() or os.environ.get("VF_SESSION_ID") or _SESSION_ID
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Session ID is empty.")
    return value


@contextmanager
def session_context(session_id):
    """Bind one browser request to its interactive session ID."""
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("Session ID is empty.")
    token = _REQUEST_SESSION.set(session_id)
    try:
        yield
    finally:
        _REQUEST_SESSION.reset(token)


def _session(root, session_id):
    inherited = _REQUEST_SESSION.get() or os.environ.get("VF_SESSION_ID")
    if os.environ.get("VF_PERMISSION_WORKER") == "1" and not inherited:
        raise ValueError("A worker must inherit its session.")
    if os.environ.get("VF_PERMISSION_WORKER") == "1" and session_id is not None and session_id != inherited:
        raise ValueError("A worker cannot use another session.")
    value = current_session(root) if session_id is None else session_id
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Session ID is empty.")
    return value


def _scope_path(root, scope):
    root = Path(root).resolve()
    if not isinstance(scope, str) or ":" not in scope:
        raise ValueError("Use a named video, brand, style, or character scope.")
    kind, identity = scope.split(":", 1)
    if kind == "video":
        parts = identity.split("/")
        if len(parts) != 2 or any(not _PART.fullmatch(part) for part in parts):
            raise ValueError("Use a canonical brand/slug video ID.")
        brand, slug = parts
        videos = root / "videos"
        brand_dir = videos / brand
        project = brand_dir / slug
        if any(path.is_symlink() for path in (videos, brand_dir, project)):
            raise ValueError("Video scope cannot use symbolic links.")
        if project.exists():
            resolve_project(root, identity)
        return brand_dir / ".permissions" / f"{slug}.json"
    if kind not in ("brand", "style", "character") or not _PART.fullmatch(identity):
        raise ValueError("Invalid named scope.")
    folder = {"brand": "brands", "style": "styles", "character": "characters"}[kind]
    parent = root / folder
    base = parent / identity
    if parent.is_symlink() or base.is_symlink() or (base.exists() and not base.is_dir()):
        raise ValueError("Named scope is not a safe folder.")
    return parent / ".permissions" / f"{identity}.json"


def _bound_scope(scope):
    if os.environ.get("VF_PERMISSION_WORKER") == "1" and os.environ.get("VF_PERMISSION_SCOPE") != scope:
        raise ValueError("A worker cannot use another scope.")


def _safe_record(root, path):
    root = Path(root).resolve()
    try:
        parts = path.relative_to(root).parts
    except ValueError as exc:
        raise ValueError("Permission record is outside the workspace.") from exc
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Permission record cannot use symbolic links.")
    if not path.resolve().is_relative_to(root):
        raise ValueError("Permission record is outside the workspace.")


def _events(path):
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("events"), list):
        raise ValueError("Permission record is invalid.")
    for event in data["events"]:
        if not isinstance(event, dict) or event.get("action") not in ("grant", "revoke"):
            raise ValueError("Permission record is invalid.")
        if event["action"] == "grant" and (event.get("mode") not in MODES or
            not isinstance(event.get("grant_id"), str) or not event["grant_id"] or
            not isinstance(event.get("selected_stages"), list) or
            any(stage not in STAGES for stage in event["selected_stages"])):
            raise ValueError("Permission record is invalid.")
    return data["events"]


def _write(path, events):
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps({"events": events}, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def session_state(root, scope, session_id=None) -> dict:
    _bound_scope(scope)
    path = _scope_path(root, scope)
    _safe_record(root, path)
    session = _session(root, session_id)
    state = {"session_id": session, "scope": scope, "mode": None, "grant_id": None,
             "selected_stages": [], "active": False}
    with _LOCK:
        for event in _events(path):
            if event.get("session_id") != session or event.get("scope") != scope:
                continue
            if event.get("action") == "grant":
                state.update(mode=event["mode"], grant_id=event.get("grant_id"),
                             selected_stages=event.get("selected_stages", []), active=True)
            elif event.get("action") == "revoke":
                state.update(mode=None, grant_id=None, selected_stages=[], active=False)
    return state


def _record(root, scope, action, *, session_id, reviewer, mode=None, selected_stages=()):
    if os.environ.get("VF_PERMISSION_WORKER") == "1":
        raise ValueError("A worker cannot change permission.")
    path = _scope_path(root, scope)
    _safe_record(root, path)
    session = _session(root, session_id)
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("A reviewer is required.")
    event = {"action": action, "session_id": session, "scope": scope,
             "reviewer": reviewer, "at": datetime.now(timezone.utc).isoformat()}
    if action == "grant":
        event.update(mode=mode, grant_id=uuid.uuid4().hex, selected_stages=list(selected_stages))
    with _LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        _safe_record(root, path)
        lock_path = path.with_suffix(".lock")
        _safe_record(root, lock_path)
        with lock_path.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            events = _events(path)
            events.append(event)
            _write(path, events)
    return session_state(root, scope, session_id=session)


def grant(root, scope, mode, selected_stages=(), *, session_id=None, reviewer="human") -> dict:
    if mode not in MODES:
        raise ValueError("Select a valid permission mode.")
    if isinstance(selected_stages, str):
        raise ValueError("Selected stages must be a list.")
    selected = tuple(selected_stages)
    if any(stage not in REVIEWABLE_STAGES for stage in selected) or len(set(selected)) != len(selected):
        raise ValueError("Selected stages are invalid.")
    if mode != "selected-stages" and selected:
        raise ValueError("Selected stages require selected-stages mode.")
    if mode == "selected-stages" and not selected:
        raise ValueError("Select at least one stage.")
    return _record(root, scope, "grant", session_id=session_id, reviewer=reviewer,
                   mode=mode, selected_stages=selected)


def revoke(root, scope, *, session_id=None, reviewer="human") -> dict:
    return _record(root, scope, "revoke", session_id=session_id, reviewer=reviewer)


def require_permission(root, scope, stage=None, *, session_id=None) -> dict:
    state = session_state(root, scope, session_id=session_id)
    if not state["active"]:
        raise ValueError("Permission is required for this session and item.")
    if stage is not None and stage not in STAGES:
        raise ValueError("Invalid stage.")
    return state


def needs_review(state, stage) -> bool:
    if not state.get("active") or stage not in STAGES:
        raise ValueError("Active permission and a valid stage are required.")
    return state["mode"] == "each-stage" or (state["mode"] == "selected-stages"
                                              and stage in state["selected_stages"])


def child_environment(root, scope) -> dict[str, str]:
    state = require_permission(root, scope)
    return {"VF_SESSION_ID": state["session_id"], "VF_PERMISSION_WORKER": "1",
            "VF_PERMISSION_SCOPE": scope}
