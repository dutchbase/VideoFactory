"""Checks for one library/fx part: the rules in library/fx/CONTEXT.md, then its demo in both engines.

    python anim.py lib fx check <id>        # all problems at once; empty list = the part passes
"""
import hashlib
import re
from pathlib import Path

import libcore as C
import library as L

KEYS = {"id", "title", "description", "tags", "kind", "engine", "status", "files", "depends", "api", "preview_at", "source"}
SOURCE_KEYS = {"site", "name", "repo", "sha", "file", "license"}
BANNED = {r"Math\.random": "Math.random (use FX.kit.rand(seed))", r"Date\.now|new Date\b": "the wall clock (Date)",
          r"\bsetTimeout\b|\bsetInterval\b": "timers", r"requestAnimationFrame": "requestAnimationFrame",
          r"performance\.now": "performance.now", r"\bfetch\(|XMLHttpRequest": "network loads", r"onUpdate|onComplete": "GSAP callbacks (use H.drive)"}
MEASURE = re.compile(r"offsetWidth|offsetHeight|getBoundingClientRect|scrollWidth|clientWidth|getBBox|getComputedTextLength|measureText")
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
FUNC_COLOR = re.compile(r"\b(?:rgba?|hsla?)\(\s*([^)]*)\)")
NEUTRAL = re.compile(r"^\s*(0\s*,\s*0\s*,\s*0|255\s*,\s*255\s*,\s*255)\s*(,\s*[\d.]+\s*)?$")  # black or white with alpha: shadows


def static(fid: str, root: Path | None = None) -> list[str]:
    """Rule problems of one part (frontmatter, files, banned calls, colours, class names)."""
    root = root or L.LIB
    folder = L._fx_dir(fid, root)
    if folder is None:
        return [f"no fx part {fid}"]
    text = (folder / "block.md").read_text(encoding="utf-8")
    problems = []
    try:
        m = C.frontmatter(text)
    except ValueError as e:
        return [f"block.md: {e}"]
    if "<" in text.split("---")[1] and re.search(r"<[A-Za-z][^>]*>", text.split("---")[1]):
        problems.append("block.md still has template placeholders like <id>")
    problems += [f"block.md: missing {k}" for k in sorted(KEYS - set(m))]
    if "rewrite this line" in " ".join(m.get("api", [])) or "What it shows, the options" in text:
        problems.append("block.md: write the real api lines and the text under the frontmatter (template text left)")
    if m.get("id") != folder.name:
        problems.append(f"block.md: id {m.get('id')!r} differs from the folder name {folder.name!r}")
    if folder.parent.name not in L.CATEGORIES["categories"]:
        problems.append(f"category folder {folder.parent.name!r} is not in library/categories.json")
    if m.get("kind") != "fx" or m.get("engine") != "both":
        problems.append('block.md: kind must be "fx" and engine "both"')
    if m.get("status") not in ("draft", "approved"):
        problems.append('block.md: status must be "draft" or "approved"')
    src = m.get("source") or {}
    problems += [f"block.md: source misses {k}" for k in sorted(SOURCE_KEYS - set(src))]
    if src.get("license") and src["license"] not in C.ALLOWED:
        problems.append(f"source licence {src['license']!r} is not on the allowlist")
    camel = re.sub(r"-([a-z0-9])", lambda x: x[1].upper(), folder.name)
    if not any(f"FX.{camel}" in a for a in m.get("api", [])):
        problems.append(f"api must show the call FX.{camel}(H, ...)")
    files = [folder / f for f in m.get("files", [])]
    problems += [f"missing file {f.name}" for f in files if not f.is_file()]
    if not (folder / "demo.js").is_file():
        problems.append("missing demo.js (the demo pages run it)")
    for f in [p for p in files if p.is_file()] + ([folder / "demo.js"] if (folder / "demo.js").is_file() else []):
        code = re.sub(r"//[^\n]*|/\*.*?\*/", "", f.read_text(encoding="utf-8"), flags=re.S)  # comments may name the upstream colours
        for pat, what in BANNED.items():
            if re.search(pat, code):
                problems.append(f"{f.name}: uses {what}")
        if HEX.search(code):
            problems.append(f"{f.name}: hex colour {HEX.search(code)[0]} (use var(--accent) and friends, or FX.kit.token)")
        for args in FUNC_COLOR.findall(code):
            if not NEUTRAL.match(args) and "var(" not in args:
                problems.append(f"{f.name}: colour function with fixed values ({args.strip()[:30]}): use brand variables")
                break
        if (f.suffix == ".js" and f.name != "demo.js" and MEASURE.search(code) and not re.search(r"\.layout\(|H\.drive\(", code)
                and "fx: measure-once (" not in f.read_text(encoding="utf-8")):
            problems.append(f"{f.name}: measures the page ({MEASURE.search(code)[0]}) outside FX.kit.layout(place) or H.drive: "
                            "the size can come from the fallback font")
        if f.suffix == ".css":
            bad = sorted({c for c in re.findall(r"\.(-?[_a-zA-Z][\w-]*)", code) if not c.startswith("fx-")})
            if bad:
                problems.append(f"{f.name}: class names must start with fx-: {', '.join(bad[:5])}")
    if "FX_DEMO" not in (folder / "demo.js").read_text(encoding="utf-8") if (folder / "demo.js").is_file() else False:
        problems.append("demo.js must set window.FX_DEMO = (H, stage) => {...}")
    return problems


def browser(fid: str, root: Path | None = None, times=(2.0, 0.5, 4.0, 0.5, 2.0, 0.0)) -> list[str]:
    """Run the demo in both engines; the same time must give the same picture, and the picture must change over time."""
    from playwright.sync_api import sync_playwright
    root = root or L.LIB
    folder = L._fx_dir(fid, root)
    rel = f"{folder.parent.name}/{folder.name}"
    problems = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        try:
            for engine in ("modern", "hf"):
                page = b.new_page(viewport={"width": 1920, "height": 1080})
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.on("console", lambda msg: msg.type == "error" and errors.append(msg.text))
                page.goto((root / "fx" / "_demo" / f"{engine}.html").as_uri() + f"?fx={rel}" + ("&render" if engine == "modern" else ""))
                page.wait_for_function("window.__ready === true || window.__fxReady === true || !!window.__fxError || !!window.__assetError",
                                       timeout=20000)
                err = page.evaluate("window.__fxError || window.__assetError || null")
                if err:
                    problems.append(f"{engine}: {err}")
                    page.close()
                    continue
                shots = []
                for t in times:
                    page.evaluate("t => window.__seek ? window.__seek(t) : window.__timelines.main.seek(t)" if engine == "modern"
                                  else "t => { window.__timelines.main.seek(t); }", t)
                    shots.append(hashlib.sha1(page.locator("#stage").screenshot()).hexdigest())
                if shots[0] != shots[4] or shots[1] != shots[3]:
                    problems.append(f"{engine}: the same time gives a different picture (the part depends on more than t)")
                if len(set(shots)) < 2:
                    problems.append(f"{engine}: the picture never changes")
                problems += [f"{engine}: {e}" for e in errors]
                page.close()
        finally:
            b.close()
    return problems


def stills(fid: str, root: Path | None = None, tall: bool = False, times=(0.5, 1.5, 3.0, 5.0)) -> Path:
    """A contact sheet of the demo: top row Modern kit, bottom row HyperFrames, one column per time. In library/cache/fx-stills/."""
    import io
    from PIL import Image
    from playwright.sync_api import sync_playwright
    root = root or L.LIB
    folder = L._fx_dir(fid, root)
    if folder is None:
        raise ValueError(f"no fx part {fid}")
    L._write(root / "fx" / "_demo" / "parts.js", L.fx_parts(root))
    w, h = (1080, 1920) if tall else (1920, 1080)
    tw, th = (w // 4, h // 4)
    sheet = Image.new("RGB", (tw * len(times), th * 2), "white")
    rel = f"{folder.parent.name}/{folder.name}" + ("&format=tall" if tall else "")
    with sync_playwright() as p:
        b = p.chromium.launch()
        try:
            for row, engine in enumerate(("modern", "hf")):
                page = b.new_page(viewport={"width": w, "height": h})
                page.goto((root / "fx" / "_demo" / f"{engine}.html").as_uri() + f"?fx={rel}" + ("&render" if engine == "modern" else ""))
                page.wait_for_function("window.__ready === true || window.__fxReady === true || !!window.__fxError || !!window.__assetError",
                                       timeout=20000)
                err = page.evaluate("window.__fxError || window.__assetError || null")
                if err:
                    raise ValueError(f"{engine}: {err}")
                for col, t in enumerate(times):
                    page.evaluate("t => window.__seek ? window.__seek(t) : window.__timelines.main.seek(t)" if engine == "modern"
                                  else "t => { window.__timelines.main.seek(t); }", t)
                    shot = Image.open(io.BytesIO(page.locator("#stage").screenshot())).convert("RGB").resize((tw, th))
                    sheet.paste(shot, (col * tw, row * th))
                page.close()
        finally:
            b.close()
    out = root / "cache" / "fx-stills" / f"{fid}{'-tall' if tall else ''}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=85)
    return out


def check(fid: str, root: Path | None = None, with_browser: bool = True) -> list[str]:
    problems = static(fid, root)
    if not problems and with_browser:
        root = root or L.LIB
        L._write(root / "fx" / "_demo" / "parts.js", L.fx_parts(root))  # the demo pages read it; the full index is `lib index`
        problems += browser(fid, root)
    return problems
