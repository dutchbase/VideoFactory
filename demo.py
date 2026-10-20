"""demo.py: make a free practice video. No network, no paid calls.

    python demo.py <slug> [--format wide|tall] [--brand videofactory]

It runs `anim.py new`, writes a short script, a silent voice.wav of matching length, words.json, transcript.md and
cues.md, then runs `anim.py cues`. You get a video folder with the first three stages filled, ready for a scene.
"""
import argparse
import json
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SENTENCES = [
    "VideoFactory turns a script into a finished video.",
    "You record your voice, and every word gets a time.",
    "The scene follows the words, so each picture lands on the right beat.",
    "One command renders the video as an MP4.",
]
CUES = """# Cues

## intro "turns a script into a finished video"
Title card. The name VideoFactory and one line below it.

## voice "you record your voice"
A microphone icon. Every word gets a time.

## scene "the scene follows the words"
Three small cards slide in, one on each beat.

## render "one command renders the video"
A single command line, then the finished video.
"""
WORD_SECONDS = 0.4  # 150 words a minute
TAIL_SECONDS = 1.0


def write_silence(path: Path, seconds: float) -> None:
    """A silent mono WAV. Uses the sound module when it exists, else the wave module (same 44100 Hz, 16 bit)."""
    try:
        sys.path.insert(0, str(ROOT / "_runtime"))
        import numpy
        import synth
        synth.write_wav(path, numpy.zeros(int(seconds * synth.SR)))
        return
    except ImportError:
        pass
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"\x00\x00" * int(seconds * 44100))


def anim(*args: str) -> int:
    return subprocess.run([sys.executable, str(ROOT / "anim.py"), *args], cwd=ROOT).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Make a free practice video: script, silent voice, words and cues. No network.")
    parser.add_argument("slug", help="folder name of the video: lowercase letters, digits, hyphens")
    parser.add_argument("--format", choices=["wide", "tall"], default="wide", help="wide is 16:9; tall is 9:16 (default wide)")
    parser.add_argument("--brand", default="videofactory", help="brand folder in brands/ (default videofactory)")
    args = parser.parse_args(argv)
    ident = f"{args.brand}/{args.slug}"
    if anim("new", args.slug, "--brand", args.brand, "--format", args.format):
        return 1
    vdir = ROOT / "videos" / args.brand / args.slug
    (vdir / "01_voice" / "script.md").write_text("# Narration draft\n\n```\n" + "\n".join(SENTENCES) + "\n```\n", encoding="utf-8")
    spoken = " ".join(SENTENCES).split()
    duration = round(len(spoken) * WORD_SECONDS + TAIL_SECONDS, 3)
    write_silence(vdir / "01_voice" / "voice.wav", duration)
    words = [{"text": w, "start": round(i * WORD_SECONDS, 3), "end": round((i + 1) * WORD_SECONDS - 0.05, 3)} for i, w in enumerate(spoken)]
    (vdir / "02_transcript" / "words.json").write_text(
        json.dumps({"voice": "voice.wav", "duration": duration, "model": "demo", "words": words}, indent=1, ensure_ascii=False), encoding="utf-8")
    sys.path.insert(0, str(ROOT))
    import anim as tool
    (vdir / "02_transcript" / "transcript.md").write_text(tool.transcript_md(ident, words, duration), encoding="utf-8")
    (vdir / "03_cues" / "cues.md").write_text(CUES, encoding="utf-8")
    if anim("cues", ident):
        return 1
    print(f"\nPractice video ready: {vdir.relative_to(ROOT)}/ (silent voice, {len(spoken)} words, {duration:.1f} s)")
    print("Next:")
    print("  - Ask the assistant to build the scene: /vf-scene")
    print(f"  - Or look at the page: python anim.py preview {ident}")
    print(f"  - Then: python anim.py stills {ident}, check, render")
    return 0


if __name__ == "__main__":
    sys.exit(main())
