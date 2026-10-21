"""Safe filesystem state for the local animation studio."""

from __future__ import annotations

import contextlib
import contextvars
import fcntl
import hashlib
import html
import inspect
import json
import math
import os
import re
import shutil
import stat
import tempfile
import uuid
from functools import wraps
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from studio.filehash import file_sha256
from studio.project_paths import iter_projects, project_id
from studio import readcache


ID = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
SHELVES = {"brands", "videos", "_shared", "_runtime", "library", "styles", "characters"}
GATES = ("research", "brief", "script", "voice-test", "voice", "transcript", "cues", "scene", "render")
SILENT_UNUSED_GATES = {"brief", "script", "voice-test", "voice", "transcript"}
BASE_KITS = {"modern"}  # the one built-in kit a style recipe can sit on
PASSED = {"approved", "accepted", "skipped", "not-applicable"}  # upstream states that let the next gate run
TEXT_LIMIT = 2 * 1024 * 1024
MEDIA_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".mp4", ".mov", ".webm", ".mp3", ".wav", ".m4a", ".ogg", ".pdf", ".txt", ".md", ".docx"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mp3", ".wav", ".m4a", ".ogg"}
_REVIEW_CACHE = contextvars.ContextVar("studio_review_cache", default=None)


@contextlib.contextmanager
def read_scope():
    token = _REVIEW_CACHE.set({})
    try:
        yield
    finally:
        _REVIEW_CACHE.reset(token)


def _read_once(function):
    signature = inspect.signature(function)
    @wraps(function)
    def read(*args, **kwargs):
        if _REVIEW_CACHE.get() is None:
            with read_scope():
                return read(*args, **kwargs)
        cache = _REVIEW_CACHE.get()
        values = tuple(signature.bind(*args, **kwargs).arguments.values())
        key = (function, str(Path(values[0]).resolve()), *values[1:])
        if key not in cache:
            cache[key] = function(*args, **kwargs)
        return cache[key]
    return read


class WorkspaceError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _id(value: str) -> str:
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise WorkspaceError("invalid", "Use lowercase letters, digits and hyphens.")
    return value


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_hash(path: Path) -> str:
    return file_sha256(path)


def safe_path(root: Path, relative: str, *, write: bool = False) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or "\x00" in relative:
        raise WorkspaceError("invalid", "Invalid workspace path.")
    parts = PurePosixPath(relative).parts
    if relative.startswith("/") or not parts or parts[0] not in SHELVES or any(p in (".", "..", "_auth") or p.startswith(".") for p in relative.split("/")):
        raise WorkspaceError("invalid", "This path is outside the public workspace.")
    base = Path(root).resolve()
    if parts[0] == "videos" and len(parts) >= 3:
        from studio.project_paths import resolve_project, ProjectPathError
        stage_names = {"00_research", "01_voice", "02_transcript", "03_cues", "04_scene", "05_render", "creative", "style"}
        count = 1 if parts[2] in stage_names or parts[2].endswith((".json", ".md")) else 2
        try:
            project = resolve_project(base, "/".join(parts[1:1 + count]))
            parts = (*project.relative_to(base).parts, *parts[1 + count:])
        except ProjectPathError as exc:
            if "ambiguous" in str(exc) or "differs" in str(exc):
                raise WorkspaceError("invalid", str(exc)) from None
    if parts[0] == "brands":
        public = len(parts) >= 4 and ID.fullmatch(parts[1]) and parts[2] == "library" and Path(parts[-1]).suffix.lower() in (MEDIA_EXTENSIONS | {".js", ".css", ".html", ".svg"})
        if write or not public:
            raise WorkspaceError("invalid", "This brand file is private.")
    if not write and (linked := _scene_link(base, parts)) is not None:
        return linked
    path = base
    for part in parts:
        path = path / part
        if path.is_symlink():
            target = base.joinpath(*parts).resolve()
            try:
                target_parts = target.relative_to(base).parts
            except ValueError:
                target_parts = ()
            if not write and parts[0] == "library" and len(target_parts) >= 4 and target_parts[0] == "brands" and ID.fullmatch(target_parts[1]) and target_parts[2] == "library":
                return safe_path(base, target.relative_to(base).as_posix())
            raise WorkspaceError("invalid", "Cannot access symbolic links in the workspace.")
    if write:
        if not _editable_path(parts):
            raise WorkspaceError("invalid", "This file is generated or read only.")
    return path


SCENE_BRAND_FILES = re.compile(r"(?:tokens\.js|(?:logo|fonts|sound)/[A-Za-z0-9_.-]+)\Z")


def _scene_link(base: Path, parts: tuple[str, ...]) -> Path | None:
    """Read a file through a scene's own runtime/, cues/ or brand/ link (made by `anim.py new`).
    Each link must point at its expected place; brand/ opens only the files a scene shows."""
    if parts[0] != "videos" or "04_scene" not in parts[2:4]:
        return None
    i = parts.index("04_scene", 2)
    if len(parts) < i + 3 or parts[i + 1] not in ("runtime", "cues", "brand"):
        return None
    link, rest = base.joinpath(*parts[:i + 2]), parts[i + 2:]
    if not link.is_symlink():
        return None
    target = link.resolve()
    if parts[i + 1] == "runtime":
        ok = target == base / "_runtime"
    elif parts[i + 1] == "cues":
        ok = target == base.joinpath(*parts[:i], "03_cues") and rest == ("cues.js",)
    else:
        ok = target.parent == base / "brands" and bool(ID.fullmatch(target.name)) and bool(SCENE_BRAND_FILES.fullmatch("/".join(rest)))
    if not ok or any(p in (".", "..") or p.startswith(".") for p in rest):
        raise WorkspaceError("invalid", "Cannot access symbolic links in the workspace.")
    path = target
    for part in rest:
        path = path / part
        if path.is_symlink():
            raise WorkspaceError("invalid", "Cannot access symbolic links in the workspace.")
    return path


def _editable_path(parts: tuple[str, ...]) -> bool:
    name = parts[-1]
    if parts[0] == "videos" and len(parts) >= 4 and ID.fullmatch(parts[1]) and ID.fullmatch(parts[2]) and parts[2] not in {"00_research", "01_voice", "02_transcript", "03_cues", "04_scene", "05_render"}:
        parts = (parts[0], parts[2], *parts[3:])
    if parts[0] == "videos" and len(parts) >= 3 and ID.fullmatch(parts[1]):
        if len(parts) == 3 and name == "materials.md":
            return True
        if len(parts) == 4:
            return (parts[2] == "00_research" and name in {"research.md", "sources.md"}) or \
                   (parts[2] == "01_voice" and name in {"brief.md", "script.md"}) or \
                   (parts[2] == "02_transcript" and name in {"words.json", "transcript.md"}) or \
                   (parts[2] == "03_cues" and name == "cues.md") or \
                   (parts[2] == "04_scene" and name in {"scene.js", "thumbnail.js", "index.html", "thumbnail.html"}) or \
                   (parts[2] == "05_render" and name == "DESCRIPTION.md")
        return parts[2] == "00_research" and len(parts) >= 4 and name.endswith((".md", ".txt"))
    if parts[0] == "styles" and len(parts) >= 3 and ID.fullmatch(parts[1]):
        return name in {"style.md", "materials.md"} or (parts[2] == "01_brief" and len(parts) == 4 and name in {"prompt.md", "answers.json", "brief.md"}) or (parts[2] == "03_sample" and len(parts) >= 5 and parts[3] in {"wide", "tall"} and name.endswith((".js", ".html", ".css", ".md"))) or (parts[2] == "template" and name.endswith((".js", ".html", ".css", ".md")))
    if parts[0] == "characters" and len(parts) >= 3 and ID.fullmatch(parts[1]):
        return name in {"character.md", "materials.md"} or (parts[2] == "01_design" and len(parts) == 4 and name in {"prompt.md", "answers.json", "brief.md"}) or (parts[2] == "03_animation" and len(parts) == 5 and ID.fullmatch(parts[3]) and name in {"assets.json", "rig.json", "motions.json"})
    if parts[:2] == ("library", "materials") and len(parts) == 4 and ID.fullmatch(parts[2]):
        return name == "material.md"
    return False


@contextlib.contextmanager
def workspace_lock(root: Path, blocking: bool = True):
    folder = Path(root) / ".studio"
    folder.mkdir(exist_ok=True)
    with (folder / "workspace.lock").open("a+b") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError:
            raise WorkspaceError("busy", "Another video is under production.") from None
        try:
            yield
        finally:
            readcache.invalidate(root)
            fcntl.flock(stream, fcntl.LOCK_UN)


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".studio-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        raise WorkspaceError("missing", "File does not exist.") from None
    except OSError:
        raise WorkspaceError("io", "Could not read file.") from None


def read_file(root: Path, relative: str) -> dict:
    path = safe_path(root, relative)
    data = _read_bytes(path)
    if len(data) > TEXT_LIMIT:
        raise WorkspaceError("invalid", "This file is too large to edit; download it instead.")
    try:
        value = data.decode("utf-8")
    except UnicodeDecodeError:
        raise WorkspaceError("invalid", "This file is binary; download it instead.") from None
    return {"path": relative, "text": value, "revision": _hash(data), "editable": _editable_path(PurePosixPath(relative).parts)}


def save_text(root: Path, relative: str, text: str, expected_revision: str | None) -> dict:
    path = safe_path(root, relative, write=True)
    parts = PurePosixPath(relative).parts
    owner = Path(root).joinpath(*parts[:3]) if parts[:2] == ("library", "materials") else Path(root).joinpath(*parts[:2]) if len(parts) > 1 else None
    if owner is None or not owner.is_dir():
        raise WorkspaceError("missing", "The owning video, style or material does not exist.")
    if not isinstance(text, str) or len(text.encode("utf-8")) > TEXT_LIMIT:
        raise WorkspaceError("invalid", "Text must be UTF-8 and no larger than 2 MiB.")
    if relative.endswith("/02_transcript/words.json"):
        try:
            data = json.loads(text)
            duration = data["duration"]
            words = data["words"]
            valid = (isinstance(duration, (int, float)) and not isinstance(duration, bool) and math.isfinite(duration) and duration > 0 and
                     isinstance(words, list) and all(isinstance(w, dict) and isinstance(w.get("text"), str) and w["text"].strip() and
                     all(isinstance(w.get(k), (int, float)) and not isinstance(w[k], bool) and math.isfinite(w[k]) for k in ("start", "end")) and
                     0 <= w["start"] < w["end"] <= duration for w in words))
        except (ValueError, TypeError, KeyError):
            valid = False
        if not valid:
            raise WorkspaceError("invalid", "Word timings need finite start/end values within the audio duration.")
    with workspace_lock(root):
        current = path.read_bytes() if path.exists() else None
        if expected_revision != (_hash(current) if current is not None else None):
            raise WorkspaceError("conflict", "File changed since you opened it.")
        try:
            _atomic_write(path, text.encode("utf-8"))
        except OSError:
            raise WorkspaceError("io", "Could not save file; the original is unchanged.") from None
    return read_file(root, relative)


def _slug_path(root: Path, slug: str) -> Path:
    from studio.project_paths import resolve_project
    try:
        return resolve_project(root, slug)
    except ValueError as exc:
        raise WorkspaceError("invalid", str(exc)) from None


def _video_id(root, slug):
    from studio.project_paths import project_id
    return project_id(root, _slug_path(root, slug))


def list_videos(root: Path, *, summary=False) -> list[dict]:
    if summary:
        return readcache.cached(root, "videos", lambda: _video_summaries(root))
    from studio.project_paths import iter_projects, project_id
    result = []
    for folder in iter_projects(root):
        try:
            result.append(video_detail(root, project_id(root, folder)))
        except WorkspaceError as exc:
            result.append({"slug": folder.name, "title": folder.name.replace("-", " ").title(), "error": str(exc), "label": "Needs attention"})
    return result


def _video_summaries(root):
    from studio.project_paths import iter_projects, project_id
    rows = []
    for folder in iter_projects(root):
        ident = project_id(root, folder)
        try:
            rows.append(video_detail(root, ident, summary=True))
        except WorkspaceError as exc:
            rows.append({"slug": ident, "video_id": ident, "title": folder.name, "error": str(exc), "reviews": {}})
    return rows


def _review_summary(gate, events, *, applicable=True):
    latest = next((event for event in reversed(events) if event["gate"] == gate), None)
    recorded = (latest.get("decision") if latest["kind"] == "decision" else
                "skipped" if latest["kind"] == "skip" else "awaiting-review") if latest else "not-started"
    return {"gate": gate, "state": "unchecked" if applicable else "not-applicable",
            "recorded_state": recorded if applicable else "not-applicable", "ready": False, "missing": [], "artifacts": []}


def video_detail(root: Path, slug: str, *, summary=False) -> dict:
    folder = _slug_path(root, slug)
    from studio.project_paths import project_id
    slug = project_id(root, folder)
    physical = folder.relative_to(Path(root).resolve()).as_posix()
    if not folder.is_dir():
        raise WorkspaceError("missing", "Video does not exist.")
    metadata = {}
    meta = safe_path(root, f"{physical}/project.json")
    if meta.exists():
        try:
            metadata = json.loads(_read_bytes(meta))
            if not isinstance(metadata, dict):
                raise ValueError
        except (ValueError, UnicodeDecodeError):
            metadata = {"error": "Malformed project metadata"}
    creative = safe_path(root, f"{physical}/creative/snapshot.json")
    if creative.is_file():
        try:
            selected_style = json.loads(_read_bytes(creative))["style_id"]
            if not isinstance(selected_style, str) or not ID.fullmatch(selected_style): raise ValueError
        except (ValueError, KeyError, TypeError):
            selected_style = None
    else:
        selected_style = None
    files = {}
    for gate, names in _GATE_FILES.items():
        files[gate] = [f"{physical}/{name}" for name in names if (folder / name).is_file()]
    exports = sorted((folder / "05_render").glob("*.mp4")) if (folder / "05_render").is_dir() else []
    thumbnail = next((p for p in (folder / "05_render/thumbnail.png", folder / "05_render/contact.png") if p.is_file()), None)
    with read_scope():
        if summary:
            events = _events(root, slug)[1]
            reviews = {gate: _review_summary(gate, events, applicable=not _not_applicable(root, slug, gate)) for gate in GATES}
        else:
            reviews = {gate: review_state(root, slug, gate) for gate in GATES}
    return {"slug": slug, "video_id": slug, "leaf_slug": folder.name, "brand": metadata.get("brand"), "title": metadata.get("title") or slug.replace("-", " ").title(),
            "label": "Setup fixture" if _slug_path(root, slug).name == "silent-first-scene" else ("Demo" if "demo" in slug else "Video"),
            "format": metadata.get("format", "wide"), "style": selected_style or metadata.get("style"),
            "creative_style": selected_style, "legacy_style": metadata.get("style"),
            "preview": f"{physical}/04_scene/index.html" if (folder / "04_scene/index.html").is_file() else None,
            "thumbnail": thumbnail.relative_to(root).as_posix() if thumbnail else None,
            "exports": [p.relative_to(root).as_posix() for p in exports], "files": files,
            "reviews": reviews, "metadata": metadata,
            "materials": _read_links(safe_path(root, f"{physical}/materials.md"))}


_GATE_FILES = {
    "research": ("00_research/research.md", "00_research/sources.md"),
    "brief": ("01_voice/brief.md",), "script": ("01_voice/script.md",),
    "voice-test": (), "voice": (),
    "transcript": ("02_transcript/words.json", "02_transcript/transcript.md"),
    "cues": ("03_cues/cues.md", "03_cues/cues.json", "03_cues/cues.js"),
    "scene": ("04_scene/scene.js", "04_scene/index.html"),
    "render": ("05_render/DESCRIPTION.md",),
}


def _review_path(root: Path, slug: str) -> Path:
    folder = _slug_path(root, slug)
    if not folder.is_dir():
        raise WorkspaceError("missing", "Video does not exist.")
    return safe_path(root, (folder / "REVIEW.md").relative_to(Path(root).resolve()).as_posix())


_REVIEW_HEADING = "## Studio review events"


@_read_once
def _events(root: Path, slug: str) -> tuple[str, list[dict]]:
    path = _review_path(root, slug)
    prose = path.read_text(encoding="utf-8") if path.exists() else "# Reviews\n"
    if _REVIEW_HEADING not in prose:
        return prose, []
    tail = prose.split(_REVIEW_HEADING, 1)[1]
    blocks = re.findall(r"```json\s*\n(.*?)\n```", tail, re.S)
    if len(blocks) != 1:
        raise WorkspaceError("invalid", "Studio review events are malformed; repair REVIEW.md before continuing.")
    try:
        events = json.loads(blocks[0])
    except ValueError:
        raise WorkspaceError("invalid", "Studio review events are malformed; repair REVIEW.md before continuing.") from None
    if not isinstance(events, list) or any(not isinstance(e, dict) or not {"gate", "kind", "fingerprint", "at"} <= e.keys() or
                                           e["gate"] not in GATES or e["kind"] not in {"ready", "decision", "skip", "acceptance"} or
                                           not isinstance(e["fingerprint"], str) or not isinstance(e["at"], str) for e in events):
        raise WorkspaceError("invalid", "Studio review events are malformed; repair REVIEW.md before continuing.")
    return prose.split(_REVIEW_HEADING, 1)[0].rstrip() + "\n", events


def _write_event(root: Path, slug: str, event: dict) -> None:
    path = _review_path(root, slug)
    prose, events = _events(root, slug)
    events = [*events, event]
    content = prose.rstrip() + "\n\n" + _REVIEW_HEADING + "\n\n```json\n" + json.dumps(events, ensure_ascii=False, indent=2) + "\n```\n"
    _atomic_write(path, content.encode("utf-8"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@_read_once
def _source_files(root: Path, slug: str) -> list[Path]:
    folder = _slug_path(root, slug)
    result = [folder / "materials.md"]
    for ident in _read_links(folder / "materials.md"):
        record = safe_path(root, f"library/materials/{ident}")
        metadata = record / "material.md"
        result.append(metadata)
        if metadata.is_file():
            try:
                data, _ = _frontmatter(metadata.read_text(encoding="utf-8"), {"id", "title", "description", "kind", "source", "rights", "tags"}, {"id", "title", "description", "kind", "source", "rights", "tags"})
                source = data["source"]
                if isinstance(source, str) and source != "upload" and not source.startswith(("http://", "https://")):
                    result.append(safe_path(root, source))
            except (WorkspaceError, UnicodeDecodeError, KeyError):
                pass  # The record itself is still fingerprinted; private paths are never read.
        if record.is_dir():
            result.extend(sorted(p for p in record.iterdir() if p.is_file() and p.name != "material.md"))
    return result


@_read_once
def _project_metadata(root: Path, slug: str) -> dict:
    path = _slug_path(root, slug) / "project.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise WorkspaceError("invalid", "Project metadata is malformed.") from None
    if not isinstance(data, dict):
        raise WorkspaceError("invalid", "Project metadata is malformed.")
    return data


def _not_applicable(root: Path, slug: str, gate: str) -> bool:
    if _slug_path(root, slug).name == "silent-first-scene" and gate in SILENT_UNUSED_GATES:
        return True
    if gate == "research" and not (_slug_path(root, slug) / "00_research").is_dir():
        return True
    return False


def set_voice_selection(root: Path, slug: str, key: str, path: str, script_fingerprint: str) -> dict:
    if key not in {"voice", "voice_test"} or not isinstance(script_fingerprint, str) or not re.fullmatch(r"[0-9a-f]{64}", script_fingerprint):
        raise WorkspaceError("invalid", "Invalid voice selection.")
    audio = safe_path(root, f"videos/{_video_id(root, slug)}/{path}")
    if not audio.is_file() or audio.suffix.lower() not in {".mp3", ".wav", ".m4a", ".ogg"} or _slug_path(root, slug) / "01_voice" not in audio.parents:
        raise WorkspaceError("missing", "Selected voice audio is missing.")
    with workspace_lock(root):
        metadata = _project_metadata(root, slug)
        metadata[key] = {"path": path, "origin": "generated", "script_fingerprint": script_fingerprint}
        _atomic_write(_slug_path(root, slug) / "project.json", (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode())
    return metadata[key]


@_read_once
def _voice_selection(root: Path, slug: str, gate: str) -> tuple[Path | None, dict]:
    folder = _slug_path(root, slug)
    selection = _project_metadata(root, slug).get("voice_test" if gate == "voice-test" else "voice")
    if selection is not None:
        if not isinstance(selection, dict) or selection.get("origin") not in {"generated", "imported"} or not isinstance(selection.get("path"), str):
            raise WorkspaceError("invalid", "Voice selection is malformed.")
        path = safe_path(root, f"videos/{slug}/{selection['path']}")
        if folder / "01_voice" not in path.parents or path.suffix.lower() not in {".mp3", ".wav", ".m4a", ".ogg"}:
            raise WorkspaceError("invalid", "Voice selection must be an audio file in 01_voice.")
        return path, selection
    if gate == "voice-test":
        return None, {}
    voice = folder / "01_voice"
    candidates = [p for p in voice.iterdir() if p.is_file() and p.name.startswith("voice.") and p.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg"}] if voice.is_dir() else []
    return (candidates[0], {"origin": "imported", "path": candidates[0].relative_to(folder).as_posix()}) if len(candidates) == 1 else (None, {})


@_read_once
def _own_paths(root: Path, slug: str, gate: str) -> list[Path]:
    folder = _slug_path(root, slug)
    paths = [folder / x for x in _GATE_FILES[gate]]
    paths.append(folder / "settings.json")
    if gate == "research":
        page_dir = folder / "00_research"
        if page_dir.is_dir():
            paths.extend(sorted(p for p in page_dir.rglob("*") if p.is_file() and p.name not in {"research.md", "sources.md"}))
    if gate in {"script", "scene"}:
        paths.extend(_source_files(root, slug))
    if gate in {"voice", "voice-test"}:
        selected, selection = _voice_selection(root, slug, gate)
        if selected:
            paths.append(selected)
            if selection.get("origin") == "generated":
                takes = folder / "01_voice/takes"
                if gate == "voice" and takes.is_dir():
                    paths.extend(sorted(p for p in takes.iterdir() if p.is_file() and re.fullmatch(r"\d+\.(mp3|txt|json)", p.name)))
                else:
                    paths.extend((selected.with_suffix(".txt"), selected.with_suffix(".json")))
    if gate == "scene":
        paths.append(folder / "05_render/check.md")
        for sub in (folder / "04_scene", Path(root) / "_runtime", folder / "style", folder / "creative"):
            if sub.is_dir():
                paths.extend(sorted(p for p in sub.rglob("*") if p.is_file() and p.suffix != ".pyc" and not any(x.startswith(".") or x in {"__pycache__", "node_modules"} for x in p.relative_to(sub).parts)))
        stills = folder / "05_render/stills"
        if stills.is_dir():
            paths.extend(sorted(p for p in stills.iterdir() if p.is_file()))
    if gate == "render":
        out = folder / "05_render"
        if out.is_dir():
            paths.extend(sorted(p for p in out.rglob("*") if p.is_file() and p.suffix.lower() in {".mp4", ".png", ".jpg", ".json", ".md", ".txt"}))
    return list(dict.fromkeys(paths))


@_read_once
def _upstream(root: Path, slug: str, gate: str) -> list[str]:
    silent = _slug_path(root, slug).name == "silent-first-scene"
    research_exists = (_slug_path(root, slug) / "00_research").is_dir()
    upstream = {
        "research": [], "brief": ["research"] if research_exists else [], "script": ["brief"] if not silent else [],
        "voice-test": ["script"], "voice": ["script", "voice-test"],
        "transcript": ["voice"], "cues": [] if silent else ["transcript"],
        "scene": ["cues"], "render": ["scene"],
    }[gate]
    if gate == "voice" and _voice_selection(root, slug, gate)[1].get("origin") == "imported":
        return ["script"]
    return upstream


@_read_once
def gate_fingerprint(root: Path, slug: str, gate: str) -> str:
    if gate not in GATES:
        raise WorkspaceError("invalid", "Unknown review gate.")
    _review_path(root, slug)
    if _not_applicable(root, slug, gate):
        return _hash(f"not-applicable:{slug}:{gate}".encode())
    pairs = []
    for path in _own_paths(root, slug, gate):
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            continue
        try:
            safe_path(root, relative)
            digest = _file_hash(path) if path.is_file() else "missing"
        except WorkspaceError:
            digest = "inaccessible"
        pairs.append((relative, digest))
    if gate in {"voice", "voice-test"}:
        pairs.append(("selection", json.dumps(_voice_selection(root, slug, gate)[1], sort_keys=True)))
    for prior in _upstream(root, slug, gate):
        state = review_state(root, slug, prior)
        pairs.append(("gate:" + prior, state["fingerprint"] if state["state"] in PASSED else "unapproved"))
    return _hash(json.dumps(sorted(pairs), separators=(",", ":")).encode())


def _substantive(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    body = re.sub(r"(?m)^\s*(#|<!--|-->|```|-)\s*", "", text).strip()
    return bool(body) and not any(x in body.lower() for x in ("replace with the real", "replace this with the script", "describe composition"))


def _engine(folder: Path) -> str:
    """project.json engine; old videos have none and are canvas."""
    try:
        return json.loads((folder / "project.json").read_text(encoding="utf-8")).get("engine") or "canvas"
    except (OSError, ValueError, AttributeError):
        return "canvas"


def _scene_check_ok(path: Path, engine: str = "canvas") -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    if engine == "hyperframes":  # anim.py hf_check writes these; the canvas rows say n/a (hyperframes)
        names = ("lint errors", "video vs voice length", "no visual layer")
    else:
        names = ("page errors", "cue warnings", "clock use", "nondeterministic frames", "text cut off", "text overlaps", "text too short to read")
    # Quality-bar rows (check.QUALITY_KEYS), sound-effect rows (check.SFX_KEYS), the
    # hyperframes sub-composition row and "invented labels" (2026-10-20): older check.md files lack them; a written row must read 0.
    later = ("sound design missing", "too few beats", "sound effect unknown", "sound effect unlicensed", "composition errors", "invented labels")
    quality_ok = not any(re.search(rf"(?m)^\s*{re.escape(name)}\s+[1-9]", text) for name in later)
    return quality_ok and all(re.search(rf"(?m)^\s*{re.escape(name)}\s+0\s*$", text) for name in names)


def _video_check_ok(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    try:  # still stretches stop the render unless the project allows them (project.json "allow")
        allow = json.loads((path.parent.parent / "project.json").read_text(encoding="utf-8")).get("allow") or []
    except (OSError, ValueError):
        allow = []
    still_ok = "still" in allow or re.search(r"(?m)^- dead stretches over 3 s \(stops the render\): 0\s*$", text)
    flat_ok = not re.search(r"(?m)^- flat frames, runs over 3 frames \(stops the render\): [1-9]", text)  # older files have no row
    return bool(still_ok and flat_ok and re.search(r"(?m)^- one-frame flashes \(must be 0\): 0\s*$", text) and
                re.search(r"(?m)^- format: .* \(ok\)\s*$", text) and
                (re.search(r"(?m)^- loudness: .*: ok\)\s*$", text) or "- loudness: no audio" in text))


def _audio_check_ok(folder: Path, export: Path) -> bool:
    import anim
    try:
        text = (folder / "05_render/check-audio.md").read_text(encoding="utf-8")
        match = re.search(r"```json\n(.*?)\n```", text, re.S)
        report = json.loads(match[1]) if match else {}
        voice = anim.find_voice(folder)
        cues = json.loads((folder / "03_cues/cues.json").read_text())
        duration = cues["meta"]["duration"]
        tolerance = anim.HF_LENGTH_TOL if _engine(folder) == "hyperframes" else .001
        if (report.get("status") != "passed" or report.get("violations") != 0 or
                report.get("required_db") != anim.SFX_DISTANCE_DB or report.get("start") != 0 or
                not isinstance(report.get("end"), (int, float)) or report["end"] <= 0 or
                not math.isfinite(report["end"]) or abs(report["end"] - duration) > tolerance or
                report.get("export") != str(export.resolve()) or not export.is_file() or
                report.get("export_sha256") != _file_hash(export) or
                report.get("sources") != anim.audio_sources(folder, voice)):
            return False
        if report.get("effects") == "none (not applicable)":
            if any(c.get("sfx") for c in cues.get("cueList", [])):
                return False
            if _engine(folder) == "hyperframes":
                anim.check_hf_audio(folder, voice, cues)
            return report.get("measured_windows") == 0 and report.get("minimum_db") is None
        if not re.fullmatch(r"[0-9a-f]{64}", report.get("effect_track_sha256", "")):
            return False
        if report.get("measured_windows") == 0 and report.get("minimum_db") is None:
            return True  # Separate stem verified; no effects in speech to compare.
        return (isinstance(report.get("minimum_db"), (int, float)) and
                math.isfinite(report["minimum_db"]) and report["minimum_db"] >= anim.SFX_DISTANCE_DB and
                report.get("measured_windows", 0) > 0)
    except (OSError, ValueError, TypeError, KeyError, SystemExit):
        return False


def _readiness(root: Path, slug: str, gate: str) -> tuple[bool, list[str]]:
    folder = _slug_path(root, slug)
    missing = []
    for prior in _upstream(root, slug, gate):
        if review_state(root, slug, prior)["state"] not in PASSED:
            missing.append(f"{prior} approval")
    if gate == "research":
        if not _substantive(folder / "00_research/research.md"):
            missing.append("research.md")
        if not _substantive(folder / "00_research/sources.md"):
            missing.append("sources.md")
    elif gate == "brief":
        text = (folder / "01_voice/brief.md").read_text(encoding="utf-8") if (folder / "01_voice/brief.md").is_file() else ""
        fields = {"audience": r"audience", "language": r"language", "outcome": r"(?:one\s+)?outcome", "video type": r"(?:video\s+)?type"}
        if re.search(r"(?im)^- Script workflow: direction-v1\s*$", text):
            fields.update({label: re.escape(label) for label in (
                "Purpose", "Evidence and uncertainties", "Opening angle 1", "Opening angle 2", "Opening angle 3",
                "Framework and reason", "Selected opening", "Beat outline", "Promised payoff", "Essential visual support")})
        for label, pattern in fields.items():
            match = re.search(rf"(?im)^[ \t]*(?:[-*][ \t]*)?{pattern}[ \t]*:[ \t]*([^\r\n]*)", text)
            if not match or not match[1].strip() or "|" in match[1]:
                missing.append(label)
    elif gate == "script":
        if not _substantive(folder / "01_voice/script.md"):
            missing.append("script.md")
    elif gate in {"voice-test", "voice"}:
        selected, selection = _voice_selection(root, slug, gate)
        if not selected or not selected.is_file():
            missing.append("selected audio")
        if selection.get("origin") == "generated":
            if selection.get("script_fingerprint") != review_state(root, slug, "script")["fingerprint"]:
                missing.append("matching script revision")
            takes = [selected] if gate == "voice-test" and selected else sorted((folder / "01_voice/takes").glob("[0-9][0-9].mp3"))
            if not takes:
                missing.append("generated takes")
            for take in takes:
                txt, meta = take.with_suffix(".txt"), take.with_suffix(".json")
                if not take.is_file() or not txt.is_file() or not meta.is_file():
                    missing.append("complete take files")
                    continue
                try:
                    request = json.loads(meta.read_text(encoding="utf-8"))
                    if request.get("body", {}).get("text") != txt.read_text(encoding="utf-8") or take.stat().st_size == 0:
                        missing.append("matching take request")
                except (ValueError, AttributeError):
                    missing.append("matching take request")
    elif gate == "transcript":
        for name in ("words.json", "transcript.md"):
            if not _substantive(folder / "02_transcript" / name):
                missing.append(name)
    elif gate == "cues":
        cues = folder / "03_cues"
        if not _substantive(cues / "cues.md"):
            missing.append("cues.md")
        for name in ("cues.json", "cues.js"):
            if not (cues / name).is_file():
                missing.append(name)
            elif (cues / "cues.md").is_file() and (cues / name).stat().st_mtime_ns < (cues / "cues.md").stat().st_mtime_ns:
                missing.append(f"stale {name}")
    elif gate == "scene":
        engine = _engine(folder)
        for name in (("index.html",) if engine == "hyperframes" else ("scene.js", "index.html")):
            if not (folder / "04_scene" / name).is_file():
                missing.append(name)
        if not list((folder / "05_render/stills").glob("*.png")):
            missing.append("stills")
        check = folder / "05_render/check.md"
        if not _scene_check_ok(check, engine):
            missing.append("zero-counter check.md")
        else:
            scene_inputs = [p for p in _own_paths(root, slug, "scene") if p.is_file() and p != check and "05_render/stills" not in p.as_posix()]
            if scene_inputs and check.stat().st_mtime_ns < max(p.stat().st_mtime_ns for p in scene_inputs):
                missing.append("stale check.md")
    elif gate == "render":
        render_dir = folder / "05_render"
        export = render_dir / f"{folder.name}.mp4"
        if not export.is_file():
            missing.append("export MP4")
        if not _substantive(folder / "05_render/DESCRIPTION.md"):
            missing.append("DESCRIPTION.md")
        if not list(render_dir.glob("thumbnail-*.png")) and slug != "silent-first-scene":
            missing.append("thumbnail")
        report = render_dir / "check-video.md"
        if not _video_check_ok(report) or (export.is_file() and report.stat().st_mtime_ns < export.stat().st_mtime_ns):
            missing.append("current video check")
        if not _audio_check_ok(folder, export):
            missing.append("current audio check")
        phone = render_dir / "phone"
        frames = list(phone.glob("*.png")) if phone.is_dir() else []
        if not frames or (export.is_file() and min(p.stat().st_mtime_ns for p in frames) < export.stat().st_mtime_ns):
            missing.append("current phone frames")
        judge = render_dir / "frame-critic.md"
        if not _substantive(judge) or (export.is_file() and judge.stat().st_mtime_ns < export.stat().st_mtime_ns):
            missing.append("current frame-critic report")
    return not missing, missing


@_read_once
def review_state(root: Path, slug: str, gate: str) -> dict:
    from studio.agent_runs import AGENT_NEXT
    if gate not in GATES:
        raise WorkspaceError("invalid", "Unknown review gate.")
    prose, events = _events(root, slug)
    if _not_applicable(root, slug, gate):
        result = {"gate": gate, "state": "not-applicable", "fingerprint": gate_fingerprint(root, slug, gate),
                  "ready": False, "missing": [], "history": [e for e in events if e["gate"] == gate],
                  "legacy": prose.strip(), "artifacts": []}
        return result
    fingerprint = gate_fingerprint(root, slug, gate)
    history = [e for e in events if e["gate"] == gate]
    ready, missing = _readiness(root, slug, gate)
    state = "draft" if any(((_slug_path(root, slug) / x).exists() for x in _GATE_FILES[gate])) else "not-started"
    skip = next((e for e in reversed(history) if e["kind"] == "skip" and e["fingerprint"] == fingerprint), None)
    current = [e for e in history if e["fingerprint"] == fingerprint]
    if gate == "research" and skip:
        state = "skipped"
    elif history and not current:
        state = "stale"
    elif not ready and missing:
        state = "blocked" if any("approval" in x for x in missing) else "draft"
    else:
        if current:
            latest = current[-1]
            if latest["kind"] == "skip":
                state = "skipped"
            elif latest["kind"] == "decision":
                state = latest.get("decision", "draft")
            elif latest["kind"] == "acceptance":
                from studio.permissions import session_state, needs_review
                permission = session_state(root, "video:" + _video_id(root, slug))
                if (permission["active"] and latest.get("grant_id") == permission["grant_id"] and
                    latest.get("session_id") == permission["session_id"] and
                    latest.get("scope") == permission["scope"] and not needs_review(permission, gate)):
                    state = "accepted"
                else:
                    state = "awaiting-review"
            elif latest["kind"] == "ready":
                state = "awaiting-review"
    result = {"gate": gate, "state": state, "fingerprint": fingerprint, "ready": ready,
            "missing": missing, "history": history, "legacy": prose.strip(),
            "upstream": {prior: {key: value for key, value in review_state(root, slug, prior).items()
                                  if key in {"gate", "state", "fingerprint", "ready"}} for prior in _upstream(root, slug, gate)},
            "artifacts": [p.relative_to(root).as_posix() for p in _own_paths(root, slug, gate) if p.is_file()]}
    next_gate = AGENT_NEXT.get(gate)
    result["next_unwritten"] = False
    if next_gate:
        try:
            path = safe_path(root, f"videos/{slug}/{_GATE_FILES[next_gate][0]}")
            result["next_unwritten"] = not _substantive(path)
        except WorkspaceError:
            pass  # An inaccessible next stage cannot offer automatic authoring.
    return result


def mark_ready(root: Path, slug: str, gate: str, expected_fingerprint: str) -> dict:
    with workspace_lock(root):
        state = review_state(root, slug, gate)
        if expected_fingerprint != state["fingerprint"]:
            raise WorkspaceError("conflict", "Review inputs changed since you opened them.")
        if not state["ready"]:
            raise WorkspaceError("blocked", "Review is incomplete: " + ", ".join(state["missing"]))
        if state["state"] in PASSED or state["state"] == "awaiting-review":
            return state
        _write_event(root, slug, {"gate": gate, "kind": "ready", "decision": None, "reviewer": None, "note": "", "fingerprint": expected_fingerprint, "at": _now()})
    return review_state(root, slug, gate)


def decide_review(root: Path, slug: str, gate: str, decision: str, reviewer: str, note: str, expected_fingerprint: str) -> dict:
    if os.environ.get("VF_PERMISSION_WORKER") == "1":
        raise WorkspaceError("blocked", "A worker cannot make a human review decision.")
    if decision not in {"approved", "changes-requested"} or not isinstance(reviewer, str) or not reviewer.strip():
        raise WorkspaceError("invalid", "Provide a reviewer and an approval or changes-requested decision.")
    with workspace_lock(root):
        state = review_state(root, slug, gate)
        if expected_fingerprint != state["fingerprint"]:
            raise WorkspaceError("conflict", "Review inputs changed since you opened them.")
        if state["state"] not in {"awaiting-review", "approved", "accepted", "changes-requested"}:
            raise WorkspaceError("blocked", "Mark this complete revision ready before deciding.")
        _write_event(root, slug, {"gate": gate, "kind": "decision", "decision": decision, "reviewer": reviewer.strip(), "note": note or "", "fingerprint": expected_fingerprint, "at": _now()})
    return review_state(root, slug, gate)


def accept_under_permission(root: Path, slug: str, gate: str, expected_fingerprint: str) -> dict:
    """Accept a ready revision under this session's grant, without a human decision."""
    from studio.permissions import needs_review, require_permission
    scope = "video:" + _video_id(root, slug)
    permission = require_permission(root, scope, gate)
    if needs_review(permission, gate):
        raise WorkspaceError("blocked", "This stage needs a human review.")
    with workspace_lock(root):
        state = review_state(root, slug, gate)
        if expected_fingerprint != state["fingerprint"]:
            raise WorkspaceError("conflict", "Review inputs changed since you opened them.")
        if not state["ready"]:
            raise WorkspaceError("blocked", "Review is incomplete: " + ", ".join(state["missing"]))
        if state["state"] == "changes-requested":
            raise WorkspaceError("blocked", "Make a new revision after the requested changes.")
        if state["state"] in PASSED:
            return state
        if state["state"] != "awaiting-review":
            raise WorkspaceError("blocked", "Mark this complete revision ready before acceptance.")
        _write_event(root, slug, {"gate": gate, "kind": "acceptance", "decision": "accepted",
                                  "reviewer": None, "note": "", "fingerprint": expected_fingerprint,
                                  "session_id": permission["session_id"], "scope": scope,
                                  "grant_id": permission["grant_id"], "at": _now()})
    return review_state(root, slug, gate)


def skip_research(root: Path, slug: str, reason: str, reviewer: str) -> dict:
    if not isinstance(reason, str) or not reason.strip() or not isinstance(reviewer, str) or not reviewer.strip():
        raise WorkspaceError("invalid", "A reviewer and nonempty reason are required to skip research.")
    if not (_slug_path(root, slug) / "00_research").is_dir():
        raise WorkspaceError("blocked", "Research has not been initialized; there is nothing to skip.")
    with workspace_lock(root):
        fingerprint = gate_fingerprint(root, slug, "research")
        _write_event(root, slug, {"gate": "research", "kind": "skip", "decision": "skipped", "reviewer": reviewer.strip(), "note": reason.strip(), "fingerprint": fingerprint, "at": _now()})
    return review_state(root, slug, "research")


def _frontmatter(text: str, required: set[str], allowed: set[str]) -> tuple[dict, str]:
    match = re.match(r"\A---\n(.*?)\n---\n?(.*)\Z", text, re.S)
    if not match:
        raise WorkspaceError("invalid", "Record needs JSON-compatible frontmatter.")
    data = {}
    for line in match[1].splitlines():
        if not line.strip():
            continue
        if ": " not in line:
            raise WorkspaceError("invalid", "Malformed frontmatter field.")
        key, raw = line.split(": ", 1)
        if key in data or key not in allowed:
            raise WorkspaceError("invalid", "Unknown or duplicate frontmatter field.")
        try:
            data[key] = json.loads(raw)
        except ValueError:
            raise WorkspaceError("invalid", "Frontmatter values must be JSON strings or arrays.") from None
    if not required <= data.keys():
        raise WorkspaceError("invalid", "Record is missing required frontmatter.")
    return data, match[2]


def _record(data: dict, body: str = "") -> str:
    return "---\n" + "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in data.items()) + "\n---\n" + body


_STYLE_FIELDS = {"id", "title", "description", "base_kit", "family_id", "renderer", "supported_formats",
                 "origin", "reference_videos", "references", "readiness", "setting", "environment",
                 "components", "captions", "voice_guidance", "motion_guidance", "visual_instructions"}


def _style_reference_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or "\x00" in relative:
        raise WorkspaceError("invalid", "Invalid style reference path.")
    parts = PurePosixPath(relative).parts
    if (relative.startswith("/") or not parts or parts[0] not in (SHELVES | {"_templates"}) or
            any(part in (".", "..", "_auth") or part.startswith(".") for part in parts)):
        raise WorkspaceError("invalid", "Style references must use public workspace paths.")
    base = Path(root).resolve()
    path = base.joinpath(*parts)
    if any(part.is_symlink() for part in (path, *path.parents) if part != base and base in part.parents):
        raise WorkspaceError("invalid", "Cannot reference symbolic links in the workspace.")
    try:
        path.resolve().relative_to(base)
    except ValueError:
        raise WorkspaceError("invalid", "Style reference leaves the workspace.") from None
    return path


def _validate_style_fields(data: dict, root: Path) -> None:
    if (not isinstance(data.get("id"), str) or not ID.fullmatch(data["id"]) or
            not isinstance(data.get("title"), str) or not data["title"].strip() or
            data.get("base_kit") not in BASE_KITS):
        raise WorkspaceError("invalid", "Malformed style recipe.")
    if data.get("family_id") is not None and (not isinstance(data["family_id"], str) or not ID.fullmatch(data["family_id"])):
        raise WorkspaceError("invalid", "Style family ID is invalid.")
    if data.get("renderer") is not None and (not isinstance(data["renderer"], str) or not ID.fullmatch(data["renderer"])):
        raise WorkspaceError("invalid", "Style renderer is invalid.")
    formats = data.get("supported_formats", [])
    if not isinstance(formats, list) or any(not isinstance(item, str) or item not in {"wide", "tall"} for item in formats):
        raise WorkspaceError("invalid", "Supported formats must be a list of wide and tall.")
    for field in ("origin", "readiness"):
        if field in data and (not isinstance(data[field], str) or not data[field].strip()):
            raise WorkspaceError("invalid", f"Style {field} must be a nonempty string.")
    for field in ("setting", "environment", "captions", "voice_guidance", "motion_guidance", "visual_instructions"):
        if field in data and (not isinstance(data[field], str) or len(data[field]) > 10000):
            raise WorkspaceError("invalid", f"Style {field} must be text under 10000 characters.")
    if "components" in data and (not isinstance(data["components"], list) or len(data["components"]) > 20 or
                                  any(not isinstance(item, str) or not item.strip() or len(item) > 1000 for item in data["components"])):
        raise WorkspaceError("invalid", "Style components must be a list of descriptions.")
    videos = data.get("reference_videos", [])
    if not isinstance(videos, list) or any(not isinstance(item, str) or not re.fullmatch(r"[a-z0-9_][a-z0-9_-]*(?:/[a-z0-9_][a-z0-9_-]*)?", item) for item in videos):
        raise WorkspaceError("invalid", "Style video references must be video IDs.")
    references = data.get("references", [])
    if not isinstance(references, list) or any(not isinstance(item, str) for item in references):
        raise WorkspaceError("invalid", "Style references must be workspace paths.")
    for reference in references:
        _style_reference_path(root, reference)


def list_style_families(root: Path) -> list[dict]:
    root = Path(root).resolve()
    shelf = Path(root) / "styles/_families"
    if not shelf.is_dir():
        return []
    families = []
    for folder in sorted(shelf.iterdir(), key=lambda path: path.name):
        if not folder.is_dir() or folder.is_symlink() or not ID.fullmatch(folder.name):
            continue
        path = safe_path(root, f"styles/_families/{folder.name}/family.md")
        raw = _read_bytes(path)
        data, body = _frontmatter(raw.decode("utf-8"),
            {"id", "title", "description", "default_variant", "base_kit", "renderer", "supported_formats", "reference_videos", "references"},
            {"id", "title", "description", "default_variant", "base_kit", "renderer", "supported_formats", "reference_videos", "references"})
        if (data["id"] != folder.name or not isinstance(data["title"], str) or not data["title"].strip() or
                not isinstance(data["description"], str) or not data["description"].strip() or
                not isinstance(data["default_variant"], str) or not ID.fullmatch(data["default_variant"]) or
                data["base_kit"] not in BASE_KITS or
                not isinstance(data["renderer"], str) or not ID.fullmatch(data["renderer"])):
            raise WorkspaceError("invalid", f"Malformed style family: {folder.name}.")
        _validate_style_fields({"id": data["default_variant"], "title": data["title"], "base_kit": data["base_kit"],
                                "renderer": data["renderer"], "supported_formats": data["supported_formats"],
                                "reference_videos": data["reference_videos"], "references": data["references"]}, root)
        families.append({**data, "body": body, "path": path.relative_to(root).as_posix()})
    return families


def _read_links(path: Path) -> list[str]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    if "## Linked materials" not in text:
        return []
    blocks = re.findall(r"```json\s*\n(.*?)\n```", text.split("## Linked materials", 1)[1], re.S)
    if len(blocks) != 1:
        raise WorkspaceError("invalid", "Malformed linked materials list.")
    try:
        ids = json.loads(blocks[0])
    except ValueError:
        raise WorkspaceError("invalid", "Malformed linked materials list.") from None
    if not isinstance(ids, list) or any(not isinstance(i, str) or not ID.fullmatch(i) for i in ids):
        raise WorkspaceError("invalid", "Malformed linked materials list.")
    return ids


def _write_links(path: Path, ids: list[str]) -> None:
    text = path.read_text(encoding="utf-8") if path.is_file() else "# Materials\n"
    before = text.split("## Linked materials", 1)[0].rstrip()
    after = ""
    if "## Linked materials" in text:
        after_section = text.split("## Linked materials", 1)[1]
        after = re.sub(r"\A.*?```json\s*\n.*?\n```", "", after_section, count=1, flags=re.S)
    _atomic_write(path, (before + "\n\n## Linked materials\n\n```json\n" + json.dumps(ids, indent=2) + "\n```" + after).encode("utf-8"))


def _material(root: Path, material_id: str) -> dict:
    path = safe_path(root, f"library/materials/{_id(material_id)}/material.md")
    data, body = _frontmatter(_read_bytes(path).decode("utf-8"), {"id", "title", "description", "kind", "source", "rights", "tags"}, {"id", "title", "description", "kind", "source", "rights", "tags"})
    if data["id"] != material_id or not all(isinstance(data[k], str) for k in ("title", "description", "kind", "source", "rights")) or not isinstance(data["tags"], list) or any(not isinstance(t, str) for t in data["tags"]):
        raise WorkspaceError("invalid", "Malformed material record.")
    files = [p.relative_to(root).as_posix() for p in path.parent.iterdir()
             if p.is_file() and not p.is_symlink() and not p.name.startswith(".") and p.name != "material.md"]
    return {**data, "body": body, "path": path.relative_to(root).as_posix(), "files": files, "origin": "described"}


@_read_once
def _material_links(root):
    links = {}
    for shelf, key in (("videos", "linked_videos"), ("styles", "linked_styles")):
        parent = Path(root) / shelf
        if not parent.is_dir():
            continue
        owners = iter_projects(root) if shelf == "videos" else sorted(parent.iterdir())
        for owner in owners:
            if owner.is_dir() and not owner.is_symlink() and ID.fullmatch(owner.name):
                owner_id = project_id(root, owner) if shelf == "videos" else owner.name
                try:
                    for ident in _read_links(safe_path(root, f"{shelf}/{owner_id}/materials.md")):
                        links.setdefault(ident, {"linked_videos": [], "linked_styles": []})[key].append(owner_id)
                except WorkspaceError:
                    pass
    return links


def _index_material(root, item):
    if not isinstance(item, dict) or not isinstance(item.get("path"), str):
        return None
    relative = "library/" + item["path"]
    try:
        path = safe_path(root, relative)
        if not path.is_file():
            return None
    except WorkspaceError:
        return None
    return {"id": item.get("ref", relative), "title": item.get("name", path.stem),
            "description": "", "kind": item.get("kind", "file"), "source": relative,
            "rights": item.get("license", "unknown"), "tags": [], "origin": "library-index",
            "files": [relative], "linked_videos": [], "linked_styles": []}


def _asset_material(item):
    return {"id": item["path"], "title": os.path.splitext(item["name"])[0].replace("-", " "),
            "description": "", "kind": "file", "source": item["path"], "rights": "unknown", "tags": [],
            "origin": "video-asset", "files": [item["path"]],
            "linked_videos": [item["path"].split("/04_scene/", 1)[0].removeprefix("videos/")], "linked_styles": []}


def _library_index(root):
    path = safe_path(root, "library/INDEX.json")
    if not path.is_file():
        return []
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(entries, list):
            raise ValueError
        return entries
    except (ValueError, UnicodeDecodeError):
        raise WorkspaceError("invalid", "Malformed generated library index") from None


def material_detail(root, ident):
    """Look up a described record, index reference or video asset without a file walk."""
    if not isinstance(ident, str):
        raise WorkspaceError("invalid", "Material ID is required.")
    if ID.fullmatch(ident) and (Path(root) / "library/materials" / ident).exists():
        return {**_material(root, ident), **_material_links(root).get(ident, {"linked_videos": [], "linked_styles": []})}
    parts = PurePosixPath(ident).parts
    if len(parts) >= 5 and ((parts[0] == "videos" and (parts[2:4] == ("04_scene", "assets") or parts[3:5] == ("04_scene", "assets"))) or (parts[0] == "brands" and parts[2] == "library")):
        path = safe_path(root, ident)
        if path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS and not any(p in {"node_modules", "frames"} for p in parts):
            return _asset_material({"path": ident, "name": path.name})
    for item in _library_index(root):
        if isinstance(item, dict) and item.get("ref", "library/" + str(item.get("path", ""))) == ident:
            record = _index_material(root, item)
            if record:
                return record
    raise WorkspaceError("missing", "Material record not found.")


def material_details(root, ids):
    rows = []
    with read_scope():
        for ident in ids:
            try:
                rows.append(material_detail(root, ident))
            except (WorkspaceError, UnicodeDecodeError) as exc:
                rows.append({"id": ident, "title": ident, "error": str(exc)})
    return rows


def _inventory(root):
    files = list_public_files(root)
    links = _material_links(root)
    result = []
    shelf = safe_path(root, "library/materials")
    if shelf.is_dir():
        for folder in sorted(shelf.iterdir()):
            if not folder.is_dir() or folder.is_symlink() or not ID.fullmatch(folder.name):
                continue
            try:
                material = _material(root, folder.name)
            except (WorkspaceError, UnicodeDecodeError) as exc:
                material = {"id": folder.name, "error": str(exc), "origin": "described"}
            result.append({**material, **links.get(folder.name, {"linked_videos": [], "linked_styles": []})})
    try:
        result.extend(record for item in _library_index(root) if (record := _index_material(root, item)))
    except WorkspaceError as exc:
        result.append({"id": "library-index", "origin": "library-index", "error": str(exc)})
    for item in files:
        parts = item["path"].split("/")
        if parts[0] == "brands" and len(parts) >= 4 and parts[2] == "library":
            result.append({**_asset_material(item), "origin": "brand-library", "linked_videos": [], "brand": parts[1]})
        elif parts[0] == "videos" and (parts[2:4] == ["04_scene", "assets"] or parts[3:5] == ["04_scene", "assets"]):
            result.append(_asset_material(item))
    return {"materials": result, "files": files}


def list_materials(root: Path, filters: dict | None = None) -> list[dict]:
    rows = _inventory(root)["materials"]
    filters = filters or {}
    rows = [row for row in rows if all(str(value).lower() in json.dumps(row, ensure_ascii=False).lower()
                                      for key, value in filters.items() if value and key != "brand")]
    brand = filters.get("brand")
    return sorted(rows, key=lambda row: not str(row.get("source", "")).startswith(f"brands/{brand}/library/")) if brand else rows


def inventory_page(root, collection, filters):
    try:
        offset, limit = int(filters.get("offset", 0)), int(filters.get("limit", 48))
        if offset < 0 or not 1 <= limit <= 100:
            raise ValueError
    except (ValueError, TypeError):
        raise WorkspaceError("invalid", "Use a nonnegative offset and a limit between 1 and 100.") from None
    inventory = readcache.cached(root, "inventory", lambda: _inventory(root))
    rows = inventory[collection]
    query, kind = filters.get("q", "").strip().lower(), filters.get("kind", "all")
    matches = [row for row in rows if (kind in ("", "all") or (row.get("kind") or os.path.splitext(row.get("path", ""))[1].lstrip(".")) == kind)
               and (not query or query in json.dumps(row, ensure_ascii=False).lower())]
    if filters.get("brand"):
        prefix = "brands/" + filters["brand"] + "/library/"
        matches.sort(key=lambda row: not str(row.get("source", row.get("path", ""))).startswith(prefix))
    return {"items": matches[offset:offset + limit], "total": len(matches), "offset": offset, "limit": limit,
            "kinds": sorted({row.get("kind") or os.path.splitext(row.get("path", ""))[1].lstrip(".") for row in rows} - {""})}


@_read_once
def list_public_files(root: Path) -> list[dict]:
    """Files eligible to be referenced by a new material record."""
    result = []
    shelves = [Path(root) / name for name in ("library", "videos")]
    shelves.extend(path / "library" for path in (Path(root) / "brands").glob("*") if path.is_dir() and not path.is_symlink() and ID.fullmatch(path.name))
    for shelf in shelves:
        if not shelf.is_dir():
            continue
        for directory, dirs, files in os.walk(shelf, followlinks=False):
            dirs[:] = [name for name in dirs if not name.startswith(".") and "\\" not in name and not os.path.islink(os.path.join(directory, name)) and name not in {"_auth", "node_modules", "frames"}]
            relative_dir = os.path.relpath(directory, root)
            for name in files:
                if name.startswith(".") or "\\" in name or os.path.splitext(name)[1].lower() not in MEDIA_EXTENSIONS:
                    continue
                try:
                    info = os.stat(os.path.join(directory, name), follow_symlinks=False)
                except FileNotFoundError:
                    continue
                if stat.S_ISREG(info.st_mode):
                    result.append({"path": relative_dir + "/" + name, "name": name, "size": info.st_size})
    return sorted(result, key=lambda item: item["path"])


def create_material(root: Path, metadata: dict, content=None, filename: str | None = None, *, _lock_held: bool = False) -> dict:
    if not isinstance(metadata, dict):
        raise WorkspaceError("invalid", "Material metadata is required.")
    allowed = {"id", "title", "description", "kind", "source", "rights", "tags"}
    if set(metadata) - allowed:
        raise WorkspaceError("invalid", "Unknown material metadata field.")
    data = {"id": metadata.get("id") or uuid.uuid4().hex[:12], "title": metadata.get("title"),
            "description": metadata.get("description"), "kind": metadata.get("kind"),
            "source": metadata.get("source"), "rights": metadata.get("rights", "unknown"),
            "tags": metadata.get("tags", [])}
    _id(data["id"])
    if not all(isinstance(data[k], str) and data[k].strip() for k in ("title", "description", "kind", "source", "rights")) or not isinstance(data["tags"], list) or any(not isinstance(t, str) for t in data["tags"]):
        raise WorkspaceError("invalid", "Material title, description, kind, source and rights are required.")
    source = data["source"]
    if source == "upload" and content is None:
        raise WorkspaceError("invalid", "An upload source needs a file.")
    if source != "upload":
        if source.startswith(("http:", "https:")):
            parsed = urlsplit(source)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
                raise WorkspaceError("invalid", "Source must be an HTTP or HTTPS URL.")
        else:
            path = safe_path(root, source)
            if not path.is_file():
                raise WorkspaceError("missing", "Source file does not exist.")
    if content is not None:
        if not (isinstance(content, bytes) or callable(getattr(content, "read", None))) or not filename or Path(filename).name != filename:
            raise WorkspaceError("invalid", "Upload filename and bytes are required.")
        suffix = Path(filename).suffix.lower()
        if suffix not in MEDIA_EXTENSIONS:
            raise WorkspaceError("invalid", "Unsupported upload format.")
        limit = 500 * 1024 * 1024 if suffix in VIDEO_EXTENSIONS else 20 * 1024 * 1024
        if isinstance(content, bytes) and len(content) > limit:
            raise WorkspaceError("invalid", "Upload exceeds the file size limit.")
        if source != "upload":
            raise WorkspaceError("invalid", "Uploaded bytes need source 'upload'.")
    with contextlib.nullcontext() if _lock_held else workspace_lock(root):
        folder = Path(root) / "library/materials" / data["id"]
        if folder.exists():
            raise WorkspaceError("conflict", "Material ID already exists.")
        folder.mkdir(parents=True)
        try:
            if content is not None:
                if isinstance(content, bytes):
                    _atomic_write(folder / filename, content)
                else:
                    fd, name = tempfile.mkstemp(prefix=".studio-", dir=folder)
                    try:
                        with os.fdopen(fd, "wb") as out:
                            size = 0
                            while chunk := content.read(1024 * 1024):
                                size += len(chunk)
                                if size > limit:
                                    raise WorkspaceError("invalid", "Upload exceeds the file size limit.")
                                out.write(chunk)
                            out.flush()
                            os.fsync(out.fileno())
                        os.replace(name, folder / filename)
                    finally:
                        if os.path.exists(name):
                            os.unlink(name)
            _atomic_write(folder / "material.md", _record(data, "\n## Provenance\nDescribe how this material may be used.\n").encode("utf-8"))
        except OSError:
            shutil.rmtree(folder)
            raise WorkspaceError("io", "Upload failed; no material was created.") from None
        except Exception:
            shutil.rmtree(folder)
            raise
    return _material(root, data["id"])


def link_material(root: Path, owner_kind: str, owner_id: str, material_id: str) -> dict:
    if owner_kind not in {"video", "style"}:
        raise WorkspaceError("invalid", "Target must be a video or style.")
    material = _material(root, material_id)
    owner = safe_path(root, f"{'videos' if owner_kind == 'video' else 'styles'}/{_id(owner_id)}")
    if not owner.is_dir():
        raise WorkspaceError("missing", "Target does not exist.")
    with workspace_lock(root):
        path = owner / "materials.md"
        ids = _read_links(path)
        if material_id not in ids:
            _write_links(path, ids + [material_id])
    return {"owner_kind": owner_kind, "owner_id": owner_id, "material_id": material_id, "linked": True}


def _style(root: Path, style_id: str) -> dict:
    root = Path(root).resolve()
    path = safe_path(root, f"styles/{_id(style_id)}/style.md")
    raw = _read_bytes(path)
    data, body = _frontmatter(raw.decode("utf-8"), {"id", "title", "base_kit"}, _STYLE_FIELDS)
    _validate_style_fields(data, root)
    if data["id"] != style_id:
        raise WorkspaceError("invalid", "Malformed style recipe.")
    family_id = data.get("family_id")
    family = next((item for item in list_style_families(root) if item["id"] == family_id), None)
    folder = path.parent
    sample = next((p for p in (folder / "template/index.html", folder / "template/thumbnail.html") if p.is_file()), None)
    return {**data, "body": body, "id": style_id, "path": path.relative_to(root).as_posix(),
            "family_id": family_id,
            "renderer": data.get("renderer", family["renderer"] if family else "modern"),
            "supported_formats": data.get("supported_formats", family["supported_formats"] if family else []),
            "origin": data.get("origin", "legacy"),
            "reference_videos": data.get("reference_videos", family["reference_videos"] if family else []),
            "references": data.get("references", family["references"] if family else []),
            "readiness": data.get("readiness", "draft"),
            "revision": _hash(raw), "materials": _read_links(folder / "materials.md"),
            "template_ready": sample is not None, "sample": sample.relative_to(root).as_posix() if sample else None}


def list_styles(root: Path) -> list[dict]:
    shelf = Path(root) / "styles"
    if not shelf.is_dir():
        return []
    styles = []
    for folder in sorted(shelf.iterdir()):
        if folder.is_dir() and not folder.is_symlink() and ID.fullmatch(folder.name):
            try:
                styles.append(_style(root, folder.name))
            except (WorkspaceError, UnicodeDecodeError) as exc:
                styles.append({"id": folder.name, "error": str(exc), "template_ready": False})
    return styles


def create_style(root: Path, style_id: str, title: str, base_kit: str = "modern", *, family_id: str | None = None,
                 renderer: str | None = None, supported_formats: list[str] | None = None,
                 origin: str | None = None, reference_videos: list[str] | None = None,
                 references: list[str] | None = None, readiness: str | None = None,
                 setting: str | None = None, environment: str | None = None,
                 components: list[str] | None = None, captions: str | None = None,
                 voice_guidance: str | None = None, motion_guidance: str | None = None,
                 visual_instructions: str | None = None) -> dict:
    _id(style_id)
    if not isinstance(title, str) or not title.strip() or base_kit not in BASE_KITS:
        raise WorkspaceError("invalid", "Style title and base kit are required.")
    folder = Path(root) / "styles" / style_id
    data = {"id": style_id, "title": title.strip(), "base_kit": base_kit}
    data.update({key: value for key, value in {
        "family_id": family_id, "renderer": renderer, "supported_formats": supported_formats,
        "origin": origin, "reference_videos": reference_videos, "references": references,
        "readiness": readiness, "setting": setting, "environment": environment,
        "components": components, "captions": captions, "voice_guidance": voice_guidance,
        "motion_guidance": motion_guidance, "visual_instructions": visual_instructions,
    }.items() if value is not None})
    data.setdefault("origin", "user-authored")
    data.setdefault("readiness", "draft")
    _validate_style_fields(data, root)
    with workspace_lock(root):
        if folder.exists():
            raise WorkspaceError("conflict", "Style ID already exists.")
        folder.mkdir(parents=True)
        try:
            recipe = _record(data, "\n## Visual direction\n\n## Motion\n\n## Template\n")
            _atomic_write(folder / "style.md", recipe.encode("utf-8"))
            _write_links(folder / "materials.md", [])
        except Exception:
            shutil.rmtree(folder)
            raise
    return _style(root, style_id)


def save_style(root: Path, style_id: str, text: str, expected_revision: str | None) -> dict:
    _id(style_id)
    data, _ = _frontmatter(text, {"id", "title", "base_kit"}, _STYLE_FIELDS)
    _validate_style_fields(data, root)
    if data["id"] != style_id:
        raise WorkspaceError("invalid", "Style ID or base kit is invalid.")
    path = f"styles/{style_id}/style.md"
    saved = save_text(root, path, text, expected_revision)
    return {**_style(root, style_id), "file": saved}


def import_existing_styles(root: Path) -> list[dict]:
    families = list_style_families(root)
    imported = []
    for family in families:
        style_id = family["default_variant"]
        relative = f"styles/{_id(style_id)}/style.md"
        style_path = safe_path(root, relative, write=True)
        folder = style_path.parent
        metadata = {
            "id": style_id,
            "title": family["title"],
            "description": family["description"],
            "base_kit": family["base_kit"],
            "family_id": family["id"],
            "renderer": family["renderer"],
            "supported_formats": family["supported_formats"],
            "origin": "existing-reference",
            "reference_videos": family["reference_videos"],
            "references": family["references"],
            "readiness": "needs-review",
        }
        _validate_style_fields(metadata, root)
        with workspace_lock(root):
            folder.mkdir(parents=True, exist_ok=True)
            created_style = not style_path.exists()
            if created_style:
                body = ("\n## Visual direction\n\nReview the linked family guide and source references.\n"
                        "\n## Motion\n\nReview the runtime guidance before use.\n"
                        "\n## Template\n\nNo style sample or template is registered yet.\n")
                _atomic_write(style_path, _record(metadata, body).encode("utf-8"))
            materials_path = safe_path(root, f"styles/{style_id}/materials.md", write=True)
            if not materials_path.exists():
                _write_links(materials_path, [])
            review_path = folder / "REVIEW.md"
            if created_style and not review_path.exists():
                _atomic_write(review_path, b"# Review\n\nImported references need review. No approval is recorded.\n")
        imported.append(style_id)
    by_id = {style.get("id"): style for style in list_styles(root)}
    return [by_id.get(style_id, {"id": style_id, "error": "Imported style could not be read."}) for style_id in imported]


def _style_files(root: Path, style_id: str) -> list[Path]:
    folder = safe_path(root, f"styles/{_id(style_id)}")
    paths = [folder / "style.md", folder / "materials.md"]
    template = folder / "template"
    if template.is_dir():
        paths.extend(sorted(p for p in template.rglob("*") if p.is_file() and not p.is_symlink()))
    result = []
    for path in paths:
        safe_path(root, path.relative_to(root).as_posix())
        if path.is_file():
            result.append(path)
    return result


def _style_revision(root: Path, style_id: str) -> str:
    pairs = [(p.relative_to(root).as_posix(), _file_hash(p)) for p in _style_files(root, style_id)]
    return _hash(json.dumps(pairs, separators=(",", ":")).encode())


def _video_style_revision(root: Path, slug: str) -> str | None:
    manifest = safe_path(root, f"videos/{slug}/style/snapshot.json")
    return _hash(manifest.read_bytes()) if manifest.is_file() else None


def apply_style(root: Path, slug: str, style_id: str, expected_revision: str | None, confirm: bool = False) -> dict:
    video = _slug_path(root, slug)
    if not video.is_dir():
        raise WorkspaceError("missing", "Video does not exist.")
    _style(root, style_id)
    source_revision = _style_revision(root, style_id)
    target_revision = _video_style_revision(root, slug)
    revision = _hash(json.dumps([target_revision, source_revision]).encode())
    if confirm and expected_revision != revision:
        raise WorkspaceError("conflict", "Style or video changed since you opened it.")
    source_files = _style_files(root, style_id)
    manifest = video / "style/snapshot.json"
    old = json.loads(manifest.read_text()) if manifest.is_file() else None
    recorded_files = old.get("files", {}) if isinstance(old, dict) else {}
    if not isinstance(recorded_files, dict) or any(not isinstance(p, str) or h is not None and not isinstance(h, str) for p, h in recorded_files.items()):
        raise WorkspaceError("invalid", "Project style snapshot is malformed.")
    previous_files = {p: h for p, h in recorded_files.items() if h is not None}
    changes = []
    incoming = set()
    for source in source_files:
        rel = source.relative_to(Path(root) / "styles" / style_id)
        target = video / "style" / rel
        incoming.add(target.relative_to(root).as_posix())
        changes.append({"path": target.relative_to(root).as_posix(), "before": _file_hash(target) if target.is_file() else None,
                        "after": _file_hash(source)})
    for relative in sorted(set(previous_files) - incoming):
        target = safe_path(root, relative)
        if video / "style" not in target.parents:
            raise WorkspaceError("invalid", "Project style snapshot contains an invalid path.")
        changes.append({"path": relative, "before": _file_hash(target) if target.is_file() else None, "after": None})
    if not confirm:
        return {"slug": slug, "style_id": style_id, "style_revision": source_revision,
                "revision": revision, "changes": changes, "applied": False}
    with workspace_lock(root):
        if _style_revision(root, style_id) != source_revision or _video_style_revision(root, slug) != target_revision:
            raise WorkspaceError("conflict", "Style or video changed before apply.")
        style_dir = safe_path(root, f"videos/{slug}/style")
        manifest = style_dir / "snapshot.json"
        old = json.loads(manifest.read_text()) if manifest.is_file() else None
        if style_dir.is_dir():
            existing = {p.relative_to(root).as_posix() for p in style_dir.rglob("*") if p.is_file() and p.name != "snapshot.json"}
            if not old or existing != set(previous_files):
                raise WorkspaceError("conflict", "Project style has local files; review them before applying an update.")
        for relative, approved_hash in previous_files.items():
            target = safe_path(root, relative)
            if style_dir not in target.parents or not target.is_file() or _file_hash(target) != approved_hash:
                raise WorkspaceError("conflict", "Project style has local edits; review them before applying an update.")
        staged = video / (".studio-style-" + uuid.uuid4().hex)
        backup = video / (".studio-style-backup-" + uuid.uuid4().hex)
        snapshot = {"style_id": style_id, "style_revision": source_revision,
                    "files": {x["path"]: x["after"] for x in changes if x["after"] is not None}, "at": _now()}
        try:
            staged.mkdir()
            for source in source_files:
                rel = source.relative_to(Path(root) / "styles" / style_id)
                _atomic_write(staged / rel, source.read_bytes())
            _atomic_write(staged / "snapshot.json", json.dumps(snapshot, indent=2).encode())
            if style_dir.exists():
                os.replace(style_dir, backup)
            try:
                os.replace(staged, style_dir)
            except OSError:
                if backup.exists():
                    os.replace(backup, style_dir)
                raise
        finally:
            if staged.exists():
                shutil.rmtree(staged)
            if backup.exists() and style_dir.exists():
                shutil.rmtree(backup)
    return {"slug": slug, "style_id": style_id, "style_revision": source_revision,
            "revision": _video_style_revision(root, slug), "changes": changes, "applied": True}


_CREATIVE_REF = re.compile(r"(?<![A-Za-z0-9_./-])(?:(?:\.\./)+|/media/|/)(?:_runtime|_shared|library|styles|characters)/[A-Za-z0-9_./-]+\.(?:js|css|png|jpg|jpeg|webp|gif|avif|svg|json|ttf|woff2?)")
_SCENE_LOCAL_REF = re.compile(r"(?P<quote>['\"])(?P<value>(?:\./|\.\./)+[A-Za-z0-9_./-]+\.(?:js|css|png|jpg|jpeg|webp|gif|avif|svg|json|ttf|woff2?))(?P=quote)")
_SCENE_IMPORT_REF = re.compile(r"(?P<prefix>\bimport\s*(?:\(\s*|(?:[^'\"`]*?\bfrom\s*)?))(?P<quote>['\"])(?P<value>(?:\./|\.\./)+[A-Za-z0-9_./-]+\.(?:js|css|png|jpg|jpeg|webp|gif|avif|svg|json|ttf|woff2?))(?P=quote)")
_SHARED_ROOTS = ("_runtime/", "_shared/", "library/", "styles/", "characters/")


def _creative_source(root: Path, style_id: str, characters: list[dict]) -> tuple[dict[str, bytes], dict]:
    """Resolve reviewed source bytes once; paths in the returned tree belong to the video."""
    from studio.creative import creative_review_state
    from studio.characters import snapshot_variant_for_style
    from studio.character_motion import compile_character_pack, ENGINE

    root = Path(root).resolve()
    style = _style(root, style_id)
    if style["origin"] == "existing-reference":
        raise WorkspaceError("blocked", "Imported reference styles need an authored approved variant.")
    review = creative_review_state(root, "style", style_id, "sample")
    if review["state"] not in {"approved", "accepted"} or not review["ready"]:
        raise WorkspaceError("blocked", "Current approved style samples are required.")
    if not isinstance(characters, list):
        raise WorkspaceError("invalid", "Characters must be a list of selected variants and actions.")
    files: dict[str, bytes] = {}
    source_hashes: dict[str, str] = {}
    def take(source: Path, target: str) -> None:
        relative = source.relative_to(root).as_posix()
        safe_path(root, relative)
        data = _read_bytes(source)
        source_hashes[relative] = _hash(data)
        files[target] = data

    style_folder = root / "styles" / style_id
    style_sources = _style_files(root, style_id)
    assets = style_folder / "02_assets"
    if assets.is_dir():
        style_sources += sorted(p for p in assets.rglob("*") if p.is_file() and not p.is_symlink())
    for source in style_sources:
        take(source, "style/" + source.relative_to(style_folder).as_posix())
    # Runtime references in authored HTML/CSS/JS follow their source path, then become owned relative URLs.
    pending = [path for path in files if Path(path).suffix.lower() in {".html", ".css", ".js"}]
    while pending:
        target = pending.pop()
        source = style_folder / target.removeprefix("style/") if target.startswith("style/") else root / target.removeprefix("deps/")
        text = files[target].decode("utf-8")
        def replace(match):
            value = match.group()
            try:
                relative = value.removeprefix("/media/").lstrip("/") if value.startswith("/") else (source.parent / value).resolve().relative_to(root).as_posix()
            except ValueError:
                raise WorkspaceError("invalid", "Creative runtime asset leaves the workspace.") from None
            dependency = safe_path(root, relative)
            if not dependency.is_file():
                raise WorkspaceError("missing", f"Creative runtime asset is missing: {relative}.")
            owned = "deps/" + relative
            if owned not in files:
                take(dependency, owned)
                if dependency.suffix.lower() in {".html", ".css", ".js"}:
                    pending.append(owned)
            return os.path.relpath(owned, Path(target).parent).replace(os.sep, "/")
        files[target] = _CREATIVE_REF.sub(replace, text).encode("utf-8")

    selected = []
    seen = set()
    if characters:
        engine = _read_bytes(ENGINE)
        files["character.js"] = engine
        source_hashes["_runtime/character.js"] = _hash(engine)
    for entry in characters:
        if not isinstance(entry, dict) or set(entry) != {"character_id", "variant_id", "actions"}:
            raise WorkspaceError("invalid", "Character selection needs character_id, variant_id and actions.")
        ident, variant = _id(entry["character_id"]), _id(entry["variant_id"])
        actions = entry["actions"]
        if not isinstance(actions, list) or not actions or any(not isinstance(a, str) or not ID.fullmatch(a) for a in actions) or len(set(actions)) != len(actions):
            raise WorkspaceError("invalid", "Select distinct reviewed character actions.")
        if (ident, variant) in seen:
            raise WorkspaceError("invalid", "Character variant was selected twice.")
        seen.add((ident, variant))
        identity = creative_review_state(root, "character", ident, "identity")
        if identity["state"] not in {"approved", "accepted"} or not identity["ready"]:
            raise WorkspaceError("blocked", "Current approved character identity is required.")
        snapshot_variant_for_style(root, ident, variant, style_id)
        for action in actions:
            gate = creative_review_state(root, "character", ident, f"animation:{variant}:{action}")
            if gate["state"] not in {"approved", "accepted"} or not gate["ready"]:
                raise WorkspaceError("blocked", f"Current approved {ident} {action} action is required.")
        compiled = compile_character_pack(root, ident, variant)
        if set(actions) - set(compiled["actions"]):
            raise WorkspaceError("unavailable", "A selected character action is unavailable.")
        base = f"characters/{ident}/{variant}"
        if f"{base}/manifest.json" in files:
            raise WorkspaceError("invalid", "Character snapshot path is already selected.")
        manifest = {"schema": 1, "canvas": compiled["canvas"], "views": json.loads(json.dumps(compiled["views"])),
                    "actions": {a: compiled["actions"][a] for a in actions}}
        source_art = {}
        for view in manifest["views"].values():
            for part in view["parts"].values():
                original = part["path"]
                source = safe_path(root, original)
                if _file_hash(source) != part["sha256"]:
                    raise WorkspaceError("conflict", "Character artwork changed before snapshot.")
                owned = source_art.setdefault(original, f"{base}/art/{part['sha256']}{source.suffix.lower()}")
                if owned not in files:
                    take(source, owned)
                part["path"] = f"videos/{{slug}}/creative/{owned}"
                part["url"] = f"../creative/{owned}"
        # The placeholder is filled after the video slug is known; no shared artwork URLs remain.
        pack = root / "characters" / ident / "03_animation" / variant
        for name in ("assets", "rig", "motions"):
            source_hashes[(pack / f"{name}.json").relative_to(root).as_posix()] = _file_hash(pack / f"{name}.json")
        files[f"{base}/rig.json"] = json.dumps({"schema": 1, "views": {v: d["rig"] for v, d in manifest["views"].items()}}, indent=2).encode()
        files[f"{base}/assets.json"] = json.dumps({"schema": 1, "canvas": manifest["canvas"], "views": {v: d["parts"] for v, d in manifest["views"].items()}}, indent=2).encode()
        files[f"{base}/motions.json"] = json.dumps({"schema": 1, "actions": manifest["actions"]}, indent=2).encode()
        files[f"{base}/manifest.json"] = json.dumps(manifest, indent=2).encode()
        selected.append({"character_id": ident, "variant_id": variant, "actions": actions,
                         "identity_revision": identity["fingerprint"],
                         "action_revisions": {a: creative_review_state(root, "character", ident, f"animation:{variant}:{a}")["fingerprint"] for a in actions},
                         "manifest": f"creative/{base}/manifest.json"})
    return files, {"style_id": style_id, "renderer": style["renderer"], "style_revision": review["fingerprint"],
                   "characters": selected, "source_files": source_hashes}


def _scene_shared_path(root: Path, index: Path, value: str) -> str:
    try:
        relative = value.removeprefix("/media/").lstrip("/") if value.startswith("/") else (index.parent / value).resolve().relative_to(root).as_posix()
    except ValueError:
        raise WorkspaceError("invalid", "Scene runtime asset leaves the workspace.") from None
    safe_path(root, relative)
    return relative


def _rewrite_scene_shared(root: Path, source: Path, text: str, resolve) -> str:
    def local(match):
        relative = _scene_shared_path(root, source, match["value"])
        if not relative.startswith(_SHARED_ROOTS):
            return match.group()
        return match.groupdict().get("prefix", "") + match["quote"] + resolve(relative, match["value"]) + match["quote"]
    pattern = _SCENE_IMPORT_REF if source.suffix.lower() == ".js" and source.relative_to(root).parts[0] != "videos" else _SCENE_LOCAL_REF
    text = pattern.sub(local, text)
    return _CREATIVE_REF.sub(lambda match: resolve(_scene_shared_path(root, source, match.group()), match.group()), text)


def creative_scene_source(root: Path, slug: str, relative: str) -> str:
    """Serve editable scene text while resolving its reviewed shared dependency inventory."""
    root = Path(root).resolve()
    video = _slug_path(root, slug)
    if not relative or Path(relative).suffix.lower() not in {".html", ".js", ".css"}:
        raise WorkspaceError("invalid", "Scene source is not HTML, JavaScript or CSS.")
    index = safe_path(root, f"videos/{slug}/04_scene/{relative}")
    if video / "04_scene" not in index.parents:
        raise WorkspaceError("invalid", "Scene source leaves its folder.")
    snapshot = video / "creative/snapshot.json"
    try:
        files = json.loads(snapshot.read_text(encoding="utf-8"))["files"]
        text = index.read_text(encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError):
        raise WorkspaceError("invalid", "Creative scene or snapshot metadata is malformed.") from None
    if not isinstance(files, dict):
        raise WorkspaceError("invalid", "Creative snapshot file list is malformed.")
    def replace(relative, value):
        owned = f"videos/{slug}/creative/deps/{relative}"
        if owned not in files or not safe_path(root, owned).is_file():
            raise WorkspaceError("conflict", "Scene runtime changed; reapply the creative snapshot.")
        return os.path.relpath(root / owned, index.parent).replace(os.sep, "/")
    return _rewrite_scene_shared(root, index, text, replace)


def creative_scene_html(root: Path, slug: str) -> str:
    return creative_scene_source(root, slug, "index.html")


def _legacy_scene_renderer(video: Path) -> tuple[str, str]:
    """Infer only unambiguous legacy engines from the video's own authored scene."""
    index = video / "04_scene/index.html"
    try:
        html = index.read_text(encoding="utf-8")
    except OSError:
        raise WorkspaceError("blocked", "Video has no recorded scene renderer; recreate or identify its scene before applying creative assets.") from None
    scripts = set(re.findall(r"(?:(?:\.\./)+_)?runtime/([a-z-]+)\.js", html))
    if "modern" not in scripts:
        raise WorkspaceError("blocked", "Video has no unambiguous recorded scene renderer.")
    renderer = "modern"
    width = re.search(r'data-width="([0-9]+)"', html)
    height = re.search(r'data-height="([0-9]+)"', html)
    if not width or not height or int(width[1]) == int(height[1]):
        raise WorkspaceError("blocked", "Video has no unambiguous scene format.")
    return renderer, "wide" if int(width[1]) > int(height[1]) else "tall"


def _creative_plan(root: Path, slug: str, style_id: str, characters: list[dict]) -> tuple[dict, dict[str, bytes]]:
    root = Path(root).resolve()
    video = _slug_path(root, slug)
    if not video.is_dir():
        raise WorkspaceError("missing", "Video does not exist.")
    metadata = _project_metadata(root, slug)
    renderer = metadata.get("renderer")
    if renderer is not None and (not isinstance(renderer, str) or not ID.fullmatch(renderer)):
        raise WorkspaceError("invalid", "Video scene renderer metadata is malformed.")
    legacy_renderer, legacy_format = (None, None)
    if renderer is None or metadata.get("format") is None:
        legacy_renderer, legacy_format = _legacy_scene_renderer(video)
    current_renderer = renderer or legacy_renderer
    selected_style = _style(root, style_id)
    if current_renderer != selected_style["renderer"]:
        raise WorkspaceError("blocked", "Video scene renderer does not match the selected style.")
    video_format = metadata.get("format") or legacy_format
    if video_format not in {"wide", "tall"}:
        raise WorkspaceError("invalid", "Video project format is malformed.")
    if selected_style["supported_formats"] and video_format not in selected_style["supported_formats"]:
        raise WorkspaceError("blocked", "Selected style has no approved sample for this video format.")
    files, provenance = _creative_source(root, style_id, characters)
    scene = video / "04_scene"
    pending = []
    if scene.is_dir():
        for source in sorted(scene.rglob("*")):
            if source.is_file() and not source.is_symlink() and source.suffix.lower() in {".html", ".js", ".css"}:
                data = _read_bytes(source)
                provenance["source_files"][source.relative_to(root).as_posix()] = _hash(data)
                _rewrite_scene_shared(root, source, data.decode("utf-8"), lambda relative, value: pending.append(relative) or value)
    visited = set()
    while pending:
        relative = pending.pop()
        if relative in visited:
            continue
        visited.add(relative)
        owned = "deps/" + relative
        source = safe_path(root, relative)
        if not source.is_file():
            raise WorkspaceError("missing", f"Scene runtime asset is missing: {relative}.")
        data = _read_bytes(source)
        provenance["source_files"][relative] = _hash(data)
        if source.suffix.lower() in {".html", ".js", ".css"}:
            def replace(dependency, value):
                pending.append(dependency)
                return os.path.relpath(video / "creative/deps" / dependency,
                                       (video / "creative" / owned).parent).replace(os.sep, "/")
            data = _rewrite_scene_shared(root, source, data.decode("utf-8"), replace).encode("utf-8")
        files[owned] = data
        if relative == "_runtime/fonts/fonts.css":
            pending.extend(p.relative_to(root).as_posix() for p in sorted((root / "_runtime/fonts").rglob("*"))
                           if p.is_file() and not p.is_symlink())
        if relative == "_runtime/lib.js":
            vendor = root / "_runtime/vendor/lottie_canvas.min.js"
            if vendor.is_file(): pending.append(vendor.relative_to(root).as_posix())
    # Resolve the video-local raster path in the browser manifest.
    for name in list(files):
        if name.endswith("/manifest.json"):
            files[name] = files[name].replace(b"{slug}", slug.encode())
    folder = video / "creative"
    manifest_path = folder / "snapshot.json"
    try:
        old = json.loads(manifest_path.read_text()) if manifest_path.is_file() else None
    except (OSError, ValueError):
        raise WorkspaceError("invalid", "Video creative snapshot metadata is malformed.") from None
    if old is not None and (not isinstance(old, dict) or set(old) != {"schema", "style_id", "renderer", "characters", "source_revision", "source_files", "files", "at"} or
                            old["schema"] != 1 or not isinstance(old["style_id"], str) or not isinstance(old["renderer"], str) or
                            not isinstance(old["characters"], list) or not isinstance(old["source_revision"], str) or
                            not isinstance(old["source_files"], dict) or not isinstance(old["at"], str) or
                            any(not isinstance(p, str) or not isinstance(h, str) or len(h) != 64 for p, h in old["source_files"].items())):
        raise WorkspaceError("invalid", "Video creative snapshot metadata is malformed.")
    previous = old.get("files", {}) if isinstance(old, dict) else {}
    if not isinstance(previous, dict) or any(not isinstance(p, str) or not isinstance(h, str) or not h for p, h in previous.items()):
        raise WorkspaceError("invalid", "Video creative snapshot metadata is malformed.")
    if folder.is_dir() and any(p.is_symlink() for p in folder.rglob("*")):
        raise WorkspaceError("invalid", "Video creative snapshot contains a symbolic link.")
    actual = {p.relative_to(root).as_posix(): _file_hash(p) for p in folder.rglob("*") if p.is_file() and p != manifest_path} if folder.is_dir() else {}
    expected = {f"videos/{slug}/creative/{name}": _hash(data) for name, data in files.items()}
    for path in previous:
        target = safe_path(root, path)
        if folder not in target.parents:
            raise WorkspaceError("invalid", "Video creative snapshot contains a path outside its folder.")
    protected = sorted(path for path in set(actual) | set(previous) if actual.get(path) != previous.get(path))
    changes = [{"path": path, "before": actual.get(path), "after": expected.get(path),
                "protected": path in protected} for path in sorted(set(actual) | set(expected)) if actual.get(path) != expected.get(path)]
    source_revision = _hash(json.dumps(provenance, sort_keys=True).encode())
    video_revision = _hash(json.dumps({"manifest": _file_hash(manifest_path) if manifest_path.is_file() else None,
                                       "actual": actual}, sort_keys=True).encode())
    proposal = {"slug": slug, "style_id": style_id, "characters": provenance["characters"],
                "source_revision": source_revision, "video_revision": video_revision,
                "source_files": provenance["source_files"],
                "revision": _hash(json.dumps([source_revision, video_revision]).encode()),
                "changes": changes, "protected": protected, "applied": False}
    return proposal, files


def propose_creative_snapshot(root: Path, slug: str, style_id: str, characters: list[dict]) -> dict:
    return _creative_plan(root, slug, style_id, characters)[0]


def apply_creative_snapshot(root: Path, slug: str, style_id: str, characters: list[dict], expected_revision: str | None,
                            confirm: bool = False) -> dict:
    if not confirm:
        return propose_creative_snapshot(root, slug, style_id, characters)
    root = Path(root).resolve()
    with workspace_lock(root):
        proposal, files = _creative_plan(root, slug, style_id, characters)
        if proposal["revision"] != expected_revision:
            raise WorkspaceError("conflict", "Creative source or video changed since proposal.")
        if proposal["protected"]:
            raise WorkspaceError("conflict", "Video creative snapshot has local edits or removals.")
        video = _slug_path(root, slug)
        target = video / "creative"
        staged = video / (".studio-creative-" + uuid.uuid4().hex)
        backup = video / (".studio-creative-backup-" + uuid.uuid4().hex)
        try:
            staged.mkdir()
            hashes = {}
            for name, data in files.items():
                _atomic_write(staged / name, data)
                hashes[f"videos/{slug}/creative/{name}"] = _hash(data)
            snapshot = {"schema": 1, "style_id": style_id, "renderer": _style(root, style_id)["renderer"],
                        "characters": proposal["characters"], "source_revision": proposal["source_revision"],
                        "source_files": proposal["source_files"],
                        "files": hashes, "at": _now()}
            _atomic_write(staged / "snapshot.json", json.dumps(snapshot, indent=2).encode())
            if _creative_plan(root, slug, style_id, characters)[0]["revision"] != expected_revision:
                raise WorkspaceError("conflict", "Creative source or video changed while preparing snapshot.")
            if target.exists():
                os.replace(target, backup)
            try:
                os.replace(staged, target)
            except OSError:
                if backup.exists(): os.replace(backup, target)
                raise
        finally:
            if staged.exists(): shutil.rmtree(staged)
            if backup.exists() and target.exists(): shutil.rmtree(backup)
    return {**proposal, "applied": True, "video_revision": _file_hash(target / "snapshot.json")}


def check_brand(root: Path, brand: str, renderer: str) -> str:
    """Validate a brand id for a new video; shared by `anim.py new` and create_video."""
    if not isinstance(brand, str) or not re.fullmatch(r"[a-z0-9_][a-z0-9_-]*", brand) or not (Path(root) / "brands" / brand / "tokens.js").is_file():
        known = sorted(p.parent.name for p in (Path(root) / "brands").glob("*/tokens.js"))
        raise WorkspaceError("invalid", f"unknown brand '{brand}'. Known brands: {', '.join(known) or 'none'} (choose a brand)")
    return brand


def stamp_brand(scene_dir: Path, brand: str) -> None:
    """Fill the {{BRAND}} placeholder in a copied scene template."""
    index = Path(scene_dir) / "index.html"
    text = index.read_text(encoding="utf-8").replace("{{BRAND}}", brand)
    videos = next((p for p in Path(scene_dir).resolve().parents if p.name == "videos"), None)
    if videos is not None:
        prefix = os.path.relpath(videos.parent, scene_dir).replace(os.sep, "/") + "/"
        text = text.replace("../../../", prefix)
    index.write_text(text, encoding="utf-8")


def stamp_modern_scene(scene_dir: Path, brand: str, title: str) -> None:
    """Fill a copied Modern scene template and link brand, runtime and cues into it.
    The page loads brand/tokens.js, runtime/player.js and cues/cues.js through these links, so a scene
    folder looks the same for every brand and the paths never depend on how deep the video sits."""
    scene_dir = Path(scene_dir)
    stamp_brand(scene_dir, brand)
    for page in scene_dir.glob("*.html"):
        page.write_text(page.read_text(encoding="utf-8").replace("{{TITLE}}", html.escape(title)), encoding="utf-8")
    videos = next(p for p in scene_dir.resolve().parents if p.name == "videos")
    prefix = os.path.relpath(videos.parent, scene_dir)
    for name, target in (("brand", f"{prefix}/brands/{brand}"), ("runtime", f"{prefix}/_runtime"), ("cues", "../03_cues")):
        if not (scene_dir / name).is_symlink():
            (scene_dir / name).symlink_to(target, target_is_directory=True)


ENGINES = ("canvas", "hyperframes")


def check_engine(engine: str, style: str | None) -> str:
    """Validate the render engine for a new video; hyperframes takes no canvas style."""
    if engine not in ENGINES:
        raise WorkspaceError("invalid", f"unknown engine '{engine}'. Known engines: {', '.join(ENGINES)} (default: canvas)")
    if engine == "hyperframes" and style not in (None, "none"):
        raise WorkspaceError("invalid", "the hyperframes engine takes no --style; leave it out or use --style none")
    return engine


def stamp_hf_scene(scene_dir: Path, brand: str, voice: str = "voice.mp3") -> None:
    """Fill a copied HyperFrames scene template and link brand, runtime, voice and cues into it.
    HyperFrames serves 04_scene/ as the project root and rejects ../ paths, so links keep paths inside it."""
    scene_dir = Path(scene_dir)
    stamp_brand(scene_dir, brand)
    index = scene_dir / "index.html"
    index.write_text(index.read_text(encoding="utf-8").replace("{{VOICE}}", voice), encoding="utf-8")
    videos = next(p for p in scene_dir.resolve().parents if p.name == "videos")
    prefix = os.path.relpath(videos.parent, scene_dir)
    for name, target in (("brand", f"{prefix}/brands/{brand}"), ("runtime", f"{prefix}/_runtime"), ("voice", "../01_voice"), ("cues", "../03_cues")):
        (scene_dir / name).symlink_to(target, target_is_directory=True)


def create_video(root: Path, slug: str, brief: dict, format: str = "wide", style: str = "modern", style_id: str | None = None, brand: str | None = None, engine: str = "canvas") -> dict:
    _id(slug)
    if style_id is not None:
        style = _id(style_id)
    if format not in {"wide", "tall"} or not isinstance(brief, dict) or any(not isinstance(brief.get(k), str) or not brief[k].strip() or "\n" in brief[k] for k in ("audience", "video_type", "language", "outcome")):
        raise WorkspaceError("invalid", "Provide audience, video type, language, outcome and a valid format.")
    check_engine(engine, None if (engine == "hyperframes" and style == "modern" and style_id is None) else style)
    hf = engine == "hyperframes"
    if hf:
        style, renderer = "none", "hyperframes"
    else:
        renderer = "modern" if style == "modern" else _style(root, style)["renderer"]
    check_brand(root, brand, renderer)
    template = Path(root) / "_templates/video"
    scene = Path(root) / "_templates" / (f"scene-hf-{format}" if hf else f"scene-{renderer}-{format}")
    if not template.is_dir() or not scene.is_dir():
        raise WorkspaceError("blocked", f"An authored {renderer} {format} scene template is required.")
    dest = Path(root) / "videos" / brand / slug
    video_id = f"{brand}/{slug}"
    with workspace_lock(root):
        if dest.exists():
            raise WorkspaceError("conflict", "Video slug already exists.")
        dest.parent.mkdir(parents=True, exist_ok=True)
        temp = dest.parent / (".studio-new-" + uuid.uuid4().hex)
        try:
            shutil.copytree(template, temp)
            shutil.copytree(scene, temp / "04_scene", dirs_exist_ok=True)
            title = slug.replace("-", " ").title()
            if hf:
                stamp_hf_scene(temp / "04_scene", brand)
            else:
                stamp_modern_scene(temp / "04_scene", brand, title)
            text = (temp / "01_voice/brief.md").read_text(encoding="utf-8")
            for label, key in (("Type", "video_type"), ("Language", "language"), ("Audience", "audience"), ("One outcome", "outcome")):
                text = re.sub(rf"(?m)^- {label}:.*$", lambda _: f"- {label}: {brief[key]}", text)
            _atomic_write(temp / "01_voice/brief.md", text.encode("utf-8"))
            _atomic_write(temp / "project.json", json.dumps({"format": format, "style": style, "renderer": renderer,
                "brand": brand, "engine": engine, "title": title}).encode())
            if not hf and style != "modern":
                source_files = _style_files(root, style)
                hashes = {}
                for source in source_files:
                    relative = source.relative_to(Path(root) / "styles" / style)
                    target = temp / "style" / relative
                    _atomic_write(target, source.read_bytes())
                    hashes[f"videos/{video_id}/style/{relative.as_posix()}"] = _file_hash(source)
                _atomic_write(temp / "style/snapshot.json", json.dumps({"style_id": style, "style_revision": _style_revision(root, style), "files": hashes, "at": _now()}, indent=2).encode())
            from studio.project_paths import settings_snapshot
            settings_snapshot(root, temp)
            os.replace(temp, dest)
        except Exception:
            if temp.exists():
                shutil.rmtree(temp)
            raise
    return video_detail(root, video_id)
