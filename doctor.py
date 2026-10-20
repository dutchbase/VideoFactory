"""doctor.py: check that this machine can run VideoFactory.

    .venv/bin/python doctor.py

Prints one row for each part: OK, MISSING (a required part is absent) or optional (a part you may add later).
Every row that is not OK has a one-line fix. Exit code 1 when a required part is MISSING, else 0.
"""
import importlib.metadata
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OK, MISSING, OPTIONAL = "OK", "MISSING", "optional"
KEYS = [("ElevenLabs key (paid AI voice: speak)", ("ELEVENLABS_API_KEY", "ELEVEN_API_KEY")),
        ("Pexels key (stock search)", ("PEXELS_API_KEY",)),
        ("Pixabay key (stock search)", ("PIXABAY_API_KEY",)),
        ("Unsplash key (stock search)", ("UNSPLASH_ACCESS_KEY",))]


def row(name: str, ok: bool, detail: str, fix: str, required: bool = True) -> dict:
    """One line of the table. A part that is absent is MISSING when required, else optional."""
    return {"name": name, "status": OK if ok else (MISSING if required else OPTIONAL), "detail": detail, "fix": "" if ok else fix}


def python_version() -> dict:
    v = sys.version_info
    return row("Python 3.12 or newer", v >= (3, 12), f"{v.major}.{v.minor}.{v.micro}",
               "Make the virtual environment with Python 3.12: python3.12 -m venv .venv")


def package(module: str, dist: str) -> dict:
    try:
        importlib.import_module(module)
        version = importlib.metadata.version(dist)
    except Exception as error:
        return row(f"Python package {dist}", False, str(error).splitlines()[0] if str(error) else type(error).__name__,
                   ".venv/bin/pip install -r requirements.txt")
    return row(f"Python package {dist}", True, version, "")


def chromium() -> dict:
    """Start a headless Chromium, open an empty page and close it again."""
    name, fix = "Chromium for Playwright", ".venv/bin/python -m playwright install chromium"
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return row(name, False, "Playwright is not installed", fix)
    last = ""
    with sync_playwright() as p:
        for label, options in (("Chromium", {}), ("Chrome", {"channel": "chrome"}), ("system Chromium", {"executable_path": "/usr/bin/chromium"})):
            try:
                browser = p.chromium.launch(**options)
            except Exception as error:
                last = last or (str(error).strip().splitlines() or [type(error).__name__])[0]
                continue
            try:
                browser.new_page().goto("about:blank")
                return row(name, True, f"{label} {browser.version} opens a page", "")
            except Exception as error:
                last = (str(error).strip().splitlines() or [type(error).__name__])[0]
            finally:
                browser.close()
    return row(name, False, last or "no browser could start", fix)


def program(name: str, fix: str) -> dict:
    path = shutil.which(name)
    if not path:
        return row(name, False, "not found on PATH", fix)
    try:
        first = subprocess.run([path, "-version"], capture_output=True, text=True, timeout=20).stdout.splitlines()[0]
    except (OSError, subprocess.SubprocessError, IndexError):
        first = path
    return row(name, True, first.replace(f"{name} version ", "").split(" Copyright")[0], "")


def fonts() -> dict:
    need = [ROOT / "_runtime" / "fonts" / "fonts.css", ROOT / "FONT-SOURCES.json"]
    absent = [p.relative_to(ROOT).as_posix() for p in need if not p.is_file()]
    return row("Fonts (local, with licences)", not absent, "fonts.css and FONT-SOURCES.json found" if not absent else "missing " + ", ".join(absent),
               "Get a full checkout of the repository: git checkout -- _runtime/fonts FONT-SOURCES.json")


def brand() -> dict:
    name = "Brand videofactory passes the brand check"
    try:
        sys.path.insert(0, str(ROOT))
        import check
        counters = check.brand_counters(ROOT, "videofactory")
    except Exception as error:
        return row(name, False, (str(error).strip().splitlines() or [type(error).__name__])[0], "Get a full checkout of the repository.")
    bad = [f"{key} {value}" for key, value in counters.items() if value]
    return row(name, not bad, "all counters read 0" if not bad else ", ".join(bad),
               "Fix brands/videofactory/tokens.js (fonts, colours, gradients) until python anim.py check passes.")


def env_value(names: tuple[str, ...]) -> bool:
    """True when one of the variables is set in the environment or in the project .env. The value is never read out."""
    if any(os.environ.get(n, "").strip() for n in names):
        return True
    env = ROOT / ".env"
    if env.is_file():
        for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() in names and value.strip().strip('"'):
                return True
    return False


def whisper() -> dict:
    return row("Whisper (transcribe: the time of every word)", importlib.util.find_spec("whisper") is not None,
               "installed" if importlib.util.find_spec("whisper") else "not installed",
               ".venv/bin/pip install -r requirements-transcription.txt", required=False)


def key(label: str, names: tuple[str, ...]) -> dict:
    found = env_value(names)
    return row(label, found, "found" if found else "not set", f"Put {names[0]}=... in .env (copy .env.example)", required=False)


def hyperframes() -> dict:
    node = shutil.which("node")
    tool = ROOT / "tools" / "hyperframes" / "node_modules" / ".bin" / "hyperframes"
    return row("HyperFrames (advanced engine: Node.js and its packages)", bool(node) and tool.is_file(),
               "Node.js and tools/hyperframes/node_modules found" if node and tool.is_file()
               else ("Node.js not found" if not node else "tools/hyperframes/node_modules not installed"),
               "Install Node.js, then: cd tools/hyperframes && npm ci --ignore-scripts", required=False)


def earshot() -> dict:
    py = ROOT / "tools" / "earshot" / ".venv" / "bin" / "python"
    return row("Earshot (listen: hear effects, music and renders)", py.is_file(),
               "tools/earshot found" if py.is_file() else "tools/earshot not installed", "bash tools/setup_earshot.sh", required=False)


def tesseract() -> dict:
    return row("Tesseract (privacy scan of captures)", shutil.which("tesseract") is not None,
               "found" if shutil.which("tesseract") else "not found on PATH", "Install the tesseract package of your system", required=False)


def run_checks() -> list[dict]:
    """Required parts first, then the optional ones. Each check is looked up by name when this runs."""
    rows = [python_version(), package("playwright", "playwright"), package("PIL", "Pillow"), package("numpy", "numpy"),
            chromium(), program("ffmpeg", "Install FFmpeg with your system package manager"),
            program("ffprobe", "Install FFmpeg (it includes ffprobe) with your system package manager"), fonts(), brand(), whisper()]
    rows += [key(label, names) for label, names in KEYS]
    return rows + [hyperframes(), earshot(), tesseract()]


def main() -> int:
    rows = run_checks()
    width = max(len(r["name"]) for r in rows)
    print("VideoFactory setup check\n")
    for r in rows:
        print(f"  {r['status']:<9} {r['name']:<{width}}  {r['detail']}")
        if r["fix"]:
            print(f"  {'':<9} {'':<{width}}  fix: {r['fix']}")
    missing = [r for r in rows if r["status"] == MISSING]
    print()
    if missing:
        print(f"{len(missing)} required part{'s' if len(missing) > 1 else ''} missing. Fix the MISSING rows, then run doctor.py again.")
        return 1
    print("All required parts are OK. Rows marked optional only unlock extra commands.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
