#!/usr/bin/env python3
"""Branded motion libraries: serve, render (mp4 / alpha), contact sheet.

    .venv/bin/python tools/motion.py serve
    .venv/bin/python tools/motion.py render --id AIM-05 --format 9:16 [--dur 6] [--transparent] [--no-out] [--img URL|FILE]
    .venv/bin/python tools/motion.py render --brand videofactory --id TYP-01 --page videos/<slug>/04_scene/motion/TYP-01.dc.html --outDir ...
    .venv/bin/python tools/motion.py sheet
Pass --brand <name> on any command to pick a motion pack. The default is videofactory.
Time is driven through window.smai.seek. Docs: brands/<brand>/library/motion/CONTEXT.md.
"""
from __future__ import annotations

import argparse, base64, functools, http.server, json, subprocess, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "brands" / "videofactory" / "library" / "motion"
PORT = 8791
MANIFEST = json.loads((LIB / "manifest.json").read_text())
ASSETS = {a["id"]: a for a in MANIFEST["assets"]}
FORMATS = ["16:9", "9:16", "1:1"]


def motion_brands():
    return {p.parents[2].name for p in (ROOT / "brands").glob("*/library/motion/manifest.json")} | {p.parent.name for p in (ROOT / "library/motion").glob("*/manifest.json")}


def select_brand(brand: str):
    global LIB, MANIFEST, ASSETS
    if brand not in motion_brands():
        raise ValueError(f"unknown motion brand: {brand}")
    owned = ROOT / "brands" / brand / "library/motion"
    LIB = owned if owned.is_dir() else ROOT / "library/motion" / brand
    MANIFEST = json.loads((LIB / "manifest.json").read_text())
    ASSETS = {a["id"]: a for a in MANIFEST["assets"]}


def default_output(brand: str) -> Path:
    base = ROOT / "library/cache/motion"
    return base if brand == "videofactory" else base / brand

# Replaces image-slot.js at render time (original stays intact): a plain cover image in a shadow root,
# so the page framework sees no foreign children.
IMG_SLOT_JS = """if (!customElements.get('image-slot')) customElements.define('image-slot', class extends HTMLElement {
  connectedCallback() { this.attachShadow({mode: 'open'}).innerHTML = '<img src="%s" style="position:absolute;inset:0;width:100%%;height:100%%;object-fit:cover;">'; }
});"""


def start_server(port: int = PORT) -> http.server.ThreadingHTTPServer:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
        def translate_path(self, path):
            rel = unquote(urlsplit(path).path).lstrip("/")
            # Besides the pack itself: the local brand fonts and the brand token file. Nothing else leaves the pack.
            shared = {"brands/videofactory/tokens.js"}
            target = (ROOT / rel).resolve()
            if rel in shared or (rel.startswith("_runtime/fonts/") and target.is_relative_to(ROOT / "_runtime/fonts")):
                return str(target)
            return super().translate_path(path)
        def list_directory(self, path):
            self.send_error(403, "Directory listing disabled")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Quiet, directory=str(LIB)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def open_stage(browser, asset: dict, fmt: str, dur: float, transparent=False, out=True, img=None, page_file=None):
    w, h = asset["formats"][fmt]
    page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    if page_file:
        # An edited copy of the asset page, served at the asset's own URL so its relative pack scripts still load.
        page.route(lambda url: urlsplit(url).path == f"/{asset['file']}", lambda r: r.fulfill(path=str(page_file), content_type="text/html"))
    if img and Path(img).is_file():
        page.route("**/__slot-image", lambda r: r.fulfill(path=str(img)))
        img = "/__slot-image"
    if img:
        page.route("**/image-slot.js", lambda r: r.fulfill(body=IMG_SLOT_JS % img, content_type="text/javascript"))
    q = f"format={fmt}&dur={dur}&clean=1" + ("&transparent=1" if transparent else "") + ("" if out else "&out=0")
    page.goto(f"http://127.0.0.1:{PORT}/{asset['file']}?{q}")
    page.wait_for_function("window.smai !== undefined")
    page.evaluate("window.smai.ready")
    # Local brand fonts load lazily: ask for the weights the pack uses before the first frame.
    page.evaluate('''async () => {
        await Promise.all(['400 16px Archivo', '500 16px Archivo', '700 16px Archivo', '900 16px Archivo',
                           '400 16px "JetBrains Mono"', '500 16px "JetBrains Mono"', '700 16px "JetBrains Mono"',
                           '400 16px Inter', '700 16px Inter'].map(font => document.fonts.load(font)));
    }''')
    page.evaluate("async () => { await document.fonts.ready; await Promise.all([...document.images].map(i => i.decode())); }")
    page.evaluate("window.smai.seek(0)")
    if errors:
        page.close()
        raise RuntimeError("; ".join(errors))
    return page


def render(browser, asset, fmt, dur, fps, out_dir, transparent=False, out=True, img=None, page_file=None) -> Path:
    page = open_stage(browser, asset, fmt, dur, transparent, out, img, page_file)
    capture = page.context.new_cdp_session(page)
    if transparent:
        capture.send("Emulation.setDefaultBackgroundColorOverride", {"color": {"r": 0, "g": 0, "b": 0, "a": 0}})
    stem = f"{asset['id']}_{fmt.replace(':', 'x')}_{dur:g}s" + ("_alpha" if transparent else "")
    out_dir.mkdir(parents=True, exist_ok=True)
    if transparent:
        enc = ["-c:v", "prores_ks", "-threads", "2", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(out_dir / f"{stem}.mov"),
               "-c:v", "libvpx-vp9", "-threads", "2", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "30", str(out_dir / f"{stem}.webm")]
        target = out_dir / f"{stem}.webm"
    else:
        target = out_dir / f"{stem}.mp4"
        enc = ["-c:v", "libx264", "-threads", "2", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart",
               "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", str(target)]
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-threads", "1", "-f", "image2pipe", "-framerate", str(fps), "-i", "-", *enc],
                          stdin=subprocess.PIPE)
    try:
        for i in range(round(dur * fps)):
            page.evaluate("t => window.smai.seek(t)", i / fps)
            shot = capture.send("Page.captureScreenshot", {"format": "png", "optimizeForSpeed": True, "captureBeyondViewport": False})
            ff.stdin.write(base64.b64decode(shot["data"]))
    finally:
        ff.stdin.close()
        code = ff.wait()
        page.close()
    if code:
        raise RuntimeError("ffmpeg failed")
    return target


def pick(a):
    ids = list(ASSETS) if a.id == "all" else list(dict.fromkeys(a.id.split(",")))
    unknown = [i for i in ids if i not in ASSETS]
    if unknown:
        sys.exit(f"unknown id: {unknown}")
    return ids, (FORMATS if a.format == "all" else [a.format])


def cmd_render(a):
    global PORT
    ids, fmts = pick(a)
    jobs = [(i, f) for i in ids for f in fmts]
    server = start_server(0)
    PORT = server.server_port
    failed = []
    def run(job):
        # One browser per worker: Playwright sync objects are not thread-safe.
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            try:
                dur = a.dur or ASSETS[job[0]]["defaultDuration"]
                t = render(b, ASSETS[job[0]], job[1], dur, a.fps, Path(a.outDir), a.transparent, not a.no_out, a.img, a.page)
                print("ok  ", t, flush=True)
            except Exception as e:
                failed.append(job); print("FAIL", job, e, flush=True)
            finally:
                b.close()
    try:
        with ThreadPoolExecutor(a.jobs) as ex:
            list(ex.map(run, jobs))
    finally:
        server.shutdown()
        server.server_close()
    if failed:
        sys.exit(f"{len(failed)} failed: {failed}")


def cmd_sheet(a):
    global PORT
    from PIL import Image
    server = start_server(0)
    PORT = server.server_port
    out = Path(a.outDir); out.mkdir(parents=True, exist_ok=True)
    cell = 240
    tiles = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for asset in ASSETS.values():
            for f in FORMATS:
                try:
                    page = open_stage(b, asset, f, 6)
                    page.evaluate("window.smai.seek(3.0)")
                    path = out / "_t.png"; page.screenshot(path=str(path)); page.close()
                    im = Image.open(path).convert("RGB"); im.thumbnail((cell, cell)); tiles[(asset["id"], f)] = im.copy()
                except Exception as e:
                    print("FAIL", asset["id"], f, e, flush=True)
        b.close()
    (out / "_t.png").unlink(missing_ok=True)
    cols = 3 * 4  # four assets per row, three formats each
    rows = -(-len(ASSETS) // 4)
    sheet = Image.new("RGB", (cols * cell, rows * cell), (11, 11, 16))
    for n, asset in enumerate(ASSETS.values()):
        for k, f in enumerate(FORMATS):
            if (asset["id"], f) in tiles:
                sheet.paste(tiles[(asset["id"], f)], (((n % 4) * 3 + k) * cell, (n // 4) * cell))
    sheet.save(out / "contact-sheet.png")
    server.shutdown()
    server.server_close()
    print(out / "contact-sheet.png", f"({len(tiles)}/{len(ASSETS) * 3} stages)")


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--brand", default="videofactory", choices=sorted(motion_brands()))
    sub.add_parser("serve", parents=[common])
    r = sub.add_parser("render", parents=[common])
    r.add_argument("--id", required=True, help="asset ID, comma-separated IDs, or all")
    r.add_argument("--format", default="9:16", choices=[*FORMATS, "all"])
    r.add_argument("--dur", type=float); r.add_argument("--fps", type=int, default=30)
    r.add_argument("--transparent", action="store_true"); r.add_argument("--no-out", action="store_true")
    r.add_argument("--img", help="URL or local image file for image-slot assets (DEV-04, DEV-05, B2B-02, UTL-05)")
    r.add_argument("--page", type=Path, help="edited copy of the asset page to render instead (one --id only)")
    r.add_argument("--jobs", type=int, default=2); r.add_argument("--outDir")
    s = sub.add_parser("sheet", parents=[common]); s.add_argument("--outDir")
    a = ap.parse_args()
    select_brand(a.brand)
    if a.cmd != "serve":
        a.outDir = a.outDir or str(default_output(a.brand))
    if a.cmd == "render" and ((a.dur is not None and not 1 <= a.dur <= 60) or a.fps < 1 or a.jobs < 1):
        ap.error("duration must be 1–60 seconds; fps and jobs must be positive")
    if a.cmd == "render" and a.page and ("," in a.id or a.id == "all" or not a.page.is_file()):
        ap.error("--page needs one --id and an existing file")
    if a.cmd == "serve":
        start_server(); print(f"http://127.0.0.1:{PORT}/Index.dc.html"); threading.Event().wait()
    elif a.cmd == "render": cmd_render(a)
    else: cmd_sheet(a)


if __name__ == "__main__":
    main()
