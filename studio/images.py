"""Brand image jobs: one responsive design exported to many platform sizes.

A job lives in images/<brand>/<slug>/: 01_brief/brief.md, 02_design/design.html, 03_export/<size-id>.png.
The sizes come from _shared/image-sizes.json (one home for every platform size). The browser part of the
export lives in anim.py (it reuses open_page); this module holds the files, the sizes and the checks."""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
from datetime import date, datetime, timezone
from pathlib import Path

from studio.filehash import file_sha256

SIZES_FILE = "_shared/image-sizes.json"
STAGES = ("01_brief", "02_design", "03_export")
BRIEF_HEADINGS = ("Message", "Text", "Sizes", "Picture plan")
PICTURE_KINDS = ("none", "library", "stock", "own", "ai")
SHAPES = ("rect", "circle")
EDGES = ("top", "right", "bottom", "left")
MAX_SIDE = 4096
LAYOUTS = ("is-avatar", "is-banner", "is-wide", "is-square", "is-portrait", "is-tall")  # an optional "layout" in a size row overrides the ratio rule
_PART = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
_TEMPLATE = Path(__file__).resolve().parents[1] / "_templates" / "image"
_PICTURE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"}


class ImageError(ValueError):
    pass


# ---------------------------------------------------------------- sizes

def ratio_class(w: int, h: int, shape: str = "rect") -> str:
    """The layout class of a content box: is-avatar, is-banner, is-wide, is-square, is-portrait or is-tall.
    Keep in step with _runtime/image-size.js, which computes the same class in the page."""
    if shape == "circle":
        return "is-avatar"
    r = w / h
    return "is-banner" if r >= 2.4 else "is-wide" if r > 1.15 else "is-square" if r >= 0.87 else "is-portrait" if r >= 0.62 else "is-tall"


def content_box(row: dict) -> tuple[int, int]:
    s = row["safe"]
    return row["w"] - s["left"] - s["right"], row["h"] - s["top"] - s["bottom"]


def _ratio(w: int, h: int) -> str:
    from math import gcd
    g = gcd(w, h)
    a, b = w // g, h // g
    return f"{a}:{b}" if max(a, b) <= 32 else f"{w / h:.2f}:1"


def load_sizes(root: Path) -> dict:
    """{'sizes': {id: row}, 'sets': {name: [ids]}}. Each row gains ratio, class and box. Raises on a bad file."""
    path = Path(root) / SIZES_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ImageError(f"cannot read {SIZES_FILE}: {error}") from None
    sizes = {}
    for row in data.get("sizes", []):
        ident = row.get("id")
        if not isinstance(ident, str) or not _PART.fullmatch(ident) or ident in sizes:
            raise ImageError(f"{SIZES_FILE}: bad or repeated id {ident!r}")
        w, h, safe = row.get("w"), row.get("h"), row.get("safe")
        if type(w) is not int or type(h) is not int or not (16 <= w <= MAX_SIDE and 16 <= h <= MAX_SIDE):
            raise ImageError(f"{SIZES_FILE}: {ident} needs whole pixel sizes from 16 to {MAX_SIDE}")
        if row.get("shape") not in SHAPES:
            raise ImageError(f"{SIZES_FILE}: {ident} shape is rect or circle")
        if not isinstance(safe, dict) or set(safe) != set(EDGES) or any(type(safe[e]) is not int or safe[e] < 0 for e in EDGES):
            raise ImageError(f"{SIZES_FILE}: {ident} safe needs top, right, bottom and left in pixels")
        if safe["left"] + safe["right"] >= w or safe["top"] + safe["bottom"] >= h:
            raise ImageError(f"{SIZES_FILE}: {ident} safe area is empty")
        for key in ("platform", "use", "source_url", "checked"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ImageError(f"{SIZES_FILE}: {ident} needs {key}")
        if row.get("layout", "") not in ("", *LAYOUTS):
            raise ImageError(f"{SIZES_FILE}: {ident} layout is one of {', '.join(LAYOUTS)}")
        bw, bh = content_box(row)
        sizes[ident] = {**row, "ratio": _ratio(w, h), "class": row.get("layout") or ratio_class(bw, bh, row["shape"]), "box": [bw, bh]}
    sets = data.get("sets", {})
    if not isinstance(sets, dict):
        raise ImageError(f"{SIZES_FILE}: sets must be an object")
    for name, ids in sets.items():
        if not _PART.fullmatch(name) or name in sizes or not isinstance(ids, list) or any(i not in sizes for i in ids):
            raise ImageError(f"{SIZES_FILE}: set {name!r} is bad or names an unknown size")
    return {"sizes": sizes, "sets": sets}


def resolve_sizes(root: Path, words) -> list[dict]:
    """Size rows for ids and set names, in order, without repeats."""
    catalog = load_sizes(root)
    if isinstance(words, str):
        words = split_words(words)
    out, seen = [], set()
    for word in words:
        ids = catalog["sets"].get(word) or ([word] if word in catalog["sizes"] else None)
        if ids is None:
            raise ImageError(f"unknown size or set '{word}'. List them: python anim.py image sizes")
        for ident in ids:
            if ident not in seen:
                seen.add(ident)
                out.append(catalog["sizes"][ident])
    return out


def split_words(text: str) -> list[str]:
    """Ids from a comma list or a markdown list; ignores bullets, comments and text after ' - ' or '#'."""
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    words = []
    for line in text.splitlines():
        line = re.sub(r"^\s*(?:[-*+]|\d+\.)\s+", "", line).split(" - ", 1)[0].split("#", 1)[0]
        words += [w.strip().strip("`") for w in line.split(",") if w.strip().strip("`")]
    return words


def size_table(root: Path, platform: str | None = None, set_name: str | None = None) -> list[str]:
    catalog = load_sizes(root)
    rows = list(catalog["sizes"].values())
    if set_name:
        if set_name not in catalog["sets"]:
            raise ImageError(f"unknown set '{set_name}'. Sets: {', '.join(catalog['sets'])}")
        rows = [catalog["sizes"][i] for i in catalog["sets"][set_name]]
    if platform:
        rows = [r for r in rows if r["platform"].lower() == platform.lower()]
    lines = [f"{'id':28}{'size':>11}  {'ratio':9}{'layout':12}use"]
    for r in rows:
        shape = " (round crop)" if r["shape"] == "circle" else ""
        lines.append(f"{r['id']:28}{str(r['w']) + 'x' + str(r['h']):>11}  {r['ratio']:9}{r['class']:12}{r['use']}{shape}")
    lines.append("")
    lines.append("sets: " + ", ".join(f"{k} ({len(v)})" for k, v in catalog["sets"].items()))
    return lines


def size_query(row: dict, guides: bool = False) -> str:
    """The query string design.html reads (see _runtime/image-size.js)."""
    s = row["safe"]
    q = f"size={row['w']}x{row['h']}&safe={s['top']},{s['right']},{s['bottom']},{s['left']}&shape={row['shape']}&id={row['id']}&layout={row['class']}"
    return q + ("&guides" if guides else "")


# ---------------------------------------------------------------- jobs

def job_id(brand: str, slug: str) -> str:
    for part in (brand, slug):
        if not isinstance(part, str) or not _PART.fullmatch(part):
            raise ImageError("use lowercase letters, digits and hyphens for brand and slug")
    return f"{brand}/{slug}"


def job_dir(root: Path, ident: str) -> Path:
    """images/<brand>/<slug> for 'brand/slug'. Refuses symbolic links and a brand that differs from project.json."""
    parts = ident.split("/") if isinstance(ident, str) else []
    if len(parts) != 2:
        raise ImageError("use the image ID brand/slug")
    job_id(*parts)
    root = Path(root).resolve()
    path = root / "images" / parts[0] / parts[1]
    for p in (root / "images", path.parent, path):
        if p.is_symlink():
            raise ImageError("image folders cannot be symbolic links")
    if not (path / "project.json").is_file():
        raise ImageError(f"no image job {ident}. Start one: python anim.py image new {parts[1]} --brand {parts[0]}")
    try:
        project = json.loads((path / "project.json").read_text(encoding="utf-8"))
    except ValueError:
        raise ImageError(f"{ident}: project.json is not valid JSON") from None
    if project.get("brand") != parts[0] or project.get("kind") != "image":
        raise ImageError(f"{ident}: project.json brand or kind differs from the folder")
    return path


def iter_jobs(root: Path):
    base = Path(root) / "images"
    if not base.is_dir():
        return
    for brand in sorted(base.iterdir()):
        if brand.is_dir() and not brand.is_symlink() and _PART.fullmatch(brand.name):
            for job in sorted(brand.iterdir()):
                if job.is_dir() and not job.is_symlink() and (job / "project.json").is_file():
                    yield f"{brand.name}/{job.name}", job


def create(root: Path, brand: str, slug: str, sizes: str | None = None, title: str | None = None) -> Path:
    """Copy _templates/image to images/<brand>/<slug>, fill the placeholders and link brand and runtime."""
    root = Path(root).resolve()
    job_id(brand, slug)
    if not (root / "brands" / brand / "tokens.js").is_file():
        known = sorted(p.parent.name for p in (root / "brands").glob("*/tokens.js"))
        raise ImageError(f"unknown brand '{brand}'. Known brands: {', '.join(known) or 'none'}")
    rows = resolve_sizes(root, sizes) if sizes else []
    dest = root / "images" / brand / slug
    if dest.exists():
        raise ImageError(f"{dest.relative_to(root)} already exists")
    title = (title or slug.replace("-", " ").title()).strip()
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(_TEMPLATE, dest)
    size_lines = "\n".join(f"- {r['id']}" for r in rows) or "<!-- size ids or set names, one per line. List: python anim.py image sizes -->"
    fills = {"{{TITLE}}": title, "{{BRAND}}": brand, "{{SIZES}}": size_lines}
    for page in [dest / "01_brief" / "brief.md", *(dest / "02_design").glob("*.html"), *(dest / "02_design").glob("*.js")]:
        text = page.read_text(encoding="utf-8")
        for key, value in fills.items():
            text = text.replace(key, html.escape(value) if page.suffix == ".html" and key == "{{TITLE}}" else value)
        page.write_text(text, encoding="utf-8")
    design = dest / "02_design"
    prefix = os.path.relpath(root, design)
    for name, target in (("brand", f"{prefix}/brands/{brand}"), ("runtime", f"{prefix}/_runtime"), ("library", f"{prefix}/library")):
        (design / name).symlink_to(target, target_is_directory=True)
    (dest / "project.json").write_text(json.dumps({"brand": brand, "kind": "image", "title": title}, indent=2) + "\n", encoding="utf-8")
    for stage in STAGES:
        (dest / stage).mkdir(exist_ok=True)
    return dest


# ---------------------------------------------------------------- brief

def parse_brief(text: str) -> dict[str, str]:
    """The '## Heading' sections of brief.md, keyed by heading."""
    sections, current = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            current = m[1]
            sections[current] = ""
        elif current:
            sections[current] += line + "\n"
    return {k: v.strip() for k, v in sections.items()}


def _filled(value: str) -> bool:
    return bool(re.sub(r"<!--.*?-->", "", value, flags=re.S).strip())


def picture_kind(plan: str) -> str:
    text = re.sub(r"<!--.*?-->", "", plan, flags=re.S)
    m = re.search(r"(?im)^\s*(?:[-*]\s*)?kind:\s*([a-z]+)", text)
    return m[1] if m else ""


def brief_problems(root: Path, job: Path) -> list[str]:
    """What the brief misses before a person can review it. Empty when complete."""
    path = job / "01_brief" / "brief.md"
    if not path.is_file():
        return ["01_brief/brief.md"]
    sections = parse_brief(path.read_text(encoding="utf-8"))
    missing = [f"brief section '{h}'" for h in BRIEF_HEADINGS if not _filled(sections.get(h, ""))]
    if _filled(sections.get("Sizes", "")):
        try:
            resolve_sizes(root, sections["Sizes"])
        except ImageError as error:
            missing.append(str(error))
    if _filled(sections.get("Picture plan", "")) and picture_kind(sections["Picture plan"]) not in PICTURE_KINDS:
        missing.append("picture plan 'kind:' (one of " + ", ".join(PICTURE_KINDS) + ")")
    return missing


def brief_sizes(root: Path, job: Path) -> list[dict]:
    sections = parse_brief((job / "01_brief" / "brief.md").read_text(encoding="utf-8"))
    rows = resolve_sizes(root, sections.get("Sizes", ""))
    if not rows:
        raise ImageError("the brief names no sizes")
    return rows


# ---------------------------------------------------------------- design and export

def design_files(job: Path) -> list[Path]:
    """Every file the final images depend on inside the job: the design and its pictures. Links are left out."""
    design = job / "02_design"
    files = [p for p in sorted(design.iterdir()) if p.is_file() and not p.is_symlink() and not p.name.startswith(".")] if design.is_dir() else []
    pictures = design / "pictures"
    if pictures.is_dir() and not pictures.is_symlink():
        files += sorted(p for p in pictures.rglob("*") if p.is_file() and not p.is_symlink()
                        and not any(part.startswith(".") for part in p.relative_to(pictures).parts))
    return files


def design_hash(job: Path) -> str:
    digest = hashlib.sha256()
    for path in design_files(job):
        digest.update(path.relative_to(job).as_posix().encode() + b"\0" + file_sha256(path).encode())
    return digest.hexdigest()


def export_files(job: Path) -> list[Path]:
    out = job / "03_export"
    return sorted(p for p in out.glob("*.png") if p.is_file() and not p.is_symlink()) if out.is_dir() else []


def contrast(a: tuple, b: tuple) -> float:
    def lum(c):
        ch = [v / 255 for v in c[:3]]
        ch = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in ch]
        return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def background_contrast(png: Path, rect: dict, color: tuple) -> float | None:
    """Contrast of a text colour against the most common colour in a thin band around its box (the background)."""
    from collections import Counter
    from PIL import Image
    with Image.open(png) as image:
        rgb = image.convert("RGB")
        pad = max(4, int(rect["h"] * 0.25))
        x0, y0 = max(0, int(rect["x"]) - pad), max(0, int(rect["y"]) - pad)
        x1, y1 = min(rgb.width, int(rect["x"] + rect["w"]) + pad), min(rgb.height, int(rect["y"] + rect["h"]) + pad)
        if x1 - x0 < 4 or y1 - y0 < 4:
            return None
        ix0, iy0, ix1, iy1 = int(rect["x"]), int(rect["y"]), int(rect["x"] + rect["w"]), int(rect["y"] + rect["h"])
        step = max(1, (x1 - x0) // 200)
        band = Counter()
        for y in range(y0, y1, step):
            for x in range(x0, x1, step):
                if not (ix0 <= x < ix1 and iy0 <= y < iy1):
                    r, g, b = rgb.getpixel((x, y))
                    band[(r // 16 * 16 + 8, g // 16 * 16 + 8, b // 16 * 16 + 8)] += 1
    if not band:
        return None
    return round(contrast(color, band.most_common(1)[0][0]), 2)


# Run in the page after __seek(0). Reports what can break a still: errors in parts that must stay visible.
CHECK_JS = r"""() => {
  const stage = document.getElementById('stage');
  const img = window.VF_IMAGE || {};
  const W = stage.offsetWidth, H = stage.offsetHeight, b = img.box || { x: 0, y: 0, w: W, h: H };
  const problems = [], warnings = [], texts = [];
  const shown = (el) => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && +cs.opacity !== 0; };
  const name = (el) => el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).join('.') : '');
  const keep = [...stage.querySelectorAll('h1,h2,h3,h4,p,li,blockquote,.vf-kicker,.vf-chip,.vf-logo,[data-keep]')]
    .filter((el) => !el.closest('[data-bleed],.vf-bg,.vf-safe') && shown(el));
  for (const el of keep) {
    const r = el.getBoundingClientRect();
    if (r.left < b.x - 1 || r.top < b.y - 1 || r.right > b.x + b.w + 1 || r.bottom > b.y + b.h + 1)
      problems.push(`${name(el)} is outside the safe area`);
    const slack = parseFloat(getComputedStyle(el).fontSize) * 0.35;  // tight line-heights let glyphs poke out a little
    if (el.matches('h1,h2,h3,h4,p,li,blockquote,.vf-kicker,.vf-chip') && (el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + slack))
      problems.push(`${name(el)} text overflows its box`);
    if (el.matches('h1,h2,h3,.vf-hero,.vf-title') && el.textContent.trim()) {
      const c = getComputedStyle(el).color.match(/\d+(\.\d+)?/g).map(Number);
      texts.push({ el: name(el), color: c.slice(0, 3), rect: { x: r.left, y: r.top, w: r.width, h: r.height } });
    }
  }
  for (const im of document.images) if (!im.closest('.vf-safe') && (!im.complete || im.naturalWidth === 0)) problems.push(`picture not loaded: ${im.getAttribute('src')}`);
  const T = window.BrandTokens || {};
  const fam = (s) => (s || '').split(',')[0].trim().replace(/^["']|["']$/g, '');
  const words = keep.some((el) => !el.matches('img,svg,.vf-logo') && el.textContent.trim());
  for (const f of new Set([fam(T.font), fam(T.head)].filter(Boolean))) {
    const faces = [...document.fonts].filter((x) => x.family.replace(/^["']|["']$/g, '') === f);
    if (faces.some((x) => x.status === 'error')) problems.push(`brand font failed to load: ${f}`);
    else if (words && faces.length && !faces.some((x) => x.status === 'loaded')) warnings.push(`brand font not used on this image: ${f}`);
    if (!faces.length) warnings.push(`brand font has no @font-face: ${f}`);
  }
  if (!stage.textContent.trim() && !stage.querySelector('img,svg,canvas')) problems.push('the image is empty');
  return { w: W, h: H, problems, warnings, texts };
}"""


def size_result(row: dict, png: Path, page: dict, errors: list[str]) -> dict:
    """One report entry for an exported size: exact pixels, page check, contrast of headings."""
    from PIL import Image
    problems = [f"page error: {e}" for e in errors[:5]] + list(page.get("problems", []))
    warnings = list(page.get("warnings", []))
    with Image.open(png) as image:
        if image.size != (row["w"], row["h"]):
            problems.append(f"image is {image.width}x{image.height}, not {row['w']}x{row['h']}")
    for text in page.get("texts", []):
        ratio = background_contrast(png, text["rect"], tuple(text["color"]))
        if ratio is not None and ratio < 3:
            warnings.append(f"{text['el']} contrast {ratio}:1 is low (aim for 4.5:1, at least 3:1)")
    return {"id": row["id"], "w": row["w"], "h": row["h"], "file": png.name, "sha256": file_sha256(png),
            "problems": problems, "warnings": warnings}


def write_report(job: Path, results: list[dict], partial: bool) -> dict:
    """Merge results into 03_export/report.json. 'ok' is true only when every brief size has a clean, current image."""
    path = job / "03_export" / "report.json"
    old = {}
    if partial and path.is_file():
        try:
            old = {r["id"]: r for r in json.loads(path.read_text(encoding="utf-8")).get("sizes", [])}
        except (ValueError, KeyError, TypeError, AttributeError):
            old = {}
    current = design_hash(job)
    if partial and path.is_file():
        try:
            if json.loads(path.read_text(encoding="utf-8")).get("design_sha256") != current:
                old = {}
        except ValueError:
            old = {}
    merged = {**old, **{r["id"]: r for r in results}}
    report = {"design_sha256": current, "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "sizes": list(merged.values())}
    report["ok"] = not report_problems(job.parents[2], job, report)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def report_problems(root: Path, job: Path, report: dict | None = None) -> list[str]:
    """Why the export is not complete and current. Empty when every brief size passed on the current design."""
    path = job / "03_export" / "report.json"
    if report is None:
        if not path.is_file():
            return ["exported images (python anim.py image export)"]
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            return ["a readable 03_export/report.json"]
    if report.get("design_sha256") != design_hash(job):
        return ["a new export: the design changed after the last export"]
    try:
        wanted = brief_sizes(root, job)
    except (ImageError, OSError) as error:
        return [str(error)]
    done = {r.get("id"): r for r in report.get("sizes", []) if isinstance(r, dict)}
    missing = []
    for row in wanted:
        entry = done.get(row["id"])
        png = job / "03_export" / f"{row['id']}.png"
        if entry is None or not png.is_file():
            missing.append(f"export of {row['id']}")
        elif entry.get("problems"):
            missing.append(f"{row['id']}: " + "; ".join(entry["problems"][:3]))
        elif entry.get("sha256") != file_sha256(png):
            missing.append(f"{row['id']}.png changed after the check")
    return missing


def add_picture(root: Path, job: Path, source: str, name: str | None = None) -> list[str]:
    """Copy a picture into 02_design/pictures and log where it came from in pictures/SOURCES.md.
    source is a local file (your own picture) or stock:provider/photo/id (downloaded and logged like `anim.py use`)."""
    pictures = job / "02_design" / "pictures"
    pictures.mkdir(parents=True, exist_ok=True)
    if source.startswith("stock:"):
        import stock
        from library import ENDORSE
        item = stock.load_item(source)
        if item.get("kind") != "photo":
            raise ImageError("a still image takes a stock photo: stock:provider/photo/id")
        src = stock.download(item)
        line = f"- {{file}}: {source} | {item['license']} | {item['page_url']} (by {item['author'] or 'unknown'}). {ENDORSE}"
    else:
        src = Path(source).expanduser()
        if not src.is_file():
            raise ImageError(f"no file {source}")
        line = "- {file}: own file, supplied by the user (" + src.name + "). The user holds the rights."
    if src.suffix.lower() not in _PICTURE_SUFFIXES:
        raise ImageError("a picture is png, jpg, webp, gif or svg")
    stem = re.sub(r"[^a-z0-9-]+", "-", (name or src.stem).lower()).strip("-") or "picture"
    dest = pictures / f"{stem}{src.suffix.lower()}"
    shutil.copyfile(src, dest)
    log = pictures / "SOURCES.md"
    head = "" if log.is_file() else "# Picture sources\n\nOne line per picture in this folder: where it came from and its licence.\n\n"
    with log.open("a", encoding="utf-8") as stream:
        stream.write(head + line.replace("{file}", dest.name) + "\n")
    return [f"{source} -> {dest.relative_to(job).as_posix()}", f"use it in design.html: <img class=\"vf-picture\" src=\"pictures/{dest.name}\" alt=\"\">"]


# ---------------------------------------------------------------- status

def job_state(root: Path, ident: str, job: Path) -> dict:
    brief = brief_problems(root, job)
    try:
        rows = brief_sizes(root, job) if not brief else []
    except ImageError:
        rows = []
    pngs = {p.stem for p in export_files(job)}
    done = sum(1 for r in rows if r["id"] in pngs)
    export = "none" if not pngs else ("current" if not report_problems(root, job) else f"{done}/{len(rows)} sizes, not current")
    reviews = {}
    try:
        from studio.creative import creative_review_state
        for gate in ("brief", "final"):
            reviews[gate] = creative_review_state(root, "image", ident, gate)["state"]
    except Exception as error:  # a broken REVIEW.md must not hide the other jobs
        reviews = {"brief": f"error: {error}", "final": ""}
    return {"id": ident, "brief": "complete" if not brief else "draft", "sizes": len(rows), "export": export, **{f"{g}_review": s for g, s in reviews.items()}}


def checked_age_days(row: dict, today: date | None = None) -> int:
    return ((today or date.today()) - date.fromisoformat(row["checked"])).days
