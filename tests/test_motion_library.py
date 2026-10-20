import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools import motion

PACK = ROOT / "brands/videofactory/library/motion"
BG = "rgb(11, 11, 16)"


class MotionLibrary(unittest.TestCase):
    def setUp(self):
        motion.select_brand("videofactory")

    def test_pack_is_complete_english_and_offline(self):
        self.assertEqual(motion.MANIFEST["brand"], "VideoFactory")
        self.assertEqual(len(motion.ASSETS), 89)
        # (host, residue) pairs that must never come back: CDN loads, the old light palette, old brand and Dutch UI strings.
        banned = ["fonts.googleapis.com", "fonts.gstatic.com", "unpkg.com", "#F4F2EC", "#EBE6D8", "#FF4D1C",
                  "Slimmer met AI", "slimmermetai", "Kopieer", "Uren admin"]
        for asset in motion.ASSETS.values():
            text = (PACK / asset["file"]).read_text()
            self.assertIn('lang="en"', text, asset["id"])
            self.assertIn("_runtime/fonts/fonts.css", text, asset["id"])
            for residue in banned:
                self.assertNotIn(residue, text, (asset["id"], residue))
            # The only absolute URLs allowed are XML namespaces.
            self.assertEqual([u for u in re.findall(r"https?://[^\s\"'<>)]+", text) if "www.w3.org" not in u], [], asset["id"])
            self.assertTrue(asset["name"].isascii() or "·" in asset["name"] or "→" in asset["name"], asset["id"])

    def test_motion_css_mirrors_brand_tokens(self):
        tokens = (ROOT / "brands/videofactory/tokens.js").read_text()
        css = (PACK / "motion.css").read_text()
        for name in ["bg", "surface", "raised", "ink", "dim", "faint", "line", "accent", "accent2", "green"]:
            value = re.search(rf"^\s*{name}: '(#[0-9A-Fa-f]{{6}})'", tokens, re.M).group(1)
            self.assertRegex(css, re.compile(rf"--vf-{name}:{re.escape(value)}", re.I), name)

    def test_bundled_runtime_matches_its_recorded_integrity(self):
        vendor = PACK / "vendor"
        sources = json.loads((vendor / "SOURCES.json").read_text())
        self.assertEqual({s["file"] for s in sources}, {"react.production.min.js", "react-dom.production.min.js"})
        for source in sources:
            actual = base64.b64encode(hashlib.sha384((vendor / source["file"]).read_bytes()).digest()).decode()
            self.assertEqual("sha384-" + actual, source["integrity"], source["file"])
        self.assertTrue((vendor / "LICENSE").is_file())

    def test_brand_selection_and_batch_ids(self):
        self.assertIn("videofactory", motion.motion_brands())
        ids, formats = motion.pick(argparse.Namespace(id="CAP-01,CAP-02,CAP-01", format="all"))
        self.assertEqual(ids, ["CAP-01", "CAP-02"])
        self.assertEqual(formats, ["16:9", "9:16", "1:1"])
        self.assertEqual(motion.default_output("videofactory"), ROOT / "library/cache/motion")
        with self.assertRaises(ValueError):
            motion.select_brand("../videofactory")
        with self.assertRaises(SystemExit):
            motion.pick(argparse.Namespace(id="MISSING", format="9:16"))

    def test_http_only_exposes_pack_and_allowlisted_shared_files(self):
        server = motion.start_server(0)
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            for path in ["/manifest.json", "/vendor/react.production.min.js", "/brands/videofactory/tokens.js", "/_runtime/fonts/fonts.css"]:
                with urlopen(base + path) as response:
                    self.assertEqual(response.status, 200, path)
            for path in ["/.env", "/_auth/", "/brands/videofactory/brand.md", "/_runtime/fonts/../../../.env", "/"]:
                with self.assertRaises(HTTPError, msg=path):
                    urlopen(base + path)
        finally:
            server.shutdown()
            server.server_close()


class MotionPreview(unittest.TestCase):
    """Browser regression checks: run through omabox, like the other browser tests."""

    def setUp(self):
        motion.select_brand("videofactory")
        self.original_port = motion.PORT
        self.server = motion.start_server(0)
        motion.PORT = self.server.server_port
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.server.shutdown()
        self.server.server_close()
        motion.PORT = self.original_port

    def test_stage_is_dark_branded_and_offline_in_all_formats(self):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for ident in ["DEV-01", "TYP-06", "AIM-05", "B2B-02"]:
                for fmt in motion.FORMATS:
                    page = motion.open_stage(browser, motion.ASSETS[ident], fmt, 6)
                    foreign = []
                    page.on("request", lambda r: foreign.append(r.url) if not r.url.startswith(("http://127.0.0.1", "data:", "blob:")) else None)
                    page.evaluate("window.smai.seek(3.5)")
                    self.assertEqual(page.locator("[data-stage]").evaluate("e=>getComputedStyle(e).backgroundColor"), BG, (ident, fmt))
                    for font in ["700 16px Archivo", "400 16px Inter", "500 16px 'JetBrains Mono'"]:
                        self.assertTrue(page.evaluate("f=>document.fonts.check(f)", font), (ident, fmt, font))
                    self.assertEqual(foreign, [], (ident, fmt))
                    page.close()
            browser.close()

    def test_transparent_overlay_has_clear_background(self):
        from PIL import Image
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = motion.open_stage(browser, motion.ASSETS["CAP-01"], "9:16", 6, transparent=True)
            page.evaluate("window.smai.seek(3.5)")
            im = Image.open(io.BytesIO(page.screenshot(omit_background=True))).convert("RGBA")
            self.assertEqual(im.getpixel((2, 2))[3], 0)
            self.assertGreater(im.getextrema()[3][1], 200, "caption is visible")
            browser.close()

    def test_text_in_ink_colour_is_readable_on_the_dark_stage(self):
        from playwright.sync_api import sync_playwright
        def luminance(rgb):
            c = [v / 255 for v in rgb]
            c = [v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4 for v in c]
            return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = motion.open_stage(browser, motion.ASSETS["TYP-06"], "1:1", 6)
            page.evaluate("window.smai.seek(3.5)")
            colours = page.evaluate('''() => [...document.querySelectorAll("[data-stage] *")]
                .filter(e => e.children.length === 0 && e.textContent.trim() && getComputedStyle(e).opacity !== "0")
                .map(e => getComputedStyle(e).color)''')
            self.assertTrue(colours)
            bg = luminance((11, 11, 16))
            for colour in colours:
                rgb = [int(v) for v in re.findall(r"\d+", colour)[:3]]
                self.assertGreaterEqual((luminance(rgb) + .05) / (bg + .05), 4.5, colour)
            browser.close()

    def test_render_can_run_while_gallery_is_open(self):
        gallery = motion.start_server(8791)
        try:
            with tempfile.TemporaryDirectory() as out:
                result = subprocess.run([sys.executable, str(ROOT / "tools/motion.py"), "render", "--brand", "videofactory",
                                         "--id", "BRD-01", "--dur", "1", "--fps", "1", "--jobs", "1", "--outDir", out],
                                        capture_output=True, text=True, timeout=60)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue((Path(out) / "BRD-01_9x16_1s.mp4").exists())
        finally:
            gallery.shutdown()
            gallery.server_close()


if __name__ == "__main__":
    unittest.main()
