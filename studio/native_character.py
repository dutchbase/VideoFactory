"""Small, guarded adapter for local Synfig character projects.

The renderer consumes editable .sif projects. A project is run from its own
directory so its relative bitmap imports remain portable and auditable.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import select
import shutil
import signal
import struct
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


class NativeCharacterError(RuntimeError):
    """A native project, render, or cue file failed a safety check."""


MAX_NATIVE_MEMORY = 4 * 1024**3
MIN_NATIVE_THREADS = 2  # Synfig 1.4.5 enforces a two-worker render-queue minimum.
MAX_NATIVE_THREADS = 4
RHUBARB_SHAPES = frozenset("ABCDEFGHX")
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PROJECT_IMPORT_CACHE: OrderedDict[str, tuple[str, ...]] = OrderedDict()
_PROJECT_IMPORT_CACHE_LOCK = threading.Lock()


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise NativeCharacterError(f"{field} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise NativeCharacterError(f"{field} must be a finite number")
    return result


def validate_rhubarb_cues(raw: Mapping[str, Any], *, duration: float) -> list[dict[str, Any]]:
    """Validate raw Rhubarb JSON and return normalized cues without mutating it."""
    duration = _finite_number(duration, "duration")
    if duration <= 0:
        raise NativeCharacterError("duration must be greater than zero")
    if not isinstance(raw, Mapping) or not isinstance(raw.get("mouthCues"), list):
        raise NativeCharacterError("Rhubarb JSON must contain a mouthCues list")

    cues: list[dict[str, Any]] = []
    previous_start = -1.0
    previous_end = 0.0
    for index, item in enumerate(raw["mouthCues"]):
        if not isinstance(item, Mapping):
            raise NativeCharacterError(f"mouth cue {index} must be an object")
        start = _finite_number(item.get("start"), f"mouth cue {index} start")
        end = _finite_number(item.get("end"), f"mouth cue {index} end")
        value = item.get("value")
        if value not in RHUBARB_SHAPES:
            raise NativeCharacterError(f"mouth cue {index} has unsupported Rhubarb shape {value!r}")
        if start < 0 or end <= start or end > duration + 1e-6:
            raise NativeCharacterError(f"mouth cue {index} must be a positive half-open interval within the audio")
        if start < previous_start or start < previous_end - 1e-6:
            raise NativeCharacterError(f"mouth cue {index} overlaps or is out of order")
        cues.append({"start": start, "end": end, "value": value})
        previous_start, previous_end = start, end
    return cues


def validate_correction_intervals(
    corrections: Sequence[Mapping[str, Any]], *, duration: float
) -> list[dict[str, Any]]:
    """Validate editor corrections as separate [start, end) cue intervals."""
    duration = _finite_number(duration, "duration")
    if duration <= 0 or not isinstance(corrections, Sequence) or isinstance(corrections, (str, bytes)):
        raise NativeCharacterError("corrections must be a list and duration must be positive")
    result: list[dict[str, Any]] = []
    previous_end = 0.0
    for index, item in enumerate(corrections):
        if not isinstance(item, Mapping):
            raise NativeCharacterError(f"correction {index} must be an object")
        start = _finite_number(item.get("start"), f"correction {index} start")
        end = _finite_number(item.get("end"), f"correction {index} end")
        value = item.get("value")
        if value not in RHUBARB_SHAPES:
            raise NativeCharacterError(f"correction {index} has unsupported Rhubarb shape {value!r}")
        if start < 0 or end <= start or end > duration + 1e-6:
            raise NativeCharacterError(f"correction {index} must be a positive half-open interval within the audio")
        if start < previous_end - 1e-6:
            raise NativeCharacterError(f"correction {index} overlaps or is out of order")
        result.append({"start": start, "end": end, "value": value})
        previous_end = end
    return result


def cue_at(
    time: float,
    cues: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    corrections: Sequence[Mapping[str, Any]] = (),
    *,
    duration: float,
) -> str:
    """Sample half-open Rhubarb intervals; corrections override raw cues and gaps are closed (X)."""
    sample_time = _finite_number(time, "cue sample time")
    duration = _finite_number(duration, "duration")
    if duration <= 0 or sample_time < 0 or sample_time > duration:
        raise NativeCharacterError("cue sample time must be within [0, duration]")
    if isinstance(cues, Mapping):
        raw = cues
    elif isinstance(cues, Sequence) and not isinstance(cues, (str, bytes)):
        raw = {"mouthCues": cues}
    else:
        raise NativeCharacterError("cues must be raw Rhubarb JSON or a cue list")
    validated_cues = validate_rhubarb_cues(raw, duration=duration)
    validated_corrections = validate_correction_intervals(corrections, duration=duration)
    for item in validated_corrections:
        if item["start"] <= sample_time < item["end"]:
            return item["value"]
    for item in validated_cues:
        if item["start"] <= sample_time < item["end"]:
            return item["value"]
    return "X"


def require_supported_shapes(cues: Sequence[Mapping[str, Any]], available_shapes: Sequence[str] | set[str]) -> None:
    """Block render when cues refer to mouth art not present in the reviewed rig."""
    available = set(available_shapes)
    missing = sorted(
        {
            "closed" if cue.get("value") == "X" else str(cue.get("value"))
            for cue in cues
            if ("closed" if cue.get("value") == "X" else cue.get("value")) not in available
        }
    )
    if missing:
        raise NativeCharacterError("missing authored mouth states: " + ", ".join(missing))


def _resolve_tool(explicit: str | os.PathLike[str] | None, env_name: str, executable: str) -> str | None:
    candidate = os.fspath(explicit) if explicit is not None else os.environ.get(env_name)
    if candidate:
        path = shutil.which(candidate) if os.path.sep not in candidate else candidate
        if path and Path(path).is_file() and os.access(path, os.X_OK):
            return str(Path(path).resolve())
        return None
    return shutil.which(executable)


def _tool_environment(binary: str) -> dict[str, str]:
    env = os.environ.copy()
    path = Path(binary).resolve()
    # Support a locally extracted official AppImage without FUSE. This is
    # intentionally path-derived; normal installations use their own loader.
    if path.name == "synfig" and path.parent.name == "bin" and path.parent.parent.name == "usr":
        root = path.parent.parent
        library_dirs = [root / "lib", root / "lib" / "x86_64-linux-gnu", root / "lib64"]
        if (root / "etc" / "synfig_modules.cfg").is_file():
            env["SYNFIG_ROOT"] = str(root)
            env["SYNFIG_MODULE_LIST"] = str(root / "etc" / "synfig_modules.cfg")
            old = env.get("LD_LIBRARY_PATH", "")
            env["LD_LIBRARY_PATH"] = os.pathsep.join(str(p) for p in library_dirs) + (os.pathsep + old if old else "")
    return env


def _version(binary: str, *, synfig: bool = False, version_flag: str = "--version") -> str:
    try:
        proc = subprocess.run(
            [binary, version_flag],
            cwd=Path(binary).parent,
            env=_tool_environment(binary) if synfig else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise NativeCharacterError(f"could not query {binary}: {exc}") from exc
    output = proc.stdout.strip()
    # Synfig 1.4.5 returns status 3 for informational switches such as
    # --version/--targets while still printing the requested result.
    if proc.returncode != 0 and not (synfig and re.search(r"\bsynfig\s+\d", output, re.I)):
        raise NativeCharacterError(f"{binary} --version failed: {output}")
    return output.splitlines()[0] if output else "unknown"


def capabilities(
    *,
    synfig_bin: str | os.PathLike[str] | None = None,
    rhubarb_bin: str | os.PathLike[str] | None = None,
    ffmpeg_bin: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Return installed local tools and pinned-version checks without rendering."""
    synfig = _resolve_tool(synfig_bin, "SYNFIG_BIN", "synfig")
    rhubarb = _resolve_tool(rhubarb_bin, "RHUBARB_BIN", "rhubarb")
    ffmpeg = _resolve_tool(ffmpeg_bin, "FFMPEG_BIN", "ffmpeg")
    result: dict[str, Any] = {"renderer": None, "lip_sync": None, "audio_converter": None}
    if synfig:
        version = _version(synfig, synfig=True)
        target_proc = subprocess.run(
            [synfig, "--targets"], env=_tool_environment(synfig), cwd=Path(synfig).parent,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20, check=False
        )
        result["renderer"] = {
            "name": "Synfig",
            "path": synfig,
            "version": version,
            "pinned": "1.4.5" in version,
            "png_target": re.search(r"\bpng\b", target_proc.stdout, re.I) is not None,
        }
    if rhubarb:
        version = _version(rhubarb)
        result["lip_sync"] = {
            "name": "Rhubarb Lip Sync",
            "path": rhubarb,
            "version": version,
            "pinned": "1.14.0" in version,
        }
    if ffmpeg:
        version = _version(ffmpeg, version_flag="-version")
        result["audio_converter"] = {"name": "FFmpeg", "path": ffmpeg, "version": version}
    return result


def _read_png(path: Path) -> tuple[int, int, int]:
    with path.open("rb") as stream:
        header = stream.read(26)
    if len(header) < 26 or header[:8] != _PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise NativeCharacterError(f"renderer output is not a valid PNG: {path}")
    width, height = struct.unpack(">II", header[16:24])
    color_type = header[25]
    return width, height, color_type


def _png_alpha_min(path: Path) -> int:
    try:
        from PIL import Image
    except ImportError as exc:
        raise NativeCharacterError("Pillow is required to verify transparent PNG output") from exc
    try:
        with Image.open(path) as image:
            if image.mode not in ("RGBA", "LA"):
                raise NativeCharacterError(f"frame does not contain an alpha channel: {path.name}")
            return image.getchannel("A").getextrema()[0]
    except OSError as exc:
        raise NativeCharacterError(f"cannot decode renderer PNG {path}: {exc}") from exc


def _read_proc_memory(pid: int) -> tuple[int, int, int]:
    try:
        fields = {}
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith(("VmRSS:", "VmHWM:", "VmSwap:")):
                key, value, *_ = line.split()
                fields[key[:-1]] = int(value) * 1024
            elif line.startswith("Threads:"):
                fields["Threads"] = int(line.split()[1])
        return max(fields.get("VmRSS", 0), fields.get("VmHWM", 0)), fields.get("VmSwap", 0), fields.get("Threads", 0)
    except (OSError, ValueError):
        return 0, 0, 0


def _stop_process_group(proc: subprocess.Popen[Any]) -> None:
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass


def _process_start_identity(pid: int) -> str:
    """Return Linux process start ticks to distinguish PID reuse in job records."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
        tail = stat[stat.rfind(")") + 1 :].split()
        return tail[19]
    except (OSError, IndexError):
        return ""


def _project_imports(raw: bytes) -> tuple[str, ...]:
    # Cache only validated XML names, never file existence, confinement or hashes.
    digest = hashlib.sha256(raw).hexdigest()
    with _PROJECT_IMPORT_CACHE_LOCK:
        if digest in _PROJECT_IMPORT_CACHE:
            _PROJECT_IMPORT_CACHE.move_to_end(digest)
            return _PROJECT_IMPORT_CACHE[digest]
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise NativeCharacterError("SIF entity declarations are not allowed")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise NativeCharacterError(f"invalid SIF XML: {exc}") from exc
    if root.tag != "canvas":
        raise NativeCharacterError("project root must be a Synfig canvas")
    try:
        fps = float(root.attrib.get("fps", "0"))
    except ValueError as exc:
        raise NativeCharacterError("SIF canvas fps must be numeric") from exc
    if not math.isfinite(fps) or fps <= 0:
        raise NativeCharacterError("SIF canvas fps must be positive")

    imports = []
    for layer in root.iter("layer"):
        if layer.attrib.get("type") != "import":
            continue
        node = layer.find("./param[@name='filename']/string")
        if node is None or not (node.text or "").strip():
            raise NativeCharacterError("each import layer must name a relative bitmap")
        rel = Path(node.text.strip())
        if rel.is_absolute() or ".." in rel.parts or rel.anchor:
            raise NativeCharacterError(f"SIF import path must stay inside the project folder: {rel}")
        imports.append(rel.as_posix())
    result = tuple(imports)
    with _PROJECT_IMPORT_CACHE_LOCK:
        _PROJECT_IMPORT_CACHE[digest] = result
        _PROJECT_IMPORT_CACHE.move_to_end(digest)
        if len(_PROJECT_IMPORT_CACHE) > 64:
            _PROJECT_IMPORT_CACHE.popitem(last=False)
    return result


def _safe_project_assets(project: Path) -> dict[str, Path]:
    try:
        raw = project.read_bytes()
    except OSError as exc:
        raise NativeCharacterError(f"cannot read project {project}: {exc}") from exc
    assets: dict[str, Path] = {}
    for name in _project_imports(raw):
        rel = Path(name)
        resolved = (project.parent / rel).resolve()
        try:
            resolved.relative_to(project.parent.resolve())
        except ValueError as exc:
            raise NativeCharacterError(f"SIF import escapes the project folder: {rel}") from exc
        if not resolved.is_file():
            raise NativeCharacterError(f"SIF import does not exist: {rel}")
        assets[rel.as_posix()] = resolved
    return assets


def project_dependencies(project_path: str | os.PathLike[str]) -> list[dict[str, str]]:
    """Return the validated relative bitmap dependency list and current hashes."""
    project = Path(project_path).resolve()
    return [
        {"path": name, "sha256": _hash_file(path)}
        for name, path in sorted(_safe_project_assets(project).items())
    ]


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_render_manifest(
    project_path: str | os.PathLike[str] | Mapping[str, str | os.PathLike[str]],
    manifest_path: str | os.PathLike[str],
    *,
    settings: Mapping[str, Any],
    capabilities_result: Mapping[str, Any],
    cues_path: str | os.PathLike[str] | None = None,
    audio_path: str | os.PathLike[str] | None = None,
    source_audio_path: str | os.PathLike[str] | None = None,
    dialog_path: str | os.PathLike[str] | None = None,
    corrections_path: str | os.PathLike[str] | None = None,
    recognition: Mapping[str, Any] | None = None,
    controls: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Write immutable-by-hash provenance for project, artwork, cues, audio and tools."""
    target = Path(manifest_path).resolve()
    projects = dict(project_path) if isinstance(project_path, Mapping) else {"default": project_path}
    if not projects:
        raise NativeCharacterError("native manifest needs at least one project")
    project_records: dict[str, dict[str, Any]] = {}
    for view, raw_project in sorted(projects.items()):
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", str(view)):
            raise NativeCharacterError(f"invalid native project/view name: {view!r}")
        project = Path(raw_project).resolve()
        try:
            project.relative_to(target.parent)
        except ValueError as exc:
            raise NativeCharacterError("registered project must stay inside its native folder") from exc
        assets = _safe_project_assets(project)
        project_records[str(view)] = {
            "path": os.path.relpath(project, target.parent),
            "sha256": _hash_file(project),
            "linked_assets": {name: {"sha256": _hash_file(path)} for name, path in sorted(assets.items())},
        }
    optional: dict[str, dict[str, str] | None] = {}
    optional_paths = (
        ("cues", cues_path),
        ("audio", audio_path),
        ("source_audio", source_audio_path),
        ("dialog", dialog_path),
        ("corrections", corrections_path),
    )
    for key, item in optional_paths:
        if item is None:
            optional[key] = None
            continue
        path = Path(item).resolve()
        if not path.is_file():
            raise NativeCharacterError(f"{key} input does not exist: {path}")
        try:
            path.relative_to(target.parent)
        except ValueError as exc:
            raise NativeCharacterError(f"registered {key} input must stay inside the native folder") from exc
        optional[key] = {"path": os.path.relpath(path, target.parent), "sha256": _hash_file(path)}
    controls_data = dict(controls or {})
    settings_data = dict(settings)
    recognition_data = dict(recognition or {})
    manifest = {
        "schema": 1,
        "projects": project_records,
        "cues": optional["cues"],
        "audio": optional["audio"],
        "source_audio": optional["source_audio"],
        "dialog": optional["dialog"],
        "corrections": optional["corrections"],
        "controls": controls_data,
        "controls_sha256": hashlib.sha256(
            json.dumps(controls_data, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "settings": settings_data,
        "settings_sha256": hashlib.sha256(
            json.dumps(settings_data, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "recognition": recognition_data,
        "recognition_sha256": hashlib.sha256(
            json.dumps(recognition_data, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "capabilities": {
            key: {
                item: value
                for item, value in record.items()
                if item in {"name", "version", "pinned", "png_target"}
            } if isinstance(record, Mapping) else record
            for key, record in capabilities_result.items()
        },
    }
    manifest["capabilities_sha256"] = hashlib.sha256(
        json.dumps(manifest["capabilities"], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def validate_native_registration(manifest_path: str | os.PathLike[str]) -> dict[str, Any]:
    """Verify registered source hashes; this never supplies or implies human approval."""
    manifest_file = Path(manifest_path).resolve()
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise NativeCharacterError(f"cannot read native manifest: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != 1:
        raise NativeCharacterError("native manifest must use schema 1")
    projects = manifest.get("projects")
    if not isinstance(projects, dict) or not projects:
        raise NativeCharacterError("native manifest is missing its projects mapping")
    for view, record in projects.items():
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise NativeCharacterError(f"registered project {view!r} is malformed")
        project = (manifest_file.parent / record["path"]).resolve()
        try:
            project.relative_to(manifest_file.parent)
        except ValueError as exc:
            raise NativeCharacterError(f"registered project {view!r} escapes its native folder") from exc
        if not project.is_file() or _hash_file(project) != record.get("sha256"):
            raise NativeCharacterError(f"registered project {view!r} hash is stale")
        actual = {entry["path"]: {"sha256": entry["sha256"]} for entry in project_dependencies(project)}
        if actual != record.get("linked_assets"):
            raise NativeCharacterError(f"registered linked artwork hashes are stale for {view!r}")
    for key in ("audio", "source_audio", "cues", "dialog", "corrections"):
        record = manifest.get(key)
        if record is None:
            continue
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise NativeCharacterError(f"registered {key} input is malformed")
        path = (manifest_file.parent / record["path"]).resolve()
        try:
            path.relative_to(manifest_file.parent)
        except ValueError as exc:
            raise NativeCharacterError(f"registered {key} input escapes its native folder") from exc
        if not path.is_file() or _hash_file(path) != record.get("sha256"):
            raise NativeCharacterError(f"registered {key} hash is stale")
    for key, digest_key in (
        ("controls", "controls_sha256"),
        ("settings", "settings_sha256"),
        ("recognition", "recognition_sha256"),
        ("capabilities", "capabilities_sha256"),
    ):
        payload = manifest.get(key)
        expected = manifest.get(digest_key)
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if digest != expected:
            raise NativeCharacterError(f"registered {key} hash is stale")
    return manifest


def render_project(
    project_path: str | os.PathLike[str],
    output_dir: str | os.PathLike[str],
    *,
    width: int,
    height: int,
    fps: float = 24,
    frame_count: int = 240,
    begin_frame: int = 0,
    threads: int = 4,
    synfig_bin: str | os.PathLike[str] | None = None,
    max_memory_bytes: int = MAX_NATIVE_MEMORY,
    require_no_swap: bool = True,
    progress_callback: Callable[[int, int], None] | None = None,
    cancel_event: threading.Event | Callable[[], bool] | None = None,
    on_process_start: Callable[[int, str], None] | None = None,
    timeout_seconds: float = 900,
) -> dict[str, Any]:
    """Render a local SIF frame sequence, enforcing conservative CPU/RAM limits."""
    project = Path(project_path).resolve()
    assets = _safe_project_assets(project)
    if width <= 0 or height <= 0 or frame_count <= 0:
        raise NativeCharacterError("width, height, and frame_count must be positive integers")
    if int(width) != width or int(height) != height or int(frame_count) != frame_count:
        raise NativeCharacterError("width, height, and frame_count must be integers")
    fps = _finite_number(fps, "fps")
    if fps <= 0:
        raise NativeCharacterError("fps must be positive")
    if isinstance(begin_frame, bool) or not isinstance(begin_frame, int) or begin_frame < 0:
        raise NativeCharacterError("begin_frame must be a nonnegative integer")
    if begin_frame + frame_count > 900 or (begin_frame + frame_count) / fps > 30:
        raise NativeCharacterError("native renders are limited to 900 frames and 30 seconds")
    timeout_seconds = _finite_number(timeout_seconds, "timeout_seconds")
    if timeout_seconds <= 0:
        raise NativeCharacterError("timeout_seconds must be positive")
    if threads < MIN_NATIVE_THREADS or threads > MAX_NATIVE_THREADS:
        raise NativeCharacterError(f"Synfig render-queue threads must be between {MIN_NATIVE_THREADS} and {MAX_NATIVE_THREADS}")
    max_memory_bytes = int(max_memory_bytes)
    if max_memory_bytes <= 0 or max_memory_bytes > MAX_NATIVE_MEMORY:
        raise NativeCharacterError("max_memory_bytes must be positive and no greater than 4 GiB")
    try:
        project_fps = float(ET.parse(project).getroot().attrib.get("fps", "0"))
    except (ET.ParseError, ValueError) as exc:
        raise NativeCharacterError(f"invalid project frame rate: {exc}") from exc
    if not math.isclose(project_fps, fps, rel_tol=0, abs_tol=1e-6):
        raise NativeCharacterError(f"project fps {project_fps:g} does not match requested fps {fps:g}")
    out_dir = Path(output_dir).resolve()
    if out_dir.exists():
        if not out_dir.is_dir():
            raise NativeCharacterError("render output path must be a directory")
        if any(out_dir.iterdir()):
            raise NativeCharacterError("render output directory must be empty; existing files are preserved")
    synfig = _resolve_tool(synfig_bin, "SYNFIG_BIN", "synfig")
    if not synfig:
        raise NativeCharacterError("Synfig executable not found; set SYNFIG_BIN")
    version = _version(synfig, synfig=True)
    if "1.4.5" not in version:
        raise NativeCharacterError(f"native render requires pinned Synfig 1.4.5; found {version}")
    env = _tool_environment(synfig)
    env["SYNFIG_RENDERING_THREADS"] = str(threads - 1)
    env["OMP_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    out_dir.mkdir(parents=True, exist_ok=True)
    if any(out_dir.iterdir()):
        raise NativeCharacterError("render output directory must be empty; existing files are preserved")
    base = out_dir / "frame.png"
    end_frame = begin_frame + frame_count - 1
    command = [
        synfig,
        # The Synfig target's scanline option creates a second worker pool;
        # keep it serial while the 4-thread render queue handles frame work.
        "-T", "1",
        "-w", str(width), "-h", str(height),
        "--begin-time", f"{begin_frame}f",
        "--end-time", f"{end_frame}f",
        "-t", "png",
        "-o", str(base),
        "-i", project.name,
    ]
    started = time.monotonic()
    try:
        proc = subprocess.Popen(
            command,
            cwd=project.parent,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,
            bufsize=0,
            start_new_session=True,
        )
    except OSError as exc:
        raise NativeCharacterError(f"could not start Synfig: {exc}") from exc
    process_start = _process_start_identity(proc.pid)
    if on_process_start:
        try:
            on_process_start(proc.pid, process_start)
        except Exception as exc:
            _stop_process_group(proc)
            raise NativeCharacterError(f"could not register Synfig process with job manager: {exc}") from exc

    log: list[str] = []
    partial = ""
    peak_rss = peak_swap = peak_process_threads = 0
    last_progress = -1
    startup_threads = 0
    frame_line = re.compile(r"Frame\s+(\d+)\s+of\s+(\d+)")
    deadline = started + timeout_seconds
    assert proc.stdout is not None
    descriptor = proc.stdout.fileno()
    os.set_blocking(descriptor, False)

    def consume(chunk: bytes) -> None:
        nonlocal partial, last_progress, startup_threads
        partial += chunk.decode("utf-8", errors="replace")
        parts = re.split(r"[\r\n]", partial)
        partial = parts.pop()
        for item in parts:
            if not item:
                continue
            log.append(item)
            thread_match = re.search(r"rendering threads\s+(\d+)", item, re.I)
            if thread_match:
                startup_threads = int(thread_match.group(1))
            if len(log) > 200:
                del log[:100]
            match = frame_line.search(item)
            if match:
                current, total = map(int, match.groups())
                last_progress = current
                if progress_callback:
                    progress_callback(current, total)

    failure: NativeCharacterError | None = None
    try:
        while True:
            active = proc.poll() is None
            if active and time.monotonic() >= deadline:
                failure = NativeCharacterError(f"Synfig render timed out after {timeout_seconds:g}s")
                break
            is_set = getattr(cancel_event, "is_set", None)
            cancelled = bool(is_set()) if callable(is_set) else bool(cancel_event and cancel_event())
            if active and cancelled:
                failure = NativeCharacterError("Synfig render cancelled")
                break
            if active:
                rss, swapped, process_threads = _read_proc_memory(proc.pid)
                peak_rss, peak_swap = max(peak_rss, rss), max(peak_swap, swapped)
                peak_process_threads = max(peak_process_threads, process_threads)
                if peak_rss > max_memory_bytes:
                    failure = NativeCharacterError(f"Synfig peak RSS exceeded {max_memory_bytes} bytes")
                    break
                if require_no_swap and peak_swap:
                    failure = NativeCharacterError(f"Synfig used {peak_swap} bytes of process swap")
                    break
            ready, _, _ = select.select([proc.stdout], [], [], 0.025)
            if ready:
                while True:
                    try:
                        chunk = os.read(descriptor, 65536)
                    except BlockingIOError:
                        break
                    if not chunk:
                        break
                    consume(chunk)
            if not active:
                break
        if failure:
            _stop_process_group(proc)
        # Drain remaining bytes without blocking, even after an exception trigger.
        while True:
            try:
                chunk = os.read(descriptor, 65536)
            except BlockingIOError:
                break
            except OSError:
                break
            if not chunk:
                break
            consume(chunk)
        if partial:
            log.append(partial)
            partial = ""
    finally:
        if proc.poll() is None:
            _stop_process_group(proc)
        proc.stdout.close()
    if failure:
        raise failure
    return_code = proc.wait()
    elapsed = time.monotonic() - started
    if return_code != 0:
        raise NativeCharacterError("Synfig failed: " + "\n".join(log[-30:]))
    if startup_threads != threads:
        observed = str(startup_threads) if startup_threads else "unreported"
        raise NativeCharacterError(f"Synfig render queue used {observed} threads; expected {threads}")

    frames = sorted(out_dir.glob("frame.*.png"))
    if not frames and (out_dir / "frame.png").is_file():
        frames = [out_dir / "frame.png"]
    if len(frames) != frame_count:
        raise NativeCharacterError(f"Synfig produced {len(frames)} frames; expected {frame_count}")
    frame_info = []
    transparent_samples: list[str] = []
    transparent_indexes = {0, len(frames) // 2, len(frames) - 1}
    for index, path in enumerate(frames):
        png_width, png_height, color_type = _read_png(path)
        if (png_width, png_height) != (width, height):
            raise NativeCharacterError(f"wrong frame dimensions in {path.name}: {png_width}x{png_height}")
        if color_type != 6:
            raise NativeCharacterError(f"frame is not RGBA-compatible (PNG color type {color_type}): {path.name}")
        if index in transparent_indexes:
            alpha_min = _png_alpha_min(path)
            if alpha_min >= 255:
                raise NativeCharacterError(f"frame has an all-opaque alpha channel: {path.name}")
            transparent_samples.append(path.name)
        frame_info.append({"file": path.name, "sha256": _hash_file(path)})
    return {
        "schema": 1,
        "status": "rendered_pending_review",
        "renderer": {"name": "Synfig", "version": version, "path": synfig, "target": "png"},
        "project": project.name,
        "project_sha256": _hash_file(project),
        "linked_assets": {name: _hash_file(path) for name, path in assets.items()},
        "pid": proc.pid,
        "process_start": process_start,
        "width": width,
        "height": height,
        "fps": fps,
        "frame_count": frame_count,
        "begin_frame": begin_frame,
        "threads": threads,
        "synfig_queue_threads": threads,
        "target_threads": 1,
        "peak_process_threads": peak_process_threads,
        "max_memory_bytes": max_memory_bytes,
        "peak_rss_bytes": peak_rss,
        "peak_swap_bytes": peak_swap,
        "elapsed_seconds": round(elapsed, 3),
        "output_dir": str(out_dir),
        "frames": frame_info,
        "alpha_verified_frames": transparent_samples,
        "log_tail": log[-20:],
        "progress_frame": last_progress,
    }
