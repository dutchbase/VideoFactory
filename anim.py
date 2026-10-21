"""anim.py: command line of the voice-first video workspace.

One command does one stage and stops: new, speak, transcribe, cues, stills, check, render, and a few helpers.
Read the output, edit it, run the next command. Run `python anim.py -h` for the list of commands.
"""
import argparse
import asyncio
import contextlib
import datetime
import difflib
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import warnings
import wave
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parent
VIDEOS = ROOT / "videos"
TEMPLATE = ROOT / "_templates" / "video"
VOCAB = ROOT / "_shared" / "vocab.txt"
AUDIO_EXT = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".mp4", ".mov", ".webm"}
STAGES = [("01_voice", "voice file"), ("02_transcript", "words.json"), ("03_cues", "cues.json"),
          ("04_scene", "scene.js"), ("05_render", "*.mp4")]
ELEVEN = "https://api.elevenlabs.io/v1"
STABILITY = {"creative": 0.0, "natural": 0.5, "robust": 1.0}  # the only values the v3 and v4 models accept
import html
import io


# ====================================================================================================
# 10-core
# ====================================================================================================

def die(msg: str) -> NoReturn:
    """Print an error to standard error and stop with status 1."""
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def video_dir(slug: str) -> Path:
    """The project folder for `<brand>/<slug>`, or a bare slug that is unique under videos/."""
    fixture = ROOT / "tests" / "fixtures" / "silent-first-scene"
    if slug == "silent-first-scene" and fixture.is_dir():
        return fixture
    from studio.project_paths import ProjectPathError, resolve_project
    try:
        return resolve_project(ROOT, slug)
    except ProjectPathError as error:
        bare = VIDEOS / str(slug)  # a plain folder without project.json (bare test and legacy folders)
        safe = re.fullmatch(r"[a-z0-9_][a-z0-9_-]*(/[a-z0-9_][a-z0-9_-]*)?", str(slug))
        if safe and bare.is_dir() and not bare.is_symlink() and bare.resolve().is_relative_to(VIDEOS.resolve()):
            return bare
        die(str(error))


def find_voice(vdir: Path) -> Path:
    """The voice recording of a project: voice.* first, else the first audio file by name."""
    folder = vdir / "01_voice"
    files = sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXT),
                   key=lambda p: p.name) if folder.is_dir() else []
    named = [p for p in files if p.stem == "voice"]
    if named or files:
        return (named or files)[0]
    die(f"no voice file in {folder} (expected voice.wav / voice.mp3 / ...)")


def probe_duration(path: Path) -> float:
    """Length of a media file in seconds."""
    run = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True)
    try:
        return float(run.stdout.strip())
    except ValueError:
        die(f"ffprobe could not read {path}: {run.stderr.strip()}")


def audio_peak(path: Path) -> float | None:
    """Loudest sample in dB (zero or negative), or None when the file has no audio."""
    err = subprocess.run(["ffmpeg", "-i", str(path), "-af", "volumedetect", "-vn", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"max_volume:\s*(-?inf|-?[0-9.]+)\s*dB", err)
    return float(m.group(1)) if m else None


def loudness(path: Path) -> tuple[float, float]:
    """Integrated loudness (LUFS) and true peak (dBTP) of a media file."""
    import check
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return check.ebur128(err)


def fmt_t(t: float) -> str:
    """Time label MM:SS.s (minutes can pass 59)."""
    minutes, seconds = divmod(max(0, t), 60)
    return f"{int(minutes):02d}:{seconds:04.1f}"


def parse_t(s: str) -> float:
    """Seconds from `3.2`, `1:04` or `1:02:03`. A bad part raises ValueError."""
    total = 0.0
    for part in str(s).split(":"):
        total = total * 60 + float(part)
    return total


def norm(word: str) -> str:
    """Comparison form of a word: lowercase, only a-z and 0-9."""
    return re.sub(r"[^a-z0-9]", "", word.lower())


def _chip():
    """The sound module (_runtime/synth.py next to this file, not under a patched ROOT), imported on first use."""
    runtime = str(Path(__file__).resolve().parent / "_runtime")
    if runtime not in sys.path:
        sys.path.insert(0, runtime)
    import synth
    return synth


# ---------------------------------------------------------------- new, research, use


def cmd_new(a) -> None:
    """Create videos/<brand>/<slug> from the templates. Nothing is written when a check fails."""
    slug = a.slug
    if not slug or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        die("slug must be lowercase letters, digits and hyphens, e.g. 2026-09-24-folder-thesis")
    brand = getattr(a, "brand", None)
    if not brand:
        die("new requires --brand <brand>")
    from studio import project_paths, workspace
    try:
        project_paths._part(brand)
    except ValueError as error:
        die(str(error))
    dest = VIDEOS / brand / slug
    if dest.exists():
        die(f"{dest} already exists")
    fmt = getattr(a, "format", None) or "wide"
    if fmt not in ("wide", "tall"):
        die("format must be wide or tall")
    engine, style = getattr(a, "engine", None) or "canvas", getattr(a, "style", None)
    try:
        workspace.check_engine(engine, style)
    except workspace.WorkspaceError as error:
        die(str(error))
    if engine == "hyperframes":
        style, renderer = "none", "hyperframes"
    elif style in (None, "", "modern"):
        style, renderer = "modern", "modern"
    else:
        renderer = workspace._style(ROOT, style)["renderer"]
    try:
        workspace.check_brand(ROOT, brand, renderer)
    except workspace.WorkspaceError as error:
        die(str(error))
    scene = ROOT / "_templates" / f"scene-{'hf' if engine == 'hyperframes' else renderer}-{fmt}"
    if not scene.is_dir():
        die(f"an authored {renderer} {fmt} scene template is required")
    voice = Path(a.voice) if getattr(a, "voice", None) else None
    if voice and not voice.is_file():
        die(f"voice file not found: {voice}")
    title = slug.replace("-", " ").title()
    try:
        shutil.copytree(TEMPLATE, dest)
        shutil.copytree(scene, dest / "04_scene", dirs_exist_ok=True)
        if engine == "hyperframes":
            workspace.stamp_hf_scene(dest / "04_scene", brand, "voice" + voice.suffix.lower() if voice else "voice.mp3")
        elif renderer == "modern":
            workspace.stamp_modern_scene(dest / "04_scene", brand, title)
        else:
            workspace.stamp_brand(dest / "04_scene", brand)
        meta = {"format": fmt, "style": style, "renderer": renderer, "brand": brand, "engine": engine, "title": title}
        (dest / "project.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        if voice:
            target = dest / "01_voice" / ("voice" + voice.suffix.lower())
            shutil.copy2(voice, target)
            print(f"voice -> {target}")
        project_paths.settings_snapshot(ROOT, dest)
    except BaseException:
        shutil.rmtree(dest, ignore_errors=True)
        raise
    shown = dest.relative_to(ROOT) if dest.is_relative_to(ROOT) else dest
    print(f"created {shown}/ ({fmt}, {style})")
    print("next: agree the direction in 01_voice/brief.md and review it, then draft and review 01_voice/script.md.\n"
          "Then record your voice into 01_voice/, or run speak with --confirm-script <fingerprint>.")


def cmd_research(a) -> None:
    """Add the optional 00_research folder to a project."""
    dest = video_dir(a.slug) / "00_research"
    if dest.exists():
        die(f"{dest} already exists")
    shutil.copytree(ROOT / "_templates" / "research", dest)
    print(f"created {dest}")
    print("next: tell the assistant the topic. It follows stages/00_research/CONTEXT.md.")


def _secs(value) -> float:
    """Seconds from "12", "12.5" or "m:ss"."""
    text = str(value).strip()
    minutes, sep, seconds = text.partition(":")
    return int(minutes) * 60 + float(seconds) if sep else float(text)


def _clip_range(start, end, length: float | None = None) -> tuple[float, float]:
    try:
        a = _secs(start) if start else 0.0
        b = _secs(end) if end else length
    except ValueError:
        die("--start and --end are seconds or m:ss")
    if b is None or not 0 <= a < b:
        die("--end must come after --start")
    return a, b


def _copy_clip(vdir: Path):
    """The clip function for library.use: a stock video becomes 12 fps frames for Modern.clip (assets/<name>/, real.js)."""
    def clip(src: Path, name: str, start: str, end: str) -> None:
        if not Path(src).is_file() or not name or not start or not end:
            die("clip needs a source file, a name, a start and an end")
        register_clip(vdir, Path(src), name, *_clip_range(start, end), 12, 1280)
    return clip


def _use_motion(vdir: Path, ref: str, name: str | None, start, end) -> None:
    """motion:<brand>/<ID>: render a motion-pack clip in the video's format (cached), then register it for Modern.clip."""
    brand, _, asset_id = ref[len("motion:"):].partition("/")
    pack = ROOT / "brands" / brand / "library" / "motion"
    try:
        assets = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))["assets"]
        asset = next(x for x in assets if x["id"] == asset_id)
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        die(f"no motion asset {asset_id!r} in {_relpath(pack)}. Ref: motion:<brand>/<ID>, e.g. motion:videofactory/AIM-05")
    if asset.get("type") == "overlay":
        die(f"{asset_id} is an overlay: it needs transparency, which a Modern clip has not. Pick a scene, device or background asset.")
    tall = json.loads((vdir / "project.json").read_text(encoding="utf-8")).get("format") == "tall"
    fmt = "9:16" if tall else "16:9"
    dur = float(asset.get("defaultDuration", 6))
    stem = f"{asset_id}_{fmt.replace(':', 'x')}_{dur:g}s.mp4"
    render = [sys.executable, str(ROOT / "tools" / "motion.py"), "render", "--brand", brand, "--id", asset_id,
              "--format", fmt, "--dur", f"{dur:g}"]
    edited = vdir / "04_scene" / "motion" / asset["file"]  # an edited copy of the page (own text) wins
    if edited.is_file():
        src = edited.parent / stem
        if not src.is_file() or src.stat().st_mtime < edited.stat().st_mtime:
            subprocess.run([*render, "--page", str(edited), "--outDir", str(edited.parent)], check=True)
    else:
        src = ROOT / "library" / "cache" / "motion" / stem
        if not src.is_file():
            subprocess.run(render, check=True)
    clip_name = name or asset_id.lower()
    register_clip(vdir, src, clip_name, *_clip_range(start, end, dur), 24, 1920)
    import libcore
    libcore.record_use(vdir, ref, "MIT", f"brands/{brand}/library/motion/{asset['file']}", f"assets/{clip_name}")
    print(f"{ref} (MIT, own work) -> 04_scene/assets/{clip_name}/  Play it: Modern.clip('#el', '{clip_name}', '<cue>')")


def cmd_use(a) -> None:
    """Copy a library or stock item into one video and log its licence."""
    vdir = video_dir(a.slug)
    if a.ref.startswith("motion:"):
        _use_motion(vdir, a.ref, a.name, a.start, a.end)
        return
    import libcore
    import library
    try:
        if a.ref.startswith("audio:"):  # the sound library, library/audio/CONTEXT.md
            import audio
            lines = audio.use(vdir, a.ref.removeprefix("audio:"), a.name, a.start, a.end)
        else:
            lines = library.use(vdir, a.ref, a.name, a.start, a.end, clip=_copy_clip(vdir))
        print("\n".join(lines))
    except (libcore.LicenseError, libcore.NetError, ValueError) as error:
        die(str(error))


# ---------------------------------------------------------------- speak


def eleven_key() -> str:
    """The ElevenLabs API key from the environment or the project .env."""
    names = ("ELEVENLABS_API_KEY", "ELEVEN_API_KEY")
    key = next((os.environ[n].strip() for n in names if os.environ.get(n, "").strip()), "")
    env = ROOT / ".env"
    if not key and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            name, sep, value = line.partition("=")
            if sep and name.strip() in names and value.strip():
                key = value.strip().strip('"')
    if not key:
        die("no ElevenLabs key. Put ELEVEN_API_KEY=sk_... in .env (copy .env.example) or set the environment variable.")
    if not key.startswith("sk_"):
        die("that is an ElevenLabs key ID, not a key. Keys start with sk_ and are shown once when created or rotated "
            "(elevenlabs.io > Developers > API Keys).")
    return key


def eleven(path: str, key: str, body: dict | None = None) -> bytes:
    """One call to the speech API. POST with a JSON body, else GET. Returns the raw answer."""
    import urllib.error
    import urllib.request
    data = json.dumps(body).encode("utf-8") if isinstance(body, dict) and body else None
    guarded = bool(body)
    if guarded:
        from studio import paid_requests
        if os.environ.get("VF_PAID_GUARD") != "1":
            raise paid_requests.BudgetError("Paid voice needs a managed run and approval of its exact cost.")
        run_root, run_id = os.environ.get("VF_RUN_ROOT"), os.environ.get("VF_RUN_ID")
        if not run_root or not run_id or Path(run_root).resolve() != ROOT.resolve():
            raise paid_requests.BudgetError("Managed paid voice needs a saved run and verified request cost.")
        request_id = hashlib.sha256(json.dumps({"path": path, "body": body}, sort_keys=True).encode("utf-8")).hexdigest()
        run_id, quote = paid_requests.managed_quote(run_root, request_id, purpose="voice",
                                                    metadata={"path": path, "body": body})
        request_id = quote["request_id"]
        paid_requests.reserve(run_root, run_id, request_id, quote["max_cost"], provider="elevenlabs", purpose="voice")
    request = urllib.request.Request(ELEVEN + path, data=data, method="POST" if data else "GET",
                                     headers={"xi-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=300) as answer:
            audio = answer.read()
    except urllib.error.HTTPError as error:
        die(f"ElevenLabs {error.code}: {error.read().decode('utf-8', 'replace')[:400]}")
    if guarded:
        paid_requests.settle(run_root, run_id, request_id, quote["max_cost"], estimated_upper_bound=True)
    return audio


def script_chunks(text: str) -> list[str]:
    """Split script.md into the pieces sent to the API one at a time (the v4 model likes short requests)."""
    block = re.search(r"```[^\n]*\n(.*?)```", text, re.S)
    source = block.group(1) if block else re.sub(r"(?m)^#.*$", "", text)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", source) if p.strip()]
    chunks, current = [], ""
    for paragraph in paragraphs:
        if current and (len(current) >= 250 or len(current) + len(paragraph) > 700):
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph
    if current:
        if chunks and len(current) < 250:
            chunks[-1] += "\n\n" + current
        else:
            chunks.append(current)
    return chunks


def cmd_speak(a) -> None:
    """Narration to 01_voice/voice.mp3: one API call per chunk, takes kept, takes joined with ffmpeg."""
    if a.dry_run and a.check:
        die("Use --dry-run or --check separately; dry runs never contact ElevenLabs")
    vdir = video_dir(a.slug)
    cfg = voice_config(vdir)
    voice_id, model = str(cfg.get("voice_id") or ""), str(cfg.get("model") or "YOUR_SUPPORTED_MODEL_ID")
    preset = a.stability or cfg.get("stability", "natural")
    if preset not in STABILITY:
        die("stability must be creative, natural or robust")
    stability = STABILITY[preset]
    try:
        similarity = float(cfg.get("similarity_boost", "0.75"))
    except (TypeError, ValueError):
        similarity = math.nan
    if not math.isfinite(similarity) or not 0 <= similarity <= 1:
        die("similarity_boost must be a finite number from 0 to 1")
    fmt = str(cfg.get("format", "mp3_44100_128"))
    if not re.fullmatch(r"mp3_\d+_\d+", fmt):
        die("format must be an MP3 output setting, e.g. mp3_44100_128")
    for value in (voice_id, model):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", value) or value.startswith("YOUR_"):
            die("Choose your permitted voice_id and supported model in this brand’s voice.md first.")
    if a.check:
        key = eleven_key()
        models = [m for m in json.loads(eleven("/models", key)) if m.get("can_do_text_to_speech")]
        ids = [m.get("model_id") for m in models]
        print(f"text-to-speech models on this key: {', '.join(str(i) for i in ids)}")
        print(f"using {model}: {'available' if model in ids else 'NOT available'}")
        if model not in ids:
            die(f"{model} is absent or lacks text-to-speech capability on this key")
        voice = json.loads(eleven(f"/voices/{voice_id}", key))
        print(f"voice {voice_id}: {voice.get('name')} ({voice.get('category')})")
        plan = json.loads(eleven("/user/subscription", key))
        left = (plan.get("character_limit") or 0) - (plan.get("character_count") or 0)
        print(f"plan {plan.get('tier')}: {left:,} characters left")
        return
    print(f"{model}, voice {voice_id}")
    script = vdir / "01_voice" / "script.md"
    if not script.exists():
        die("no 01_voice/script.md. Write it first (style: _shared/voice.md).")
    chunks = script_chunks(script.read_text(encoding="utf-8"))
    spoken = re.sub(r"\[[^\[\]]*\]", " ", "\n".join(chunks)) if model == "eleven_v4" else "\n".join(chunks)
    if not spoken.strip():
        die("narration is empty; write spoken words in script.md")
    if a.chunk is not None and not 1 <= a.chunk <= len(chunks):
        die(f"chunk must be from 1 to {len(chunks)}")
    if model == "eleven_v4" and any(len(c) > 10000 for c in chunks):
        die("V4 chunk exceeds 10,000 characters; split the oversized paragraph")
    tone_gate(vdir, {"script": spoken}, a.skip_tone)
    for i, chunk in enumerate(chunks, 1):
        note = "  (under 250 chars: may come out uneven)" if len(chunk) < 250 else ""
        print(f"chunk {i}: {len(chunk)} chars{note}  | {chunk[:70].replace(chr(10), ' ')}")
    if a.dry_run:
        return
    require_script_confirmation(vdir, getattr(a, "confirm_script", None))
    folder = vdir / "01_voice"
    for other in folder.glob("voice.*"):
        if other.suffix.lower() != ".mp3":
            die(f"01_voice already has {other.name}. Move it out first so the new voice is the only one.")
    key = eleven_key()
    takes = folder / "takes"
    takes.mkdir(exist_ok=True)
    settings = {"stability": stability, "similarity_boost": similarity} if model == "eleven_v4" else {"stability": stability}
    requests = [{"path": f"/text-to-speech/{voice_id}?output_format={fmt}",
                 "body": {"text": chunk, "model_id": model, "voice_settings": settings}} for chunk in chunks]

    def fresh(i: int) -> bool:
        base = takes / f"{i:02d}"
        try:
            return (base.with_suffix(".mp3").stat().st_size > 0 and base.with_suffix(".txt").read_text(encoding="utf-8") == chunks[i - 1]
                    and json.loads(base.with_suffix(".json").read_text(encoding="utf-8")) == requests[i - 1])
        except (OSError, ValueError):
            return False

    for i, (chunk, request) in enumerate(zip(chunks, requests), 1):
        if (a.chunk != i) if a.chunk is not None else fresh(i):  # --chunk N always redoes N; otherwise only stale takes
            continue
        print(f"speaking chunk {i}/{len(chunks)} ...")
        audio = eleven(request["path"], key, request["body"])
        if not audio:
            die(f"ElevenLabs returned empty audio for chunk {i}")
        base = takes / f"{i:02d}"
        base.with_suffix(".json").unlink(missing_ok=True)  # an interrupted run must never look current
        base.with_suffix(".mp3").write_bytes(audio)
        base.with_suffix(".txt").write_text(chunk, encoding="utf-8")
        base.with_suffix(".json").write_text(json.dumps(request, indent=2), encoding="utf-8")
    stale = [i for i in range(1, len(chunks) + 1) if not fresh(i)]
    if stale:
        print(f"Stale or missing takes: {', '.join(map(str, stale))}. Final recording unchanged; run without --chunk to generate the rest.")
        return
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for i in range(1, len(chunks) + 1):
        cmd += ["-i", str(takes / f"{i:02d}.mp3")]
    legs = "".join(f"[{i}:a]aresample=44100,aformat=channel_layouts=mono,apad=pad_dur=0.3[a{i}];" for i in range(len(chunks)))
    legs += "".join(f"[a{i}]" for i in range(len(chunks))) + f"concat=n={len(chunks)}:v=0:a=1[out]"
    final = folder / "voice.mp3"
    with tempfile.TemporaryDirectory(prefix=".voice-", dir=folder) as work:
        joined = Path(work) / "voice.mp3"
        subprocess.run([*cmd, "-filter_complex", legs, "-map", "[out]", "-c:a", "libmp3lame", "-q:a", "2", str(joined)], check=True)
        os.replace(joined, final)
    # Record the takes as the voice selection, like the Studio voice job does, so the voice gates can open.
    from studio.workspace import set_voice_selection
    for key, path in (("voice_test", "01_voice/takes/01.mp3"), ("voice", "01_voice/voice.mp3")):
        set_voice_selection(ROOT, a.slug, key, path, a.confirm_script)
    print(f"-> {final}  ({fmt_t(probe_duration(final))}). Listen; redo a bad chunk with --chunk N.")
    print(f"Review: python anim.py review {a.slug} voice-test, then voice (the user approves both in the Studio).")


# ---------------------------------------------------------------- transcribe


def cmd_transcribe(a) -> None:
    """Whisper on the voice file: words.json with a start and end per word, and transcript.md."""
    vdir = video_dir(a.slug)
    voice = find_voice(vdir)
    stage = vdir / "02_transcript"
    stage.mkdir(exist_ok=True)
    words_file = stage / "words.json"
    if words_file.exists() and not a.force:
        die("02_transcript/words.json exists (you may have edited it). Re-run with --force to overwrite.")
    warnings.filterwarnings("ignore", message=r"(?s).*Triton")
    warnings.filterwarnings("ignore", message=r"(?s).*FP16 is not supported")
    try:
        import gc
        import torch
        import whisper
    except ImportError:
        die("local transcription needs Whisper: .venv/bin/pip install -r requirements-transcription.txt")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    prompt = a.prompt
    if prompt is None and VOCAB.exists():
        lines = [line.strip() for line in VOCAB.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
        prompt = ", ".join(lines) or None
    print(f"whisper {a.model} on {device} <- {voice.name}")
    started = time.time()

    def load(name, dev):
        if dev != "cuda":
            return whisper.load_model(name, device=dev)
        # Whisper loads 32-bit weights straight onto the GPU; load on the CPU, make the big layers 16-bit, then move.
        m = whisper.load_model(name, device="cpu")
        for part in m.modules():
            if isinstance(part, (torch.nn.Linear, torch.nn.Conv1d, torch.nn.Embedding)):
                part.half()
        return m.to("cuda")

    def run(name, dev):
        m = load(name, dev)
        return m, m.transcribe(str(voice), word_timestamps=True, condition_on_previous_text=False, initial_prompt=prompt,
                               language=a.language, fp16=dev == "cuda", verbose=None)

    # A small GPU cannot hold large-v3 (about 10 GB): use large-v3-turbo there; the CPU (much slower) is the last step.
    first = a.model
    if device == "cuda" and a.model == "large-v3" and torch.cuda.get_device_properties(0).total_memory < 8 * 1024 ** 3:
        first = "large-v3-turbo"
        print("GPU under 8 GB: using large-v3-turbo (the script fixes its odd words)")
    tries = [(first, device)] + ([(a.model, "cpu")] if device == "cuda" else [])
    model = result = None
    used = first
    for name, dev in tries:
        if dev != device:
            print(f"not enough GPU memory for {name}; running on the CPU instead (slower)")
        oom = False
        try:
            model, result = run(name, dev)
            device, used = dev, name
            break
        except torch.cuda.OutOfMemoryError:
            oom = True
        if oom:  # outside the except block, so the failed model is no longer referenced and its memory can go
            model = result = None
            gc.collect()
            torch.cuda.empty_cache()
    words = [{"text": w["word"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)}
             for segment in result["segments"] for w in segment.get("words", []) if w["word"].strip()]
    script = vdir / "01_voice" / "script.md"
    script_text = script.read_text(encoding="utf-8") if script.exists() else ""
    if script_text.strip() and "Replace this with the script" not in script_text:
        fixed, notes = snap_to_script(words, script_text)
        print(f"{fixed} words re-spelled from script.md")
        if notes and not a.no_verify:
            del model
            if device == "cuda":
                torch.cuda.empty_cache()
            second_name = "large-v3-turbo" if used != "large-v3-turbo" else ("medium.en" if a.language == "en" else "medium")
            second = load(second_name, device)
            audio = whisper.load_audio(str(voice))
            for t, message in notes:
                print(f"  {fmt_t(t)} {message}")
                clip = audio[int(max(0, t - 2.5) * 16000):int((t + 3.0) * 16000)]
                heard = second.transcribe(clip, language=a.language, condition_on_previous_text=False,
                                          fp16=device == "cuda", verbose=None)["text"].strip()
                print(f"        second model hears: {heard}")
        else:
            for t, message in notes:
                print(f"  {fmt_t(t)} {message}")
        print_pace(vdir, words)
    duration = probe_duration(voice)
    words_file.write_text(json.dumps({"voice": voice.name, "duration": round(duration, 3), "model": used, "words": words},
                                     indent=1, ensure_ascii=False), encoding="utf-8")
    markdown = stage / "transcript.md"
    markdown.write_text(transcript_md(a.slug, words, duration), encoding="utf-8")
    print(f"{len(words)} words, {fmt_t(duration)} of audio, {time.time() - started:.1f}s")
    print(f"-> {markdown}  (read it; fix misheard words in words.json)")


def print_pace(vdir: Path, words: list[dict]) -> None:
    """Words per minute for each take, so a slow or rushed chunk can be rewritten and re-rolled."""
    takes = sorted((vdir / "01_voice" / "takes").glob("*.mp3"))
    if not takes:
        return
    print("pace per take (target: _shared/voice.md, Pace):")
    offset, flagged = 0.0, False
    for take in takes:
        window = probe_duration(take) + 0.3  # the pad that speak adds after every take
        inside = [w for w in words if offset <= w["start"] < offset + window]
        if len(inside) > 5 and inside[-1]["end"] > inside[0]["start"]:
            wpm = len(inside) / (inside[-1]["end"] - inside[0]["start"]) * 60
            n = int(take.stem) if take.stem.isdigit() else take.stem
            line = f"  {take.stem}  {fmt_t(offset)}  {wpm:4.0f} wpm"
            if wpm < 165:
                line += f"   slow: rewrite it as talk, then speak --chunk {n}"
            elif wpm > 205:
                line += f"   fast: give it a landing beat, then speak --chunk {n}"
            flagged = flagged or wpm < 165 or wpm > 205
            print(line)
        offset += window
    if flagged:
        print("  then transcribe again with --force")


def snap_to_script(words: list[dict], script_md: str) -> tuple[int, list[tuple[float, str]]]:
    """Spell the words like the script, keep Whisper's timing, drop stray repeats. Changes `words` in place."""
    for i in range(len(words) - 1, 0, -1):  # one word that Whisper split in two: `e` + `-mail`, `$2` + `.65`
        if re.match(r"[-.,']\w", words[i]["text"]):
            words[i - 1]["text"] += words[i]["text"]
            words[i - 1]["end"] = words[i]["end"]
            del words[i]
    block = re.search(r"```[^\n]*\n(.*?)```", script_md, re.S)
    source = re.sub(r"\[[A-Za-z ,'\-]+\]", " ", block.group(1) if block else script_md)
    ref = [t for t in source.split() if norm(t)]
    heard = [norm(w["text"]) for w in words]
    expected = [norm(t) for t in ref]
    clip = False
    blocks = [m for m in difflib.SequenceMatcher(None, heard, expected, autojunk=False).get_matching_blocks() if m.size >= 3]
    if blocks:
        first, last = blocks[0].b, blocks[-1].b + blocks[-1].size
        if last - first < 0.8 * len(expected):  # the audio is a stretch of a longer script
            clip = True
            ref, expected = ref[max(0, first - 3):last + 3], expected[max(0, first - 3):last + 3]
    kept, notes, fixed = [], [], 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, heard, expected, autojunk=False).get_opcodes():
        span = words[i1:i2]
        said = " ".join(w["text"] for w in span)
        before, after = (heard[i1 - 1] if i1 > 0 else ""), (heard[i2] if i2 < len(heard) else "")
        if op in ("equal", "replace") and i2 - i1 == j2 - j1:
            for word, spelling in zip(span, ref[j1:j2]):
                fixed += op == "replace" and word["text"] != spelling
                word["text"] = spelling
            kept += span
        elif op == "delete" and len(span) <= 2 and all(w["end"] - w["start"] < 0.25 or norm(w["text"]) in (before, after) for w in span):
            if i2 < len(words) and heard[i2] and heard[i2] == norm(span[-1]["text"]):  # "the the"
                words[i2]["start"] = span[0]["start"]
            elif kept:
                kept[-1]["end"] = span[-1]["end"]
            notes.append((span[0]["start"], f"dropped {said!r}: not in the script"))
        elif op == "replace" and len(span) <= 3 and j2 - j1 <= 3 and not re.search(r"\d", said):
            tokens, start, end = ref[j1:j2], span[0]["start"], span[-1]["end"]
            total, pos = sum(len(t) for t in tokens), start
            for n, token in enumerate(tokens):
                stop = end if n == len(tokens) - 1 else pos + (end - start) * len(token) / total
                kept.append({"text": token, "start": round(pos, 3), "end": round(stop, 3)})
                pos = stop
            fixed += len(tokens)
        elif op == "insert" and clip and i1 in (0, len(words)):
            continue  # script words before or after the recorded part
        else:
            if not (op == "replace" and len(span) <= 3 and re.search(r"\d", said)):  # digits stay as Whisper wrote them
                when = span[0]["start"] if span else (kept[-1]["end"] if kept else 0)
                notes.append((when, f"heard {said!r}, script says {' '.join(ref[j1:j2])[:80]!r}: listen"))
            kept += span
    words[:] = kept
    return fixed, notes


def transcript_md(slug: str, words: list[dict], duration: float) -> str:
    """Readable transcript: one line per sentence or pause, with the start time."""
    lines, current = [], []
    for i, word in enumerate(words):
        current.append(word)
        ends = i + 1 == len(words)
        gap = 99 if ends else words[i + 1]["start"] - word["end"]
        if word["text"][-1:] in ".?!" or gap > 0.7 or len(current) >= 22:  # an empty text counts as punctuation
            line = f"`{fmt_t(current[0]['start'])}` " + " ".join(w["text"] for w in current)
            if gap > 1.2 and not ends:
                line += f"  _(pause {gap:.1f}s)_"
            lines.append(line)
            current = []
    return (f"# Transcript: {slug}\n\n{len(words)} words, {fmt_t(duration)}. Generated from words.json. "
            "Edit words.json, not this file.\n\n" + "\n\n".join(lines) + "\n")


# ---------------------------------------------------------------- cues

HEAD = re.compile(r"^##\s+([\w.\-]+)\s*(.*)$")


def parse_cues_md(text: str) -> list[dict]:
    """Read 03_cues/cues.md: a cue per `## id "phrase" @time +offset [sfx: ...]` line, notes below it."""
    cues = []
    for line in text.splitlines():
        head = HEAD.match(line)
        if head:
            cid, rest = head.groups()
            sfx = [item.strip() for group in re.findall(r"\[sfx:\s*([^\]]*)\]", rest) for item in group.split(",") if item.strip()]
            rest = re.sub(r"\[sfx:\s*[^\]]*\]", "", rest)
            phrase = re.search(r'"([^"]+)"', rest)
            at = re.search(r"@\s*([\d:.]+)", rest)
            offset = re.search(r"(?:^|(?<=\s))([+-]\d*\.?\d+)s?", re.sub(r'"[^"]*"', "", rest))
            try:
                when = parse_t(at.group(1)) if at else None
            except ValueError:
                die(f'cue "{cid}": cannot read the time "@{at.group(1)}"')
            if not phrase and when is None:
                die(f'cue "{cid}" needs a "spoken phrase" or an @time')
            cues.append({"id": cid, "phrase": phrase.group(1) if phrase else None, "at": when,
                         "offset": float(offset.group(1)) if offset else 0.0, "note": [], "sfx": sfx})
        elif cues and not line.startswith("# "):
            if "[sfx:" in line:
                die(f'cue "{cues[-1]["id"]}": put [sfx: ...] on the "## {cues[-1]["id"]}" heading line, not in its description')
            cues[-1]["note"].append(line)
    for cue in cues:
        cue["note"] = "\n".join(cue["note"]).strip()
    return cues


def match_phrase(phrase: str, toks: list[str], cursor: int) -> tuple[int, int, float]:
    """Find a spoken phrase in the normalised transcript words from `cursor`: (first, last, score) or (-1, -1, 0.0)."""
    target = [t for t in (norm(w) for w in phrase.split()) if t]
    if not target:
        return -1, -1, 0.0
    text, n, wanted = " ".join(target), len(target), set(target)
    seen, best = [], 0.0
    for i in range(cursor, len(toks)):
        for size in (n, n - 1, n + 1):
            if size < 1 or i + size > len(toks) or wanted.isdisjoint(toks[i:i + size]):
                continue
            score = difflib.SequenceMatcher(None, text, " ".join(toks[i:i + size])).ratio()
            if score >= 0.999:
                return i, i + size - 1, score
            seen.append((i, i + size - 1, score))
            best = max(best, score)
    return next(((first, last, score) for first, last, score in seen if score >= best - 0.03), (-1, -1, 0.0))


def cmd_cues(a) -> None:
    """cues.md plus words.json to 03_cues/cues.json and cues.js."""
    vdir = video_dir(a.slug)
    words_file, sheet = vdir / "02_transcript" / "words.json", vdir / "03_cues" / "cues.md"
    if not words_file.exists():
        die("no 02_transcript/words.json yet. Run transcribe first.")
    if not sheet.exists():
        die("no 03_cues/cues.md. Write the cue sheet first (see stages/03_cues/CONTEXT.md).")
    data = json.loads(words_file.read_text(encoding="utf-8"))
    words, duration = data["words"], data["duration"]
    sheet_text = sheet.read_text(encoding="utf-8")
    cues = parse_cues_md(sheet_text)
    if not cues:
        die('cues.md has no cues. Each cue is a line like: ## intro "every folder is a workspace"')
    toks = [norm(w["text"]) for w in words]
    cursor, problems, found, ids = 0, [], [], set()
    for cue in cues:
        if cue["id"] in ids:
            problems.append(f"duplicate id {cue['id']}")
        ids.add(cue["id"])
        if cue["phrase"]:
            first, last, score = match_phrase(cue["phrase"], toks, cursor)
            if first < 0 or score < a.threshold:
                after = fmt_t(words[cursor]["start"] if cursor < len(words) else duration)
                closest = " ".join(toks[first:last + 1]) if first >= 0 else "-"
                problems.append(f'{cue["id"]}: "{cue["phrase"]}" not found after {after} (closest: "{closest}" {score:.2f})')
                continue
            start, phrase_end, said, score = words[first]["start"], words[last]["end"], " ".join(w["text"] for w in words[first:last + 1]), round(score, 2)
            cursor = first
        else:
            start = phrase_end = cue["at"]
            said, score = "", 1.0
            cursor = next((k for k, w in enumerate(words) if w["start"] >= start), cursor)
        found.append({"id": cue["id"], "start": round(max(0.0, start + cue["offset"]), 3), "end": 0, "phraseEnd": phrase_end,
                      "phrase": cue["phrase"], "text": said, "note": cue["note"], "score": score, "sfx": cue["sfx"]})
    if problems:
        for problem in problems:
            print(f"  x {problem}")
        die("fix cues.md (reword the phrase to match transcript.md, or use @time) and re-run")
    if any(cue["sfx"] for cue in cues):
        synth = _chip()
        for cue in cues:
            for token in cue["sfx"]:
                try:
                    kind, name, _ = synth.parse_sfx(token)
                except ValueError as error:
                    print(f"  ! cue {cue['id']}: {error}")
                    continue
                if kind == "file" and not sfx_file(vdir, name):
                    print(f"  ! cue {cue['id']}: sound effect file not found: {name} (04_scene/assets/ or library/sfx/)")
    order = sorted(found, key=lambda c: c["start"])
    for n, cue in enumerate(order):
        depth = cue["id"].count(".")
        cue["end"] = next((o["start"] for o in order[n + 1:] if o["id"].count(".") <= depth), round(duration, 3))
    head = sheet_text.split("\n## ", 1)[0]
    music = re.search(r"(?m)^music:\s*(file:[A-Za-z0-9._-]+|\w+)(?:[ \t]+(\d*\.?\d+))?", head)
    meta = {"duration": duration, "voice": "../01_voice/" + (data.get("voice") or find_voice(vdir).name), "slug": a.slug,
            "music": music.group(1) if music else None, "music_gain": float(music.group(2)) if music and music.group(2) else 0.3}
    payload = {"meta": meta, "cueList": order, "cues": {c["id"]: c for c in order}, "words": words}
    snapshot = creative_snapshot(vdir)
    if snapshot:
        meta["creative_revision"] = hashlib.sha256((vdir / "creative" / "snapshot.json").read_bytes()).hexdigest()
        payload["creative"] = {"characters": [{"id": c["character_id"], "variant": c["variant_id"], "manifest": "../" + c["manifest"]}
                                              for c in snapshot["characters"]]}
    out = vdir / "03_cues"
    (out / "cues.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    payload["levels"] = voice_levels(vdir)
    (out / "cues.js").write_text("// Generated by the cues command. Do not edit; edit cues.md and run cues again.\n"
                                 "window.ANIM = " + json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"{'cue':<24}{'start':>8}{'end':>8}  said")
    for cue in order:
        fuzzy = f"  (fuzzy {cue['score']:.2f})" if cue["score"] < 0.9 else ""
        print(f"{'  ' * cue['id'].count('.') + cue['id']:<24}{fmt_t(cue['start']):>8}{fmt_t(cue['end']):>8}  {cue['text'][:60]}{fuzzy}")
    print(f"-> {out / 'cues.js'}")


def voice_levels(vdir: Path, rate: int = 60) -> dict:
    """Level curve of the voice, 0 to 100 per 1/rate second (moves character mouths). Cached in levels.json."""
    voice, cache = find_voice(vdir), vdir / "02_transcript" / "levels.json"
    if cache.exists() and cache.stat().st_mtime >= voice.stat().st_mtime:
        return json.loads(cache.read_text(encoding="utf-8"))
    import numpy as np
    run = subprocess.run(["ffmpeg", "-v", "error", "-i", str(voice), "-ac", "1", "-ar", "12000", "-f", "s16le", "-"],
                         capture_output=True)
    if run.returncode and b"does not contain any stream" not in run.stderr:
        die(f"ffmpeg could not read {voice}: {run.stderr.decode('utf-8', 'replace').strip()}")
    samples = np.frombuffer(run.stdout[:len(run.stdout) // 2 * 2], dtype="<i2").astype(np.float64) / 32768
    window = 12000 // rate
    count = len(samples) // window
    if not count or np.abs(samples).max() < 1e-7:
        result = {"rate": rate, "data": [0] * max(1, int(len(samples) / 12000 * rate))}
    else:
        frames = samples[:count * window].reshape(count, window)
        db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1) + 1e-10))
        top = np.percentile(db, 97)
        level = np.clip((db - (top - 38)) / 38, 0, 1) ** 1.4
        data, running = [], 0.0
        for value in level:  # opens at once, closes gradually
            running = float(value) if value > running else running + (float(value) - running) * 0.35
            data.append(int(round(running * 100)))
        result = {"rate": rate, "data": data}
    cache.write_text(json.dumps(result, separators=(",", ":")), encoding="utf-8")
    return result


# ---------------------------------------------------------------- status, preview, studio


def stage_state(vdir: Path) -> list[str]:
    """`done` or `-` for each stage in STAGES."""
    def files(folder: str) -> list[Path]:
        path = vdir / folder
        return [p for p in path.iterdir() if p.is_file()] if path.is_dir() else []

    scene = vdir / "04_scene"
    scene_file = scene / "scene.js" if (scene / "scene.js").exists() else scene / "index.html"
    cues_json, cues_md = vdir / "03_cues" / "cues.json", vdir / "03_cues" / "cues.md"
    done = [
        any(p.suffix.lower() in AUDIO_EXT for p in files("01_voice")),
        (vdir / "02_transcript" / "words.json").exists(),
        cues_json.exists() and cues_md.exists() and cues_json.stat().st_mtime >= cues_md.stat().st_mtime,
        scene_file.exists() and "TEMPLATE" not in scene_file.read_text(encoding="utf-8", errors="replace"),
        any(p.suffix == ".mp4" for p in files("05_render")),
    ]
    return ["done" if flag else "-" for flag in done]


def cmd_status(a) -> None:
    """Table of all videos, or one, by stage."""
    from studio import project_paths
    try:
        projects = [video_dir(a.slug)] if a.slug else list(project_paths.iter_projects(ROOT))
    except project_paths.ProjectPathError as error:
        die(str(error))
    if not projects:
        print("no videos yet. `python anim.py new <slug> <voice-file> --brand <brand>`")
        return
    fixture = ROOT / "tests" / "fixtures" / "silent-first-scene"

    def identity(path: Path) -> str:
        if path == fixture:
            return "silent-first-scene"
        try:
            return project_paths.project_id(ROOT, path)
        except project_paths.ProjectPathError:
            return path.name

    names = [identity(p) for p in projects]
    width = max(36, max(len(n) for n in names) + 2)
    print("video".ljust(width) + "00_research".ljust(15) + "".join(folder.ljust(15) for folder, _ in STAGES))
    for name, path in zip(names, projects):
        research = "present" if (path / "00_research").is_dir() else "not used"
        print(name.ljust(width) + research.ljust(15) + "".join(state.ljust(15) for state in stage_state(path)))


def cmd_preview(a) -> None:
    """Show the scene live: the page address (canvas) or a HyperFrames preview server."""
    vdir = video_dir(a.slug)
    if video_engine(vdir) != "hyperframes":
        print(scene_url(vdir).removesuffix("?render"))
        print("  (or `python anim.py studio`)")
        return
    if a.stop:
        hf("preview", "--stop", cwd=vdir / "04_scene")
        return
    run = hf("preview", "--port", str(a.port), "--no-open", "--background", cwd=vdir / "04_scene")
    if run.returncode:
        die("hyperframes preview did not start")
    print(f"preview -> http://localhost:{a.port}  (stop it: python anim.py preview {a.slug} --stop)")


def cmd_studio(a) -> None:
    """Start the local studio web app (runs until interrupted)."""
    from studio import server
    server.serve(ROOT, a.port)


def cmd_studio_job(a) -> None:
    """Run one validated production job and wait for it. A failed job still exits 0; read its state."""
    from studio import jobs
    options_file = getattr(a, "options", None)
    options = json.loads(Path(options_file).read_text(encoding="utf-8")) if options_file else {}
    busy = ("queued", "running", "cancelling")
    job = jobs.start_job(ROOT, a.action, a.slug, options, getattr(a, "expected", None),
                         getattr(a, "request_id", None) or uuid.uuid4().hex)
    try:
        while job["state"] in busy:
            time.sleep(0.1)
            job = jobs.job_detail(ROOT, job["id"])
    except KeyboardInterrupt:
        job = jobs.cancel_job(ROOT, job["id"])
        while job["state"] in busy:
            time.sleep(0.1)
            job = jobs.job_detail(ROOT, job["id"])
    print(json.dumps(job, ensure_ascii=False))


# ====================================================================================================
# 20-browser
# ====================================================================================================

HF_LENGTH_TOL = 0.5  # largest allowed gap in seconds between the HyperFrames MP4 and the voice
_creative_http = None  # local server for creative snapshot videos, started on first use

CONTACT = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__SLUG__ stills</title>
__FONTS__
<style>
  :root { --bg: #0B0B10; --card: #14141B; --line: #262630; --text: #F5F2EA; --muted: #B9B5A8; --faint: #8A867C; --accent: #FF5B2E; }
  * { box-sizing: border-box; }
  body { margin: 0; padding: 24px; background: var(--bg); color: var(--text); font: 14px/1.45 Inter, system-ui, sans-serif; }
  h1 { margin: 0 0 20px; font-size: 22px; font-weight: 600; letter-spacing: -0.01em; }
  h1::before { content: ""; display: inline-block; width: 10px; height: 10px; margin-right: 10px; border-radius: 50%; background: var(--accent); }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 20px; }
  .card { margin: 0; background: var(--card); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
  .card a { display: block; line-height: 0; }
  .card img { display: block; width: 100%; height: auto; border-radius: 6px 6px 0 0; }
  .cap { padding: 10px 12px 12px; }
  .cap b { font-weight: 600; }
  .cap .t { margin-left: 8px; color: var(--accent); font: 13px "JetBrains Mono", ui-monospace, monospace; }
  .cap .text { margin-top: 4px; color: var(--muted); }
  .cap .text:not(:empty)::before { content: "\\201C"; }
  .cap .text:not(:empty)::after { content: "\\201D"; }
  .cap .note { margin-top: 6px; color: var(--faint); font-size: 12px; white-space: pre-wrap; }
</style>
</head>
<body>
<h1>__SLUG__</h1>
<div class="grid">
__CARDS__
</div>
</body>
</html>
"""


def scene_url(vdir: Path) -> str:
    """URL of the scene page in render mode: a file:// URI, or the local creative server for snapshot videos."""
    global _creative_http
    page = vdir / "04_scene" / "index.html"
    if not page.is_file():
        die("no 04_scene/index.html")
    if not (vdir / "03_cues" / "cues.js").is_file():
        die("no 03_cues/cues.js. Run `cues` first.")
    ensure_clips(vdir)
    if creative_snapshot(vdir) is None:
        return page.resolve().as_uri() + "?render"
    import studio.server
    import studio.workspace
    studio.workspace.creative_scene_html(ROOT, vdir.resolve().relative_to((ROOT / "videos").resolve()).as_posix())
    try:
        revision = json.loads((vdir / "03_cues" / "cues.json").read_text(encoding="utf-8"))["meta"]["creative_revision"]
    except (OSError, ValueError, KeyError, TypeError):
        revision = None
    if revision != hashlib.sha256((vdir / "creative" / "snapshot.json").read_bytes()).hexdigest():
        die("creative snapshot changed; run `cues` again before preview, stills, check or render")
    if _creative_http is None:
        _creative_http = studio.server.make_server(ROOT, 0)
        threading.Thread(target=_creative_http.serve_forever, daemon=True).start()
    rel = vdir.resolve().relative_to(ROOT.resolve()).as_posix()
    return f"http://127.0.0.1:{_creative_http.server_port}/{rel}/04_scene/index.html?render"


async def open_page(p, url: str, init: str | None = None):
    """Open a scene page in a fresh browser and wait until it is ready. Returns (browser, page, size, errors)."""
    browser = await launch_browser(p)
    try:
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        errors: list[str] = []
        page.anim_warnings = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        def on_console(m) -> None:
            if m.type == "error":
                errors.append(m.text)
            elif m.type == "warning" and m.text.startswith("[anim]"):
                page.anim_warnings.append(m.text)
        page.on("console", on_console)
        if init:
            await page.add_init_script(path=init)
        if os.environ.get("ANIM_OFFLINE") == "1":
            async def offline(route) -> None:
                u = route.request.url
                if u.startswith(("http://", "https://")) and not u.startswith(("http://127.0.0.1:", "http://localhost:")):
                    await route.abort()
                else:
                    await route.continue_()
            await page.route("**/*", offline)
        await page.goto(url)
        await page.wait_for_function("window.__ready === true || !!window.__assetError", timeout=30000)
        asset_error = await page.evaluate("window.__assetError")
        if asset_error or errors:
            raise RuntimeError("scene startup failed: " + "; ".join(([str(asset_error)] if asset_error else []) + errors[:5]))
        size = await page.evaluate("window.__size")
        await page.set_viewport_size({"width": size["w"], "height": size["h"]})
        await page.evaluate("window.__seek(0)")
        return browser, page, size, errors
    except BaseException:
        try:
            await browser.close()
        except Exception:
            pass
        raise


async def seek_shot(page, t: float, fmt: str = "jpeg", quality: int = 92) -> bytes:
    """Draw the scene at time t and capture the viewport (PNG, or JPEG with the given quality)."""
    await page.evaluate(f"window.__seek({t:.4f})")
    if fmt == "png":
        return await page.screenshot(type="png")
    return await page.screenshot(type="jpeg", quality=quality)


# ---- stills ----------------------------------------------------------------

def cmd_stills(a) -> None:
    from playwright.async_api import async_playwright
    vdir = video_dir(a.slug)
    tone_gate(vdir, screen_text(vdir), getattr(a, "skip_tone", False))
    hyperframes = video_engine(vdir) == "hyperframes"
    url = None if hyperframes else scene_url(vdir)
    cues = json.loads((vdir / "03_cues" / "cues.json").read_text(encoding="utf-8")).get("cueList") or []
    out = vdir / "05_render" / "stills"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    hold, at = getattr(a, "hold", 0.9), getattr(a, "at", None)
    if at:
        shots = [{"id": f"t{t:.1f}", "t": t, "text": "", "note": ""} for t in map(parse_t, at.split(","))]
    else:
        shots = [{"id": c["id"], "t": c["start"] + min(hold, 0.6 * (c["end"] - c["start"])),
                  "text": c.get("text", ""), "note": c.get("note", "")} for c in cues]
    for i, s in enumerate(shots):
        s["file"] = f"{i:03d}_{s['id']}.png"

    async def shoot() -> list[str]:
        async with async_playwright() as p:
            browser, page, _, errors = await open_page(p, url)
            try:
                for s in shots:
                    (out / s["file"]).write_bytes(await seek_shot(page, s["t"], "png"))
            finally:
                await browser.close()
            return list(errors)
    errors = hf_stills(vdir, out, shots) if hyperframes else asyncio.run(shoot())
    write_contact(vdir, vdir.name, shots)
    n = write_sheets(vdir, shots)
    for e in errors[:10]:
        print(f"  page error: {e}")
    print(f"{len(shots)} stills -> {vdir / '05_render' / 'contact.html'}  (+ contact.png, sheets/ x{n})")


def hf_stills(vdir: Path, out: Path, shots: list[dict], fps: int = 30) -> list:
    """Cut the shot frames out of a draft render (HyperFrames has no seek-and-shoot). Returns no page errors."""
    draft = vdir / "05_render" / "_hf_stills.mp4"
    try:
        r = hf("render", "-o", str(draft), "-q", "draft", "--fps", str(fps), "--quiet", cwd=vdir / "04_scene")
        if r.returncode != 0 or not draft.exists():
            die("hyperframes draft render failed")
        for i, s in enumerate(shots):
            s["file"] = f"{i:03d}_{s['id']}.png"
            n = max(0, round(s["t"] * fps))
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(draft), "-vf", f"select=eq(n\\,{n})",
                            "-frames:v", "1", "-fps_mode", "passthrough", str(out / s["file"])], check=True)
    finally:
        draft.unlink(missing_ok=True)
    return []


def write_sheets(vdir: Path, shots: list[dict]) -> int:
    """Labelled review sheets in 05_render/sheets/. Returns the number of sheets."""
    from PIL import Image, ImageDraw
    sheets = vdir / "05_render" / "sheets"
    shutil.rmtree(sheets, ignore_errors=True)
    sheets.mkdir(parents=True)
    tall = 'data-height="1920"' in (vdir / "04_scene" / "index.html").read_text(encoding="utf-8")
    (cw, ch), cols, rows = ((270, 480), 5, 2) if tall else ((640, 360), 3, 4)
    per, strip = cols * rows, 22
    for n in range(math.ceil(len(shots) / per)):
        sheet = Image.new("RGB", (cw * cols, (ch + strip) * rows), (20, 18, 16))
        draw = ImageDraw.Draw(sheet)
        for i, s in enumerate(shots[n * per:(n + 1) * per]):
            x, y = (i % cols) * cw, (i // cols) * (ch + strip)
            draw.text((x + 6, y + 4), f"{s['id']}  {fmt_t(s['t'])}", fill=(240, 200, 150))
            with Image.open(vdir / "05_render" / "stills" / s["file"]) as im:
                sheet.paste(im.convert("RGB").resize((cw, ch), Image.NEAREST), (x, y + strip))
        sheet.save(sheets / f"sheet_{n:02d}.png")
    return math.ceil(len(shots) / per)


def write_contact(vdir: Path, slug: str, shots: list[dict]) -> None:
    """Write 05_render/contact.html (all stills with captions) and its full-page picture contact.png."""
    from playwright.async_api import async_playwright
    esc = html.escape
    cards = "\n".join(
        f'<figure class="card"><a href="stills/{esc(s["file"])}"><img src="stills/{esc(s["file"])}" alt="{esc(str(s["id"]))}" loading="lazy"></a>'
        f'<figcaption class="cap"><b>{esc(str(s["id"]))}</b><span class="t">{esc(fmt_t(s["t"]))}</span>'
        f'<div class="text">{esc(s.get("text") or "")}</div><div class="note">{esc(s.get("note") or "")}</div></figcaption></figure>'
        for s in shots)
    page = vdir / "05_render" / "contact.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    fonts = ROOT / "_runtime" / "fonts" / "fonts.css"
    link = ""
    if fonts.is_file():
        rel = Path(os.path.relpath(fonts.resolve(), page.parent.resolve())).as_posix()
        link = f'<link rel="stylesheet" href="{esc(rel)}">'
    page.write_text(CONTACT.replace("__FONTS__", link).replace("__SLUG__", esc(slug)).replace("__CARDS__", cards), encoding="utf-8")

    async def shoot() -> None:
        async with async_playwright() as p:
            browser = await launch_browser(p)
            try:
                tab = await browser.new_page(viewport={"width": 1800, "height": 900})
                await tab.goto(page.resolve().as_uri())
                await tab.evaluate("document.fonts.ready")
                await tab.screenshot(path=str(page.with_suffix(".png")), full_page=True)
            finally:
                await browser.close()
    asyncio.run(shoot())


# ---- scene check -----------------------------------------------------------

def run_check(vdir: Path, fps: float = 6) -> dict:
    """Seek through the whole scene and count the defects that must be zero. Writes 05_render/check.md."""
    import check
    from playwright.async_api import async_playwright
    url = scene_url(vdir)
    dur = float(json.loads((vdir / "03_cues" / "cues.json").read_text(encoding="utf-8"))["meta"]["duration"])
    times = [k / fps for k in range(int(dur * fps) + 1) if k / fps < dur]
    probes = [dur * (k + 0.5) / 5 for k in range(5)]

    async def browse():
        async with async_playwright() as p:
            browser, page, size, errors = await open_page(p, url, init=str(ROOT / "_runtime" / "textcheck.js"))
            try:
                async def probe() -> list[str]:
                    return [hashlib.sha1(await seek_shot(page, t, "png")).hexdigest() for t in probes]
                first = await probe()
                await page.evaluate("window.__texts()")
                frames = []
                for t in times:
                    await page.evaluate(f"window.__seek({t:.4f})")
                    frames.append((t, await page.evaluate("window.__texts()")))
                again = await probe()
            finally:
                await browser.close()
            return size, list(errors), list(page.anim_warnings), frames, sum(x != y for x, y in zip(first, again))
    size, errors, warnings, frames, drift = asyncio.run(browse())
    w, h, dt = size["w"], size["h"], 1 / fps
    details: list[str] = []
    unmapped = sum(r.get("unmapped", 0) for _, r in frames)

    cut_seen: set[str] = set()
    for t, r in frames:
        for b in r["boxes"]:
            if b["s"] not in cut_seen and check.cut_off(b, w, h):
                cut_seen.add(b["s"])
                details.append(f"{fmt_t(t)}  cut off: '{b['s']}'")

    pairs: dict[tuple, list[float]] = {}
    for t, r in frames:
        for pair in check.overlaps(r["boxes"]):
            pairs.setdefault(pair, []).append(t)
    lasting = check.lasting(pairs, dt)
    details += [f"{fmt_t(pairs[pair][0])}  overlap: '{pair[0]}' / '{pair[1]}'" for pair in lasting]

    short = check.too_short([(t, [b["s"] for b in r["boxes"]]) for t, r in frames], dt, dur)
    details += [f"{fmt_t(t0)}  too short ({shown:.1f}s < {check.read_floor(s):.1f}s): '{s}'" for s, t0, shown in short]

    invented = check.invented_labels([b["s"] for _, r in frames for b in r["boxes"]])
    details += [f"invented label ({rule}): '{s}'" for s, rule in invented]

    scene_js = vdir / "04_scene" / "scene.js"
    clock = check.clock_use(scene_js.read_text(encoding="utf-8")) if scene_js.is_file() else []
    details += [f"scene.js uses {name}" for name in clock]
    details += [f"page error: {e}" for e in errors]
    distinct = sorted(set(warnings))
    details += [f"cue warning: {x}" for x in distinct]

    counters = {"page errors": len(errors), "cue warnings": len(distinct), "clock use": len(clock),
                "nondeterministic frames": drift, "text cut off": len(cut_seen), "text overlaps": len(lasting),
                "text too short to read": len(short), "invented labels": len(invented)}
    quality, quality_details = quality_check(vdir)
    sfx, sfx_details = sfx_check(vdir)
    counters |= quality | sfx | check.brand_counters(ROOT, video_brand(vdir))
    details += quality_details + sfx_details
    info = {"frames checked (info)": len(times), "unmapped text (info)": unmapped,
            "brief overlaps, cross-fades (info)": len(pairs) - len(lasting), **music_info(vdir)}
    block = check.report(counters, info)
    text = f"# Check: {vdir.name}\n\n```\n{block}\n```\n\n" + "\n".join(f"- {d}" for d in details[:40])
    if len(details) > 40:
        text += f"\n\n... and {len(details) - 40} more"
    (vdir / "05_render").mkdir(parents=True, exist_ok=True)
    (vdir / "05_render" / "check.md").write_text(text, encoding="utf-8")
    return {"counters": counters, "info": info, "details": details, "block": block}


def music_info(vdir: Path) -> dict:
    """Info row for a missing music bed (a warning, never a failing counter)."""
    try:
        data = json.loads((vdir / "03_cues" / "cues.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict) or not isinstance(data.get("meta"), dict) or data["meta"].get("music"):
        return {}
    return {"music: none (warning)": 1}


def hf_check(vdir: Path) -> dict:
    """The gate for HyperFrames videos: lint, text analysis and the MP4 length. Writes 05_render/check.md."""
    import check
    scene = vdir / "04_scene"
    r = hf("lint", "--json", cwd=scene, capture=True)
    try:
        lint = json.loads(r.stdout)
    except ValueError:
        die("hyperframes lint gave no JSON:\n" + ((r.stdout or "") + (r.stderr or ""))[-2000:])
    details = [f"lint {f.get('severity') or '?'}: {f.get('code') or ''} {f.get('message') or ''}".rstrip()
               for f in lint.get("findings") or []]
    counters = {"lint errors": lint.get("errorCount", 0), "video vs voice length": 0}
    info = {"lint warnings (info)": lint.get("warningCount", 0), **music_info(vdir)}

    docs, problems = check.scene_documents(scene)
    counters["composition errors"] = len(problems)
    details += problems
    if len(docs) > 1:
        info["sub-compositions read (info)"] = len(docs) - 1
    text_only = 0 if "text-only" in project_allow(vdir) else check.no_visual_layer("\n".join(t for _, t in docs))
    counters["no visual layer"] = text_only
    if text_only:
        details.append("text only: add a library block, screen, image or stock shot (_shared/motion.md); a text video only when the user asks")
    labels = check.invented_labels(screen_text(vdir).get("index.html", "").split("\n"))
    counters["invented labels"] = len(labels)
    details += [f"invented label ({rule}): '{s}'" for s, rule in labels]

    mp4 = vdir / "05_render" / f"{vdir.name}.mp4"
    if mp4.exists():
        gap = probe_duration(mp4) - probe_duration(find_voice(vdir))
        counters["video vs voice length"] = int(abs(gap) > HF_LENGTH_TOL)
        details.append(f"video is {gap:+.2f}s against the voice (limit {HF_LENGTH_TOL:g}s)")
    else:
        info["video vs voice length: no MP4 yet (info)"] = 0

    counters |= check.brand_counters(ROOT, video_brand(vdir))
    quality, quality_details = quality_check(vdir)
    sfx, sfx_details = sfx_check(vdir)
    counters |= quality | sfx
    details += quality_details + sfx_details

    rows = [(k, str(counters.get(k, 0))) for k in check.HF_FAIL_KEYS]
    rows += [(k, "n/a (hyperframes)") for k in check.FAIL_KEYS if k not in check.HF_FAIL_KEYS]
    rows += [(k, str(v)) for k, v in sorted(info.items())]
    wid = max(len(k) for k, _ in rows)
    block = "\n".join(f"{k:<{wid}}  {v}" for k, v in rows)
    (vdir / "05_render").mkdir(parents=True, exist_ok=True)
    (vdir / "05_render" / "check.md").write_text(
        f"# Check: {vdir.name} (hyperframes)\n\n```\n{block}\n```\n\n" + "\n".join(f"- {d}" for d in details[:40]),
        encoding="utf-8")
    return {"counters": counters, "info": info, "details": details, "block": block, "fail_keys": check.HF_FAIL_KEYS}


def load_sfx_files(vdir: Path, events) -> dict:
    """Decode every file sound effect in events [(time, token)] to a mono float array. Dies on a bad or missing effect."""
    import numpy as np
    try:
        import synth
    except ImportError:
        sys.path.insert(0, str(ROOT / "_runtime"))
        import synth
    files: dict = {}
    for _, token in events:
        try:
            kind, name, _ = synth.parse_sfx(token)
        except ValueError as e:
            die(f"{e} (03_cues/cues.md, _shared/sound.md)")
        if kind != "file" or name in files:
            continue
        path = sfx_file(vdir, name)
        if path is None:
            die(f"sound effect file not found: {name} (looked in 04_scene/assets/ and library/sfx/; _shared/sound.md)")
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f64le", "-ac", "1", "-ar", str(synth.SR), "-"],
                             capture_output=True, check=True).stdout
        files[name] = np.frombuffer(raw, dtype="<f8").astype(np.float64)
        if not len(files[name]):
            die(f"sound effect file has no audio: {path}")
    return files


# ---- thumbnails and chapters -----------------------------------------------

def cmd_thumbnail(a) -> None:
    from playwright.async_api import async_playwright
    from PIL import Image
    vdir = video_dir(a.slug)
    if video_engine(vdir) == "hyperframes":
        return hf_thumbnail(vdir, vdir.name)
    page = vdir / "04_scene" / "thumbnail.html"
    if not page.is_file():
        die("no 04_scene/thumbnail.html (copy the one from a past video and change thumbnail.js)")
    out = vdir / "05_render"
    out.mkdir(parents=True, exist_ok=True)
    uri = page.resolve().as_uri()

    async def shoot() -> list[str]:
        async with async_playwright() as p:
            browser, tab, _, errors = await open_page(p, uri + "?render&v=1")
            try:
                for v in await tab.evaluate("window.THUMBS") or []:
                    await tab.goto(f"{uri}?render&v={v}")
                    await tab.wait_for_function("window.__ready === true", timeout=30000)
                    await tab.evaluate("window.__seek(0)")
                    (out / f"thumbnail-{v}.png").write_bytes(await tab.screenshot(type="png"))
                    print(f"  thumbnail-{v}.png")
            finally:
                await browser.close()
            return list(errors)
    errors = asyncio.run(shoot())
    size = "1280x720"
    for f in sorted(out.glob("thumbnail-*.png")):
        with Image.open(f) as im:
            tall = im.height > im.width
            fixed = None if tall else im.resize((1280, 720), Image.LANCZOS)
        if fixed is not None:
            fixed.save(f)
        size = "1080x1920" if tall else "1280x720"
    for e in errors[:10]:
        print(f"  page error: {e}")
    print(f"-> {out}  ({size})")


def hf_thumbnail(vdir: Path, slug: str) -> None:
    """Take one frame from the rendered MP4 (or the first still) as the thumbnail."""
    render = vdir / "05_render"
    render.mkdir(parents=True, exist_ok=True)
    png, mp4, stills = render / f"thumbnail-{slug}.png", render / f"{slug}.mp4", sorted((render / "stills").glob("*.png"))
    if mp4.exists():
        src = ["-ss", f"{min(1.0, probe_duration(mp4) / 2):.3f}", "-i", str(mp4)]
    elif stills:
        src = ["-i", str(stills[0])]
    else:
        die(f"no 05_render/{slug}.mp4 and no stills yet; run `anim.py render` or `anim.py stills` first")
    scale = "scale=w='if(gt(iw,ih),1280,iw)':h='if(gt(iw,ih),720,ih)':flags=lanczos"
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *src, "-frames:v", "1", "-vf", scale, str(png)],
                       capture_output=True, text=True)
    if r.returncode != 0 or not png.exists():
        die("ffmpeg thumbnail failed:\n" + (r.stderr or "")[-2000:])
    print(f"  thumbnail-{slug}.png")
    print(f"-> {render}")


def cmd_chapters(a) -> None:
    cues = json.loads((video_dir(a.slug) / "03_cues" / "cues.json").read_text(encoding="utf-8"))["cueList"]
    top = [c for c in cues if "." not in str(c["id"])]
    keep = [c for i, c in enumerate(top) if i in (0, len(top) - 1) or top[i + 1]["start"] - c["start"] >= 10]
    print("Top-level cues (merge any under 10 s; YouTube needs 0:00 first and 10 s per chapter). Write real titles:")
    for c in keep:
        s = 0 if c is top[0] else int(c["start"])
        print(f"{s // 60}:{s % 60:02d} {c['id']}: {c.get('text', '')}")


# ====================================================================================================
# 30-render
# ====================================================================================================

FX_GAIN = 0.8  # input level of the effect stem when 03_cues/cues.md has no sfx: line
SFX_DISTANCE_DB = 3  # during speech the effects stay this far under the voice (RMS and peak); chosen by ear, 2026-10-21
HF_BIN = ROOT / "tools" / "hyperframes" / "node_modules" / ".bin" / "hyperframes"
EARSHOT_PY = ROOT / "tools" / "earshot" / ".venv" / "bin" / "python"
MAX_RECORD_SECONDS = 90  # longest recording; at 12 fps that is about 1000 frame files
SFX_LIBRARY = ROOT / "library" / "sfx"  # shared sound files for [sfx: file:<name>]
SOUND_EXT = ("ogg", "wav", "mp3", "flac")  # brand sound files, in the order they are tried


# ---------------------------------------------------------------- audio helpers


def _relpath(path: Path) -> str:
    """The path relative to the workspace when it is inside it, else as it is."""
    try:
        return str(Path(path).resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def decode_pcm(path: Path, sample_rate: int = 44100):
    """Read an audio file as float samples, shape (frames, channels). The channel count stays as it is."""
    import numpy as np
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels", "-of", "json",
                            str(path)], capture_output=True, text=True, check=True)
    streams = json.loads(probe.stdout or "{}").get("streams") or []
    if not streams:
        raise ValueError(f"no audio stream in {path}")
    channels = int(streams[0]["channels"])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-map", "0:a:0", "-f", "f64le", "-acodec", "pcm_f64le",
                          "-ar", str(sample_rate), "-ac", str(channels), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<f8").reshape(-1, channels).astype(np.float64)


def bed_from_file(src: Path, seconds: float, gain: float, out: Path) -> None:
    """Use a stock music file as the music bed: looped or cut to the video length plus one second, faded out, mono."""
    if not Path(src).exists():
        die(f"music file not found: {src}. Fetch it: python anim.py stock search openverse \"...\" --type audio, "
            "then python anim.py use <slug> <ref>")
    fade = f"afade=t=out:st={max(0, seconds - 2):.3f}:d=2,volume={gain},aresample=44100"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", str(src), "-t", f"{seconds + 1:.3f}",
                    "-af", fade, "-ac", "1", str(out)], check=True)


def master(final: Path, lufs: float = -14.0) -> tuple[float, float] | None:
    """Set the loudness of a finished MP4 to the target by measure, correct, repeat. Returns (LUFS, true peak) or None."""
    if not has_audio(final):
        print("  no audio, master skipped")
        return None
    measured, peak = loudness(final)
    if measured <= -70:
        print("  silent audio, master skipped")
        return None
    tmp = final.with_name(f"{final.stem}-master.mp4")
    gain, ceiling = lufs - measured, -2.0
    try:
        for _ in range(4):
            chain = (f"volume={gain:.2f}dB,alimiter=limit={max(0.0625, 10 ** (ceiling / 20)):.4f}:level=0:attack=1:release=50,"
                     "aresample=44100")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(final), "-map", "0", "-c:v", "copy", "-af", chain,
                            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(tmp)], check=True)
            measured, peak = loudness(tmp)
            if abs(measured - lufs) <= 0.5 and peak <= -1.0:
                break
            gain += lufs - measured
            if peak > -1.0:
                ceiling -= peak + 1.2
        os.replace(tmp, final)
    finally:
        tmp.unlink(missing_ok=True)
    if abs(measured - lufs) > 1 or peak > -1.0:
        print(f"  master: target missed ({measured:.1f} LUFS, true peak {peak:.1f} dBTP; target {lufs:.0f} LUFS, <= -1 dBTP). "
              "The mix has very sharp peaks: lower the loudest effects (_shared/sound.md)")
    return measured, peak


def video_check(final: Path, fps: int, lufs_target: float = -14.0) -> dict:
    """Look for one-frame flashes, flat runs, still stretches, wrong codec or colour tags and wrong loudness. Writes check-video.md."""
    import check
    import numpy as np
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,pix_fmt,color_space,width,height",
                            "-of", "json", str(final)], capture_output=True, text=True, check=True)
    streams = json.loads(probe.stdout).get("streams") or []
    video = next(s for s in streams if s.get("codec_type") == "video")
    audio = [s.get("codec_name", "?") for s in streams if s.get("codec_type") == "audio"]
    space = video.get("color_space")
    space = space if space not in (None, "", "unknown") else "untagged"
    fmt = f"{video.get('codec_name')} {video.get('pix_fmt')} {space}, audio: {', '.join(audio) or 'none'}"
    format_ok = (video.get("codec_name") == "h264" and video.get("pix_fmt") == "yuv420p" and space == "bt709"
                 and (audio == ["aac"] or not audio))
    w, h = 160, max(2, round(video["height"] * 160 / video["width"] / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(final), "-an", "-vf", f"scale={w}:{h}", "-pix_fmt", "gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, dtype=np.uint8)
    g = frames[:len(frames) // (w * h) * w * h].reshape(-1, h, w)
    flashes, flat, dead = ([], [], []) if len(g) < 2 else (check.flashes(g), check.flat_runs(g, fps), check.dead(g, fps))
    lufs, tp = loudness(final) if audio else (None, None)
    loudness_ok = not audio or lufs <= -70 or (abs(lufs - lufs_target) <= 1 and tp <= -1.0)
    lines = [f"# Video check: {final.name}", "",
             f"- one-frame flashes (must be 0): {len(flashes)}", *[f"  - {fmt_t(n / fps)}" for n in flashes],
             f"- flat frames, runs over 3 frames (stops the render): {len(flat)}", *[f"  - {fmt_t(s)} - {fmt_t(e)}" for s, e in flat],
             f"- dead stretches over 3 s (stops the render): {len(dead)}", *[f"  - {fmt_t(s)} - {fmt_t(e)}" for s, e in dead],
             f"- format: {fmt} ({'ok' if format_ok else 'NOT h264/yuv420p/bt709/aac'})"]
    if audio:
        lines.append(f"- loudness: {lufs} LUFS, true peak {tp} dBTP (target {lufs_target:.0f} LUFS, <= -1 dBTP: "
                     f"{'ok' if loudness_ok else 'MISSED'})")
    else:
        lines.append("- loudness: no audio")
    (final.parent / "check-video.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"flashes": flashes, "flat": flat, "dead": dead, "format": fmt, "format_ok": format_ok,
            "lufs": lufs, "tp": tp, "loudness_ok": loudness_ok}


def phone_copy(final: Path, smooth: bool = True) -> Path:
    """A smaller copy for phones and web players (about 28 MiB at most), named <stem>-<height>p.mp4. `smooth` is kept for old calls."""
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                            "-of", "json", str(final)], capture_output=True, text=True, check=True)
    info = json.loads(probe.stdout)
    width, height, dur = info["streams"][0]["width"], info["streams"][0]["height"], float(info["format"]["duration"])
    audio = 96 if dur < 300 else 48
    budget = int(28 * 2 ** 20 * 8 / dur / 1000) - audio
    num, den = (2, 3) if budget >= 600 else (1, 2) if budget >= 150 else (1, 3)
    bitrate = max(budget, 1500)  # floor: a very long video keeps a usable picture and may pass the size goal
    out_w, out_h = width * num // den // 2 * 2, height * num // den // 2 * 2
    target = final.with_name(f"{final.stem}-{out_h}p.mp4")
    for old in final.parent.glob(f"{final.stem}-*p.mp4"):
        if re.fullmatch(re.escape(final.stem) + r"-\d+p\.mp4", old.name):
            old.unlink()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(final), "-map", "0:v", "-map", "0:a?",
                    "-vf", f"scale={out_w}:{out_h}:flags=lanczos", "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                    "-maxrate", f"{bitrate}k", "-bufsize", f"{2 * bitrate}k", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", f"{audio}k", *(["-ac", "1"] if audio == 48 else []),
                    "-movflags", "+faststart", str(target)], check=True)
    return target


def after_render(a, vdir: Path, final: Path, fps: int, started: float, audio_report: dict | None = None) -> None:
    """Level or master the audio, write the audio check, check the picture, make the phone copy."""
    if a.no_master:
        peak = audio_peak(final)
        if peak is not None and peak > -0.5:
            level = final.with_name(f"{final.stem}-level.mp4")
            try:
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(final), "-map", "0", "-c:v", "copy",
                                "-af", f"volume={-1.0 - peak:.2f}dB", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                                str(level)], check=True)
                os.replace(level, final)
            finally:
                level.unlink(missing_ok=True)
            print(f"  audio peak was {peak:.1f} dB, mix lowered to -1 dB")
            peak = audio_peak(final)
        print(f"-> {final}  ({time.time() - started:.0f}s, audio peak {f'{peak:.1f}' if peak is not None else '?'} dB)")
    else:
        lv = master(final, a.lufs)
        elapsed = time.time() - started
        print(f"-> {final}  ({elapsed:.0f}s, audio {lv[0]:.1f} LUFS, true peak {lv[1]:.1f} dBTP)" if lv
              else f"-> {final}  ({elapsed:.0f}s)")
    if audio_report is not None:
        write_audio_check(vdir, final, audio_report)  # after the master: the report holds the SHA-256 of the final file
    if a.start in (None, "") and a.end in (None, ""):
        vc = video_check(final, fps, a.lufs)
        report = _relpath(final.parent / "check-video.md")
        print(f"  video check -> {report}  ({len(vc['dead'])} dead stretches over 3 s; "
              f"format {'ok' if vc['format_ok'] else 'NOT ok'}; loudness {'ok' if vc['loudness_ok'] else 'MISSED'})")
        problems = []
        if vc["flashes"]:
            problems.append((f"video check: {len(vc['flashes'])} one-frame flashes, see {report}",
                             " (--skip-check if the flash is on purpose)"))
        if vc["flat"]:
            problems.append((f"video check: {len(vc['flat'])} runs of flat frames (one solid colour, over 3 frames), see {report}",
                             " (--skip-check if the flat frames are on purpose)"))
        if vc["dead"] and "still" not in project_allow(vdir):
            problems.append((f"video check: {len(vc['dead'])} still stretches over 3 s, see {report} "
                             "(add motion; \"allow\": [\"still\"] in project.json only on the user's request)", ""))
        for message, hint in problems:
            if not a.skip_check:
                die(message + hint)
            print(f"  warning: {message}")
    if a.phone:
        small = phone_copy(final)
        print(f"-> {small}  ({small.stat().st_size / 2 ** 20:.0f} MiB)")


# ---------------------------------------------------------------- effect limiter


def _sfx_windows(voice, effects, speech_intervals, sample_rate, no_voice: bool = False):
    """Walk the effect stream in 20 ms windows: (lo, hi, None) outside speech, else (lo, hi, (voice rms, voice peak, fx rms, fx peak)).

    The voice level is measured over the 1 s around each window, so a soft word start or a stop consonant
    does not read as silence and mute the effect over it."""
    import numpy as np
    voice, effects = np.asarray(voice, dtype=np.float64), np.asarray(effects, dtype=np.float64)
    if sample_rate <= 0 or voice.ndim not in (1, 2) or effects.ndim not in (1, 2):
        raise ValueError("Invalid PCM shape or sample rate")
    if not (np.isfinite(voice).all() and np.isfinite(effects).all()):
        raise ValueError("Audio samples must be finite")
    if no_voice and voice.any():
        raise ValueError("A no-voice project must have a silent voice track (01_voice/voice.wav)")
    intervals = [(float(s), float(e)) for s, e in speech_intervals]
    if effects.any() and not intervals and not no_voice:
        raise ValueError("Effects with voice require corrected word timings in 02_transcript/words.json")
    if any(not (math.isfinite(s) and math.isfinite(e)) or s < 0 or e < s for s, e in intervals):
        raise ValueError("Invalid word timings")
    fx = effects.reshape(-1, 1) if effects.ndim == 1 else effects
    n = len(fx)
    mask = np.zeros(n, dtype=bool)
    for s, e in intervals:  # 50 ms before and 150 ms after every word
        mask[max(0, math.floor((s - 0.05) * sample_rate)):min(n, math.ceil((e + 0.15) * sample_rate))] = True
    v = voice.reshape(-1, 1) if voice.ndim == 1 else voice
    v = v[:n] if len(v) >= n else np.vstack([v, np.zeros((n - len(v), v.shape[1]))])
    step, reach = max(1, round(0.02 * sample_rate)), round(0.49 * sample_rate)
    marks = np.concatenate(([0], np.cumsum(mask)))

    def windows():
        for lo in range(0, n, step):
            hi = min(n, lo + step)
            if marks[hi] == marks[lo]:
                yield lo, hi, None
                continue
            vm, em = v[max(0, lo - reach):min(n, hi + reach)], fx[lo:hi][mask[lo:hi]]
            yield lo, hi, (float(np.sqrt(np.mean(vm ** 2, axis=0)).min()), float(np.abs(vm).max(axis=0).min()),
                           float(np.sqrt(np.mean(em ** 2, axis=0)).max()), float(np.abs(em).max()))
    return windows()


def limit_sfx(voice, effects, speech_intervals, sample_rate, no_voice: bool = False):
    """Lower the effects wherever they come too close to the voice (SFX_DISTANCE_DB plus 1 dB margin). The voice is never changed."""
    import numpy as np
    out = np.array(effects, dtype=np.float64)
    windows = list(_sfx_windows(voice, out, speech_intervals, sample_rate, no_voice))
    if not windows:
        return out
    ratio = 10 ** (-(SFX_DISTANCE_DB + 1) / 20)
    caps, previous = [], 1.0
    for lo, hi, levels in windows:
        if levels is None:
            cap = min(1.0, previous + (hi - lo) / (0.21 * sample_rate))
        else:
            voice_rms, voice_peak, fx_rms, fx_peak = levels
            cap = 1.0 if not fx_peak else min(1.0, ratio * voice_rms / fx_rms if fx_rms else 1.0, ratio * voice_peak / fx_peak)
        caps.append(cap)
        previous = cap
    edges = [caps[0]] + [min(caps[i - 1], caps[i]) for i in range(1, len(caps))] + [caps[-1]]
    positions = [lo for lo, _, _ in windows] + [len(out)]
    curve = np.interp(np.arange(len(out)), positions, edges)
    return out * (curve[:, None] if out.ndim == 2 else curve)


def prepare_effects(vdir: Path, voice: Path, effects, out: Path, start: float, end: float) -> dict:
    """Limit the summed effects under the voice, write them as a WAV file and measure the written file."""
    import numpy as np
    synth = _chip()
    pcm = decode_pcm(voice)
    declared = declared_no_voice(vdir)
    silent = not np.any(pcm)
    if declared and not silent:
        raise ValueError("project.json says template_voice none, but 01_voice/voice.wav is not silent")
    no_voice = declared and silent
    fx = np.asarray(effects, dtype=np.float64)
    intervals: list = []
    if np.any(fx) and not no_voice:
        try:
            cue_words = json.loads((vdir / "03_cues/cues.json").read_text(encoding="utf-8"))["words"]
            file_words = json.loads((vdir / "02_transcript/words.json").read_text(encoding="utf-8"))["words"]
            if not isinstance(cue_words, list) or cue_words != file_words:
                raise ValueError
            intervals = [(float(w["start"]), float(w["end"])) for w in cue_words]
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            raise ValueError("Effects require corrected word timings in 02_transcript/words.json") from None
    synth.write_wav(out, limit_sfx(pcm, fx, intervals, 44100, no_voice))
    report = check_sfx(pcm, decode_pcm(out), intervals, 44100, start, end, no_voice)
    if no_voice:
        report["no_voice"] = "template reel, voice A: silent voice track, no speech to protect"
    try:
        events = sfx_events(json.loads((vdir / "03_cues/cues.json").read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, TypeError):
        events = []
    report.update(voice=str(voice),
                  effects="summed effects, measured after WAV encoding" if np.any(fx) or events else "none (not applicable)",
                  effect_events=events, effect_track_sha256=hashlib.sha256(Path(out).read_bytes()).hexdigest(),
                  start=start, end=end, sources=audio_sources(vdir, voice))
    if report["violations"]:
        (vdir / "05_render").mkdir(parents=True, exist_ok=True)
        write_audio_check(vdir, vdir / "05_render/failed.mp4", report)
        raise ValueError(f"Audio balance failed: written effects must be at least {SFX_DISTANCE_DB} dB below voice")
    return report


# ---------------------------------------------------------------- mixer


def _brand_sound(vdir: Path, kind: str, name: str) -> Path | None:
    """brands/<brand>/sound/<kind>/<name>.(ogg|wav|mp3|flac) when the video has a brand and the file exists."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        return None
    try:
        brand = video_brand(vdir)
    except Exception:  # bare folders without project.json have no brand
        return None
    for ext in SOUND_EXT:
        path = ROOT / "brands" / brand / "sound" / kind / f"{name}.{ext}"
        if path.is_file():
            return path
    return None


def _music_plan(vdir: Path, music: str, synth) -> tuple[str, Path | None]:
    """(source label, music file or None for a generated song). Raises ValueError for an unknown song."""
    if not music:
        return "none", None
    if music.startswith("file:"):
        name = music[5:]
        if not name or ".." in Path(name).parts or Path(name).is_absolute():
            raise ValueError(f"music file '{name}' must be a relative path inside 04_scene/assets/")
        return "project file", vdir / "04_scene" / "assets" / name
    brand_file = _brand_sound(vdir, "music", music)
    if brand_file:
        return "brand file", brand_file
    if music in synth.SONGS:
        return "generated", None
    raise ValueError(f"unknown music '{music}': built-in songs are {', '.join(synth.SONGS)}; a music file is file:<name>")


def _split_effects(vdir: Path, events, synth) -> tuple[list, list, dict]:
    """Events for the synth, events that use a brand sound file, and the source of every effect name."""
    generated, branded, sources = [], [], {}
    for at, token in events:
        kind, name, gain = synth.parse_sfx(token)
        path = _brand_sound(vdir, "sfx", name) if kind == "builtin" else None
        if path:
            branded.append((at, name, gain, path))
            sources[name] = "brand file"
        else:
            generated.append((at, token))
            sources.setdefault(name if kind == "builtin" else f"file:{name}", "generated" if kind == "builtin" else "project file")
    return generated, branded, sources


def _add_brand_effects(fx, branded, synth) -> None:
    """Add brand sound files to the effect stem like file effects: normalised to FILE_PEAK, times the gain."""
    import numpy as np
    clips: dict = {}
    for at, name, gain, path in branded:
        if path not in clips:
            clip = decode_pcm(path).mean(axis=1)
            peak = float(np.max(np.abs(clip))) if len(clip) else 0.0
            clips[path] = clip * (synth.FILE_PEAK / peak) if peak else clip
        clip = clips[path] * gain
        first = int(max(0.0, at) * synth.SR)
        if name in synth.END_ALIGNED:
            first = max(0, first - len(clip))
        last = min(len(fx), first + len(clip))
        if last > first:
            fx[first:last] += clip[:last - first]


def _effect_level(vdir: Path) -> float:
    """The sfx: level in the header of cues.md (the text before the first '## ' line), else FX_GAIN."""
    path = vdir / "03_cues" / "cues.md"
    if path.is_file():
        head = re.split(r"(?m)^## ", path.read_text(encoding="utf-8"), maxsplit=1)[0]
        found = re.search(r"(?m)^sfx:\s*([\d.]+)", head)
        if found:
            try:
                return float(found.group(1))
            except ValueError:
                pass
    return FX_GAIN


def _voice_layout(voice: Path) -> str:
    """mono for a one-channel voice file, else stereo."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels", "-of", "csv=p=0",
                          str(voice)], capture_output=True, text=True).stdout.strip()
    return "mono" if out == "1" else "stereo"


def mix_soundtrack(vdir: Path, voice: Path, video_args: list[str], out: Path, t0: float, t1: float) -> dict:
    """Lay the voice, a music bed that ducks under the voice and the sound effects under the video; write the MP4."""
    cues = json.loads((vdir / "03_cues/cues.json").read_text(encoding="utf-8"))
    meta = cues["meta"]
    cut = ["-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}"]
    events = sfx_events(cues)
    files = load_sfx_files(vdir, events)  # dies on a bad token, unknown effect or missing file before anything is mixed
    report = {"voice": str(voice), "effects": "none (not applicable)", "start": t0, "end": t1, "required_db": SFX_DISTANCE_DB, "minimum_db": None,
              "violations": 0, "measured_windows": 0, "status": "passed", "sources": audio_sources(vdir, voice)}
    music = meta.get("music") or ""
    part = out.with_name(f"{out.stem}.mixing{out.suffix}")
    with tempfile.TemporaryDirectory() as folder:
        tmp = Path(folder)
        if not music and not events:
            inputs = [*cut, "-i", str(voice)]
            graph = "[1:a]alimiter=limit=0.89:level=0[a]"
        else:
            synth, gain = _chip(), meta.get("music_gain", 0.3)
            try:
                label, music_file = _music_plan(vdir, music, synth)
                generated, branded, effect_sources = _split_effects(vdir, events, synth)
                bed, fx = synth.soundtrack(meta["duration"], music if label == "generated" else None, generated, gain, files=files)
                _add_brand_effects(fx, branded, synth)
            except ValueError as error:
                die(f"{error} (_shared/sound.md)")
            fx = fx * _effect_level(vdir)
            bed_path = tmp / "music.wav"
            if music_file:
                bed_from_file(music_file, meta["duration"], gain, bed_path)
            else:
                synth.write_wav(bed_path, bed)
            report = prepare_effects(vdir, voice, fx, tmp / "fx.wav", t0, t1)
            if isinstance(report, dict):
                report["sound_sources"] = {"music": label, "effects": effect_sources}
            inputs = [*cut, "-i", str(voice), *cut, "-i", str(bed_path), *cut, "-i", str(tmp / "fx.wav")]
            layout = _voice_layout(voice)  # music and effects are mono; the mix keeps the layout of the voice
            graph = (f"[1:a]aresample=44100,aformat=channel_layouts={layout},asplit=2[vm][vk];[vk]aformat=channel_layouts=mono[key];"
                     "[2:a][key]sidechaincompress=threshold=0.05:ratio=4:attack=15:release=500[duck];"  # gentle duck, about 6 dB under speech
                     f"[duck]aformat=channel_layouts={layout}[ducked];[3:a]aformat=channel_layouts={layout}[fx];"
                     "[vm][ducked][fx]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.89:level=0[a]")
        try:
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *video_args, *inputs, "-filter_complex", graph, "-map", "0:v",
                            "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest",
                            str(part)], check=True)
            os.replace(part, out)
        finally:
            part.unlink(missing_ok=True)
    return report


# ---------------------------------------------------------------- render


def _segment_cmd(seg: Path, fps, crf) -> list[str]:
    """ffmpeg reads JPEG frames from stdin and writes one H.264 segment. The frames go through RGB to the bt709 matrix and
    tv range, so the bt709 tags are true. setparams writes the primaries and transfer tags (the output options alone do not)."""
    vf = ("format=rgb24,pad=ceil(iw/2)*2:ceil(ih/2)*2,scale=out_range=tv:out_color_matrix=bt709,format=yuv420p,"
          "setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv")
    return ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(fps), "-i", "-", "-vf", vf,
            "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-colorspace", "bt709",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", str(seg)]


def _average_jpegs(shots: list[bytes], quality: int) -> bytes:
    """The mean of several JPEG shots as one JPEG: floats, rounded."""
    import numpy as np
    from PIL import Image
    total = None
    for data in shots:
        pixels = np.asarray(Image.open(io.BytesIO(data)).convert("RGB"), dtype=np.float32)
        total = pixels if total is None else total + pixels
    out = io.BytesIO()
    Image.fromarray(np.clip(total / len(shots) + 0.5, 0, 255).astype(np.uint8)).save(out, "JPEG", quality=quality)
    return out.getvalue()


def _segment_failure(k: int, log: Path) -> str:
    """The message for a failed segment encoder, with the last line ffmpeg wrote."""
    lines = log.read_text(encoding="utf-8", errors="replace").strip().splitlines() if log.is_file() else []
    return f"ffmpeg failed on segment {k}" + (f": {lines[-1]}" if lines else "")


async def _render_worker(k, lo, hi, p, url, work, a, fps, t0, cuts, total, stop, counter, began):
    """One browser and one ffmpeg: frames lo..hi-1 into seg<k>.mp4. Returns (segment, errors, browser version, scene size)."""
    import check
    browser, page, size, errors = await open_page(p, url)
    proc = None
    try:
        version, seg = browser.version, work / f"seg{k:02d}.mp4"
        log = work / f"seg{k:02d}.log"
        with log.open("wb") as log_file:
            proc = await asyncio.create_subprocess_exec(*_segment_cmd(seg, fps, a.crf), stdin=asyncio.subprocess.PIPE,
                                                        stdout=asyncio.subprocess.DEVNULL, stderr=log_file)
        for f in range(lo, hi):
            if stop.is_set():
                raise RuntimeError("render cancelled after a worker failed")
            t = t0 + f / fps
            if a.blur <= 1:
                data = await seek_shot(page, t, quality=a.quality)
            else:
                shots = [await seek_shot(page, s, quality=95) for s in check.subtimes(t, a.blur, fps, cuts)]
                data = await asyncio.to_thread(_average_jpegs, shots, a.quality)
            if stop.is_set():
                raise RuntimeError("render cancelled after a worker failed")
            try:
                proc.stdin.write(data)
                await proc.stdin.drain()
            except (BrokenPipeError, ConnectionResetError):
                await proc.wait()
                raise RuntimeError(_segment_failure(k, log)) from None
            if errors:
                raise RuntimeError("scene failed while rendering: " + "; ".join(errors[:5]))
            counter[0] += 1
            if k == 0 and counter[0] % (fps * 2) == 0:
                rate = counter[0] / max(time.time() - began, 1e-6)
                print(f"\r  {counter[0]}/{total} frames  {rate:.1f} fps  eta {fmt_t((total - counter[0]) / rate)}", end="", flush=True)
        proc.stdin.close()
        with contextlib.suppress(Exception):
            await proc.stdin.wait_closed()
        if await proc.wait() != 0:
            raise RuntimeError(_segment_failure(k, log))
        return seg, errors, version, size
    finally:
        if proc is not None and proc.returncode is None:
            proc.kill()
            await proc.wait()
        with contextlib.suppress(Exception):
            await browser.close()


async def _render_frames(url, work, a, fps, t0, total, workers, cuts) -> list:
    """Run the workers side by side. A failure stops the others (10 s to finish, then cancel) and is raised."""
    from playwright.async_api import async_playwright
    stop, counter, began = asyncio.Event(), [0], time.time()
    async with async_playwright() as p:
        tasks = [asyncio.ensure_future(_render_worker(k, k * total // workers, (k + 1) * total // workers, p, url, work, a, fps, t0,
                                                      cuts, total, stop, counter, began)) for k in range(workers)]
        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
            if any(t.done() and (t.cancelled() or t.exception()) for t in tasks):
                stop.set()
                pending = [t for t in tasks if not t.done()]
                if pending:
                    await asyncio.wait(pending, timeout=10)
        finally:
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
    failed = [t.exception() for t in tasks if t.done() and not t.cancelled() and t.exception()]
    if failed:
        raise next((e for e in failed if "render cancelled" not in str(e)), failed[0])
    return [t.result() for t in tasks]


def cmd_render(a) -> None:
    """Render the scene frame by frame with Playwright, then mix voice, music and effects under it."""
    started = time.time()
    if not shutil.which("ffmpeg"):
        die("ffmpeg not on PATH")
    vdir = video_dir(a.slug)
    if video_engine(vdir) == "hyperframes":
        return hf_render(a, vdir)
    tone_gate(vdir, screen_text(vdir), a.skip_tone)
    url = scene_url(vdir)
    cues = json.loads((vdir / "03_cues/cues.json").read_text(encoding="utf-8"))
    duration = cues["meta"]["duration"]
    voice = find_voice(vdir)
    partial = a.start not in (None, "") or a.end not in (None, "")
    t0 = parse_t(a.start) if a.start not in (None, "") else 0.0
    t1 = min(parse_t(a.end), duration) if a.end not in (None, "") else duration
    if t1 <= t0:
        die("--end must be after --start")
    if not partial and not a.skip_check:
        check_gate(vdir)
    fps = a.fps
    total = math.ceil((t1 - t0) * fps)
    workers = max(1, min(a.workers, total // (fps * 2) or 1))
    render_dir = vdir / "05_render"
    final = render_dir / f"{Path(a.slug).name}{f'_{int(t0)}-{int(t1)}s' if partial else ''}.mp4"
    work = render_dir / "_segments"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    try:
        print(f"rendering {total} frames @ {fps}fps, {workers} workers, {fmt_t(t0)} -> {fmt_t(t1)}")
        cuts = [c["start"] for c in cues.get("cueList") or [] if "." not in str(c.get("id", ""))]
        results = asyncio.run(_render_frames(url, work, a, fps, t0, total, workers, cuts))
        print()
        listing = work / "list.txt"
        listing.write_text("".join(f"file '{seg.name}'\n" for seg, *_ in results), encoding="utf-8")
        audio_report = mix_soundtrack(vdir, voice, ["-f", "concat", "-safe", "0", "-i", str(listing)], work / "final.mp4", t0, t1)
        os.replace(work / "final.mp4", final)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    size = results[0][3]
    final.with_suffix(".render.json").write_text(json.dumps({
        "browser": "Chromium", "browser_version": results[0][2],
        "browser_connection": "CDP" if os.environ.get("ANIM_CDP_URL") else "Playwright launch",
        "width": size["w"], "height": size["h"], "fps": fps, "workers": workers, "frames": total, "start": t0, "end": t1,
        "elapsed_seconds": round(time.time() - started, 3)}, indent=2) + "\n", encoding="utf-8")
    for text in sorted({e for _, errors, _, _ in results for e in errors})[:10]:
        print(f"  page error: {text}")
    after_render(a, vdir, final, fps, started, audio_report)


def hf_render(a, vdir: Path) -> None:
    """HyperFrames draws the picture; the same mixer lays voice, music and effects under it."""
    started = time.time()
    if a.start not in (None, "") or a.end not in (None, "") or a.blur > 1:
        die("--start, --end and --blur are canvas-only; a hyperframes video renders whole")
    tone_gate(vdir, screen_text(vdir), a.skip_tone)
    if not a.skip_check:
        check_gate(vdir)
    cues = json.loads((vdir / "03_cues/cues.json").read_text(encoding="utf-8"))
    voice = find_voice(vdir)
    check_hf_audio(vdir, voice, cues)
    render_dir = vdir / "05_render"
    render_dir.mkdir(parents=True, exist_ok=True)
    name = Path(a.slug).name
    final, frames = render_dir / f"{name}.mp4", render_dir / f".{name}-frames.mp4"
    print(f"rendering with hyperframes @ {a.fps}fps")
    try:
        run = hf("render", "-o", str(frames), "--fps", str(a.fps), "-q", "high", cwd=vdir / "04_scene")
        if run.returncode != 0 or not frames.exists():
            die("hyperframes render failed")
        audio_report = mix_soundtrack(vdir, voice, ["-i", str(frames)], final, 0.0, cues["meta"]["duration"])
    finally:
        frames.unlink(missing_ok=True)
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json",
                            str(final)], capture_output=True, text=True, check=True)
    shape = json.loads(probe.stdout)["streams"][0]
    length, voice_len = probe_duration(final), probe_duration(find_voice(vdir))
    package = json.loads((ROOT / "tools" / "hyperframes" / "package.json").read_text(encoding="utf-8"))
    final.with_suffix(".render.json").write_text(json.dumps({
        "engine": "hyperframes", "hyperframes_version": package["dependencies"]["hyperframes"], "width": shape["width"],
        "height": shape["height"], "fps": a.fps, "frames": round(length * a.fps), "start": 0.0, "end": round(length, 3),
        "voice_seconds": round(voice_len, 3), "elapsed_seconds": round(time.time() - started, 3)}, indent=2) + "\n", encoding="utf-8")
    if abs(length - voice_len) > HF_LENGTH_TOL:
        print(f"  warning: video {length:.2f}s, voice {voice_len:.2f}s (more than 0.5s apart; `check` counts it)")
    audio_report["end"] = length  # the report covers the real video length
    after_render(a, vdir, final, a.fps, started, audio_report)


# ---------------------------------------------------------------- sounds and listen


def cmd_sounds(a) -> None:
    """Write every built-in song and effect to _shared/sound/ to listen to."""
    import numpy as np
    synth = _chip()
    out = ROOT / "_shared" / "sound"
    out.mkdir(parents=True, exist_ok=True)
    for name in synth.SONGS:
        synth.write_wav(out / f"song-{name}.wav", synth.render_song(name, 30), peak=0.8)
        print(f"  song-{name}.wav")
    reel = []
    for name in synth.SFX:
        clip = synth.render_sfx(name)
        synth.write_wav(out / f"sfx-{name}.wav", clip, peak=0.8)
        top = float(np.max(np.abs(clip)))
        reel += [clip * (0.8 / top) if top else clip, np.zeros(int(0.45 * synth.SR))]
    synth.write_wav(out / "sfx-all.wav", np.concatenate(reel))
    print(f"  sfx-*.wav ({', '.join(synth.SFX)}) + sfx-all.wav\n-> {_relpath(out)}")


def cmd_listen(a) -> None:
    """Run earshot on the rendered MP4 and save the report to 05_render/listen.md. Evidence only, never a gate."""
    vdir = video_dir(a.slug)
    if not EARSHOT_PY.is_file():
        die("earshot is not installed. Run: bash tools/setup_earshot.sh")
    mp4 = vdir / "05_render" / f"{vdir.name}.mp4"
    if not mp4.is_file():
        die(f"no render at {_relpath(mp4)}. Run `anim.py render {a.slug}` first")
    starts, kind = [], "Cue starts"
    cues_file = vdir / "03_cues" / "cues.json"
    if cues_file.is_file():
        cues = json.loads(cues_file.read_text(encoding="utf-8"))
        # with effects, earshot checks that each one lands (cue start + @offset); without, it checks the cue starts
        starts = sorted({round(at, 3) for at, _ in sfx_events(cues)})
        if starts:
            kind = "Effect times"
        else:
            starts = [float(c["start"]) for c in cues.get("cueList") or []]
    timeline = ["timeline", str(mp4)]
    if starts:
        timeline += ["--cues", ",".join(str(round(s, 3)) for s in starts)]
    timeline.append("--fresh")
    if not (ROOT / "tools" / "earshot" / ".cache" / "hf").exists():
        print("first run downloads about 1.4 GB of models and can take several minutes")
    env = {"EARSHOT_THREADS": "3", **os.environ}
    outputs = []
    for command in (timeline, ["measure", str(mp4)]):
        try:
            run = subprocess.run([str(EARSHOT_PY), "-m", "earshot", *command], capture_output=True, text=True, timeout=900, env=env)
        except subprocess.TimeoutExpired:
            die(f"earshot {command[0]} took over 15 minutes")
        if run.returncode != 0:
            die(next((line for line in run.stderr.splitlines() if line.strip()), f"earshot {command[0]} failed"))
        outputs.append(run.stdout.strip())
    shown = ", ".join(f"{s:.2f}" for s in starts) or "none"
    report = vdir / "05_render" / "listen.md"
    report.write_text(f"# Listening report: {mp4.name}\n\nEvidence, not approval (`_shared/sound.md`). "
                      f"{kind} passed to earshot: {shown}.\n\n## Timeline\n\n{outputs[0]}\n\n## Measure\n\n{outputs[1]}\n",
                      encoding="utf-8")
    print(f"-> {_relpath(report)}")


# ---------------------------------------------------------------- capture: grab, login, record


async def _grab_one(opts: dict, a, bp: str, shot: Path) -> None:
    """Open the page in a fresh browser at this breakpoint and save the screenshot to `shot`."""
    import capture
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser, ctx = await capture.open_context(p, opts, None, bp)
        try:
            page = await ctx.new_page()
            await page.goto(a.url, wait_until="networkidle", timeout=60000)
            if a.wait_for:
                await page.wait_for_selector(a.wait_for)
            await page.wait_for_timeout(2500)  # fonts and animations settle
            if a.selector:
                await page.locator(a.selector).first.screenshot(path=str(shot))
                return
            view = page.viewport_size["width"]
            top = 0
            if a.find:
                target = page.get_by_text(a.find).first
                await target.scroll_into_view_if_needed()
                box = await target.bounding_box()
                if not box:
                    raise RuntimeError(f"text '{a.find}' is not visible on the page")
                top = max(0, int(box["y"] + await page.evaluate("window.scrollY") - a.above))
            await page.screenshot(path=str(shot), full_page=True,
                                  clip={"x": 0, "y": top, "width": min(a.width or view, view), "height": a.height})
        finally:
            await browser.close()


def cmd_grab(a) -> None:
    """Screenshot of a web page into 04_scene/assets/<name>.png, after the privacy scan."""
    import capture
    from playwright.async_api import Error as PlaywrightError
    vdir = video_dir(a.slug)
    assets = vdir / "04_scene" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    try:
        bps = capture.breakpoints({}, a.bp)
    except ValueError as error:
        die(str(error))
    opts = {"scheme": "light" if a.light else "dark"}
    if a.auth:
        opts["auth"] = a.auth
    if a.mask:
        opts["mask"] = a.mask
    for bp in bps:
        name = capture.suffix(a.name, bps, bp)
        with tempfile.TemporaryDirectory() as folder:
            shot = Path(folder) / f"{name}.png"
            try:
                asyncio.run(_grab_one(opts, a, bp, shot))
            except (RuntimeError, ValueError, PlaywrightError) as error:
                die(str(error))
            refuse_private([shot])  # a hit stops here and nothing reaches assets/
            target = assets / f"{name}.png"
            shutil.move(str(shot), str(target))
        capture.log_capture(assets, name, "screenshot", a.url, bool(a.auth), bp)
        print(f"-> {_relpath(target)}  (use it in a scene: <div class=\"vf-browser\"><div class=\"top\"><i></i><i></i><i></i></div>"
              f"<img src=\"assets/{name}.png\"></div>)")


async def _login_by_hand(site: str, url: str) -> Path:
    """A visible browser: the user logs in, presses Enter, the session is saved."""
    import capture
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        try:
            ctx = await browser.new_context()
            page = await ctx.new_page()
            await page.goto(url)
            await asyncio.to_thread(input, "Log in in the browser window, then press Enter here... ")
            return capture.save_auth(site, await ctx.storage_state())
        finally:
            await browser.close()


def cmd_login(a) -> None:
    """Log in once by hand and save the browser session for grab and record."""
    import capture
    from playwright.async_api import Error as PlaywrightError
    try:
        capture.auth_path(a.site)
        expect = getattr(a, "expect", None)
        if expect:
            saved = asyncio.run(capture.login_session(a.site, a.url, expect, getattr(a, "timeout", None) or 600))
        else:
            saved = asyncio.run(_login_by_hand(a.site, a.url))
    except (RuntimeError, ValueError, PlaywrightError) as error:
        die(str(error))
    print(f"-> saved login '{a.site}' ({_relpath(saved)}). Use it with: grab ... --auth {a.site}  or  auth: {a.site} in a steps file. "
          "Never commit, share or read it.")


def _load_real_js(index: Path) -> None:
    """Make 04_scene/index.html load assets/real.js: before runtime/modern.js, else before scene.js. No page, no change."""
    if not index.is_file():
        return
    html = index.read_text(encoding="utf-8")
    if "assets/real.js" in html:
        return
    found = (re.search(r"<script\b[^>]*\bsrc=[\"'][^\"']*runtime/modern\.js[\"'][^>]*>", html)
             or re.search(r"<script\b[^>]*\bsrc=[\"'][^\"']*scene\.js[\"'][^>]*>", html))
    if found:
        index.write_text(html[:found.start()] + "<script src=\"assets/real.js\"></script>\n" + html[found.start():], encoding="utf-8")


def _cut_frames(src: Path, folder: Path, start: float, end: float, fps: int, width: int) -> int:
    """Cut src into numbered JPEG frames in folder; return the frame count."""
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("f*.jpg"):
        old.unlink()
    vf = f"fps={fps}" + (f",scale='min({width},iw)':-2" if width else "")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-t", str(end - start), "-i", str(src), "-vf", vf,
                    "-q:v", "3", str(folder / "f%03d.jpg")], check=True)
    return len(list(folder.glob("f*.jpg")))


def _read_real(registry: Path) -> dict:
    data: dict = {}
    if registry.is_file():
        text = registry.read_text(encoding="utf-8")
        with contextlib.suppress(ValueError):
            data = json.loads(text[text.index("window.REAL = ") + len("window.REAL = "):text.rindex(";")])
    return data


def register_clip(vdir: Path, src: Path, name: str, start: float, end: float, fps: int, width: int) -> None:
    """Cut a recording into numbered JPEG frames and note the clip in 04_scene/assets/real.js.
    A source inside the video folder is noted by path; its frames stay out of git and `ensure_clips` cuts them again."""
    assets = vdir / "04_scene" / "assets"
    folder = assets / name
    frames = _cut_frames(src, folder, start, end, fps, width)
    registry = assets / "real.js"
    data = _read_real(registry)
    for key in ("files", "trees", "runs", "clips"):
        data.setdefault(key, {})
    clip = {"n": frames, "fps": fps, "src": Path(src).name, "start": start, "end": end}
    with contextlib.suppress(ValueError):
        clip.update(path=Path(src).resolve().relative_to(vdir.resolve()).as_posix(), width=width)
        ignore = assets / ".gitignore"
        lines = ignore.read_text(encoding="utf-8").splitlines() if ignore.is_file() else []
        if f"/{name}/" not in lines:
            ignore.write_text("\n".join([*lines, f"/{name}/"]) + "\n", encoding="utf-8")
    data["clips"][name] = clip
    data["captured"] = time.strftime("%Y-%m-%d")
    registry.write_text("// generated by anim.py record, do not edit\nwindow.REAL = " + json.dumps(data, indent=1, ensure_ascii=False) + ";\n",
                        encoding="utf-8")
    _load_real_js(vdir / "04_scene" / "index.html")
    print(f"clip  {name}: {frames} frames at {fps} fps -> {_relpath(folder)}")


def ensure_clips(vdir: Path) -> None:
    """Cut again the frames of every clip whose source sits in the video folder, when they are missing (a fresh clone)."""
    assets = vdir / "04_scene" / "assets"
    for name, clip in _read_real(assets / "real.js").get("clips", {}).items():
        src, folder = vdir / clip.get("path", ""), assets / name
        if "path" in clip and src.is_file() and len(list(folder.glob("f*.jpg"))) != clip["n"]:
            frames = _cut_frames(src, folder, clip["start"], clip["end"], clip["fps"], clip.get("width", 0))
            print(f"clip  {name}: {frames} frames cut again from {clip['path']}")


def _record_breakpoint(vdir: Path, opts: dict, steps: list, bps: list, bp: str, a) -> None:
    """Play the steps at one breakpoint while recording, scan, register the clip, move the shots."""
    import capture
    assets = vdir / "04_scene" / "assets"
    name = capture.suffix(a.name, bps, bp)
    width, start, fps = min(capture.size(bp)[0], 1280), getattr(a, "start", 0.3), getattr(a, "fps", 12)
    with tempfile.TemporaryDirectory() as folder:
        tmp = Path(folder)
        state = asyncio.run(capture.run(opts, capture.steps_for(steps, bp), tmp / "shots", tmp, bp, "" if len(bps) == 1 else f"-{bp}"))
        webm = next(iter(sorted(tmp.glob("*.webm"))), None)
        if webm is None:
            raise RuntimeError("the browser made no recording")
        try:  # a Playwright WebM often has no duration header
            with contextlib.redirect_stderr(io.StringIO()):
                end = probe_duration(webm)
        except SystemExit:
            end = start + MAX_RECORD_SECONDS
        if end - start > MAX_RECORD_SECONDS:
            die(f"recording is longer than {MAX_RECORD_SECONDS} s: split the steps into two files")
        src = crop_video(webm, state["crop"], tmp / "crop.mp4") if state.get("crop") else webm
        scan = tmp / "scan"
        scan.mkdir()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-i", str(src), "-vf",
                        f"fps={fps},scale='min({width},iw)':-2", str(scan / "s%04d.png")], check=True)
        refuse_private(sorted(scan.glob("*.png")) + sorted((tmp / "shots").glob("*.png")))  # nothing enters assets/ before this passes
        register_clip(vdir, src, name, start, end, fps, width)
        for png in sorted((tmp / "shots").glob("*.png")):
            shutil.move(str(png), str(assets / png.name))
    capture.log_capture(assets, name, "recording", opts.get("url", "(steps)"), "auth" in opts, bp)


def cmd_record(a) -> None:
    """Run a steps file in a browser once per breakpoint while recording; store frames and shots in 04_scene/assets/."""
    import capture
    from playwright.async_api import Error as PlaywrightError
    vdir = video_dir(a.slug)
    (vdir / "04_scene" / "assets").mkdir(parents=True, exist_ok=True)
    try:
        opts, steps = capture.parse_steps(Path(a.steps).read_text(encoding="utf-8"))
        bps = capture.breakpoints(opts, getattr(a, "bp", None))
        for bp in bps:
            _record_breakpoint(vdir, opts, steps, bps, bp, a)
    except (OSError, RuntimeError, ValueError, PlaywrightError) as error:
        die(str(error))
    except subprocess.CalledProcessError as error:
        die(f"ffmpeg failed: {error}")


# ====================================================================================================
# 50-kept
# ====================================================================================================

def hf(*args: str, cwd: Path, capture: bool = False) -> "subprocess.CompletedProcess":
    """Run the pinned HyperFrames CLI with telemetry off. capture=True returns text stdout/stderr."""
    if not HF_BIN.is_file():
        die("hyperframes is not installed. Run: cd tools/hyperframes && npm ci --ignore-scripts")
    env = {**os.environ, "HYPERFRAMES_NO_TELEMETRY": "1", "DO_NOT_TRACK": "1"}
    return subprocess.run([str(HF_BIN), *args], cwd=str(cwd), env=env,
                          capture_output=capture, text=capture)


def has_audio(path: Path) -> bool:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout
    return bool(out.strip())


def voice_config(vdir: Path) -> dict:
    """Provider settings frozen for this video at creation."""
    from studio.project_paths import settings_snapshot
    return settings_snapshot(ROOT, vdir).get("voice", {})


def tone_gate(vdir: Path, texts: dict[str, str], skip: bool) -> None:
    """Stop on tone problems (_shared/tone.md). texts: label -> text."""
    from tone import lint_text
    brief = vdir / "01_voice" / "brief.md"
    m = re.search(r"^- Language:\s*(\w+)", brief.read_text(encoding="utf-8"), re.M) if brief.exists() else None
    lang = m.group(1).lower() if m else "en"
    bad = [f"  {k}: {p}" for k, t in texts.items()
           for p in lint_text(t, lang, brand=video_brand(vdir), narration=k == "script")]
    if bad and not skip:
        die("tone problems (see _shared/tone.md; --skip-tone to override):\n" + "\n".join(bad))


def screen_text(vdir: Path) -> dict[str, str]:
    """On-screen strings per file for the tone gate. HyperFrames: index.html and every sub-composition it mounts
    (data-composition-src, recursively; check.scene_documents)."""
    from tone import html_text, screen_strings
    out = {}
    if video_engine(vdir) == "hyperframes":  # text sits in the HTML body, not in L.text() calls
        import check
        docs, _ = check.scene_documents(vdir / "04_scene")  # missing or circular compositions: hf_check counts them
        for name, text in docs:
            out[name] = html_text(text)
        out.setdefault("index.html", "")
    for f in ("scene.js", "thumbnail.js"):
        p = vdir / "04_scene" / f
        if p.exists():
            out[f] = "\n".join(screen_strings(p.read_text(encoding="utf-8")))
    return out


def require_script_confirmation(vdir: Path, fingerprint: str | None) -> None:
    from studio.paid_requests import managed_stage_validated
    if managed_stage_validated(ROOT, vdir, "script"):
        return
    from studio.workspace import WorkspaceError, review_state
    try:
        from studio.project_paths import project_id
        state = review_state(ROOT, project_id(ROOT, vdir), "script")
    except WorkspaceError as error:
        die(str(error))
    if state["state"] not in ("approved", "inherited") or fingerprint != state["fingerprint"]:  # inherited: template reel, voice B
        die("Paid voice requires current script approval and --confirm-script <user-confirmed fingerprint>. "
            "Use anim.py review <slug> script for the review link.")


def creative_snapshot(vdir: Path) -> dict | None:
    """Read and rehash the installed snapshot before the normal scene pipeline uses it."""
    path = vdir / "creative/snapshot.json"
    if not path.is_file():
        return None
    try:
        from studio import workspace as ws
        data = json.loads(path.read_text(encoding="utf-8"))
        files = data["files"]
        if data["schema"] != 1 or not isinstance(files, dict) or not isinstance(data["characters"], list):
            raise ValueError
        for relative, digest in files.items():
            if not isinstance(relative, str) or not relative.startswith(f"{vdir.relative_to(ROOT).as_posix()}/creative/") or not isinstance(digest, str) or len(digest) != 64:
                raise ValueError
            target = ws.safe_path(ROOT, relative)
            if not target.is_file(): raise ValueError
            if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise ValueError
        seen_manifests = set()
        for choice in data["characters"]:
            ident, variant = ws._id(choice["character_id"]), ws._id(choice["variant_id"])
            manifest = choice["manifest"]
            if (manifest not in {f"creative/characters/{ident}/{variant}/manifest.json",
                                 f"creative/characters/{ident}-{variant}/manifest.json"} or
                    manifest in seen_manifests or f"{vdir.relative_to(ROOT).as_posix()}/{manifest}" not in files):
                raise ValueError
            seen_manifests.add(manifest)
            pack = json.loads((vdir / manifest).read_text(encoding="utf-8"))
            if set(pack["actions"]) != set(choice["actions"]): raise ValueError
            for view in pack["views"].values():
                for part in view["parts"].values():
                    owned = part["path"]
                    if owned not in files or files[owned] != part["sha256"] or part["url"] != "../" + owned.removeprefix(f"{vdir.relative_to(ROOT).as_posix()}/"):
                        raise ValueError
        return data
    except (KeyError, TypeError, ValueError, OSError, ws.WorkspaceError):
        die("creative snapshot has missing, edited or invalid files; review and apply it again")


async def launch_browser(p):
    import os
    endpoint = os.environ.get("ANIM_CDP_URL")
    if endpoint:
        return await p.chromium.connect_over_cdp(endpoint)
    try:
        return await p.chromium.launch()
    except Exception:
        try:
            return await p.chromium.launch(channel="chrome")
        except Exception:
            return await p.chromium.launch(executable_path="/usr/bin/chromium")


def video_brand(vdir: Path) -> str:
    from studio.project_paths import project_brand
    return project_brand(vdir)


def project_allow(vdir: Path) -> set[str]:
    """Exceptions in project.json "allow" ("text-only", "still"); set only when the user asks for it."""
    try:
        return set(json.loads((vdir / "project.json").read_text(encoding="utf-8")).get("allow") or [])
    except (OSError, ValueError):
        return set()


def quality_check(vdir: Path) -> tuple[dict, list[str]]:
    """Quality-bar counters for brands in check.QUALITY_BRANDS: music bed,
    sound effects, 04_scene/assets/sound.md with licences, a hook cue by 2 s and a new cue every 5 s at most.
    Zero for other brands and when the user allowed a minimal video ("allow": ["minimal"] in project.json)."""
    import check
    zero = dict.fromkeys(check.QUALITY_KEYS, 0)
    if video_brand(vdir) not in check.QUALITY_BRANDS or "minimal" in project_allow(vdir):
        return zero, []
    try:
        cues = json.loads((vdir / "03_cues" / "cues.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return dict.fromkeys(check.QUALITY_KEYS, 1), ["quality bar: no 03_cues/cues.json, run anim.py cues <slug>"]
    sound = vdir / "04_scene" / "assets" / "sound.md"
    return check.quality_counters(cues.get("meta") or {}, cues.get("cueList") or [],
                                  sound.read_text(encoding="utf-8") if sound.is_file() else None)


def sfx_file(vdir: Path, name: str) -> Path | None:
    """A file effect ([sfx: file:<name>]): 04_scene/assets/<name> first, then the shared library/sfx/<name>."""
    for folder in (vdir / "04_scene" / "assets", SFX_LIBRARY):
        path = folder / name
        if path.is_file() and path.resolve().is_relative_to(folder.resolve()):
            return path
    return None


def sfx_events(cues: dict) -> list[tuple[float, str]]:
    """(time, token) for every effect: the cue start plus its `@<seconds>` offset (synth.sfx_offset)."""
    offset = _chip().sfx_offset
    return [(round(c["start"] + offset(s), 3), s) for c in cues.get("cueList") or [] for s in c.get("sfx") or []]


def sfx_file_paths(vdir: Path, events) -> dict[str, Path]:
    """name -> path for every file effect in events that exists (unknown ones are left to check and render)."""
    chip, out = _chip(), {}
    for _, token in events:
        try:
            kind, name, _ = chip.parse_sfx(token)
        except ValueError:
            continue
        if kind == "file" and sfx_file(vdir, name):
            out[name] = sfx_file(vdir, name)
    return out


def sfx_check(vdir: Path) -> tuple[dict, list[str]]:
    """Counters for [sfx: ...] in cues.json, every brand: unknown names or missing files, and file effects without
    a source and licence line in 04_scene/assets/sound.md (check.sfx_counters)."""
    import check
    try:
        cues = json.loads((vdir / "03_cues" / "cues.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return dict.fromkeys(check.SFX_KEYS, 0), []
    sound = vdir / "04_scene" / "assets" / "sound.md"
    return check.sfx_counters(cues.get("cueList") or [], sound.read_text(encoding="utf-8") if sound.is_file() else None,
                              lambda name: sfx_file(vdir, name), _chip().parse_sfx)


def video_engine(vdir: Path) -> str:
    """project.json engine; old videos have none and are canvas."""
    try:
        return json.loads((vdir / "project.json").read_text(encoding="utf-8")).get("engine") or "canvas"
    except (OSError, ValueError):
        return "canvas"


def check_gate(vdir: Path, fps: float = 6) -> dict:
    """run_check, print the block, stop the run if any counter that must be zero is not."""
    import check
    r = hf_check(vdir) if video_engine(vdir) == "hyperframes" else run_check(vdir, fps)
    print(r["block"])
    for d in r["details"][:15]:
        print("  " + d)
    if any(r["counters"][k] for k in r.get("fail_keys", check.FAIL_KEYS)):
        die(f"check failed: fix the non-zero counters ({vdir / '05_render' / 'check.md'}, _shared/review.md)")
    return r


def cmd_check(a) -> None:
    check_gate(video_dir(a.slug), a.fps)
    print("check: all counters read 0")


def check_sfx(voice, effects, speech_intervals, sample_rate, start, end, no_voice: bool = False):
    """Measure the written effect stem in timeline-anchored 20 ms speech windows."""
    minimum = math.inf
    violations = measured = 0
    for lo, hi, levels in _sfx_windows(voice, effects, speech_intervals, sample_rate, no_voice):
        if hi <= start * sample_rate or lo >= end * sample_rate or levels is None:
            continue
        vr, vp, er, ep = levels
        if not ep:
            continue
        measured += 1
        distances = [20 * math.log10(v / e) if v else -math.inf
                     for v, e in ((vr, er), (vp, ep))]
        minimum = min(minimum, *distances)
        violations += int(min(distances) < SFX_DISTANCE_DB)
    return {"required_db": SFX_DISTANCE_DB, "minimum_db": minimum if math.isfinite(minimum) else None,
            "violations": violations, "measured_windows": measured,
            "status": "failed" if violations else "passed"}


def audio_sources(vdir: Path, voice: Path) -> dict:
    paths = [voice, vdir / "02_transcript/words.json", vdir / "03_cues/cues.json",
             vdir / "03_cues/cues.md", vdir / "project.json", vdir / "04_scene/index.html",
             ROOT / "anim.py", ROOT / "_runtime/synth.py"]
    try:  # brand sound files win over the generator: a changed file makes the audio check stale
        paths.extend(sorted(p for p in (ROOT / "brands" / video_brand(vdir) / "sound").rglob("*") if p.is_file()))
    except Exception:  # a bare folder without project.json has no brand
        pass
    paths.extend(sorted(p for p in (vdir / "04_scene").rglob("*") if p.is_file() and p.suffix in {".js", ".mjs", ".html"}))
    try:  # file effects ([sfx: file:<name>]) are mixed in: a changed file makes the audio check stale
        paths.extend(sorted(set(sfx_file_paths(vdir, sfx_events(json.loads((vdir / "03_cues/cues.json").read_text(encoding="utf-8")))).values())))
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        pass
    for name in ("brand/tokens.js", "runtime/vendor/gsap.min.js", "runtime/hf-bridge.js", "cues/cues.js"):
        path = vdir / "04_scene" / name
        if path.is_file():
            paths.append(path)
    return {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None for p in paths}


def write_audio_check(vdir: Path, final: Path, report: dict) -> None:
    report = dict(report, export=str(final.resolve()),
                  export_sha256=hashlib.sha256(final.read_bytes()).hexdigest() if final.is_file() else None)
    distance = report.get("minimum_db")
    text = ("# Audio balance check\n\n"
            f"- Voice: {report['voice']}\n- Effects: {report['effects']}\n"
            f"- Export period: {report['start']}–{report['end']} s\n"
            f"- Required distance: {SFX_DISTANCE_DB} dB (RMS and peak); internal margin: {SFX_DISTANCE_DB + 1} dB\n"
            f"- Smallest distance: {distance if distance is not None else 'n/a (no measurable effects)'} dB\n"
            f"- Violations: {report['violations']}\n- Status: {report['status']}\n"
            f"- Effect events: {report.get('effect_events', [])}\n"
            "- Windows: 20 ms, anchored to full timeline; 50 ms before / 150 ms after words\n"
            "- Listening review: pending (headphones and phone speaker)\n\n"
            "```json\n" + json.dumps(report, indent=2, allow_nan=False) + "\n```\n")
    (vdir / "05_render/check-audio.md").write_text(text, encoding="utf-8")


def declared_no_voice(vdir: Path) -> bool:
    """project.json declares no voice: a template reel ("template": "carousel-reel") with "template_voice": "none"."""
    try:
        meta = json.loads((vdir / "project.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return meta.get("template") == "carousel-reel" and (meta.get("template_voice") or "none") == "none"


def check_hf_audio(vdir: Path, voice: Path, cues: dict) -> None:
    """One declarative, unchanged voice source; music and effects come from mix_soundtrack at render.
    A <video> must be a silent file inside the scene, so every sound goes through the measured mixer."""
    from html.parser import HTMLParser
    sources = []
    videos = []
    unsupported = []
    script_sources = []
    class AudioTags(HTMLParser):
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "audio":
                sources.append(attrs.get("src", ""))
                if any(key in attrs for key in ("loop", "muted", "data-volume", "data-duration", "data-trim-start", "data-trim-end", "data-playback-rate")):
                    unsupported.append(tag)
                if attrs.get("data-start", "0") not in {"0", "0.0"}:
                    unsupported.append(tag)
            elif tag == "script" and attrs.get("src"):
                script_sources.append(attrs["src"])
            elif tag == "video":
                videos.append(attrs.get("src", ""))
                if attrs.get("data-has-audio") == "true":
                    unsupported.append(tag)
            elif tag in {"source", "iframe"}:
                unsupported.append(tag)
    scene = vdir / "04_scene"
    import check
    docs, problems = check.scene_documents(scene)  # sub-compositions carry tags too: every sound goes through the mixer
    if problems:
        raise ValueError("HyperFrames compositions: " + "; ".join(problems))
    text = "\n".join(t for _, t in docs)
    for _, doc in docs:
        AudioTags().feed(doc)
    # lib.js (Lottie, morphs) and animicon.js play no sound; lottie-web plays audio layers only through Howler, never loaded
    trusted = {"brand/tokens.js", "runtime/vendor/gsap.min.js", "runtime/hf-bridge.js", "cues/cues.js", "runtime/lib.js",
               "runtime/animicon.js"}
    for source in script_sources:
        path = scene / source
        if source in trusted:
            continue
        if (not path.is_file() or not path.resolve().is_relative_to(scene.resolve()) or
                path.suffix not in {".js", ".mjs"}):
            unsupported.append(source)
    for source in videos:
        path = scene / source
        if not source or not path.is_file() or not path.resolve().is_relative_to(scene.resolve()) or has_audio(path):
            unsupported.append(source or "video")
    scripts = "\n".join(p.read_text(encoding="utf-8") for p in scene.rglob("*")
                        if p.is_file() and p.suffix in {".js", ".mjs"})
    dynamic = re.search(r"\b(?:Audio|AudioContext|webkitAudioContext)\s*\(|createElement\s*\(\s*['\"](?:audio|video)|\.volume\s*=|\.src\s*=", text + scripts)
    if unsupported or dynamic or len(sources) != 1 or (scene / sources[0]).resolve() != voice.resolve():
        raise ValueError("HyperFrames audio must be one voice <audio> and silent <video> files; music and effects are separate tracks "
                         "that the render mixes (cues.md music: and [sfx:])")


def refuse_private(paths: list[Path]) -> None:
    """The privacy scan every capture runs (_shared/capture.md). Stops with kind, frame and place only; the caller removes the files."""
    import privacy
    hits = privacy.scan_frames(paths)
    if hits:
        die(privacy.message(hits) + "; the capture was removed. Crop to the part the video needs (steps: crop SEL, grab: --selector).")


def crop_video(src: Path, box: dict, out: Path) -> Path:
    """Keep only the crop box of a recording (even sizes for H.264)."""
    w, h, x, y = (box["width"] // 2 * 2, box["height"] // 2 * 2, box["x"], box["y"])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vf", f"crop={w}:{h}:{x}:{y}", "-c:v", "libx264",
                    "-crf", "18", "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


def cmd_review(a) -> None:
    from studio.workspace import GATES, WorkspaceError, accept_under_permission, decide_review, mark_ready, review_state
    gate = a.gate
    if gate is None:
        pending = [name for name in GATES if review_state(ROOT, a.slug, name)["state"] == "awaiting-review"]
        if len(pending) != 1:
            raise WorkspaceError("invalid", "Give a gate; exactly one stage must await review to omit it.")
        gate = pending[0]
    action = a.ready or a.approve or a.changes or a.accept
    if action and not a.expected:
        die("A review action requires --expected <fingerprint>.")
    if a.ready:
        state = mark_ready(ROOT, a.slug, gate, a.expected)
    elif a.accept:
        state = accept_under_permission(ROOT, a.slug, gate, a.expected)
    elif a.approve or a.changes:
        if os.environ.get("VF_PERMISSION_WORKER") == "1":
            raise WorkspaceError("blocked", "A worker cannot make a human review decision.")
        if not a.reviewer:
            die("A human decision requires --reviewer NAME.")
        state = decide_review(ROOT, a.slug, gate, "approved" if a.approve else "changes-requested",
                              a.reviewer, a.note or "", a.expected)
    else:
        state = review_state(ROOT, a.slug, gate)
    print(f"{gate}: {state['state']}")
    print(f"fingerprint: {state['fingerprint']}")
    print(f"http://127.0.0.1:{a.port}/videos/{a.slug}/review/{gate}")


def cmd_permission(a) -> None:
    from studio.permissions import SESSION_CHOICES, SESSION_QUESTION, grant, revoke, session_state
    if a.grant:
        state = grant(ROOT, a.scope, a.grant, a.stages or (), session_id=a.session, reviewer=a.reviewer)
    elif a.revoke:
        state = revoke(ROOT, a.scope, session_id=a.session, reviewer=a.reviewer)
    else:
        state = session_state(ROOT, a.scope, session_id=a.session)
    print(SESSION_QUESTION)
    print("choices: " + ", ".join(SESSION_CHOICES))
    print(json.dumps(state, ensure_ascii=False))


def cmd_catalog_import(a) -> None:
    from studio.permissions import require_permission
    from studio.workspace import import_existing_styles, list_style_families
    # Check every target before import_existing_styles writes the first style.
    for family in list_style_families(ROOT):
        require_permission(ROOT, "style:" + family["default_variant"])
    styles = import_existing_styles(ROOT)
    print(json.dumps({"imported": len(styles), "styles": [style.get("id") for style in styles]}, ensure_ascii=False))


def cmd_studio_request(a) -> None:
    from studio.jobs import claim_request, finish_request
    if a.claim:
        result = claim_request(ROOT, a.id, a.claim)
    elif a.finish:
        result = finish_request(ROOT, a.id, {"state": a.finish, "note": a.note or "", "outputs": a.outputs or []})
    else:
        die("select --claim or --finish")
    print(json.dumps(result, ensure_ascii=False))


def _run_lib(mod: str, a) -> None:
    import importlib
    import libcore
    try:
        importlib.import_module(mod).run(a)
    except (libcore.LicenseError, libcore.KeyMissing, libcore.NetError, ValueError) as e:
        die(str(e))


def cmd_lib(a) -> None:
    if a.kind == "adapt":
        from studio.asset_adaptation import adapt_asset
        try:
            record = adapt_asset(ROOT, a.source, a.source_brand, a.brand, rights=a.rights,
                                 changes=a.changes, source_kind=a.source_kind, replacement=a.replacement,
                                 tokens=json.loads(Path(a.tokens).read_text()) if a.tokens else None,
                                 validation=json.loads(Path(a.validation).read_text()) if a.validation else None)
            print(json.dumps(record, indent=2))
        except ValueError as e:
            die(str(e))
        return
    _run_lib("library", a)


def cmd_stock(a) -> None:
    _run_lib("stock", a)


def cmd_audio(a) -> None:
    _run_lib("audio", a)


def cmd_run(a) -> None:
    from studio.autonomous import run_video
    print(json.dumps(run_video(ROOT, a.slug, resume=a.resume), indent=2, default=str))


def cmd_run_quote(a) -> None:
    from studio.paid_requests import inspect_quote, record_quote
    record_quote(ROOT, a.run_id, a.request_id, a.max_cost, a.evidence, retry=a.retry)
    print(json.dumps(inspect_quote(ROOT, a.run_id, a.request_id), indent=2))


def cmd_run_approve(a) -> None:
    from studio.paid_requests import approve_quote
    print(json.dumps(approve_quote(ROOT, a.run_id, a.request_id, a.expected, a.reviewer), indent=2))


def cmd_run_reconcile(a) -> None:
    from studio.paid_requests import reconcile
    print(json.dumps(reconcile(ROOT, a.run_id, a.request_id, a.actual, a.provider_request_id, evidence=a.evidence), indent=2))


def _dispatch(a) -> None:
    """Keep direct CLI writers in the same lease as Studio and managed runs."""
    read_only = a.cmd in {"studio", "studio-job", "studio-request", "status", "preview", "run", "chapters"}
    read_only = read_only or (a.cmd == "review" and not (a.ready or a.approve or a.changes or a.accept))
    read_only = read_only or (a.cmd == "permission" and not (a.grant or a.revoke))
    read_only = read_only or (a.cmd == "queue")  # the queue leases each render itself
    read_only = read_only or (a.cmd == "lib" and (a.kind in ("find", "fx") or getattr(a, "act", None) == "search"))  # fx: generated files only
    read_only = read_only or (a.cmd == "stock" and a.act == "search")
    read_only = read_only or (a.cmd == "speak" and (a.dry_run or a.check))
    read_only = read_only or (a.cmd == "audio" and a.act == "find")
    if read_only:
        return a.fn(a)
    from studio.production import production_lock
    with production_lock(ROOT, "cli:" + a.cmd):
        from studio.permissions import require_permission
        from studio.project_paths import project_id, resolve_project
        if a.cmd == "new":
            require_permission(ROOT, f"video:{a.brand}/{a.slug}")
        elif a.cmd in {"research", "speak", "transcribe", "cues", "stills", "check", "render", "thumbnail", "use", "listen", "grab", "record"}:
            if a.cmd == "speak" and (a.dry_run or a.check):
                pass
            else:
                slug = getattr(a, "slug", None)
                if not slug:
                    raise ValueError("Give a video ID for this write.")
                video_id = project_id(ROOT, resolve_project(ROOT, slug))
                require_permission(ROOT, "video:" + video_id)
                from studio.workspace import review_state
                previous = {"speak": "script", "transcribe": "voice", "cues": "transcript",
                            "stills": "cues", "check": "cues", "render": "cues",
                            "thumbnail": "cues"}.get(a.cmd)
                if previous and review_state(ROOT, video_id, previous)["state"] not in {"approved", "accepted", "skipped", "not-applicable"}:
                    raise ValueError(f"Complete the current {previous} review before {a.cmd}.")
                if a.cmd == "use":
                    brand_scope = "brand:" + video_id.split("/", 1)[0]
                    if a.ref.startswith("stock:"):
                        import stock
                        item = stock.load_item(a.ref)
                        media, _ = stock._paths(item["provider"], item["kind"], item["id"])
                        if not media.is_file():
                            require_permission(ROOT, brand_scope)
                    elif a.ref.startswith("audio:"):
                        import audio
                        aid = a.ref.removeprefix("audio:")
                        local = {r["id"]: r for r in audio._jsonl(audio._state() / "local.jsonl")}
                        if aid not in local or not (audio.AUDIO / local[aid]["path"]).is_file():
                            require_permission(ROOT, brand_scope)
        elif a.cmd == "lib" and getattr(a, "kind", None) == "adapt":
            require_permission(ROOT, "brand:" + a.brand)
        elif a.cmd == "lib" and getattr(a, "kind", None) not in {"find", "fx"}:
            scope = getattr(a, "permission_scope", None)
            if not scope or scope.split(":", 1)[0] not in {"brand", "style", "character"}:
                raise ValueError("Give --permission-scope brand:ID, style:ID, or character:ID for this shared change.")
            require_permission(ROOT, scope)
        elif a.cmd in {"stock", "audio", "sounds", "login"}:
            scope = getattr(a, "permission_scope", None)
            if not scope or scope.split(":", 1)[0] not in {"brand", "style", "character"}:
                raise ValueError("Give --permission-scope brand:ID, style:ID, or character:ID for this shared change.")
            require_permission(ROOT, scope)
        elif a.cmd == "run-quote":
            from studio.paid_requests import _run_scope
            require_permission(ROOT, _run_scope(ROOT, a.run_id))
        return a.fn(a)


# ====================================================================================================
# 90-main
# ====================================================================================================

HELP = """Voice-first video workspace. Each command does one stage and stops: read the output, edit it, run the next.

  new           start a video folder (needs --brand)
  research      add the optional research folder
  speak         narration from 01_voice/script.md to voice.mp3 (ElevenLabs)
  transcribe    voice file to words.json with a time for every word (Whisper)
  cues          03_cues/cues.md plus words.json to timed cues
  stills        a picture of the scene at every cue
  check         scene sensors: counters that must read 0
  render        scene, voice, music and effects to an MP4
  thumbnail     thumbnail pictures from thumbnail.html
  chapters      YouTube chapter lines from the top-level cues
  preview       open a scene preview
  status        table of all videos by stage
  studio        local web app (dashboard and review pages)
  review        a review gate's state and its studio address
  studio-job    run one validated production job
  studio-request  claim or finish a dashboard agent request
  catalog       register existing style references
  grab          screenshot of a web page into the scene
  login         log in once by hand and save the session
  record        play a steps file in a browser and record it
  lib           search and add icons, graphics, Lottie files; adapt assets
  stock         search and download stock video, photo and audio
  audio         sound library: fetch packs, find and get effects and music
  use           copy a library or stock item into one video
  sounds        write the built-in sound effects and songs as WAV files
  listen        earshot listening report for the render
  run           run a whole video as a managed job
  run-quote     save an evidenced maximum cost for one paid request
  run-reconcile record the verified cost of an uncertain paid request

Needs ffmpeg and ffprobe on the path, the packages in requirements.txt, and Chrome or Playwright Chromium.
Whisper is optional (requirements-transcription.txt). Run `python anim.py <command> -h` for the options."""


def build_parser() -> argparse.ArgumentParser:
    """One parser with a sub-command for every command; each stores its handler in `fn`."""
    parser = argparse.ArgumentParser(prog="anim.py", description=HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True, metavar="command")

    def command(name: str, fn, text: str, parent=None) -> argparse.ArgumentParser:
        extra = {} if parent is None else {"help": text}
        p = (parent or sub).add_parser(name, description=text, **extra)
        p.set_defaults(fn=fn)
        return p

    p = command("new", cmd_new, "Start a video: folders, a scene template and project.json. Optionally import your own voice recording.")
    p.add_argument("slug", help="folder name of the video: lowercase letters, digits, hyphens")
    p.add_argument("voice", nargs="?", help="path of an existing recording to import as the voice")
    p.add_argument("--format", choices=["wide", "tall"], help="wide is 16:9 for YouTube; tall is 9:16 for Shorts (default wide)")
    p.add_argument("--style", help="a catalog style id whose recipe names a scene renderer (default modern)")
    p.add_argument("--engine", choices=["canvas", "hyperframes"], default="canvas",
                   help="canvas (default) or hyperframes (HTML plus GSAP, optional)")
    p.add_argument("--brand", required=True, help="brand folder in brands/")

    p = command("research", cmd_research, "Add the optional research folder to a video.")
    p.add_argument("slug")

    p = command("speak", cmd_speak, "Generate the narration from 01_voice/script.md with ElevenLabs and join the takes into voice.mp3.")
    p.add_argument("slug")
    p.add_argument("--chunk", type=int, help="generate only this chunk number again")
    p.add_argument("--dry-run", action="store_true", help="show the chunks; call nothing")
    p.add_argument("--confirm-script", help="the user-confirmed fingerprint of the approved script; needed for paid generation")
    p.add_argument("--check", action="store_true", help="check the key, model and voice; generate nothing")
    p.add_argument("--stability", choices=["creative", "natural", "robust"], help="override the voice setting of the project")
    p.add_argument("--skip-tone", action="store_true", help="do not stop on tone problems")

    p = command("transcribe", cmd_transcribe, "Run Whisper on the voice file and write 02_transcript/words.json and transcript.md.")
    p.add_argument("slug")
    p.add_argument("--model", default="large-v3",
                   help="Whisper model name (default large-v3; large-v3-turbo is about three times faster but drops or doubles the odd word)")
    p.add_argument("--language", default="en", help="spoken language code (default en)")
    p.add_argument("--prompt", help="names and jargon hint (default: _shared/vocab.txt)")
    p.add_argument("--force", action="store_true", help="overwrite an existing words.json")
    p.add_argument("--no-verify", action="store_true", help="skip the second-model check of flagged words")

    p = command("cues", cmd_cues, "Turn 03_cues/cues.md and words.json into cues.json and cues.js.")
    p.add_argument("slug")
    p.add_argument("--threshold", type=float, default=0.75, help="lowest fuzzy-match score accepted, 0 to 1 (default 0.75)")

    p = command("stills", cmd_stills, "Take a picture of the scene at every cue (05_render/stills).")
    p.add_argument("slug")
    p.add_argument("--skip-tone", action="store_true", help="do not stop on tone problems")
    p.add_argument("--hold", type=float, default=0.9, help="seconds after each cue start to take the picture (default 0.9)")
    p.add_argument("--at", help="comma-separated times to use instead of the cues, for example 3.2,1:04")

    p = command("check", cmd_check, "Scene sensors: counters that must read 0.")
    p.add_argument("slug")
    p.add_argument("--fps", type=float, default=6, help="text samples per second (default 6)")

    p = command("render", cmd_render, "Render the scene with the voice, music and effects to an MP4.")
    p.add_argument("slug")
    p.add_argument("--skip-tone", action="store_true", help="do not stop on tone problems")
    p.add_argument("--fps", type=int, default=30, help="frames per second (default 30)")
    p.add_argument("--start", help="render only from here (seconds or m:ss)")
    p.add_argument("--end", help="render only to here (seconds or m:ss)")
    p.add_argument("--workers", type=int, default=4, help="parallel browser pages (default 4)")
    p.add_argument("--crf", type=int, default=18, help="x264 quality; lower is better (default 18)")
    p.add_argument("--quality", type=int, default=92, help="JPEG quality of the frames (default 92)")
    p.add_argument("--phone", action="store_true",
                   help="also write a copy under 30 MB for phone and web viewers (720p; 540p past about five minutes)")
    p.add_argument("--skip-check", action="store_true", help="do not run check first")
    p.add_argument("--lufs", type=float, default=-14.0, help="loudness target of the master (default -14)")
    p.add_argument("--blur", type=int, default=1,
                   help="motion blur: number of shots per frame, for example 4; N times slower (modern look only)")
    p.add_argument("--no-master", action="store_true", help="skip the loudness master (only lower a peak above -0.5 dB)")

    p = command("thumbnail", cmd_thumbnail, "Make the thumbnail pictures.")
    p.add_argument("slug")

    p = command("chapters", cmd_chapters, "Print the top-level cues as YouTube chapter lines.")
    p.add_argument("slug")

    p = command("preview", cmd_preview, "Open a scene preview (HyperFrames: background server, stop it with --stop).")
    p.add_argument("slug")
    p.add_argument("--port", type=int, default=4567, help="preview port (default 4567)")
    p.add_argument("--stop", action="store_true", help="stop the HyperFrames preview server")

    p = command("status", cmd_status, "Table of all videos, or one, by stage.")
    p.add_argument("slug", nargs="?")

    p = command("studio", cmd_studio, "Start the local studio web app.")
    p.add_argument("--port", type=int, default=8765, help="studio port (default 8765)")

    p = command("review", cmd_review, "Print a gate's review state and the exact studio address.")
    p.add_argument("slug")
    p.add_argument("gate", nargs="?", choices=["research", "brief", "script", "voice-test", "voice", "transcript", "cues", "scene", "render"])
    actions = p.add_mutually_exclusive_group()
    actions.add_argument("--ready", action="store_true", help="mark the gate ready for review")
    actions.add_argument("--approve", action="store_true", help="human approves this revision")
    actions.add_argument("--changes", action="store_true", help="human requests changes")
    actions.add_argument("--accept", action="store_true", help="accept under this session's permission")
    p.add_argument("--expected", help="the current input fingerprint")
    p.add_argument("--reviewer", help="name of the human reviewer")
    p.add_argument("--note", help="short review note")
    p.add_argument("--port", type=int, default=8765, help="studio port (default 8765)")

    p = command("permission", cmd_permission, "Inspect or change this session's permission for one named item.")
    p.add_argument("--scope", required=True, help="video:brand/slug, brand:id, style:id or character:id")
    actions = p.add_mutually_exclusive_group()
    actions.add_argument("--grant", choices=["full", "each-stage", "selected-stages"])
    actions.add_argument("--revoke", action="store_true")
    p.add_argument("--stages", nargs="+", help="stages that need review when --grant selected-stages")
    p.add_argument("--session", help="explicit chat session ID; use VF_SESSION_ID for following commands")
    p.add_argument("--reviewer", default="human", help="name of the person granting or revoking permission")

    p = command("studio-job", cmd_studio_job, "Start a validated production job.")
    p.add_argument("action")
    p.add_argument("slug")
    p.add_argument("--options", help="JSON file of action options")
    p.add_argument("--expected", help="the current input fingerprint")
    p.add_argument("--request-id", default=None, help="id of the request this job answers")

    p = command("studio-request", cmd_studio_request, "Claim or finish a dashboard agent request.")
    p.add_argument("id")
    p.add_argument("--claim", help="claim the request for this agent name")
    p.add_argument("--finish", choices=["succeeded", "failed", "cancelled"], help="finish the request with this state")
    p.add_argument("--note", help="a short note for the dashboard")
    p.add_argument("--output", action="append", dest="outputs", help="an output file; repeat for more")

    p = command("catalog", cmd_catalog_import, "Style catalog tools.")
    catalog = p.add_subparsers(dest="catalog_action", required=True, metavar="action")
    command("import", cmd_catalog_import, "Register existing style references; add missing default variants without overwriting authored files.",
            parent=catalog)

    p = command("grab", cmd_grab, "Screenshot of a web page into 04_scene/assets.")
    p.add_argument("slug")
    p.add_argument("url", help="page address")
    p.add_argument("name", help="file name without extension")
    p.add_argument("--find", help="scroll to this text first")
    p.add_argument("--above", type=int, default=140, help="CSS pixels kept above the found text (default 140)")
    p.add_argument("--height", type=int, default=1600, help="CSS pixels of page to keep (default 1600)")
    p.add_argument("--width", type=int, help="CSS pixels wide from the left; smaller means a tight crop (default: the breakpoint width)")
    p.add_argument("--light", action="store_true", help="light colour scheme (default dark)")
    p.add_argument("--auth", help="a saved login (see login)")
    p.add_argument("--bp", help="breakpoints: mobile, tablet, laptop (default), desktop, all, or WxH; comma list")
    p.add_argument("--mask", help="CSS selectors to blur (emails, names)")
    p.add_argument("--selector", help="capture only this element")
    p.add_argument("--wait-for", dest="wait_for", help="wait for this selector before the picture")

    p = command("login", cmd_login, "Log in once by hand and save the session for grab and record.")
    p.add_argument("site")
    p.add_argument("url")
    p.add_argument("--permission-scope", help="named brand, style, or character grant for shared login data")
    p.add_argument("--expect", help="text or selector that shows when logged in; the session is saved then, no Enter needed")
    p.add_argument("--timeout", type=float, default=600, help="seconds to wait for --expect (default 600)")

    p = command("record", cmd_record, "Play a steps file in a browser and record it.")
    p.add_argument("slug")
    p.add_argument("name", help="clip name without extension")
    p.add_argument("steps", help="steps file")
    p.add_argument("--bp", help="breakpoints as in grab (default: the breakpoints: line of the file, else laptop)")
    p.add_argument("--fps", type=int, default=12, help="frames per second of the clip (default 12)")
    p.add_argument("--start", type=float, default=0.3, help="seconds to skip at the start, the blank first moments (default 0.3)")

    p = command("lib", cmd_lib, "The shared library: icons, graphics, Lottie files, search, adapt.")
    lib = p.add_subparsers(dest="kind", required=True, metavar="kind")
    icon = command("icon", cmd_lib, "Search and add icons.", parent=lib).add_subparsers(dest="act", required=True, metavar="action")
    q = command("search", cmd_lib, "Search icons by name.", parent=icon)
    q.add_argument("query")
    q.add_argument("--set", help="icon set to search")
    q.add_argument("--limit", type=int, default=20, help="most results (default 20)")
    q = command("add", cmd_lib, "Add icons to the library.", parent=icon)
    q.add_argument("refs", nargs="+", help="icon references like lucide/rocket")
    q.add_argument("--permission-scope", help="named brand, style, or character grant for shared assets")
    lottie = command("lottie", cmd_lib, "Add a Lottie animation.", parent=lib).add_subparsers(dest="act", required=True, metavar="action")
    q = command("add", cmd_lib, "Add a Lottie file.", parent=lottie)
    q.add_argument("url", help="direct link to a .json Lottie file")
    q.add_argument("--name")
    q.add_argument("--license", required=True, help="an id from the allow list, for example CC0-1.0 or Lottie-Simple")
    q.add_argument("--license-ok", action="store_true", help="I checked the licence is free for commercial use")
    q.add_argument("--page", help="the animation's own page, where you read the licence")
    q.add_argument("--creator", help="who made it, as the page shows")
    q.add_argument("--title", help="a short title for the catalog")
    q.add_argument("--group", help="a group such as loading, success, arrows (see library/lottie/GALLERY.html)")
    q.add_argument("--tags", help="search words, comma separated")
    q.add_argument("--permission-scope", help="named brand, style, or character grant for shared assets")
    graphic = command("graphic", cmd_lib, "Add a graphic.", parent=lib).add_subparsers(dest="act", required=True, metavar="action")
    q = command("add", cmd_lib, "Add an SVG graphic.", parent=graphic)
    q.add_argument("url", help="direct link to an .svg file")
    q.add_argument("set")
    q.add_argument("name")
    q.add_argument("--license", required=True, help="an SPDX id from the allow list")
    q.add_argument("--permission-scope", help="named brand, style, or character grant for shared assets")
    q = command("find", cmd_lib, "Search the library by words, kind and category (map: library/CATALOG.md).", parent=lib)
    q.add_argument("query", nargs="?", default="", help="words that must all match (empty: everything)")
    q.add_argument("--brand", required=True)
    q.add_argument("--kind", dest="only_kind", help="fx, block, motion, animicon, icon, graphic, lottie, capture or upstream")
    q.add_argument("--category", help="a category from library/categories.json, for example text or transitions")
    q = command("upstream", cmd_lib, "Rebuild the catalog of components we can rewrite (library/upstream/*.json).", parent=lib)
    q.add_argument("--permission-scope", help="named brand, style, or character grant for shared assets")
    q = command("port", cmd_lib, "Start a new fx part from an upstream component (draft; guide: _shared/porting.md).", parent=lib)
    q.add_argument("ref", help="upstream:<source>/<name>, from lib find --kind upstream")
    q.add_argument("--id", help="the fx id (default: the upstream name)")
    q.add_argument("--slug", help="the video it is made for, <brand>/<slug>")
    q.add_argument("--permission-scope", help="named brand, style, or character grant for shared assets")
    fx = command("fx", cmd_lib, "Check or look at one fx part.", parent=lib).add_subparsers(dest="act", required=True, metavar="action")
    q = command("check", cmd_lib, "Rules and a demo run in both engines; prints OK or the problems.", parent=fx)
    q.add_argument("id")
    q.add_argument("--no-browser", action="store_true", help="rules only, no demo run")
    q = command("stills", cmd_lib, "A contact sheet of the demo at 4 times in both engines (library/cache/fx-stills/).", parent=fx)
    q.add_argument("id")
    q.add_argument("--tall", action="store_true", help="the 9:16 format")
    q = command("adapt", cmd_lib, "Make a draft asset for another brand.", parent=lib)
    q.add_argument("source")
    q.add_argument("--source-brand", required=True)
    q.add_argument("--brand", required=True)
    q.add_argument("--rights", required=True)
    q.add_argument("--changes", required=True)
    q.add_argument("--source-kind", default="unknown")
    q.add_argument("--tokens", help="JSON file with target token values")
    q.add_argument("--replacement")
    q.add_argument("--validation", help="JSON file with target-brand evidence")
    q = command("index", cmd_lib, "Rebuild library/INDEX.json.", parent=lib)
    q.add_argument("--permission-scope", help="named brand, style, or character grant for shared assets")
    q = command("gallery", cmd_lib, "PNG contact sheets of every icon and graphic.", parent=lib)
    q.add_argument("--permission-scope", help="named brand, style, or character grant for shared assets")

    p = command("stock", cmd_stock, "Search and download stock video, photo and audio.")
    stock = p.add_subparsers(dest="act", required=True, metavar="action")
    q = command("search", cmd_stock, "Search a stock provider.", parent=stock)
    q.add_argument("provider", choices=["pexels", "pixabay", "unsplash", "openverse", "all"])
    q.add_argument("query")
    q.add_argument("--type", choices=["video", "photo", "audio"], default="video")
    q.add_argument("--orientation", choices=["landscape", "portrait"], help="default: from the format of --slug, else landscape")
    q.add_argument("--slug", help="a video; its format sets the orientation")
    q.add_argument("--limit", type=int, default=12)
    q = command("get", cmd_stock, "Download stock items.", parent=stock)
    q.add_argument("refs", nargs="+", help="references like stock:pexels/video/123")
    q.add_argument("--permission-scope", help="named brand, style, or character grant for shared assets")

    p = command("audio", cmd_audio, "Sound library: download packs, list remote collections, find and get sounds.")
    audio = p.add_subparsers(dest="act", required=True, metavar="action")
    q = command("fetch", cmd_audio, "Download the small packs and sort library/audio/inbox/ into the library.", parent=audio)
    q.add_argument("ids", nargs="*", help="source ids from library/audio/sources.json (default: all)")
    q.add_argument("--force", action="store_true", help="download a source again")
    q.add_argument("--permission-scope", help="named brand, style, or character grant for shared assets")
    q = command("catalog", cmd_audio, "List every file of the remote collections (Sonniss, SSE) without downloading audio.", parent=audio)
    q.add_argument("ids", nargs="*", help="remote source ids (default: all)")
    q.add_argument("--permission-scope", help="named brand, style, or character grant for shared assets")
    q = command("get", cmd_audio, "Download remote sounds to the library.", parent=audio)
    q.add_argument("ids", nargs="*", help="ids from the index, like sonniss-2024:3fa9c1d2")
    q.add_argument("--pack", help="every file of one pack: <source-id>/<pack name>")
    q.add_argument("--permission-scope", help="named brand, style, or character grant for shared assets")
    q = command("index", cmd_audio, "Rebuild library/audio/INDEX.md and index/*.tsv.", parent=audio)
    q.add_argument("--permission-scope", help="named brand, style, or character grant for shared assets")
    q = command("find", cmd_audio, "Search the sound index (every word must match).", parent=audio)
    q.add_argument("query")
    q.add_argument("--kind", choices=["sfx", "music"])
    q.add_argument("--cat", help="one category, e.g. whoosh or lofi-chill (INDEX.md)")
    q.add_argument("--local", action="store_true", help="only files on disk")
    q.add_argument("--max-s", type=float, help="at most this many seconds long")
    q.add_argument("-n", type=int, default=20, help="number of results")

    p = command("use", cmd_use, "Copy a library or stock item into one video and log the licence.")
    p.add_argument("slug")
    p.add_argument("ref", help="icon:lucide/rocket, graphic:set/name, lottie:name, stock:pexels/video/123, motion:videofactory/AIM-05 or audio:<id>")
    p.add_argument("--as", dest="name", help="name in 04_scene/assets (stock, motion clips and sounds)")
    p.add_argument("--start", help="clip or sound range start (seconds or m:ss)")
    p.add_argument("--end", help="clip or sound range end (seconds or m:ss)")

    p = command("sounds", cmd_sounds, "Write the built-in sound effects and songs as WAV files to listen to.")
    p.add_argument("--permission-scope", help="named brand, style, or character grant for shared assets")

    p = command("listen", cmd_listen, "Earshot listening report for the render, written to 05_render/listen.md.")
    p.add_argument("slug")

    p = command("run", cmd_run, "Run a whole video as a managed job.")
    p.add_argument("slug")
    p.add_argument("--resume", help="id of the run to resume")

    p = command("run-quote", cmd_run_quote, "Save an evidenced maximum cost for one managed paid request.")
    p.add_argument("run_id")
    p.add_argument("request_id")
    p.add_argument("--max-cost", required=True, help="the maximum cost, as text")
    p.add_argument("--evidence", required=True)
    p.add_argument("--retry", action="store_true")

    p = command("run-approve", cmd_run_approve, "Human approval of one exact priced request in this session.")
    p.add_argument("run_id")
    p.add_argument("request_id")
    p.add_argument("--expected", required=True, help="quote fingerprint printed by run-quote")
    p.add_argument("--reviewer", required=True, help="name of the human reviewer")

    p = command("run-reconcile", cmd_run_reconcile, "Record the verified cost of an uncertain paid request.")
    p.add_argument("run_id")
    p.add_argument("request_id")
    p.add_argument("--actual", required=True, help="the actual cost, as text")
    p.add_argument("--evidence", required=True)
    p.add_argument("--provider-request-id", default="")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    from studio.production import ProductionBusy
    from studio.workspace import WorkspaceError
    try:
        _dispatch(args)
    except (WorkspaceError, ProductionBusy, ValueError) as error:
        die(str(error))


if __name__ == "__main__":
    main()
