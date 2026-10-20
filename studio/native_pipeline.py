"""Validated, cached Synfig character renders for the local Studio."""

from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import uuid
from pathlib import Path

from PIL import Image, ImageDraw

from studio.filehash import file_sha256
from studio.native_character import NativeCharacterError, _resolve_tool, _version, render_project, validate_native_registration


def _hash(path):
    return file_sha256(path)


_REQUEST = contextvars.ContextVar("native_request_cache", default=None)


@contextlib.contextmanager
def request_cache():
    """Reuse tree hashes and manifest validation for one read-only Studio request."""
    if _REQUEST.get() is not None:
        yield
        return
    token = _REQUEST.set({})
    try:
        yield
    finally:
        _REQUEST.reset(token)


def _request_cached(kind, key, compute):
    cache = _REQUEST.get()
    if cache is None:
        return compute()
    if (kind, key) not in cache:
        cache[(kind, key)] = compute()
    return cache[(kind, key)]


def source_tree_hash(folder):
    """Hash registered source and evidence, excluding generated render cache."""
    folder = Path(folder)
    files = sorted(path for path in folder.rglob("*") if path.is_file() and
                   path.relative_to(folder).parts[0] != "renders")
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(folder).as_posix().encode() + b"\0" + _hash(path).encode())
    return digest.hexdigest()


def _json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _selection(root, character, variant, view, action, expression):
    from studio.workspace import _id, safe_path

    for value in (character, variant, view, action, expression):
        _id(value)
    manifest_path = safe_path(root, f"characters/{character}/03_animation/{variant}/native/manifest.json")
    native = manifest_path.parent
    candidate = native.parent / "native-candidate/manifest.json"
    if candidate.is_file() and (not manifest_path.is_file() or
                                _request_cached("tree", candidate.parent, lambda: source_tree_hash(candidate.parent)) !=
                                _request_cached("tree", native, lambda: source_tree_hash(native))):
        raise NativeCharacterError("approved native candidate has not been activated")
    manifest = _request_cached("manifest", manifest_path, lambda: validate_native_registration(manifest_path))
    projects = manifest["projects"]
    controls = manifest.get("controls", {})
    if view not in projects or view not in ("front", "three-quarter-right"):
        raise NativeCharacterError("native view is not registered")
    # A project timeline must explicitly bind the selected action and expression.
    bindings = controls.get("bindings", {})
    binding = bindings.get(view, {}).get(action, {}).get(expression) if isinstance(bindings, dict) else None
    registered_paths = {item["path"] for name, item in projects.items() if name == view or name.startswith(view + "-")}
    if not isinstance(binding, dict) or binding.get("project") not in registered_paths:
        raise NativeCharacterError("native action/expression has no verified project binding")
    if (action != "idle" or expression != "neutral") and binding["project"] == projects[view]["path"]:
        raise NativeCharacterError("this action/expression needs its own registered project")
    if action == "talk" and any(not manifest.get(name) for name in ("audio", "cues", "corrections", "dialog")):
        raise NativeCharacterError("talk needs registered approved audio, raw cues, corrections and dialog")
    project = (native / binding["project"]).resolve()
    settings = manifest.get("settings", {})
    width, height, fps, frames = (settings.get(key) for key in ("width", "height", "fps", "frame_count"))
    if (not all(type(value) is int and value > 0 for value in (width, height, frames)) or
            isinstance(fps, bool) or not isinstance(fps, (int, float)) or fps <= 0):
        raise NativeCharacterError("native render settings are incomplete")
    if frames > 900 or frames / fps > 30:
        raise NativeCharacterError("native render exceeds the 30-second or 900-frame limit")
    synfig = _resolve_tool(None, "SYNFIG_BIN", "synfig")
    if not synfig or "1.4.5" not in _version(synfig, synfig=True):
        raise NativeCharacterError("pinned Synfig 1.4.5 is unavailable")
    ffmpeg = _resolve_tool(None, "FFMPEG_BIN", "ffmpeg")
    if not ffmpeg:
        raise NativeCharacterError("FFmpeg is unavailable")
    key = hashlib.sha256(json.dumps({"manifest": _hash(manifest_path), "view": view, "action": action,
                                     "expression": expression, "renderer_binary": _hash(synfig),
                                     "preview_encoder_binary": _hash(ffmpeg),
                                     "compositor_source": _hash(Path(__file__))}, sort_keys=True).encode()).hexdigest()
    return native, manifest, project, (width, height, fps, frames), key


def _valid_cache(directory, key, frame_count):
    try:
        data = _json(directory / "render.json")
        if data.get("source_fingerprint") != key or len(data.get("frames", [])) != frame_count:
            return None
        if _hash(directory / "preview.mp4") != data.get("preview_sha256"):
            return None
        if any((not isinstance(item.get("file"), str) or Path(item["file"]).name != item["file"] or
                not item["file"].endswith(".png") or
                _hash(directory / "frames" / item["file"]) != item["sha256"]) for item in data["frames"]):
            return None
        return data
    except (OSError, ValueError, TypeError, KeyError):
        return None


def render_native(root, character, variant, view, action, expression, *, progress=None, cancel_event=None):
    root = Path(root).resolve()
    native, manifest, project, (width, height, fps, frame_count), key = _selection(
        root, character, variant, view, action, expression)
    renders = native / "renders"
    target = renders / view / action / expression / key
    current = target.parent / "current.json"
    try: previous = _json(current)
    except (OSError, ValueError): previous = None
    cached = _valid_cache(target, key, frame_count) if target.is_dir() else None
    if cached:
        _atomic_json(current, {"source_fingerprint": key, "path": target.relative_to(root).as_posix()})
        if progress: progress(frame_count, frame_count)
        return cached | {"cached": True, "path": target.relative_to(root).as_posix()}
    if target.exists():
        raise NativeCharacterError("native cache exists but failed validation; inspect it before retrying")
    staging = renders / (".staging-" + uuid.uuid4().hex)
    staging.mkdir(parents=True)
    try:
        frame_dir = staging / "frames"
        data = render_project(project, frame_dir, width=width, height=height, fps=fps,
                              frame_count=frame_count, threads=4, progress_callback=progress, cancel_event=cancel_event)
        if cancel_event and cancel_event.is_set():
            raise NativeCharacterError("native render cancelled")
        # Only explicit names in the validated frame manifest reach ffmpeg.
        sequence = staging / "sequence"
        sequence.mkdir()
        for index, item in enumerate(data["frames"]):
            os.link(frame_dir / item["file"], sequence / f"{index:06d}.png")
        tile = Image.new("RGB", (width, height), "#eeeeee")
        draw = ImageDraw.Draw(tile)
        for y in range(0, height, 32):
            for x in range(0, width, 32):
                if (x // 32 + y // 32) % 2:
                    draw.rectangle((x, y, x + 31, y + 31), fill="#cccccc")
        tile.save(staging / "checker.png")
        ffmpeg = _resolve_tool(None, "FFMPEG_BIN", "ffmpeg")
        if not ffmpeg:
            raise NativeCharacterError("FFmpeg is unavailable")
        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-filter_threads", "1",
                   "-filter_complex_threads", "1", "-loop", "1", "-framerate", str(fps),
                   "-i", str(staging / "checker.png"), "-framerate", str(fps), "-i", str(sequence / "%06d.png")]
        audio = manifest.get("audio") if action == "talk" else None
        if audio:
            command += ["-i", str(native / audio["path"])]
        command += ["-filter_complex", "[0:v][1:v]overlay=shortest=1:format=auto,format=yuv420p[v]",
                    "-map", "[v]"]
        if audio: command += ["-map", "2:a:0", "-c:a", "aac", "-b:a", "160k"]
        command += ["-frames:v", str(frame_count), "-c:v", "libx264", "-threads", "4",
                    "-x264-params", "threads=4:lookahead_threads=1", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(staging / "preview.mp4")]
        run = subprocess.run(command, capture_output=True, text=True, timeout=900)
        if cancel_event and cancel_event.is_set():
            raise NativeCharacterError("native render cancelled")
        if run.returncode or not (staging / "preview.mp4").is_file():
            raise NativeCharacterError("FFmpeg preview failed: " + run.stderr[-2000:])
        if _selection(root, character, variant, view, action, expression)[-1] != key:
            raise NativeCharacterError("native source changed during render; previous clip remains available")
        shutil.rmtree(sequence)
        (staging / "checker.png").unlink()
        data.pop("output_dir", None)
        data.update(source_fingerprint=key, selection={"character": character, "variant": variant,
                    "view": view, "action": action, "expression": expression},
                    preview_sha256=_hash(staging / "preview.mp4"), cached=False)
        _atomic_json(staging / "render.json", data)
        target.parent.mkdir(parents=True, exist_ok=True)
        if cancel_event and cancel_event.is_set():
            raise NativeCharacterError("native render cancelled")
        os.replace(staging, target)
        if cancel_event and cancel_event.is_set():
            raise NativeCharacterError("native render cancelled")
        _atomic_json(current, {"source_fingerprint": key, "path": target.relative_to(root).as_posix()})
        if cancel_event and cancel_event.is_set():
            if previous is None: current.unlink(missing_ok=True)
            else: _atomic_json(current, previous)
            raise NativeCharacterError("native render cancelled")
        return data | {"path": target.relative_to(root).as_posix()}
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def render_status(root, character, variant, view, action, expression):
    from studio.workspace import _id, safe_path

    for value in (character, variant, view, action, expression):
        _id(value)
    root = Path(root).resolve()
    native = safe_path(root, f"characters/{character}/03_animation/{variant}/native")
    current = native / "renders" / view / action / expression / "current.json"
    prior = None
    try:
        pointer = _json(current)
        directory = (root / pointer["path"]).resolve()
        directory.relative_to((native / "renders" / view / action / expression).resolve())
        record = _json(directory / "render.json")
        if _valid_cache(directory, record["source_fingerprint"], record["frame_count"]):
            prior = {"path": pointer["path"], "preview": pointer["path"] + "/preview.mp4",
                     "frame_count": record["frame_count"], "source_fingerprint": record["source_fingerprint"]}
    except (OSError, ValueError, TypeError, KeyError):
        pass
    try:
        _, _, _, _, key = _selection(root, character, variant, view, action, expression)
        return {"current": bool(prior and prior["source_fingerprint"] == key), "clip": prior,
                "source_fingerprint": key, "error": None}
    except NativeCharacterError as exc:
        return {"current": False, "clip": prior, "source_fingerprint": None, "error": str(exc)}


if __name__ == "__main__":
    if len(sys.argv) != 8 or sys.argv[1] != "render":
        raise SystemExit("usage: python -m studio.native_pipeline render ROOT CHARACTER VARIANT VIEW ACTION EXPRESSION")
    try:
        cancelled = threading.Event()
        signal.signal(signal.SIGTERM, lambda *_: cancelled.set())
        result = render_native(*sys.argv[2:], progress=lambda count, total: print(f"Frame {count} of {total}", flush=True),
                               cancel_event=cancelled)
        print("OUTPUT " + result["path"], flush=True)
    except NativeCharacterError as exc:
        print(str(exc), file=sys.stderr, flush=True)
        raise SystemExit(1)
