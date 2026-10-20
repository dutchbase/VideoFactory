"""The sound library in library/audio/: effects and music for every video.

Small packs are downloaded and sorted by `anim.py audio fetch`. Large collections (Sonniss, SSE) are listed by
`audio catalog` and fetched one file at a time by `audio get` or `use <slug> audio:<id>`. Agents read
library/audio/INDEX.md and index/*.tsv (written by `audio index`, never by hand).
Sources and licences: library/audio/sources.json. Contract: library/audio/CONTEXT.md."""
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import libcore as C

AUDIO = C.ROOT / "library" / "audio"
UA = "VideoFactory-fetch/1.0 (personal sound library)"
EXT_RANK = {".wav": 0, ".flac": 1, ".aif": 2, ".aiff": 2, ".mp3": 3, ".ogg": 4, ".m4a": 5}  # best first
ARCHIVES = {".zip", ".7z", ".rar"}
KEEP = set(EXT_RANK) | ARCHIVES | {".json"}
FORMAT_DIRS = re.compile(r"^(wav|wave|flac|mp3|ogg|aiff?|m4a)s?( files| version)?$", re.I)
DELAY = {"opengameart.org": 10.0}  # robots.txt Crawl-delay; every other host gets 1 s between requests
_last: dict[str, float] = {}

SFX_COLS = ["id", "where", "category", "dur_s", "size_kb", "format", "name", "pack", "source", "licence", "path"]
MUSIC_COLS = ["id", "where", "category", "dur_s", "loop", "title", "author", "pack", "source", "licence", "path"]

# Universal Category System (UCS) file names start with a CatID: category code + subcategory, e.g. WHSHAir_...
UCS = {"WHSH": "whoosh", "SWSH": "whoosh", "UI": "ui", "BEEP": "ui", "ALRM": "ui", "AMB": "ambience",
       "COMP": "tech", "COM": "tech", "COMM": "tech", "ELEC": "tech", "SCI": "tech", "SCIF": "tech", "FUT": "tech",
       "ROBO": "tech", "LASR": "tech", "MAGC": "designed", "MAGIC": "designed", "TOON": "designed", "DSGN": None,
       "EXPL": "impact", "FGHT": "impact", "DEST": "impact", "FIRWK": "impact",
       "WATR": "nature", "WIND": "nature", "RAIN": "nature", "WTHR": "nature", "FIRE": "nature", "ICE": "nature",
       "SNOW": "nature", "ROCK": "nature", "DIRT": "nature", "MUD": "nature", "LIQ": "nature", "GEOT": "nature",
       "NATDIS": "nature", "FOLY": "foley", "CLOTH": "foley", "FEET": "foley", "DOOR": "foley", "DRWR": "foley",
       "PAPR": "foley", "OBJ": "foley", "FOOD": "foley", "DRINK": "foley", "GLAS": "foley", "WOOD": "foley",
       "METL": "foley", "PLAS": "foley", "RUBR": "foley", "CERM": "foley", "LETHR": "foley", "ROPE": "foley",
       "CHAIN": "foley", "TOY": "foley", "EQUI": "foley", "EQUIP": "foley", "SPRT": "foley", "CLOCK": "foley",
       "MOVE": "foley", "WNDW": "foley", "GAME": "foley", "BELL": "music-element", "MUSC": "music-element",
       "MACH": "mechanical", "MECH": "mechanical", "MOTR": "mechanical", "TOOL": "mechanical", "VEH": "vehicle",
       "AERO": "vehicle", "AIRC": "vehicle", "BOAT": "vehicle", "TRAN": "vehicle", "TRN": "vehicle", "HORN": "vehicle",
       "GUN": "weapon", "WEAP": "weapon", "BLLT": "weapon", "ANML": "creature", "CREA": "creature", "BIRD": "creature",
       "INSC": "creature", "GORE": "creature", "HUM": "human", "VOX": "human", "CROWD": "human", "BRTH": "human",
       "FART": "human", "WHSTL": "human", "AIR": "whoosh"}
UCS_SUB = [("whoosh", ("whsh", "swsh", "woosh", "whoosh", "swish")), ("transition", ("rise", "riser", "swell", "sweep")),
           ("impact", ("impt", "impact", "hit", "crsh", "crash", "boom", "thud"))]
_UCS = re.compile(r"^([A-Z]{2,6})([A-Z][a-z0-9][A-Za-z0-9]*)?$")


def _words(pattern: str) -> re.Pattern:
    return re.compile(rf"\b({pattern})\b")


SFX_WORDS = [  # first match wins: specific things before general styles
    ("vehicle", _words(r"cars?|vehicles?|truck\w*|trains?|bus|buses|motorcycle\w*|tanks?|aircraft|airplane\w*|helicopter\w*|boats?|ships?|onbrd|onboard|exhaust|rpm|gearshift\w*")),
    ("transition", _words(r"risers?|rise|uplifter\w*|downlifter\w*|build ?up\w*|sweeps?|reversed?|transitions?|swells?|suck ?back")),
    ("whoosh", _words(r"whoosh\w*|woosh\w*|swoosh\w*|swosh\w*|swish\w*|swipe\w*|pass ?by\w*|fly ?by\w*|whip\w*|swing\w*")),
    ("impact", _words(r"impact\w*|hits?|punch\w*|thud\w*|slam\w*|boom\w*|braam\w*|bang\w*|crash\w*|smash\w*|knock\w*|stomp\w*|explo\w*|blast\w*|thump\w*")),
    ("weapon", _words(r"guns?|rifle\w*|pistol\w*|gunshot\w*|shotgun\w*|reload\w*|swords?|blades?|arrows?|cannon\w*|grenade\w*|weapon\w*|bullet\w*|shots?|firing|magnum|caliber|\d+(?:[.,]\d+)?mm")),
    ("ui", _words(r"ui|gui|interface|click\w*|button\w*|menu\w*|select\w*|toggle\w*|confirm\w*|notif\w*|alert\w*|beep\w*|blip\w*|tick|ticks|switch\w*|pops?|ding\w*|error\w*|cursor|hover|taps?|coins?|gems?|items?|pickup\w*|power ?up\w*|level ?up")),
    ("tech", _words(r"glitch\w*|digital|computer\w*|data|sci ?fi|laser\w*|robot\w*|electr\w*|static|zap\w*|hologram\w*|scan\w*|servo\w*|synth\w*|retro|8 ?bit|chiptune|bleep\w*")),
    ("designed", _words(r"magic\w*|spell\w*|sparkl\w*|shimmer\w*|twinkl\w*|weird\w*|cartoon\w*|boing\w*|springs?|plop\w*|wobbl\w*|textures?")),
    ("creature", _words(r"creature\w*|monster\w*|zombie\w*|animal\w*|dogs?|cats?|birds?|insect\w*|growl\w*|roar\w*|beast\w*|horses?")),
    ("ambience", _words(r"ambien\w*|atmos\w*|room ?tone\w*|background\w*|drones?|city|street\w*|traffic|forest\w*|office|cafe|restaurant|loops?")),
    ("nature", _words(r"water\w*|rain\w*|wind|thunder\w*|storm\w*|fire|flames?|waves?|ocean\w*|rivers?|streams?|splash\w*|ice|snow|rocks?|stones?|mud|leaves")),
    ("human", _words(r"voice\w*|vocal\w*|scream\w*|laugh\w*|breath\w*|cough\w*|crowd\w*|applause|cheer\w*|grunt\w*|whisper\w*|shout\w*|yell\w*|walla")),
    ("mechanical", _words(r"machine\w*|motor\w*|engine\w*|mechanic\w*|gears?|pneumatic|hydraulic|clockwork|ratchet\w*|drill\w*|tools?")),
    ("music-element", _words(r"jingle\w*|stinger\w*|sting|fanfare\w*|musical|chords?|melod\w*|drums?|piano|guitar\w*|bells?|chime\w*|harp\w*|gong\w*")),
    ("foley", _words(r"footsteps?|steps?|cloth\w*|paper\w*|pages?|doors?|drawers?|glass\w*|wood\w*|metal\w*|keys|zipper\w*|bags?|cups?|bottles?|books?|typewriter\w*|keyboard\w*|chairs?|lock\w*|objects?|plastic\w*|cards?|dice|chips?")),
]
MUSIC_WORDS = [
    ("jingles-stingers", _words(r"jingle\w*|stinger\w*|fanfare\w*")),
    ("dark-tension", _words(r"horror|spooky|dark\w*|tension|suspense\w*|creepy|haunt\w*|scary")),
    ("cinematic", _words(r"epic|trailer|cinematic|orchestra\w*|heroic|battle|adventure")),
    ("inspirational", _words(r"inspir\w*|uplift\w*|hope\w*|motivat\w*|triumph\w*")),
    ("lofi-chill", _words(r"lo ?fi|chill\w*|jazz\w*|boom ?bap")),
    ("piano-classical", _words(r"piano|classical|sonata|nocturne|etude|waltz|symphon\w*|prelude|minuet")),
    ("electronic", _words(r"synth\w*|electro\w*|edm|techno|house|dnb|drum and bass|retro ?wave|synthwave|trance")),
    ("playful-game", _words(r"chiptune\w*|8 ?bit|arcade|game|silly|funny|cartoon")),
    ("ambient-calm", _words(r"ambient|calm|relax\w*|peace\w*|meditat\w*|dream\w*|soft")),
    ("corporate-upbeat", _words(r"corporate|business|upbeat|happy|positive|funk\w*|pop")),
    ("rock-pop", _words(r"rock|punk|metal|j ?pop|karaoke")),
]
JFPX_STYLE = {"Ambient": "ambient-calm", "Electronic": "electronic", "DnB": "electronic", "Synth composition": "electronic",
              "Jazz": "lofi-chill", "Chiptune": "playful-game", "Silly": "playful-game", "Spooky": "dark-tension",
              "Funk": "corporate-upbeat"}
JFPX_MOOD = {"Cinematic": "cinematic", "Suspense": "dark-tension", "Mysterious": "dark-tension", "Upbeat": "corporate-upbeat",
             "Energetic": "corporate-upbeat", "Calm": "ambient-calm", "Dreamy": "ambient-calm", "Adventure": "cinematic"}


# ---------------------------------------------------------------- names and sorting

def slug(s: str, limit: int = 80) -> str:
    """A path part that is safe in [sfx: file:...]: lowercase a-z, 0-9, '.', '_', '-'."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\.{2,}", ".", re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9._-]+", "-", s)))
    return s[:limit].strip("-._") or "x"


def _text(path: str) -> str:
    return re.sub(r"[_\-/.,()\[\]]+", " ", path.lower())


def _ucs(name: str) -> tuple[str | None, str | None]:
    """(category, CatID code) from a UCS file name, or (None, None)."""
    m = _UCS.match(name.split("_", 1)[0]) if "_" in name else None
    if not m or m[1] not in UCS:
        return None, None
    sub = (m[2] or "").lower()
    for cat, starts in UCS_SUB:
        if sub.startswith(starts):
            return cat, m[1]
    return UCS[m[1]], m[1]


def classify_sfx(relpath: str, default: str | None = None) -> str:
    """UCS CatID first, then the pack's own category, then words in the folder and file name."""
    cat, code = _ucs(relpath.rsplit("/", 1)[-1])
    if cat:
        return cat
    if default:
        return default
    hit = _by_words(_text(relpath.rsplit("/", 1)[-1])) or _by_words(_text(relpath))  # the file name before its folders
    return hit or ("designed" if code == "DSGN" else "other")


def _by_words(text: str) -> str | None:
    return next((c for c, rx in SFX_WORDS if rx.search(text)), None)


def pack_of(name: str) -> str:
    """The sound library a file belongs to: its first folder, past a 'Sonniss ... Game Audio Bundle Part n' folder."""
    parts = name.split("/")[:-1]
    while len(parts) > 1 and re.search(r"(?i)sonniss|game audio bundle", parts[0]):
        parts = parts[1:]
    return parts[0] if parts else ""


def classify_music(text: str, default: str | None = None, mixed: bool = False) -> str:
    """A mixed pack sorts by the words in the title; a single-genre pack keeps its own category."""
    if mixed or not default:
        hit = next((c for c, rx in MUSIC_WORDS if rx.search(_text(text))), None)
        if hit:
            return hit
    return default or "other"


def title_of(path: str) -> str:
    """A readable name: the FXName of a UCS name (CatID_FXName_Creator_Source), else the file name."""
    stem = Path(path).stem
    parts = stem.split("_")
    if len(parts) >= 2 and _ucs(Path(path).name)[1]:
        stem = parts[1]
    return re.sub(r"\s+", " ", stem.replace("_", " ")).strip() or Path(path).stem


def audio_id(source: str, orig: str) -> str:
    """Stable id: source + 8 hex of the original path inside the source."""
    return f"{source}:{hashlib.sha1(orig.encode('utf-8')).hexdigest()[:8]}"


# ---------------------------------------------------------------- state files

def sources() -> dict:
    return json.loads((AUDIO / "sources.json").read_text(encoding="utf-8"))


def source(sid: str) -> dict:
    s = next((s for s in sources()["sources"] if s["id"] == sid), None)
    if s is None:
        raise ValueError(f"unknown audio source {sid!r}: see library/audio/sources.json")
    return s


def _state() -> Path:
    d = AUDIO / "_state"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _jsonl(f: Path) -> list[dict]:
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()] if f.exists() else []


def _write_jsonl(f: Path, rows: list[dict]) -> None:
    tmp = f.with_name(f.name + ".tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    tmp.replace(f)


def _append_local(rec: dict) -> None:
    with open(_state() / "local.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _load(name: str, default):
    f = _state() / name
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else default


def _save(name: str, data) -> None:
    f = _state() / name
    tmp = f.with_name(f.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(f)


def _crc(path: Path) -> int:
    crc = 0
    with open(path, "rb") as f:
        while block := f.read(1 << 20):
            crc = zlib.crc32(block, crc)
    return crc


# ---------------------------------------------------------------- network

def _open(url: str, headers: dict | None = None):
    if os.environ.get("ANIM_OFFLINE") == "1":
        raise C.NetError("ANIM_OFFLINE=1: network is off")
    host = urllib.parse.urlsplit(url).hostname or ""
    gap = next((d for h, d in DELAY.items() if host.endswith(h)), 1.0)
    pause = _last.get(host, 0.0) + gap - time.monotonic()
    if pause > 0:
        time.sleep(pause)
    _last[host] = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    try:
        return urllib.request.urlopen(req, timeout=120)
    except urllib.error.HTTPError as e:
        raise C.NetError(f"HTTP {e.code} for {url}") from None
    except urllib.error.URLError as e:
        raise C.NetError(f"network error for {url}: {e.reason}") from None


def http_text(url: str) -> str:
    with _open(url) as r:
        return r.read().decode("utf-8", "replace")


def download(url: str, dest: Path) -> Path:
    """Stream url to dest. A .part file from a broken run resumes with a range request."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    have = part.stat().st_size if part.exists() else 0
    try:
        r = _open(url, {"Range": f"bytes={have}-"} if have else None)
    except C.NetError as e:
        if have and "HTTP 416" in str(e):  # the .part file is already complete
            return part.replace(dest)
        raise
    with r, open(part, "ab" if have and r.status == 206 else "wb") as f:
        shutil.copyfileobj(r, f, 1 << 20)
    return part.replace(dest)


def _ranges(url: str):
    """open_range(start, end) for one URL (end inclusive): a response that streams those bytes."""
    def open_range(start: int, end: int):
        for attempt in range(3):  # a CDN sometimes answers one range request with a plain 200 or an error
            try:
                r = _open(url, {"Range": f"bytes={start}-{end}"})
            except C.NetError:
                if attempt == 2:
                    raise
                time.sleep(5 * (attempt + 1))
                continue
            if r.status == 206:
                return r
            r.close()
            time.sleep(5 * (attempt + 1))
        raise C.NetError(f"{url} refused 3 range requests")
    return open_range


def _size(url: str) -> int:
    with _ranges(url)(0, 0) as r:
        return int(r.headers["Content-Range"].rsplit("/", 1)[1])


# ---------------------------------------------------------------- ZIP by byte ranges

def _read(open_range, start: int, end: int) -> bytes:
    with open_range(start, end) as r:
        return r.read()


def zip_entries(open_range, size: int) -> list[dict]:
    """Files in the central directory of a remote ZIP (also ZIP64), read with a few small range requests."""
    tail = _read(open_range, max(0, size - 65558), size - 1)
    i = tail.rfind(b"PK\x05\x06")
    if i < 0:
        raise ValueError("not a ZIP file (no end record)")
    n, cd_size, cd_off = struct.unpack("<HII", tail[i + 10:i + 20])
    if 0xFFFFFFFF in (cd_size, cd_off) or n == 0xFFFF:
        j = tail.rfind(b"PK\x06\x07", 0, i)
        z64 = struct.unpack("<Q", tail[j + 8:j + 16])[0]
        n, cd_size, cd_off = struct.unpack("<QQQ", _read(open_range, z64, z64 + 55)[32:56])
    cd = _read(open_range, cd_off, cd_off + cd_size - 1)
    out, p = [], 0
    while cd[p:p + 4] == b"PK\x01\x02":
        flags, method = struct.unpack("<HH", cd[p + 8:p + 12])
        crc, csize, size_ = struct.unpack("<III", cd[p + 16:p + 28])
        nl, el, cl = struct.unpack("<HHH", cd[p + 28:p + 34])
        off = struct.unpack("<I", cd[p + 42:p + 46])[0]
        name = cd[p + 46:p + 46 + nl].decode("utf-8" if flags & 0x800 else "cp437")
        extra = cd[p + 46 + nl:p + 46 + nl + el]
        q = 0
        while 0xFFFFFFFF in (size_, csize, off) and q + 4 <= len(extra):
            hid, hl = struct.unpack("<HH", extra[q:q + 4])
            if hid == 1:
                vals = list(struct.unpack(f"<{hl // 8}Q", extra[q + 4:q + 4 + hl // 8 * 8]))
                size_ = vals.pop(0) if size_ == 0xFFFFFFFF else size_
                csize = vals.pop(0) if csize == 0xFFFFFFFF else csize
                off = vals.pop(0) if off == 0xFFFFFFFF else off
                break
            q += 4 + hl
        if not name.endswith("/"):
            out.append({"name": name, "method": method, "flags": flags, "crc": crc, "csize": csize, "size": size_, "offset": off})
        p += 46 + nl + el + cl
    return out


def zip_member(open_range, entry: dict, dest: Path) -> Path:
    """Write one member of a remote ZIP to dest (stored or deflate) and check its CRC32."""
    if entry["flags"] & 1:
        raise ValueError(f"{entry['name']}: encrypted ZIP member")
    if entry["method"] not in (0, 8):
        raise ValueError(f"{entry['name']}: unsupported ZIP compression method {entry['method']}")
    head = _read(open_range, entry["offset"], entry["offset"] + 29)
    if head[:4] != b"PK\x03\x04":
        raise ValueError(f"{entry['name']}: bad local header")
    nl, el = struct.unpack("<HH", head[26:30])
    start = entry["offset"] + 30 + nl + el
    inflate = zlib.decompressobj(-15) if entry["method"] == 8 else None
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp, crc = dest.with_name(dest.name + ".part"), 0
    with open(tmp, "wb") as f:
        if entry["csize"]:
            with open_range(start, start + entry["csize"] - 1) as r:
                while block := r.read(1 << 20):
                    data = inflate.decompress(block) if inflate else block
                    crc = zlib.crc32(data, crc)
                    f.write(data)
        if inflate:
            data = inflate.flush()
            crc = zlib.crc32(data, crc)
            f.write(data)
    if crc != entry["crc"]:
        tmp.unlink()
        raise ValueError(f"{entry['name']}: CRC check failed (download broken); try again")
    return tmp.replace(dest)


# ---------------------------------------------------------------- local packs: download, unpack, sort

def _kenney(s: dict) -> list[str]:
    m = re.search(r"https://kenney\.nl/media/pages/assets/[^\"'\s]+\.zip", http_text(s["page"]))
    if not m:
        raise C.NetError(f"no ZIP link on {s['page']}")
    return [m[0]]


def _oga(s: dict) -> tuple[list[str], str | None]:
    """File links of an OpenGameArt page, after its licence field is checked for CC0."""
    html = http_text(s["page"])
    lic = re.search(r"field-name-field-art-licenses(.*?)field-name-", html, re.S)
    if not lic or ">CC0<" not in lic[1]:
        raise C.LicenseError(f"{s['page']} does not list CC0: not downloaded")
    author = re.search(r"field-name-author-submitter.*?/users/[^\"]+\">([^<]+)<", html, re.S)
    links = re.findall(r"href=\"(https://opengameart\.org/sites/default/files/[^\"]+)\"", html)
    links = [u for u in dict.fromkeys(links)
             if not re.search(r"/(css|js|styles|license_images|audio_preview|pictures)/", u)
             and Path(urllib.parse.unquote(u)).suffix.lower() in KEEP]
    archives = [u for u in links if Path(urllib.parse.unquote(u)).suffix.lower() in ARCHIVES]
    return archives or links, author[1].strip() if author else None


def _extract(archive: Path, dest: Path) -> None:
    """Unpack only audio, archives and JSON. Names with '..' or an absolute path are skipped."""
    dest.mkdir(parents=True, exist_ok=True)
    if archive.suffix.lower() == ".zip":
        with zipfile.ZipFile(archive) as z:
            for info in z.infolist():
                name = info.filename.replace("\\", "/")
                parts = [p for p in name.split("/") if p not in ("", ".")]
                if info.is_dir() or not parts or ".." in parts or name.startswith("/") or ":" in parts[0]:
                    continue
                if Path(name).suffix.lower() not in KEEP:
                    continue
                target = dest.joinpath(*parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as r, open(target, "wb") as w:
                    shutil.copyfileobj(r, w, 1 << 20)
        return
    if not shutil.which("bsdtar"):
        raise ValueError(f"{archive.name}: a .7z or .rar pack needs bsdtar (package libarchive)")
    subprocess.run(["bsdtar", "-xf", str(archive), "-C", str(dest)], check=True)


def _audio_files(stage: Path) -> list[Path]:
    base = stage.resolve()
    return sorted(p for p in stage.rglob("*")
                  if p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(base)
                  and p.suffix.lower() in EXT_RANK and not p.name.startswith("._") and "__MACOSX" not in p.parts
                  and p.stem.lower() != "preview")  # a pack's demo montage, not a sound


def _best_format(files: list[Path], stage: Path) -> list[Path]:
    """One file per track: the same name in wav/, mp3/ or ogg/ folders keeps the best format only."""
    best: dict[tuple, Path] = {}
    for p in files:
        rel = p.relative_to(stage).parts
        key = (tuple(x.lower() for x in rel[:-1] if not FORMAT_DIRS.match(x)), p.stem.lower())
        if key not in best or EXT_RANK[p.suffix.lower()] < EXT_RANK[best[key].suffix.lower()]:
            best[key] = p
    return sorted(best.values())


def _extra_meta(s: dict, stage: Path) -> dict:
    """Per-file metadata that a source ships: jfpx catalog.json, open-game-sfx-index index.json. Key: file name."""
    meta = {}
    if s.get("catalog"):
        data = json.loads(http_text(s["catalog"]))
        tracks = next((v for v in data.values() if isinstance(v, list) and v and isinstance(v[0], dict) and "path" in v[0]), [])
        for t in tracks:
            cat = JFPX_MOOD.get(t.get("mood")) or JFPX_STYLE.get(t.get("style"))
            meta[Path(t["path"]).name.lower()] = {"title": t.get("title"), "author": t.get("author"), "page": t.get("source"),
                                                  "category": cat, "loop": "loop" in (t.get("title") or "").lower() or None}
    for f in stage.rglob("index.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue
        for snd in data.get("sounds") or [] if isinstance(data, dict) else []:
            for k in ("file_wav", "file_flac", "file_ogg", "file_mp3"):
                if snd.get(k):
                    meta[Path(snd[k]).name.lower()] = {"title": snd.get("title"), "tags": snd.get("tags") or []}
    return meta


def _unique(dest: Path) -> Path:
    n, cand = 2, dest
    while cand.exists():
        cand = dest.with_name(f"{dest.stem}-{n}{dest.suffix}")
        n += 1
    return cand


def _ingest(s: dict, files: list[Path], seen: set, author: str | None = None, log=print) -> tuple[int, int]:
    """Unpack, pick formats, drop duplicates, sort and move files to the shelf. Returns (added, duplicates)."""
    stage = AUDIO / "_cache" / s["id"] / "x"
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)
    for f in files:
        if f.suffix.lower() in ARCHIVES:
            _extract(f, stage / f.stem)
        elif f.suffix.lower() in EXT_RANK:
            shutil.copy2(f, _unique(stage / f.name))
    for f in [p for p in stage.rglob("*") if p.is_file() and p.suffix.lower() in ARCHIVES]:  # packs inside packs
        _extract(f, f.with_suffix(""))
        f.unlink()
    found = _audio_files(stage)
    if s.get("only"):
        found = [p for p in found if any(f"/{o}" in "/" + p.relative_to(stage).as_posix() for o in s["only"])]
    meta, packs = _extra_meta(s, stage), s.get("packs") or {}
    added = dups = 0
    for p in _best_format(found, stage):
        rel = p.relative_to(stage).as_posix()
        key = (_crc(p), p.stat().st_size)
        if key in seen:
            dups += 1
            continue
        seen.add(key)
        pack = next((x for x in rel.split("/")[:-1] if x in packs), "")
        info, m = packs.get(pack, {}), meta.get(p.name.lower(), {})
        page = info.get("page") or m.get("page") or s["page"]
        if s.get("url_from_name") and (u := re.match(s["url_from_name"][0], p.name)):
            page = s["url_from_name"][1].format(u[1])
        title = m.get("title") or title_of(p.name)
        if s["kind"] == "sfx":
            cat = classify_sfx(" ".join([rel, *(m.get("tags") or [])]), _default_category(s, pack))
        else:
            cat = m.get("category") or classify_music(title, s.get("category"), s.get("mixed", False))
        folder = AUDIO / s["kind"] / cat / s["id"] / (slug(pack) if pack else "")
        dest = _unique(folder / (slug(p.stem) + p.suffix.lower()))
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), dest)
        _append_local({"id": audio_id(s["id"], rel), "kind": s["kind"], "category": cat, "path": dest.relative_to(AUDIO).as_posix(),
                       "source": s["id"], "pack": pack, "orig": rel, "title": title, "tags": m.get("tags") or [],
                       "author": m.get("author") or info.get("author") or author or s.get("author") or "", "page": page,
                       "licence": s["licence"], "crc": key[0], "size": key[1],
                       "loop": bool(m.get("loop") or re.search(r"\bloop", _text(rel)))})
        added += 1
    shutil.rmtree(AUDIO / "_cache" / s["id"], ignore_errors=True)
    return added, dups


def _file_name(url: str, sid: str) -> str:
    name = Path(urllib.parse.unquote(urllib.parse.urlsplit(url).path)).name
    return name if Path(name).suffix.lower() in KEEP else f"{sid}.zip"  # e.g. a GitHub codeload link ends in /main


def fetch(ids: list[str] | None = None, force: bool = False, log=print) -> None:
    """Download every local source (or the given ids) once, and sort what waits in inbox/<id>/."""
    cfg = sources()
    known = {s["id"] for s in cfg["sources"]}
    if bad := [i for i in ids or [] if i not in known]:
        raise ValueError(f"unknown audio source(s): {', '.join(bad)} (see library/audio/sources.json)")
    done = _load("fetched.json", {})
    seen = {(r["crc"], r["size"]) for r in _jsonl(_state() / "local.jsonl")}
    for s in cfg["sources"]:
        if s.get("remote") or (ids and s["id"] not in ids):
            continue
        C.check_license(s["licence"])
        inbox = AUDIO / "inbox" / s["id"]
        if s["method"] == "inbox":
            files = sorted(p for p in inbox.rglob("*") if p.is_file() and p.suffix.lower() in KEEP) if inbox.exists() else []
            if not files:
                continue
            added, dups = _ingest(s, files, seen, log=log)
            for f in files:
                f.unlink()
            log(f"{s['id']}: {added} files from inbox/{s['id']}/ ({dups} duplicates skipped)")
            continue
        if s["id"] in done and not force:
            continue
        try:
            author = None
            if s["method"] == "kenney":
                urls = _kenney(s)
            elif s["method"] == "oga":
                urls, author = _oga(s)
            else:
                urls = [s["url"]]
            if not urls:
                log(f"{s['id']}: no download on {s['page']}")
                continue
            cache = AUDIO / "_cache" / "downloads" / s["id"]
            files = [download(u, cache / _file_name(u, s["id"])) for u in urls]
            added, dups = _ingest(s, files, seen, author=author, log=log)
            shutil.rmtree(cache, ignore_errors=True)
        except (C.NetError, C.LicenseError, ValueError, zipfile.BadZipFile, subprocess.CalledProcessError) as e:
            log(f"{s['id']}: skipped: {e}")
            continue
        done[s["id"]] = {"urls": urls, "files": added, "duplicates": dups, "date": time.strftime("%Y-%m-%d")}
        _save("fetched.json", done)
        log(f"{s['id']}: {added} files ({dups} duplicates skipped)")
    for d in sorted((AUDIO / "_cache").rglob("*"), key=lambda x: len(x.parts), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()


# ---------------------------------------------------------------- remote collections: list now, fetch per file

def catalog(ids: list[str] | None = None, log=print) -> None:
    """List every audio file of the remote sources in _state/remote-<id>.jsonl. Downloads no audio."""
    for s in sources()["sources"]:
        if not s.get("remote") or (ids and s["id"] not in ids):
            continue
        rows, failed = [], []
        if s["method"] == "sonniss":
            for url in s["parts"]:
                try:
                    entries = zip_entries(_ranges(url), _size(url))
                except (C.NetError, ValueError) as e:
                    failed.append(url)
                    log(f"{s['id']}: skipped {url.rsplit('/', 1)[-1]}: {e}")
                    continue
                for e in entries:
                    if Path(e["name"]).suffix.lower() not in EXT_RANK or "__MACOSX" in e["name"]:
                        continue
                    rows.append({"id": audio_id(s["id"], e["name"]), "source": s["id"], "pack": pack_of(e["name"]),
                                 "orig": e["name"], "title": title_of(e["name"]), "category": classify_sfx(e["name"]),
                                 "size": e["size"], "crc": e["crc"], "dur": None, "url": url,
                                 "zip": {k: e[k] for k in ("name", "method", "flags", "crc", "csize", "offset")}})
                log(f"{s['id']}: {url.rsplit('/', 1)[-1]}: {len(rows)} files so far")
        elif s["method"] == "archive":
            for item, default in s["items"].items():
                meta = json.loads(http_text(f"https://archive.org/metadata/{item}"))
                for f in meta.get("files") or []:
                    if f.get("source") != "original" or Path(f["name"]).suffix.lower() not in EXT_RANK:
                        continue
                    rows.append({"id": audio_id(s["id"], f"{item}/{f['name']}"), "source": s["id"], "pack": item,
                                 "orig": f"{item}/{f['name']}", "title": title_of(f["name"]),
                                 "category": classify_sfx(f["name"], default), "size": int(f.get("size") or 0),
                                 "crc": int(f["crc32"], 16) if f.get("crc32") else 0,
                                 "dur": float(f["length"]) if f.get("length") else None,
                                 "url": f"https://archive.org/download/{item}/{urllib.parse.quote(f['name'])}"})
            log(f"{s['id']}: {len(rows)} files in {len(s['items'])} items")
        _write_jsonl(_state() / f"remote-{s['id']}.jsonl", rows)
        if failed:
            log(f"{s['id']}: {len(failed)} part(s) not listed: run `anim.py audio catalog {s['id']}` again later")


# Packs whose names are mostly vehicle models: words like "pass-by", "reverse" or "blip" there describe a car.
# Only the listed word categories may win; every other file of the pack gets the pack's category.
PACK_CATEGORY = [(re.compile(r"(?i)pole position"), "vehicle", {"weapon", "impact", "ambience", "creature"})]


def _default_category(s: dict, pack: str, relpath: str = "") -> str | None:
    for rx, cat, keep in PACK_CATEGORY:
        if rx.search(pack):
            hit = _by_words(_text(relpath))
            return hit if hit in keep else cat
    if s.get("items"):
        return s["items"].get(pack)
    return (s.get("packs") or {}).get(pack, {}).get("category") or s.get("category")


def _remote_rows() -> dict[str, dict]:
    """Every remote file, sorted with the current rules (so a rule change needs no new catalog)."""
    out = {}
    for s in sources()["sources"]:
        if s.get("remote"):
            for r in _jsonl(_state() / f"remote-{s['id']}.jsonl"):
                if s["method"] == "sonniss":
                    r["pack"] = pack_of(r["orig"])
                r["category"] = classify_sfx(r["orig"], _default_category(s, r["pack"], r["orig"]))
                out[r["id"]] = r
    return out


def _resort(local: list[dict], srcs: dict, log=print) -> None:
    """Move effects whose category changed with the sorting rules or sources.json."""
    moved = 0
    for r in local:
        s = srcs.get(r["source"])
        if r["kind"] != "sfx" or s is None:
            continue
        cat = classify_sfx(" ".join([r["orig"], *r.get("tags", [])]), _default_category(s, r["pack"], r["orig"]))
        if cat == r["category"]:
            continue
        rest = Path(r["path"]).relative_to(Path("sfx") / r["category"])
        dest = _unique(AUDIO / "sfx" / cat / rest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(AUDIO / r["path"]), dest)
        r["category"], r["path"] = cat, dest.relative_to(AUDIO).as_posix()
        moved += 1
    if moved:
        for d in sorted((AUDIO / "sfx").rglob("*"), key=lambda x: len(x.parts), reverse=True):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()
        log(f"{moved} effects moved to another category (sorting rules or sources.json changed)")


def get(ids: list[str] | None = None, pack: str | None = None, log=print) -> list[dict]:
    """Download remote files to the shelf (sfx/<category>/<source>/<pack>/) and record them as local."""
    remote = _remote_rows()
    local = {r["id"]: r for r in _jsonl(_state() / "local.jsonl")}
    want = list(ids or [])
    if pack:
        sid, _, name = pack.partition("/")
        want += [i for i, r in remote.items() if r["source"] == sid and r["pack"] == name]
        if not want:
            raise ValueError(f"no remote pack {pack!r}: run `anim.py audio catalog`, then copy source/pack from the index")
    out = []
    for aid in dict.fromkeys(want):
        if aid in local:
            out.append(local[aid])
            continue
        r = remote.get(aid)
        if r is None:
            raise ValueError(f"no sound {aid!r} in the index: find one with `anim.py audio find <words>`")
        s = source(r["source"])
        folder = AUDIO / "sfx" / r["category"] / s["id"] / (slug(r["pack"]) if r["pack"] else "")
        dest = _unique(folder / (slug(Path(r["orig"]).stem) + Path(r["orig"]).suffix.lower()))
        log(f"get {aid}: {r['title']} ({r['size'] / 1e6:.1f} MB)")
        if s["method"] == "sonniss":
            zip_member(_ranges(r["url"]), r["zip"], dest)
        else:
            download(r["url"], dest)
            if r["crc"] and _crc(dest) != r["crc"]:
                dest.unlink()
                raise ValueError(f"{aid}: CRC check failed (download broken); try again")
        rec = {"id": aid, "kind": "sfx", "category": r["category"], "path": dest.relative_to(AUDIO).as_posix(), "source": s["id"],
               "pack": r["pack"], "orig": r["orig"], "title": r["title"], "tags": [], "author": s.get("author", ""),
               "page": s["page"], "licence": s["licence"], "crc": r["crc"] or _crc(dest), "size": dest.stat().st_size, "loop": False}
        _append_local(rec)
        local[aid] = rec
        out.append(rec)
    return out


# ---------------------------------------------------------------- index for agents

def _probe(path: Path) -> list:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=channels,sample_rate",
                        "-of", "json", str(path)], capture_output=True, text=True)
    try:
        d = json.loads(r.stdout or "{}")
        st = (d.get("streams") or [{}])[0]
        return [round(float(d["format"]["duration"]), 2), int(st.get("channels") or 0), int(st.get("sample_rate") or 0)]
    except (KeyError, ValueError, TypeError):
        return [None, 0, 0]


def _probe_all(local: list[dict]) -> dict:
    cache = _load("probe.json", {})
    todo = []
    for r in local:
        st = (AUDIO / r["path"]).stat()
        if cache.get(r["path"], [None, None])[:2] != [st.st_size, st.st_mtime_ns]:
            todo.append((r["path"], st))
    with ThreadPoolExecutor(8) as pool:
        for (p, st), info in zip(todo, pool.map(lambda t: _probe(AUDIO / t[0]), todo)):
            cache[p] = [st.st_size, st.st_mtime_ns] + info
    cache = {r["path"]: cache[r["path"]] for r in local}
    _save("probe.json", cache)
    return cache


def _cell(v) -> str:
    return "-" if v in (None, "") else re.sub(r"[\t\r\n]+", " ", str(v))


def _examples(rows: list[dict], key: str, n: int = 5) -> str:
    names = list(dict.fromkeys(r[key] for r in rows if r[key]))
    pick = names if len(names) <= n else [names[i * len(names) // n] for i in range(n)]
    return "; ".join(x[:40] for x in pick)


def index(log=print) -> dict:
    """Write INDEX.md (overview) and index/<kind>-<category>.tsv (every file) from the shelf and the remote lists."""
    cfg = sources()
    order = {s["id"]: i for i, s in enumerate(cfg["sources"])}
    srcs = {s["id"]: s for s in cfg["sources"]}
    local = [r for r in _jsonl(_state() / "local.jsonl") if (AUDIO / r["path"]).exists()]
    local = list({r["id"]: r for r in local}.values())
    _resort(local, srcs, log)
    _write_jsonl(_state() / "local.jsonl", local)
    probe = _probe_all(local)
    seen_ids, seen = {r["id"] for r in local}, {(r["crc"], r["size"]) for r in local}
    rows = []
    for r in local:
        dur, ch = probe[r["path"]][2], probe[r["path"]][3]
        rows.append({"id": r["id"], "kind": r["kind"], "where": "local", "category": r["category"], "dur_s": dur,
                     "size_kb": round(r["size"] / 1024), "format": Path(r["path"]).suffix[1:] + (f"/{ch}ch" if ch else ""),
                     "name": r["title"], "title": r["title"], "author": r["author"], "loop": "yes" if r.get("loop") else "-",
                     "pack": r["pack"], "source": r["source"], "licence": r["licence"], "path": f"library/audio/{r['path']}"})
    for r in _remote_rows().values():
        if r["id"] in seen_ids or (r["crc"] and (r["crc"], r["size"]) in seen):
            continue
        seen.add((r["crc"], r["size"]))
        rows.append({"id": r["id"], "kind": "sfx", "where": "remote", "category": r["category"], "dur_s": r.get("dur"),
                     "size_kb": round(r["size"] / 1024), "format": Path(r["orig"]).suffix[1:].lower(), "name": r["title"],
                     "pack": r["pack"], "source": r["source"], "licence": srcs[r["source"]]["licence"], "path": ""})
    rows.sort(key=lambda r: (r["where"] != "local", order.get(r["source"], 999), r["pack"].lower(), r["name"].lower()))
    out = AUDIO / "index"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    groups: dict[tuple, list] = {}
    for r in rows:
        groups.setdefault((r["kind"], r["category"]), []).append(r)
    for (kind, cat), rs in groups.items():
        cols = SFX_COLS if kind == "sfx" else MUSIC_COLS
        (out / f"{kind}-{cat}.tsv").write_text("\t".join(cols) + "\n" + "".join(
            "\t".join(_cell(r.get(c)) for c in cols) + "\n" for r in rs), encoding="utf-8")
    (AUDIO / "INDEX.md").write_text(_index_md(cfg, rows, groups), encoding="utf-8")
    stats = {"sfx_local": sum(r["kind"] == "sfx" and r["where"] == "local" for r in rows),
             "sfx_remote": sum(r["where"] == "remote" for r in rows), "music": sum(r["kind"] == "music" for r in rows)}
    log(f"library/audio/INDEX.md: {stats['sfx_local']} local effects, {stats['sfx_remote']} remote effects, {stats['music']} music tracks")
    return stats


def _cats(cfg: dict, groups: dict, kind: str) -> list[tuple[str, str]]:
    known = cfg["categories"][kind]
    return list(known.items()) + sorted((c, "") for k, c in groups if k == kind and c not in known)


def _index_md(cfg: dict, rows: list[dict], groups: dict) -> str:
    sfx = [r for r in rows if r["kind"] == "sfx"]
    music = [r for r in rows if r["kind"] == "music"]
    mins = sum(r["dur_s"] or 0 for r in music) / 60
    lines = ["# Sound library index", "",
             f"Generated by `anim.py audio index` on {time.strftime('%Y-%m-%d')}. Do not edit. Contract: `library/audio/CONTEXT.md`.", "",
             f"**{len(sfx):,} effects** ({sum(r['where'] == 'local' for r in sfx):,} on disk, {sum(r['where'] == 'remote' for r in sfx):,} remote) "
             f"and **{len(music):,} music tracks** ({mins:,.0f} minutes). Every file is free for commercial videos without credit.", "",
             "## Find and use",
             "- Search: `anim.py audio find \"<words>\" [--kind sfx|music] [--cat <category>] [--local] [--max-s 3]`, "
             "or `rg -i <word> library/audio/index/sfx-<category>.tsv`.",
             "- Columns: `id`, `where` (local = on disk, remote = downloads on first use), `dur_s` (`-` = not known before download), name, pack, source, licence, path.",
             "- Into a video: `anim.py use <slug> audio:<id> --as <name> [--start s --end s]`. It copies (and cuts) the file and writes the licence line in `04_scene/assets/sound.md`.",
             "- Sonniss and SSE files often hold several takes in one file. Listen, then cut one take with `--start/--end`.", "",
             "## Effects", "", "| category | what | on disk | remote | file | examples |", "|---|---|---:|---:|---|---|"]
    for cat, what in _cats(cfg, groups, "sfx"):
        rs = groups.get(("sfx", cat), [])
        if rs:
            lines.append(f"| {cat} | {what} | {sum(r['where'] == 'local' for r in rs):,} | {sum(r['where'] == 'remote' for r in rs):,} "
                         f"| `index/sfx-{cat}.tsv` | {_examples(rs, 'name')} |")
    lines += ["", "## Music", "", "| category | what | tracks | minutes | loops | file | examples |", "|---|---|---:|---:|---:|---|---|"]
    for cat, what in _cats(cfg, groups, "music"):
        rs = groups.get(("music", cat), [])
        if rs:
            lines.append(f"| {cat} | {what} | {len(rs)} | {sum(r['dur_s'] or 0 for r in rs) / 60:.0f} | {sum(r['loop'] == 'yes' for r in rs)} "
                         f"| `index/music-{cat}.tsv` | {_examples(rs, 'title')} |")
    lines += ["", "## Sources", "", "| source | kind | on disk | remote | licence | page |", "|---|---|---:|---:|---|---|"]
    empty = []
    for s in cfg["sources"]:
        rs = [r for r in rows if r["source"] == s["id"]]
        if not rs:
            empty.append(s["id"])
            continue
        lines.append(f"| {s['id']} | {s['kind']} | {sum(r['where'] == 'local' for r in rs):,} | {sum(r['where'] == 'remote' for r in rs):,} "
                     f"| {s['licence']} | {s['page']} |")
    if empty:
        lines += ["", f"Not on disk yet: {', '.join(empty)}. Inbox sources wait for a hand download (`library/audio/CONTEXT.md`)."]
    lines += ["", "Licences: " + "; ".join(f"**{k}**: {v['terms']}" for k, v in cfg["licences"].items()), ""]
    return "\n".join(lines)


def _tsv(f: Path) -> list[dict]:
    head, *body = f.read_text(encoding="utf-8").splitlines()
    cols = head.split("\t")
    return [dict(zip(cols, line.split("\t"))) for line in body]


def find(query: str, kind: str | None = None, category: str | None = None, local: bool = False,
         max_s: float | None = None, limit: int = 20) -> list[dict]:
    """Rows whose name, pack, category or source hold every word of the query. Files on disk come first."""
    words = query.lower().split()
    hits = []
    for f in sorted((AUDIO / "index").glob(f"{kind or '*'}-{category or '*'}.tsv")):
        for r in _tsv(f):
            text = " ".join((r.get("name") or r.get("title", ""), r["pack"], r["category"], r["source"], r["id"])).lower()
            if not all(w in text for w in words) or (local and r["where"] != "local"):
                continue
            if max_s is not None and (r["dur_s"] == "-" or float(r["dur_s"]) > max_s):
                continue
            hits.append(r)
    hits.sort(key=lambda r: r["where"] != "local")
    return hits[:limit]


# ---------------------------------------------------------------- into a video

def _seconds(t: str) -> float:
    m, _, sec = str(t).rpartition(":")
    return (int(m) * 60 if m else 0) + float(sec)


def _record(aid: str) -> dict:
    local = {r["id"]: r for r in _jsonl(_state() / "local.jsonl")}
    if aid in local and (AUDIO / local[aid]["path"]).exists():
        return local[aid]
    return get([aid])[0]


def use(vdir: Path, aid: str, name: str | None = None, start: str | None = None, end: str | None = None) -> list[str]:
    """Copy (or cut) one library sound into 04_scene/assets/, write its licence line in assets/sound.md, log it."""
    vdir = Path(vdir)
    rec = _record(aid)
    lic = sources()["licences"].get(rec["licence"], {})
    C.check_license(rec["licence"])
    src = AUDIO / rec["path"]
    n = C.safe_name(name or slug(Path(rec["orig"]).stem, 40))
    assets = vdir / "04_scene" / "assets"
    ext = ".wav" if (start or end) else src.suffix.lower()
    dest = assets / "sfx" / f"{n}{ext}" if rec["kind"] == "sfx" else assets / f"music-{n}{ext}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if start or end:
        a = _seconds(start or "0")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a:.3f}"]
        fade = "afade=t=in:d=0.005"
        if end:
            b = _seconds(end)
            if b <= a:
                raise ValueError("--end must be after --start")
            cmd += ["-to", f"{b:.3f}"]
            fade += f",afade=t=out:st={max(0.0, b - a - 0.01):.3f}:d=0.01"
        subprocess.run(cmd + ["-i", str(src), "-af", fade, "-c:a", "pcm_s24le", str(dest)], check=True)
    else:
        shutil.copy2(src, dest)
    rel = dest.relative_to(vdir / "04_scene").as_posix()
    cut = f", cut {start or 0}-{end or 'end'} s" if (start or end) else ""
    line = (f"- {dest.name}: {rec['page']} (licence: {rec['licence']}, {lic.get('url', '')}), \"{rec['title']}\""
            f" from {rec['source']}{' / ' + rec['pack'] if rec['pack'] else ''}, original {Path(rec['orig']).name}{cut}\n")
    sound_md = assets / "sound.md"
    text = sound_md.read_text(encoding="utf-8") if sound_md.exists() else "# Sound design\n\n## Rights\n"
    if line not in text:
        sound_md.write_text(text + ("" if text.endswith("\n") else "\n") + line, encoding="utf-8")
    C.record_use(vdir, f"audio:{aid}", rec["licence"], rec["page"], rel)
    tag = f"[sfx: file:{dest.relative_to(assets).as_posix()}]" if rec["kind"] == "sfx" else f"music: file:{dest.name} 0.2"
    return [f"audio:{aid} ({rec['licence']}) -> {dest.relative_to(vdir)}", f"in cues.md: {tag}",
            "sound.md: licence line added; add the cue id and purpose."]


# ---------------------------------------------------------------- CLI

def run(a) -> None:
    """CLI entry for `anim.py audio ...`."""
    if a.act == "fetch":
        fetch(a.ids, force=a.force)
        index()
    elif a.act == "catalog":
        catalog(a.ids)
        index()
    elif a.act == "get":
        for r in get(a.ids, pack=a.pack):
            print(f"{r['id']} -> library/audio/{r['path']}")
        index()
    elif a.act == "index":
        index()
    elif a.act == "find":
        hits = find(a.query, a.kind, a.cat, a.local, a.max_s, a.n)
        if not hits and not (AUDIO / "index").exists():
            print("no index yet: run `anim.py audio fetch` (library/audio/CONTEXT.md)")
        for r in hits:
            print(f"{r['id']:<26} {r['where']:<6} {r['dur_s']:>7}s {r['category']:<15} {(r.get('name') or r.get('title'))[:60]}"
                  + (f"  [{r['pack'][:40]}]" if r["pack"] != "-" else ""))
