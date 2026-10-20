"""Guarded headless Blender renderer for one synthetic character pilot.

Only the pinned self-contained fixture is accepted. This module does not
register a character, grant review approval, or enable production rendering.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import select
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable


class BlenderCharacterError(RuntimeError):
    """The Blender project, tool, or output failed a pilot constraint."""


MAX_FRAMES = 900
MAX_SECONDS = 30
MAX_THREADS = 4
MAX_MEMORY_BYTES = 4 * 1024**3
PINNED_VERSION = "5.2.2 LTS"
PILOT_PROJECT_SHA256 = "171f57d6c77315aa1c23ca152cc023dc47d658dd2229ba8e835f50c5057fbc3b"


def _binary(explicit: str | os.PathLike[str] | None) -> str:
    candidate = os.fspath(explicit) if explicit is not None else os.environ.get("BLENDER_BIN", "blender")
    found = shutil.which(candidate) if os.path.sep not in candidate else candidate
    if not found or not Path(found).is_file() or not os.access(found, os.X_OK):
        raise BlenderCharacterError("Blender executable not found; set BLENDER_BIN")
    return str(Path(found).resolve())


def _version(binary: str) -> str:
    try:
        completed = subprocess.run(
            [binary, "-b", "--version"], capture_output=True, text=True,
            timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BlenderCharacterError(f"could not query Blender: {exc}") from exc
    version = completed.stdout.splitlines()[0] if completed.stdout else ""
    if completed.returncode or PINNED_VERSION not in version:
        raise BlenderCharacterError(f"requires Blender {PINNED_VERSION}; found {version or 'unknown'}")
    return version


def capabilities(*, blender_bin: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Report a real pinned local renderer without implying rig readiness."""
    try:
        binary = _binary(blender_bin)
        version = _version(binary)
    except BlenderCharacterError as exc:
        return {"renderer": None, "error": str(exc)}
    return {"renderer": {"name": "Blender", "path": binary, "version": version,
                         "pinned": True, "png_target": True}}


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise BlenderCharacterError(f"{name} must be a positive integer")
    return value


def _trusted_project_hash(project: Path) -> str:
    digest = hashlib.sha256(project.read_bytes()).hexdigest()
    if digest != PILOT_PROJECT_SHA256:
        raise BlenderCharacterError("Blender pilot accepts only the pinned packed synthetic fixture")
    return digest


def _proc_stats(pid: int) -> tuple[int, int, int]:
    values: dict[str, int] = {}
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith(("VmRSS:", "VmHWM:", "VmSwap:")):
                key, number, *_ = line.split()
                values[key[:-1]] = int(number) * 1024
            elif line.startswith("Threads:"):
                values["Threads"] = int(line.split()[1])
    except (OSError, ValueError):
        pass
    return max(values.get("VmRSS", 0), values.get("VmHWM", 0)), values.get("VmSwap", 0), values.get("Threads", 0)


def _process_start(pid: int) -> str:
    try:
        data = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
        return data[data.rfind(")") + 1:].split()[19]
    except (OSError, IndexError):
        return ""


def _stop(proc: subprocess.Popen[bytes]) -> None:
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
        proc.wait(timeout=2)


def _validate_frames(directory: Path, width: int, height: int, count: int) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise BlenderCharacterError("Pillow is required to validate Blender frames") from exc
    frames = sorted(directory.glob("frame_*.png"))
    expected = [f"frame_{index:04d}.png" for index in range(count)]
    if [path.name for path in frames] != expected:
        raise BlenderCharacterError(f"Blender wrote {len(frames)} frames; expected {count} contiguous frames")
    for index in sorted({0, count // 2, count - 1}):
        try:
            with Image.open(frames[index]) as image:
                image.load()
                if image.mode != "RGBA" or image.size != (width, height):
                    raise BlenderCharacterError(f"frame {index} is not {width}x{height} RGBA")
                if image.getchannel("A").getextrema()[0] == 255:
                    raise BlenderCharacterError(f"frame {index} lost transparency")
        except OSError as exc:
            raise BlenderCharacterError(f"cannot decode frame {index}: {exc}") from exc


def render_project(
    project_path: str | os.PathLike[str],
    output_dir: str | os.PathLike[str],
    *, width: int, height: int, fps: int = 24, frame_count: int = 240,
    threads: int = MAX_THREADS,
    blender_bin: str | os.PathLike[str] | None = None,
    max_memory_bytes: int = MAX_MEMORY_BYTES,
    require_no_swap: bool = True,
    progress_callback: Callable[[int, int], None] | None = None,
    cancel_event: threading.Event | Callable[[], bool] | None = None,
    on_process_start: Callable[[int, str], None] | None = None,
    timeout_seconds: float = 900,
) -> dict[str, Any]:
    """Render transparent PNGs with pinned Blender and bounded resources.

    Existing output files are never removed. Use a fresh staging directory.
    """
    project = Path(project_path).resolve()
    if project.suffix.lower() != ".blend" or not project.is_file():
        raise BlenderCharacterError("project must be an existing .blend file")
    width, height = _positive_int(width, "width"), _positive_int(height, "height")
    fps, frame_count = _positive_int(fps, "fps"), _positive_int(frame_count, "frame_count")
    threads = _positive_int(threads, "threads")
    if threads > MAX_THREADS:
        raise BlenderCharacterError("Blender renders are limited to four renderer threads")
    if frame_count > MAX_FRAMES or frame_count / fps > MAX_SECONDS:
        raise BlenderCharacterError("Blender renders are limited to 900 frames and 30 seconds")
    max_memory_bytes = _positive_int(max_memory_bytes, "max_memory_bytes")
    if max_memory_bytes > MAX_MEMORY_BYTES:
        raise BlenderCharacterError("Blender memory limit cannot exceed 4 GiB")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise BlenderCharacterError("timeout_seconds must be a positive finite number")
    source_hash = _trusted_project_hash(project)
    binary = _binary(blender_bin)
    version = _version(binary)
    target = Path(output_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)
    if any(target.iterdir()):
        raise BlenderCharacterError("Blender output directory must be empty")
    # Only validated numeric values enter this expression; no source strings.
    settings = (
        "import bpy; s=bpy.context.scene; "
        f"s.render.resolution_x={width}; s.render.resolution_y={height}; "
        f"s.render.fps={fps}; s.render.resolution_percentage=100; "
        f"s.render.threads_mode='FIXED'; s.render.threads={threads}; "
        "s.render.film_transparent=True; "
        "s.render.image_settings.file_format='PNG'; "
        "s.render.image_settings.color_mode='RGBA'"
    )
    command = [
        binary, "-b", "--disable-autoexec", str(project), "-t", str(threads),
        "-s", "0", "-e", str(frame_count - 1),
        "-o", str(target / "frame_"), "-F", "PNG",
        "--python-expr", settings, "-a",
    ]
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(threads)
    env["OPENBLAS_NUM_THREADS"] = str(threads)
    started = time.monotonic()
    try:
        proc = subprocess.Popen(
            command, cwd=project.parent, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, bufsize=0, start_new_session=True,
        )
    except OSError as exc:
        raise BlenderCharacterError(f"could not start Blender: {exc}") from exc
    if on_process_start:
        try:
            on_process_start(proc.pid, _process_start(proc.pid))
        except Exception as exc:
            _stop(proc)
            raise BlenderCharacterError(f"could not register Blender process: {exc}") from exc
    assert proc.stdout is not None
    descriptor = proc.stdout.fileno()
    os.set_blocking(descriptor, False)
    buffer = ""
    log: list[str] = []
    finished = 0
    peak_rss = peak_swap = peak_threads = 0
    failure: BlenderCharacterError | None = None

    def consume(data: bytes) -> None:
        nonlocal buffer, finished
        buffer += data.decode("utf-8", errors="replace")
        lines = re.split(r"[\r\n]", buffer)
        buffer = lines.pop()
        for line in lines:
            if not line:
                continue
            log.append(line)
            if len(log) > 200:
                del log[:100]
            if "Saved:" in line and ".png" in line:
                finished += 1
                if progress_callback:
                    progress_callback(finished, frame_count)

    try:
        while True:
            active = proc.poll() is None
            if active:
                if time.monotonic() - started > timeout_seconds:
                    failure = BlenderCharacterError(f"Blender render timed out after {timeout_seconds:g}s")
                is_set = getattr(cancel_event, "is_set", None)
                cancelled = bool(is_set()) if callable(is_set) else bool(cancel_event and cancel_event())
                if cancelled:
                    failure = BlenderCharacterError("Blender render cancelled")
                rss, swap, process_threads = _proc_stats(proc.pid)
                peak_rss, peak_swap, peak_threads = max(peak_rss, rss), max(peak_swap, swap), max(peak_threads, process_threads)
                if peak_rss > max_memory_bytes:
                    failure = BlenderCharacterError(f"Blender peak RSS exceeded {max_memory_bytes} bytes")
                if require_no_swap and peak_swap:
                    failure = BlenderCharacterError(f"Blender used {peak_swap} bytes of process swap")
            if failure:
                _stop(proc)
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
            if not active or failure:
                break
        while True:
            try:
                chunk = os.read(descriptor, 65536)
            except (BlockingIOError, OSError):
                break
            if not chunk:
                break
            consume(chunk)
        if buffer:
            log.append(buffer)
    except Exception:
        _stop(proc)
        raise
    finally:
        proc.stdout.close()
    if failure:
        raise BlenderCharacterError(
            f"{failure}; completed {finished}/{frame_count} frames in {time.monotonic() - started:.2f}s, "
            f"peak RSS {peak_rss} bytes, swap {peak_swap} bytes"
        ) from failure
    if proc.returncode:
        raise BlenderCharacterError(f"Blender exited {proc.returncode}: {log[-1] if log else 'no output'}")
    if _trusted_project_hash(project) != source_hash:
        raise BlenderCharacterError("Blender pilot source changed during render")
    _validate_frames(target, width, height, frame_count)
    return {
        "renderer": version, "project_sha256": source_hash,
        "width": width, "height": height, "fps": fps, "frame_count": frame_count,
        "elapsed_seconds": time.monotonic() - started,
        "peak_rss_bytes": peak_rss, "peak_swap_bytes": peak_swap,
        "peak_process_threads": peak_threads, "renderer_threads": threads,
        "last_frame": finished - 1, "log_tail": log[-40:],
    }
