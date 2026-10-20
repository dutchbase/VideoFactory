"""The asset library: icons (Iconify), Lottie files, vector graphics. Files live under library/."""
import json
import math
import re
from pathlib import Path
from urllib.parse import quote

import libcore as C

LIB = C.ROOT / "library"
SOURCES = json.loads((LIB / "sources.json").read_text(encoding="utf-8"))
ICON_SETS = set(SOURCES["icons"])
ICONIFY = "https://api.iconify.design"


def _set_license(prefix: str, fetch) -> str:
    """Licence of an icon set as Iconify reports it (checked live, then against the allowlist)."""
    info = json.loads(C.http_get(f"{ICONIFY}/collections?prefixes={prefix}", fetch=fetch))
    spdx = (info.get(prefix) or {}).get("license", {}).get("spdx", "unknown")
    C.check_license(spdx)
    return spdx


def icon_search(query: str, set: str | None = None, limit: int = 20, fetch=None) -> list[str]:
    prefixes = set or ",".join(sorted(ICON_SETS))
    if set and set not in ICON_SETS:
        raise C.LicenseError(f"icon set {set!r} is not on the allowlist: {', '.join(sorted(ICON_SETS))}")
    url = f"{ICONIFY}/search?query={quote(query)}&prefixes={prefixes}&limit={limit}"
    return json.loads(C.http_get(url, fetch=fetch)).get("icons", [])


def icon_add(ref: str, fetch=None, root: Path | None = None) -> Path:
    """ref = 'lucide/rocket' (or 'lucide:rocket'). Idempotent. Returns the SVG path."""
    prefix, _, name = ref.replace(":", "/").partition("/")
    if prefix not in ICON_SETS:
        raise C.LicenseError(f"icon set {prefix!r} is not on the allowlist: {', '.join(sorted(ICON_SETS))}")
    name = C.safe_name(name)
    dest = (root or LIB) / "icons" / prefix / f"{name}.svg"
    if dest.exists():
        return dest
    _set_license(prefix, fetch)
    svg = C.http_get(f"{ICONIFY}/{prefix}/{name}.svg", fetch=fetch)
    if not svg.lstrip().startswith(b"<svg"):
        raise C.NetError(f"no icon {prefix}/{name}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(svg)
    return dest


def gallery(kind: str = "icons", root: Path | None = None, out: Path | None = None) -> Path:
    """One PNG contact sheet of every icon or graphic, drawn through Lib.icon / Lib.graphic so it also tests lib.js."""
    import tempfile
    from playwright.sync_api import sync_playwright
    root = root or LIB
    out = out or C.ROOT / "_shared" / "gallery" / f"library-{kind}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    names = sorted(f"{p.parent.name}/{p.stem}" for p in (root / kind).glob("*/*.svg"))
    if not names:
        raise ValueError(f"no {kind} yet. Run: python anim.py lib {kind[:-1] if kind == 'icons' else 'graphic'} add ...")
    draw = "Lib.icon(ctx, n, x, y, 64, '#F3F0E8')" if kind == "icons" else "Lib.graphic(ctx, n, x, y, 84)"
    cols, cell = 10, 150
    rows = -(-len(names) // cols)
    html = f"""<!doctype html><meta charset=utf-8><body style="margin:0;background:#111"><canvas id=c width={cols * cell} height={rows * cell}></canvas>
<script src="{(C.ROOT / '_runtime' / 'lib.js').as_uri()}"></script><script>
Lib.bases.{kind} = [{json.dumps((root / kind).as_uri() + '/')}];
const names = {json.dumps(names)}, ctx = document.getElementById('c').getContext('2d');
const ims = names.map(n => Lib.load('{kind}', n, 'svg'));
Promise.all(ims.map(im => new Promise(r => im.complete && im.naturalWidth ? r() : (im.onload = r, setTimeout(r, 8000))))).then(() => {{
  ctx.font = '14px monospace'; ctx.textAlign = 'center';
  names.forEach((n, i) => {{
    const x = (i % {cols}) * {cell} + {cell} / 2, y = Math.floor(i / {cols}) * {cell} + 62;
    {draw};
    ctx.fillStyle = '#77736B'; ctx.fillText(n.split('/')[1].slice(0, 16), x, y + 56);
  }});
  window.__ready = true;
}});
</script>"""
    with tempfile.TemporaryDirectory() as d:
        page = Path(d) / "g.html"
        page.write_text(html, encoding="utf-8")
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": cols * cell, "height": rows * cell})
            pg.goto(page.as_uri())
            pg.wait_for_function("window.__ready === true", timeout=30000)
            pg.locator("#c").screenshot(path=str(out))
            b.close()
    return out


def lottie_add(src: str, name: str | None = None, license_ok: bool = False, fetch=None, root: Path | None = None,
               license: str | None = None, page: str | None = None, creator: str | None = None, title: str | None = None,
               group: str | None = None, tags: list[str] | None = None) -> Path:
    """Save a Lottie JSON from a direct URL with its checked licence. page (the animation's web page, where the licence was read),
    creator, title, group (loading, success, confetti ...) and tags go into <name>.meta.json, so `lib find` can match them."""
    if not license_ok:
        raise C.LicenseError("check the file's licence on its page, then add --license <licence> --license-ok")
    if not license:
        raise C.LicenseError("new Lottie imports need --license from the allowlist")
    C.check_license(license)
    raw = C.http_get(src, fetch=fetch)
    if len(raw) > 5_000_000:
        raise ValueError("lottie file is over 5 MB: too heavy to render frame by frame")
    try:
        data = json.loads(raw)
    except ValueError:
        raise ValueError("not Lottie JSON. A .lottie file is a zip: download the JSON version instead") from None
    if not isinstance(data, dict) or not {"v", "fr", "ip", "op", "w", "h", "layers"} <= set(data):
        raise ValueError("not a Lottie animation (needs v, fr, ip, op, w, h, layers)")
    if (not isinstance(data["layers"], list) or
            any(type(data[k]) not in (int, float) or not math.isfinite(data[k]) for k in ("fr", "ip", "op", "w", "h")) or
            data["fr"] <= 0 or data["op"] <= data["ip"] or data["w"] <= 0 or data["h"] <= 0):
        raise ValueError("invalid Lottie dimensions, frame range, frame rate or layers")
    if not isinstance(data.get("assets", []), list):
        raise ValueError("invalid Lottie assets")
    for asset in data.get("assets", []):
        if "p" in asset and asset.get("e") != 1:  # an image that sits next to the file cannot load in a render
            raise ValueError("this Lottie links to external images. Pick one without images, or one with images embedded")
    n = C.safe_name(name or Path(src.split("?")[0]).stem)
    dest = (root or LIB) / "lottie" / f"{n}.json"
    if dest.exists():
        old = json.loads(dest.with_suffix(".meta.json").read_text(encoding="utf-8"))
        if dest.read_bytes() != raw or (old.get("license"), old.get("source")) != (license, src):
            raise ValueError(f"lottie {n!r} already exists with different data or rights; choose another --name")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    meta = {"license": license, "source": src, **{k: v for k, v in {"page": page, "creator": creator, "title": title,
            "group": group, "tags": [t.strip() for t in tags or [] if t.strip()]}.items() if v}}
    dest.with_suffix(".meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    # A render opens scenes from file://, where a page cannot fetch JSON. Lib.lottie loads this script instead.
    dest.with_suffix(".js").write_text(f"// GENERATED from {dest.name} by `anim.py lib lottie add`. Never edit.\n"
                                       f"(window.LOTTIE_DATA = window.LOTTIE_DATA || {{}})[{json.dumps(n)}] = {json.dumps(data, separators=(',', ':'))};\n",
                                       encoding="utf-8")
    return dest


def sanitize_svg(svg: str) -> str:
    """An SVG can carry script and remote loads. Keep drawing only: no script, foreignObject, on* handlers, javascript: or remote hrefs."""
    svg = re.sub(r"<script\b.*?</script\s*>|<script\b[^>]*/>", "", svg, flags=re.S | re.I)
    svg = re.sub(r"<foreignObject\b.*?</foreignObject\s*>", "", svg, flags=re.S | re.I)
    svg = re.sub(r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", "", svg, flags=re.I)

    def href(m):  # keep in-file (#id) and embedded (data:image) links only
        v = m.group(3).strip().lower()
        return m.group(0) if v.startswith(("#", "data:image/")) else ""
    return re.sub(r"\s((?:xlink:)?href)\s*=\s*([\"'])(.*?)\2", href, svg, flags=re.S | re.I)


def graphic_add(url: str, set: str, name: str, license: str, fetch=None, root: Path | None = None) -> Path:
    """Save one vector graphic (SVG) from a direct URL, sanitized, with its licence beside it."""
    C.check_license(license)
    set, name = C.safe_name(set), C.safe_name(name)
    raw = C.http_get(url, fetch=fetch)
    text = raw.decode("utf-8", errors="replace")
    if not re.search(r"<svg\b", text[:2000], re.I):
        raise ValueError("not an SVG file")
    dest = (root or LIB) / "graphics" / set / f"{name}.svg"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(sanitize_svg(text), encoding="utf-8")
    dest.with_suffix(".meta.json").write_text(json.dumps({"license": license, "source": url}), encoding="utf-8")
    return dest


CATEGORIES = json.loads((LIB / "categories.json").read_text(encoding="utf-8"))


def _json(p: Path, default=None):
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else default


def _icon_tags(folder: Path, name: str) -> list[str]:
    """Search words for an icon from its set's TAGS.json (tools/icon_meta.py, tools/iconanim): tags, then groups."""
    t = _json(folder / "TAGS.json", {}).get(name, {})
    return [*t.get("tags", []), *t.get("groups", [])]


def scan(root: Path | None = None) -> list[dict]:
    """Every item on one shelf (library/ or brands/<b>/library/), sorted by ref. Pure: writes nothing."""
    root = root or LIB
    items = []
    for p in (root / "icons").glob("*/*.svg"):
        items.append({"ref": f"icon:{p.parent.name}/{p.stem}", "kind": "icon", "set": p.parent.name, "name": p.stem, "category": "icons",
                      "tags": _icon_tags(p.parent, p.stem),
                      "license": SOURCES["icons"].get(p.parent.name, {}).get("spdx", "unknown"), "path": p.relative_to(root).as_posix()})
    for p in (root / "icons-animated").glob("*/*.svg"):
        items.append({"ref": f"animicon:{p.parent.name}/{p.stem}", "kind": "animicon", "set": p.parent.name, "name": p.stem, "category": "icons",
                      "tags": _icon_tags(p.parent, p.stem),
                      "license": SOURCES.get("icons_animated", {}).get(p.parent.name, {}).get("spdx", "unknown"), "path": p.relative_to(root).as_posix()})
    for p in (root / "graphics").glob("*/*.svg"):
        items.append({"ref": f"graphic:{p.parent.name}/{p.stem}", "kind": "graphic", "set": p.parent.name, "name": p.stem, "category": "pictograms",
                      "license": json.loads(p.with_suffix(".meta.json").read_text(encoding="utf-8"))["license"], "path": p.relative_to(root).as_posix()})
    for p in (root / "lottie").glob("*.json"):
        if p.name.endswith(".meta.json"):
            continue
        meta = json.loads(p.with_suffix(".meta.json").read_text(encoding="utf-8"))
        items.append({"ref": f"lottie:{p.stem}", "kind": "lottie", "set": "lottie", "name": p.stem, "category": "animations",
                      **({"title": meta["title"]} if meta.get("title") else {}),
                      "tags": [*([meta["group"]] if meta.get("group") else []), *meta.get("tags", [])],
                      "license": meta["license"], "path": p.relative_to(root).as_posix()})
    for p in (root / "blocks").glob("*/block.md"):
        m = C.frontmatter(p.read_text(encoding="utf-8"))
        items.append({"ref": f"block:{m['id']}", "kind": "block", "set": "blocks", "name": m["id"], "title": m["title"],
                      "description": m["description"], "tags": m["tags"], "category": m.get("category"),
                      "engine": m.get("engine", "hyperframes"), "license": "own", "path": p.parent.relative_to(root).as_posix()})
    for p in (root / "fx").glob("*/*/block.md"):  # rewritten components, engine-neutral (library/fx/CONTEXT.md)
        m = C.frontmatter(p.read_text(encoding="utf-8"))
        items.append({"ref": f"fx:{m['id']}", "kind": "fx", "set": p.parent.parent.name, "name": m["id"], "title": m["title"],
                      "description": m["description"], "tags": m["tags"], "category": p.parent.parent.name, "status": m.get("status", "draft"),
                      "engine": m.get("engine", "both"), "license": (m.get("source") or {}).get("license", "own"),
                      "path": p.parent.relative_to(root).as_posix()})
    for p in (root / "captures").glob("*.md"):
        m = C.frontmatter(p.read_text(encoding="utf-8"))
        items.append({"ref": f"capture:{m['id']}", "kind": "capture", "set": "captures", "name": m["id"], "title": m["title"],
                      "description": m["description"], "tags": m["tags"], "category": "media", "license": "own", "path": f"captures/{m['steps']}"})
    for p in [*(root / "motion").glob("*/manifest.json"), *(([root / "motion/manifest.json"]) if (root / "motion/manifest.json").is_file() else [])]:  # rendered clips, not scene blocks: tools/motion.py
        brand = root.parent.name if p.parent == root / "motion" else p.parent.name
        for a in json.loads(p.read_text(encoding="utf-8"))["assets"]:
            ref = f"{brand}/{a['id']}"
            items.append({"ref": f"motion:{ref}", "kind": "motion", "set": brand, "name": a["id"], "title": a["name"],
                          "description": f"{brand}: {a['section']}, {a['type']}. Render: python tools/motion.py render --brand {brand} --id {a['id']} (see {p.parent.relative_to(root).as_posix()}/CONTEXT.md)",
                          "tags": [brand, a["type"], a["section"].split(" ", 1)[1].lower(), "motion"], "license": "own",
                          "category": CATEGORIES["motion_sections"].get(a["section"]),
                          "path": f"{p.parent.relative_to(root).as_posix()}/{a['file']}"})
    for p in (root / "upstream").glob("*.json"):  # components not rewritten yet (generated by `lib upstream`)
        if p.name == "sources.json":
            continue
        for u in json.loads(p.read_text(encoding="utf-8")):
            if u["status"] not in ("available", "covered"):
                continue
            items.append({"ref": f"upstream:{p.stem}/{u['name']}", "kind": "upstream", "set": p.stem, "name": u["name"], "title": u["title"],
                          "description": u["description"], "tags": u.get("tags", []), "category": u["category"], "status": u["status"],
                          **({"covered_by": u["covered_by"]} if u.get("covered_by") else {}),
                          "difficulty": u["difficulty"], "license": u["license"], "path": f"upstream/{p.name}"})
    items.sort(key=lambda e: e["ref"])
    return items


def _write(path: Path, text: str) -> None:
    """Write a generated file in one step (a temp file, then rename), so a reader never sees half a file."""
    tmp = path.with_name(f".{path.name}.{__import__('os').getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def index(root: Path | None = None) -> list[dict]:
    """Scan library/ and write INDEX.json (sorted, so a rebuild is identical). Generated: never hand-edited.
    For the shared library, also write CATALOG.md (with the brand shelves), the agent's map of what exists."""
    shared = root is None
    root = root or LIB
    items = scan(root)
    _write(root / "INDEX.json", json.dumps(items, indent=1) + "\n")
    if (root / "fx" / "_demo").is_dir():
        _write(root / "fx" / "_demo" / "parts.js", fx_parts(root))
    if shared:
        brands = {b.parent.name: scan(b) for b in sorted((C.ROOT / "brands").glob("*/library")) if b.is_dir()}
        _write(root / "CATALOG.md", catalog(items, brands))
    return items


# How to use each kind: shown in CATALOG.md. Engines: "both" = Modern kit and HyperFrames.
KIND_USE = {
    "fx": ("library/fx/<category>/<id>/", "both", "`use <slug> fx:<id>`; API in its `block.md`; look: `fx/GALLERY.html`"),
    "block": ("library/blocks/<id>/", "HyperFrames", "`use <slug> block:<id>`; API in its `block.md`; look: `blocks/GALLERY.html`"),
    "motion": ("brands/<brand>/library/motion/", "a rendered clip", "`python tools/motion.py render --brand <brand> --id <ID>`"),
    "animicon": ("library/icons-animated/<set>/", "both", "`use <slug> animicon:<set>/<name>`, then `<i data-icon=\"<set>/<name>\" data-play=\"@word\">` (HyperFrames: `AnimIcon.play`; `use` prints the lines)"),
    "icon": ("library/icons/<set>/", "both", "`<i data-icon=\"name\">` (Lucide) or `use <slug> icon:<set>/<name>`; more: `lib icon add <set>/<name>`"),
    "graphic": ("library/graphics/<set>/", "both", "`use <slug> graphic:<set>/<name>`, then `<img>`"),
    "lottie": ("library/lottie/", "both", "`use <slug> lottie:<name>`, then `Lib.lottie('<name>', {colors: 'brand'})`; `use` prints the lines for the engine"),
    "capture": ("library/captures/", "recording", "copy the steps file, then `anim.py record` (`_shared/capture.md`)"),
    "upstream": ("library/upstream/<source>.json", "not rewritten yet", "`lib port upstream:<source>/<name>`, then follow `_shared/porting.md`"),
}


def catalog(items: list[dict], brands: dict[str, list[dict]] | None = None) -> str:
    """CATALOG.md: counts per category and kind, a few examples, and how to use each kind. Generated."""
    from collections import Counter
    every = [*items, *(e for b in (brands or {}).values() for e in b)]
    kinds = list(KIND_USE)
    count = Counter((e.get("category") or "uncategorised", e["kind"]) for e in every)
    per_kind = Counter(e["kind"] for e in every)
    cats = [*CATEGORIES["categories"], *(["uncategorised"] if any(c == "uncategorised" for c, _ in count) else [])]
    used = [k for k in kinds if per_kind[k]]
    out = ["# Library catalog", "",
           "GENERATED by `python anim.py lib index` from the shelves. Never edit. Categories: `categories.json`. Rules and licences: `CONTEXT.md`.", "",
           "- Find: `python anim.py lib find [words] --brand <brand> [--kind <kind>] [--category <category>]`",
           "- Use: `python anim.py use <slug> <ref>` copies the item into the video and logs its licence.",
           "- Not on the shelf yet: `upstream:` items are components we can rewrite on demand (`_shared/porting.md`). The new part joins `library/fx/` as a draft.",
           *(["- Sound effects and music: a separate shelf, `audio/CONTEXT.md` (`python anim.py audio find <words>`)."]
             if (LIB / "audio" / "CONTEXT.md").is_file() else []), "",
           "## Kinds", "", "| Kind | Items | Where | Engine | How to use |", "|---|---|---|---|---|"]
    out += [f"| {k} | {per_kind[k]} | `{KIND_USE[k][0]}` | {KIND_USE[k][1]} | {KIND_USE[k][2]} |" for k in used]
    out += ["", "## Categories", "", "| Category | What | " + " | ".join(used) + " |", "|---|---|" + "---|" * len(used)]
    for c in cats:
        if not any(count[c, k] for k in used):
            continue
        meaning = CATEGORIES["categories"].get(c, "No category set yet: add one.")
        out.append(f"| {c} | {meaning} | " + " | ".join(str(count[c, k] or "") for k in used) + " |")
    out += ["", "## Examples per category", "",
            "Ready items first (fx, block, motion), then items to rewrite. More: `lib find --category <category> --brand <brand>`.", ""]
    for c in cats:
        ready = [e for e in every if (e.get("category") or "uncategorised") == c and e["kind"] in ("fx", "block", "motion", "lottie")]
        todo = [e for e in every if (e.get("category") or "uncategorised") == c and e["kind"] == "upstream" and e["status"] == "available"]
        if not ready and not todo:
            continue
        ready.sort(key=lambda e: (["fx", "block", "lottie", "motion"].index(e["kind"]), e.get("status") == "draft", e["ref"]))
        label = lambda e: f"`{e['ref']}` {e.get('title', '')[:32]}".rstrip() + (" (draft)" if e.get("status") == "draft" else "")
        line = "; ".join(label(e) for e in ready[:5])
        out.append(f"- **{c}**: {line or 'nothing ready yet'}" + (f"; {len(ready) - 5} more" if len(ready) > 5 else ""))
        if todo:
            out.append(f"  - to rewrite ({len(todo)}): " + ", ".join(f"`{e['ref']}`" for e in todo[:4]) + (", ..." if len(todo) > 4 else ""))
    groups = Counter(g for e in every if e["kind"] in ("icon", "animicon") for g in e.get("tags", [])
                     if g in _icon_groups())
    if groups:
        out += ["", "## Icon groups", "", "Search any group or word: `lib find <word> --kind animicon --brand <brand>` (or `--kind icon`).", "",
                ", ".join(f"{g} ({n})" for g, n in sorted(groups.items()))]
    return "\n".join(out) + "\n"


def _icon_groups() -> set[str]:
    """Lucide category names (the groups in TAGS.json)."""
    return {g for f in [*(LIB / "icons").glob("*/TAGS.json"), *(LIB / "icons-animated").glob("*/TAGS.json")]
            for t in _json(f, {}).values() for g in t.get("groups", [])}


def find(query: str = "", root: Path | None = None, brand: str | None = None,
         kind: str | None = None, category: str | None = None) -> list[dict]:
    """Items where every word of the query is in the ref, title, description or tags (rebuilds INDEX.json first).
    Shelf items come before upstream items (components not rewritten yet)."""
    words = query.lower().split()
    text = lambda e: " ".join([e["ref"], e.get("title", ""), e.get("description", ""), *e.get("tags", [])]).lower()
    if not brand or root is not None:
        items = index(root)
    else:
        from studio.project_paths import _part
        _part(brand)
        owned = C.ROOT / "brands" / brand / "library"
        items = [*(index(owned) if owned.is_dir() else []), *index(LIB)]
        items = [entry for entry in items if entry.get("kind") != "motion" or entry.get("set") == brand]
        unique = {}
        for entry in items:
            unique.setdefault(entry["ref"], entry)
        items = list(unique.values())
    hits = [e for e in items if all(w in text(e) for w in words)
            and (not kind or e["kind"] == kind) and (not category or e.get("category") == category)]
    return sorted(hits, key=lambda e: e["kind"] == "upstream")


def _block_order(bid: str, root: Path, seen: list[str]) -> list[str]:
    """The block and its depends, dependencies first."""
    meta = root / "blocks" / C.safe_name(bid) / "block.md"
    if not meta.exists():
        raise ValueError(f"no block {bid}. Find one: python anim.py lib find <words>")
    for dep in C.frontmatter(meta.read_text(encoding="utf-8")).get("depends", []):
        if dep not in seen:
            _block_order(dep, root, seen)
    if bid not in seen:
        seen.append(bid)
    return seen


def use_block(vdir: Path, bid: str, root: Path) -> list[str]:
    """Copy a block and its dependencies into 04_scene/blocks/ (real files: the render trusts only scripts inside the scene)."""
    lines = []
    for b in _block_order(bid, root, []):
        folder = root / "blocks" / b
        files = C.frontmatter((folder / "block.md").read_text(encoding="utf-8"))["files"]
        dests = [_copy(folder / C.safe_name(f), Path(vdir) / "04_scene" / "blocks" / C.safe_name(f)) for f in files]
        C.record_use(vdir, f"block:{b}", "own", f"library/blocks/{b}", ", ".join(f"blocks/{d.name}" for d in dests))
        lines += [f'<link rel="stylesheet" href="blocks/{d.name}">' if d.suffix == ".css" else f'<script src="blocks/{d.name}"></script>'
                  for d in dests]
    return [f"block:{bid} (own) -> 04_scene/blocks/; paste in index.html, after hf-bridge.js:"] + ["  " + l for l in lines]


def _fx_dir(fid: str, root: Path) -> Path | None:
    hits = sorted((root / "fx").glob(f"*/{C.safe_name(fid)}/block.md"))
    return hits[0].parent if hits else None


def fx_files(fid: str, root: Path, seen: list[Path] | None = None) -> list[Path]:
    """Every file an fx part needs, in load order: its depends (blocks such as core, or other fx), the kit, then its own files."""
    seen = [] if seen is None else seen
    folder = _fx_dir(fid, root)
    if folder is None:
        raise ValueError(f"no fx part {fid}. Find one: python anim.py lib find <words> --kind fx --brand <brand>")
    m = C.frontmatter((folder / "block.md").read_text(encoding="utf-8"))
    for dep in m.get("depends", []):
        if _fx_dir(dep, root) is not None:
            fx_files(dep, root, seen)
        else:
            for b in _block_order(dep, root, []):
                for f in C.frontmatter((root / "blocks" / b / "block.md").read_text(encoding="utf-8"))["files"]:
                    if (p := root / "blocks" / b / C.safe_name(f)) not in seen:
                        seen.append(p)
    for p in [root / "fx" / "_kit" / "kit.js", *(folder / C.safe_name(f) for f in m["files"])]:
        if p not in seen:
            seen.append(p)
    return seen


def fx_parts(root: Path) -> str:
    """fx/_demo/parts.js: the load order of every part for the demo pages (a file:// page cannot read block.md). Generated.
    A part whose block.md does not parse yet (work in progress) is left out; `lib fx check` names its problem."""
    parts = {}
    for p in sorted((root / "fx").glob("*/*/block.md")):
        try:
            parts[f"{p.parent.parent.name}/{p.parent.name}"] = [f.relative_to(root).as_posix() for f in fx_files(p.parent.name, root)]
        except (ValueError, KeyError):
            continue
    return ("// GENERATED by `anim.py lib index` from library/fx/*/*/block.md. Never edit.\n"
            f"window.FX_PARTS = {json.dumps(parts, indent=1)};\n")


def use_fx(vdir: Path, fid: str, root: Path) -> list[str]:
    """Copy an fx part and what it needs into the scene (04_scene/blocks/ for blocks, 04_scene/fx/ for the rest) and log it.
    Prints the lines for the video's engine."""
    folder = _fx_dir(fid, root)
    files = fx_files(fid, root)
    m = C.frontmatter((folder / "block.md").read_text(encoding="utf-8"))
    dests = [_copy(f, Path(vdir) / "04_scene" / ("blocks" if f.is_relative_to(root / "blocks") else "fx") / f.name) for f in files]
    src = m.get("source") or {}
    C.record_use(vdir, f"fx:{fid}", src.get("license", "own"), f"library/{folder.relative_to(root).as_posix()}"
                 + (f" (rewritten from {src.get('site')} {src.get('name')}, {src.get('repo')})" if src else ""),
                 ", ".join(d.relative_to(Path(vdir) / "04_scene").as_posix() for d in dests))
    tags = [f'<link rel="stylesheet" href="{d.relative_to(Path(vdir) / "04_scene").as_posix()}">' if d.suffix == ".css" else
            f'<script src="{d.relative_to(Path(vdir) / "04_scene").as_posix()}"></script>' for d in dests]
    hf = _engine(vdir) == "hyperframes"
    where = "after hf-bridge.js" if hf else "after runtime/modern.js, before scene.js"
    setup = ("const H = Blocks.core(tl);   // in the inline script, after the timeline" if hf
             else "const H = Blocks.core(P.timeline());   // at the top of scene.js")
    status = " (draft: approve it with the video)" if m.get("status", "draft") == "draft" else ""
    return ([f"fx:{fid}{status} -> 04_scene/; paste in index.html, {where}:"] + ["  " + t for t in tags]
            + [f"then: {setup}", *(f"  {a}" for a in m.get("api", []))])


def blocks_gallery(root: Path | None = None) -> Path:
    """A preview.png per block (its demo at preview_at, 360x640) and blocks/GALLERY.html with a card per block. Generated."""
    import html
    import io
    from PIL import Image
    from playwright.sync_api import sync_playwright
    root = root or LIB
    items = [e for e in index(root) if e["kind"] == "block"]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        for e in items:
            d = root / e["path"]
            m = C.frontmatter((d / "block.md").read_text(encoding="utf-8"))
            page.goto((d / "demo.html").resolve().as_uri())
            page.wait_for_function("!!(window.__timelines && window.__timelines.main)")  # a GSAP timeline is thenable
            page.evaluate("t => { window.__timelines.main.seek(t); }", m["preview_at"])
            page.evaluate("() => Promise.all([document.fonts.ready, ...[...document.images].map(i => i.decode().catch(() => null))]).then(() => true)")
            im = Image.open(io.BytesIO(page.screenshot()))
            im.thumbnail((360, 640))
            im.save(d / "preview.png", optimize=True)
            e["api"] = m["api"]
        browser.close()
    esc = html.escape
    cards = "".join(
        f'<article><img src="{esc(e["name"])}/preview.png" alt=""><h2>{esc(e["title"])}</h2><p class="ref">{esc(e["ref"])}</p>'
        f'<p>{esc(e["description"])}</p><p class="tags">{esc(", ".join(e["tags"]))}</p>'
        f'<ul>{"".join(f"<li><code>{esc(a)}</code></li>" for a in e["api"])}</ul>'
        f'<p class="use"><code>anim.py use &lt;slug&gt; {esc(e["ref"])}</code> &middot; demo: <code>library/blocks/{esc(e["name"])}/demo.html</code></p></article>'
        for e in items)
    out = root / "blocks" / "GALLERY.html"
    out.write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Blocks</title><style>'
                   "body{font:16px/1.4 system-ui,sans-serif;margin:24px;background:#f4f2ec;color:#1a1a1a}"
                   "main{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px}"
                   "article{background:#fff;border:3px solid #1a1a1a;padding:14px}img{width:100%;display:block;border:1px solid #c9c3b4}"
                   "h2{font-size:18px;margin:10px 0 2px}.ref{font-family:monospace;color:#b33613;margin:0}.tags{color:#6b6b6b;font-size:13px}"
                   "ul{padding-left:18px;font-size:12px}code{font-size:12px}</style></head><body>"
                   f"<h1>Blocks ({len(items)})</h1><p>Search: <code>anim.py lib find &lt;words&gt;</code>. Generated by <code>anim.py lib gallery</code>; do not edit by hand.</p>"
                   f"<main>{cards}</main></body></html>\n", encoding="utf-8")
    return out


def fx_gallery(root: Path | None = None) -> Path:
    """A preview.jpg per fx part (its HyperFrames demo at preview_at, 480x270) and fx/GALLERY.html grouped by category. Generated."""
    import html
    import io
    from PIL import Image
    from playwright.sync_api import sync_playwright
    root = root or LIB
    items = [e for e in index(root) if e["kind"] == "fx"]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        for e in items:
            d = root / e["path"]
            m = C.frontmatter((d / "block.md").read_text(encoding="utf-8"))
            page.goto((root / "fx" / "_demo" / "hf.html").as_uri() + f"?fx={e['category']}/{e['name']}")
            page.wait_for_function("window.__fxReady === true || !!window.__fxError", timeout=20000)
            page.evaluate("t => { window.__timelines.main.seek(t); }", m["preview_at"])
            im = Image.open(io.BytesIO(page.locator("#stage").screenshot())).convert("RGB")
            im.thumbnail((480, 270))
            im.save(d / "preview.jpg", quality=78, optimize=True)
            e["api"], e["source"] = m["api"], m.get("source") or {}
        browser.close()
    esc = html.escape
    card = lambda e: (
        f'<article><img src="{esc(e["category"])}/{esc(e["name"])}/preview.jpg" alt=""><h3>{esc(e["title"])}'
        f'{" <small>draft</small>" if e.get("status") == "draft" else ""}</h3><p class="ref">{esc(e["ref"])}</p>'
        f'<p>{esc(e["description"])}</p><ul>{"".join(f"<li><code>{esc(a)}</code></li>" for a in e["api"])}</ul>'
        f'<p class="use"><a href="_demo/modern.html?fx={esc(e["category"])}/{esc(e["name"])}">Modern demo</a> &middot; '
        f'<a href="_demo/hf.html?fx={esc(e["category"])}/{esc(e["name"])}">HyperFrames demo</a>'
        + (f' &middot; from <a href="{esc(e["source"].get("repo", ""))}">{esc(e["source"].get("site", ""))}</a>' if e["source"] else "")
        + "</p></article>")
    groups = "".join(f'<h2 id="{esc(c)}">{esc(c)} ({n})</h2><main>{"".join(card(e) for e in items if e["category"] == c)}</main>'
                     for c in CATEGORIES["categories"] if (n := sum(e["category"] == c for e in items)))
    out = root / "fx" / "GALLERY.html"
    out.write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>fx parts</title><style>'
                   "body{font:16px/1.4 system-ui,sans-serif;margin:24px;background:#f4f2ec;color:#1a1a1a}"
                   "main{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:20px}"
                   "article{background:#fff;border:3px solid #1a1a1a;padding:14px}img{width:100%;display:block;border:1px solid #c9c3b4}"
                   "h3{font-size:18px;margin:10px 0 2px}small{color:#b33613}.ref{font-family:monospace;color:#b33613;margin:0}"
                   "ul{padding-left:18px;font-size:12px}code{font-size:12px}</style></head><body>"
                   f"<h1>fx parts ({len(items)})</h1><p>Search: <code>anim.py lib find &lt;words&gt; --kind fx</code>. "
                   "Generated by <code>anim.py lib gallery</code>; do not edit by hand. Every part works in the Modern kit and in HyperFrames.</p>"
                   f"{groups}</body></html>\n", encoding="utf-8")
    return out


ENDORSE = "People in stock footage and photos must not look like they endorse your brand (every stock licence forbids implied endorsement)."


def video_orientation(vdir: Path) -> str:
    """portrait for a 9:16 video, else landscape (tall scenes declare data-height=1920)."""
    f = Path(vdir) / "04_scene" / "index.html"
    return "portrait" if f.exists() and 'data-height="1920"' in f.read_text(encoding="utf-8") else "landscape"


def _copy(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())
    return dest


def _engine(vdir: Path) -> str:
    pj = Path(vdir) / "project.json"
    return json.loads(pj.read_text(encoding="utf-8")).get("engine", "canvas") if pj.exists() else "canvas"


def _seconds(t: str) -> float:
    m, _, sec = str(t).rpartition(":")
    return (int(m) * 60 if m else 0) + float(sec)


def _silent_clip(src: Path, dest: Path, start: str, end: str) -> Path:
    """Cut start..end of a stock video to an H.264 file without audio (HyperFrames <video> asset)."""
    import subprocess
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{_seconds(start):.3f}", "-to", f"{_seconds(end):.3f}", "-i", str(src),
                    "-an", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(dest)], check=True)
    return dest


def use(vdir: Path, ref: str, name: str | None = None, start: str | None = None, end: str | None = None,
        clip=None, fetch=None, root: Path | None = None) -> list[str]:
    """Copy one library or stock item into a video's 04_scene/assets/ and log it. Returns lines to print.
    clip(src, name, start, end) cuts a stock video into frames (anim.py passes its `real clip`)."""
    import stock
    vdir = Path(vdir)
    if root is None:
        from studio.project_paths import project_brand
        brand = project_brand(vdir)
        owned = C.ROOT / "brands" / brand / "library"
        kind_, rest_ = C.parse_ref(ref)
        parts = rest_.split("/")
        owned_fx = _fx_dir(rest_, owned) if kind_ == "fx" else None
        candidate = {"block": owned / "blocks" / rest_ / "block.md",
                     "fx": owned_fx / "block.md" if owned_fx else None,
                     "animicon": owned / "icons-animated" / (rest_ + ".svg"),
                     "graphic": owned / "graphics" / (rest_ + ".svg"),
                     "icon": owned / "icons" / (rest_ + ".svg"),
                     "lottie": owned / "lottie" / (rest_ + ".json")}.get(kind_)
        root = owned if candidate is not None and candidate.is_file() else LIB
    assets = vdir / "04_scene" / "assets"
    kind, rest = C.parse_ref(ref)
    if kind == "adaptation":
        import hashlib
        from studio.project_paths import project_brand
        brand = project_brand(vdir)
        record_path = C.ROOT / "brands" / brand / "library/adaptations" / C.safe_name(rest) / "adaptation.json"
        record = json.loads(record_path.read_text())
        src = (C.ROOT / record["artifact"]).resolve()
        owned = (C.ROOT / "brands" / brand / "library").resolve()
        if record.get("target_brand") != brand or not src.is_relative_to(owned) or hashlib.sha256(src.read_bytes()).hexdigest() != record.get("artifact_sha256"):
            raise ValueError("adapted asset does not match this brand or its recorded bytes")
        dest = _copy(src, assets / "adaptations" / (C.safe_name(rest) + src.suffix))
        C.record_use(vdir, ref, record["rights"], record["source"], dest.relative_to(vdir / "04_scene").as_posix())
        return [f"{ref} (draft) -> {dest.relative_to(vdir)}"]
    if kind == "block":
        return use_block(vdir, rest, root)
    if kind == "fx":
        return use_fx(vdir, rest, root)
    if name:
        name = C.safe_name(name)
    if kind in ("icon", "graphic"):
        prefix, _, n = rest.partition("/")
        n = C.safe_name(n)
        folder = "icons" if kind == "icon" else "graphics"
        if kind == "icon":
            src = icon_add(rest, fetch=fetch, root=root)
            lic = SOURCES["icons"][prefix]["spdx"]
            url = SOURCES["icons"][prefix]["url"]
        else:
            src = root / "graphics" / C.safe_name(prefix) / f"{n}.svg"
            if not src.exists():
                raise ValueError(f"no graphic {rest}. Find it: python anim.py lib find {n}")
            meta = json.loads(src.with_suffix(".meta.json").read_text(encoding="utf-8"))
            lic, url = meta["license"], meta["source"]
        dest = _copy(src, assets / folder / C.safe_name(prefix) / f"{n}.svg")
        msgs = []
    elif kind == "lottie":
        n = C.safe_name(rest)
        src = root / "lottie" / f"{n}.json"
        if not src.exists():
            raise ValueError(f"no lottie {rest}. Add it: python anim.py lib lottie add <url> --license-ok")
        meta = json.loads(src.with_suffix(".meta.json").read_text(encoding="utf-8"))
        lic, url = meta["license"], meta["source"]
        dest = _copy(src.with_suffix(".js"), assets / "lottie" / f"{n}.js")
        msgs = (['paste after runtime/hf-bridge.js: <script src="runtime/lib.js"></script>',
                 f"then in the inline script: const clip = Lib.lottie('{n}', {{ colors: 'brand' }}); draw it with "
                 "clip.at(ctx, t - start, x, y, w, h) inside H.drive((p, t) => {...}, start, end) (blocks/core.js)"]
                if _engine(vdir) == "hyperframes" else
                ['paste after runtime/player.js: <script src="runtime/lib.js"></script>',
                 f"then in scene.js: const clip = Lib.lottie('{n}', {{ colors: 'brand' }}); draw it with clip.at(ctx, t, x, y, w, h) from P.onFrame"])
    elif kind == "animicon":
        prefix, _, n = rest.partition("/")
        prefix, n = C.safe_name(prefix), C.safe_name(n)
        src = root / "icons-animated" / prefix / f"{n}.js"
        if not src.exists():
            raise ValueError(f"no animated icon {rest}. Find one: python anim.py lib find {n} --kind animicon")
        lic, url = SOURCES["icons_animated"][prefix]["spdx"], SOURCES["icons_animated"][prefix]["url"]
        dest = _copy(src, assets / "icons-animated" / prefix / f"{n}.js")
        rel = dest.relative_to(vdir / "04_scene").as_posix()
        msgs = ([f'paste after runtime/hf-bridge.js: <script src="runtime/animicon.js"></script> <script src="{rel}"></script>',
                 f"then: AnimIcon.mount(el, '{prefix}/{n}'); AnimIcon.play(tl, el, '{prefix}/{n}', cue('<cue>'))"]
                if _engine(vdir) == "hyperframes" else
                [f'paste before runtime/modern.js: <script src="runtime/animicon.js"></script> <script src="{rel}"></script>',
                 f'then: <i data-icon="{prefix}/{n}" data-play="@word"></i> (data-loop, data-gap, data-speed: _shared/modern.md)'])
    elif kind == "stock":
        item = stock.load_item(ref)
        media = stock.download(item, fetch=fetch)
        n = name or C.safe_name(f"{item['provider']}-{item['id']}")
        lic = item["license"]
        url = f"{item['page_url']} (by {item['author']})"
        if item["kind"] == "audio":
            dest = _copy(media, assets / f"music-{n}.mp3")
            msgs = []
        elif item["kind"] == "photo":
            from PIL import Image
            im = Image.open(media).convert("RGB")
            im.thumbnail((2400, 2400))
            dest = assets / f"{n}.jpg"
            dest.parent.mkdir(parents=True, exist_ok=True)
            im.save(dest, quality=88)
        else:
            if not (start and end):
                raise ValueError("a stock video needs --start and --end (seconds or m:ss), e.g. --start 0 --end 5")
            if _engine(vdir) == "hyperframes":  # a silent <video> asset; every sound goes through the render's mixer
                dest = _silent_clip(media, assets / f"{n}.mp4", start, end)
            else:
                if clip is None:
                    raise ValueError("no clip cutter given")
                clip(media, n, start, end)
                dest = assets / n
        if item["kind"] != "audio":
            msgs = [ENDORSE]
    else:
        raise ValueError(f"unknown ref kind {kind!r}: icon, animicon, graphic, lottie, stock, block, fx (motion: python tools/motion.py render, see library/motion/*/CONTEXT.md)")
    C.record_use(vdir, ref, lic, url, dest.relative_to(vdir / "04_scene").as_posix())
    return [f"{ref} ({lic}) -> {dest.relative_to(vdir)}"] + msgs


def run(a) -> None:
    """CLI entry for `anim.py lib ...`."""
    if a.kind == "icon" and a.act == "search":
        for r in icon_search(a.query, a.set, a.limit):
            print(r)
    elif a.kind == "icon" and a.act == "add":
        for r in a.refs:
            print(f"icon:{r.replace(':', '/')} -> {icon_add(r).relative_to(C.ROOT)}")
    elif a.kind == "lottie" and a.act == "add":
        print(f"lottie:{lottie_add(a.url, a.name, a.license_ok, license=a.license, page=a.page, creator=a.creator, title=a.title, group=a.group, tags=(a.tags or '').split(',')).stem} -> library/lottie/")
    elif a.kind == "graphic" and a.act == "add":
        print(f"graphic:{a.set}/{graphic_add(a.url, a.set, a.name, a.license).stem} -> library/graphics/{a.set}/")
    elif a.kind == "upstream":
        import upstream
        for s, items in upstream.catalog_all().items():
            print(f"library/upstream/{s}.json: {len(items)} components, {sum(i['status'] == 'available' for i in items)} to rewrite")
        index()
    elif a.kind == "port":
        import upstream
        for line in upstream.port(a.ref, a.id, a.slug):
            print(line)
    elif a.kind == "fx" and a.act == "check":
        import fxcheck
        problems = fxcheck.check(a.id, with_browser=not a.no_browser)
        for p in problems:
            print(f"  {p}")
        print(f"fx:{a.id}: " + ("OK" if not problems else f"{len(problems)} problem(s)"))
        if problems:
            raise SystemExit(1)
    elif a.kind == "fx" and a.act == "stills":
        import fxcheck
        print(f"-> {fxcheck.stills(a.id, tall=a.tall).relative_to(C.ROOT)}  (top row: Modern kit, bottom row: HyperFrames)")
    elif a.kind == "gallery":
        print(f"-> {blocks_gallery().relative_to(C.ROOT)}  (studio: http://127.0.0.1:8765/library/blocks/GALLERY.html)")
        print(f"-> {fx_gallery().relative_to(C.ROOT)}  (studio: http://127.0.0.1:8765/library/fx/GALLERY.html)")
        for k in ("icons", "graphics"):
            try:
                print(f"-> {gallery(k).relative_to(C.ROOT)}")
            except ValueError as e:
                print(f"  skipped {k}: {e}")
    elif a.kind == "index":
        n = len(index())
        print(f"library/INDEX.json: {n} items; map: library/CATALOG.md")
    elif a.kind == "find":
        for e in find(a.query, brand=getattr(a, "brand", None), kind=a.only_kind, category=a.category):
            note = {"draft": " [draft]", "available": " [to rewrite: lib port]", "covered": f" [use {e.get('covered_by')}]"}.get(e.get("status"), "")
            print(f"{e['ref']:<46} {e['license']:<10} {e.get('title', '')}{note}".rstrip())
