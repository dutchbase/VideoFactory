"""Privacy scan for real captures (rule: never private data on screen).

Every grab and record runs it: tesseract OCR on each picture, enlarged 2x, then patterns for e-mail addresses,
phone numbers, IBANs, card numbers, key-like strings and token queries. A hit stops the capture.
Results name the kind, frame and position only, never the text that was found (it must not reach logs or chats).
shortcut: OCR misses small, slanted or stylised text; that is why captures also crop (capture.md), upgrade with a second engine if a miss shows up.
"""
import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<![\w.,])(?:\+|00|0)\(?\d[\d\s().-]{7,18}\d(?![\w,])")
GROUPED = re.compile(r"(?<![\w.,])\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?![\w,])")  # 415-555-2671, (415) 555-2671
IBAN_START = re.compile(r"\b([A-Z]{2})\d{2}")
# shortcut: IBAN lengths for common European countries only; add a country here when a capture needs it
IBAN_LEN = {"NL": 18, "BE": 16, "DE": 22, "FR": 27, "GB": 22, "ES": 24, "IT": 27, "AT": 20, "CH": 21, "LU": 20, "IE": 22,
            "PT": 25, "DK": 18, "SE": 24, "NO": 15, "FI": 18, "PL": 28}
CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
KEY = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|sk_[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|xox[abp]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}"
                 r"|AIza[0-9A-Za-z_-]{30,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})")
QUERY = re.compile(r"[?&](?:token|key|code|session|access_token|api_key|auth)=[^\s&]+", re.I)


def _phone(m: str) -> bool:
    digits = re.sub(r"\D", "", m)
    if m.startswith(("+", "00")):
        return 9 <= len(digits) <= 15
    return len(digits) == 10  # national numbers: a leading 0 plus 9 digits


def _iban(m: str) -> bool:
    s = m.replace(" ", "")
    n = int("".join(str(int(c, 36)) for c in s[4:] + s[:4]))
    return n % 97 == 1


def _ibans(text: str) -> list[tuple[int, int]]:
    """Spans of valid IBANs: the country's own length (spaces allowed), then mod 97; trailing text is not pulled in."""
    out = []
    for m in IBAN_START.finditer(text):
        n = IBAN_LEN.get(m.group(1))
        if not n:
            continue
        chars, end = [], m.start()
        for i in range(m.start(), len(text)):
            if text[i].isalnum():
                chars.append(text[i])
            elif text[i] != " ":
                break
            end = i + 1
            if len(chars) == n:
                break
        if len(chars) == n and _iban("".join(chars)):
            out.append((m.start(), end))
    return out


def _luhn(m: str) -> bool:
    d = [int(c) for c in re.sub(r"\D", "", m)][::-1]
    return 13 <= len(d) <= 19 and sum(x if i % 2 == 0 else (x * 2 - 9 if x * 2 > 9 else x * 2) for i, x in enumerate(d)) % 10 == 0


def scan_text(text: str) -> list[str]:
    """Kinds of private data in a piece of text, in a fixed order, each once."""
    found = []
    ibans = _ibans(text)
    inside = lambda m: any(a <= m.start() < b for a, b in ibans)  # the digits of an IBAN are not a phone number
    if EMAIL.search(text): found.append("email")
    if any(_phone(m.group(0)) and not inside(m) for m in PHONE.finditer(text)) or GROUPED.search(text): found.append("phone")
    if ibans: found.append("iban")
    if any(_luhn(m.group(0)) for m in CARD.finditer(text)): found.append("card")
    if KEY.search(text): found.append("key")
    if QUERY.search(text): found.append("url-query")
    return found


def scan_image(path: Path) -> list[dict]:
    """OCR one picture (grey, enlarged 2x, inverted when dark) and scan it line by line.
    Returns [{"kind": kind, "box": [x, y, w, h]}] in the picture's own pixels; never the text."""
    from PIL import Image, ImageOps, ImageStat
    im = ImageOps.autocontrast(Image.open(path).convert("L"))
    if ImageStat.Stat(im).mean[0] < 128:  # light text on a dark app reads better inverted
        im = ImageOps.invert(im)
    im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "scan.png"
        im.save(src)
        tsv = subprocess.run(["tesseract", str(src), "stdout", "--psm", "11", "-l", "eng", "tsv"],
                             capture_output=True, text=True, check=True, env={**os.environ, "OMP_THREAD_LIMIT": "1"}).stdout  # pool already parallel
    lines = {}
    for row in tsv.splitlines()[1:]:
        f = row.split("\t")
        if len(f) < 12 or not f[11].strip():
            continue
        key = tuple(f[1:5])  # page, block, paragraph, line
        x, y, w, h = (int(v) for v in f[6:10])
        lines.setdefault(key, []).append((x, y, w, h, f[11]))
    hits = []
    for words in lines.values():
        text = " ".join(t for *_, t in words)
        for kind in scan_text(text) + scan_text(text.replace(" ", "")):
            x0, y0 = min(w[0] for w in words), min(w[1] for w in words)
            x1, y1 = max(w[0] + w[2] for w in words), max(w[1] + w[3] for w in words)
            hit = {"kind": kind, "box": [x0 // 2, y0 // 2, (x1 - x0) // 2, (y1 - y0) // 2]}
            if hit not in hits:
                hits.append(hit)
    return hits


def _scan_one(path: str) -> list[dict]:
    return scan_image(Path(path))


def scan_frames(paths: list[Path]) -> list[dict]:
    """Scan every distinct picture (identical files once), in parallel. Hits get "frame": 1-based position in `paths`."""
    first = {}
    for i, p in enumerate(paths, 1):
        first.setdefault(hashlib.sha1(Path(p).read_bytes()).hexdigest(), (i, str(p)))
    jobs = list(first.values())
    if not jobs:
        return []
    from multiprocessing import Pool
    with Pool(min(len(jobs), os.cpu_count() or 2)) as pool:
        results = pool.map(_scan_one, [p for _, p in jobs])
    return [dict(h, frame=i) for (i, _), hs in zip(jobs, results) for h in hs]


def message(hits: list[dict]) -> str:
    """Per kind: the first frame and box, and how many frames show it. Never the text itself."""
    out = []
    for kind in dict.fromkeys(h["kind"] for h in hits):
        hs = [h for h in hits if h["kind"] == kind]
        more = f" (and in {len(hs) - 1} other frames)" if len(hs) > 1 else ""
        out.append(f"privacyscan: {kind} in frame {hs[0].get('frame', 1)} at {hs[0]['box']}{more}")
    return "; ".join(out)
