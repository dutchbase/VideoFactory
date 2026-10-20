"""Shared helpers for the asset library and stock fetch: names, refs, licences, keys, http, provenance."""
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALLOWED = {"CC0-1.0", "MIT", "ISC", "Apache-2.0", "Pexels", "Pixabay", "Unsplash", "Lottie-Simple",
           "Sonniss-GDC", "Mixkit-Free"}  # the last two: sound library only (library/audio/sources.json)
SIGNUP = {
    "PEXELS_API_KEY": ("Pexels", "https://www.pexels.com/api/"),
    "PIXABAY_API_KEY": ("Pixabay", "https://pixabay.com/api/docs/"),
    "UNSPLASH_ACCESS_KEY": ("Unsplash", "https://unsplash.com/developers"),
}


class LicenseError(Exception): pass
class KeyMissing(Exception): pass
class NetError(Exception): pass


def safe_name(s: str) -> str:
    s = s.strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", s) or ".." in s:
        raise ValueError(f"bad name {s!r}: use letters, digits, . _ - only")
    return s


def frontmatter(text: str) -> dict:
    """`key: <json>` lines between --- fences (the repo's record format, see studio/workspace.py)."""
    m = re.match(r"\A---\n(.*?)\n---", text, re.S)
    if not m:
        raise ValueError("no frontmatter between --- lines")
    return {k: json.loads(v) for k, _, v in (line.partition(": ") for line in m[1].splitlines() if line.strip())}


def parse_ref(ref: str) -> tuple[str, str]:
    kind, sep, rest = ref.partition(":")
    if not sep or not kind or not rest:
        raise ValueError(f"bad ref {ref!r}: expected kind:path, e.g. icon:lucide/rocket")
    return kind, rest


def check_license(spdx: str) -> None:
    if spdx not in ALLOWED:
        raise LicenseError(f"licence {spdx!r} is not allowed. Allowed: {', '.join(sorted(ALLOWED))}")


def env_key(*names: str, env_file: Path | None = None) -> str:
    for n in names:
        if os.environ.get(n):
            return os.environ[n]
    env = env_file or ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            k, _, v = line.partition("=")
            if k.strip() in names and v.strip():
                return v.strip().strip('"')
    who, url = SIGNUP.get(names[0], (names[0], ""))
    raise KeyMissing(f"no {who} key. Put {names[0]}=... in .env" + (f" (free key: {url})." if url else "."))


def _urlopen(url: str, headers: dict) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "videofactory/1.0", **headers})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def http_get(url: str, headers: dict | None = None, fetch=None) -> bytes:
    if os.environ.get("ANIM_OFFLINE") == "1":
        raise NetError("ANIM_OFFLINE=1: network is off")
    try:
        return (fetch or _urlopen)(url, headers or {})
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise NetError("rate limit reached (HTTP 429). Wait and try again.") from None
        if e.code in (401, 403):
            raise NetError(f"the server refused the key (HTTP {e.code}). Check the key in .env.") from None
        raise NetError(f"HTTP {e.code} for {url.split('?')[0]}") from None
    except urllib.error.URLError as e:
        raise NetError(f"network error: {e.reason}") from None
    except (TimeoutError, ConnectionError) as e:  # a read can time out after the connection opened
        raise NetError(f"network error: {type(e).__name__}, the server did not answer in time. Try again.") from None


def record_use(video_dir: Path, ref: str, license: str, source_url: str, file: str) -> None:
    f = Path(video_dir) / "04_scene" / "assets" / "library.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    text = f.read_text(encoding="utf-8") if f.exists() else "# Library items used\n\nref | licence | source | file\n--- | --- | --- | ---\n"
    if any(l.startswith(ref + " |") for l in text.splitlines()):
        return
    f.write_text(text + f"{ref} | {license} | {source_url} | {file}\n", encoding="utf-8")
