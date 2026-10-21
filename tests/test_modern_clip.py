"""Modern.clip plays frame folders on the scene clock; o.from skips into the clip and o.speed scales the clock."""
import asyncio
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from playwright.async_api import async_playwright

import anim

ROOT = Path(__file__).resolve().parent.parent
PAGE = """<!doctype html><html><body><div id="stage" data-width="320" data-height="180">
<div id="plain"></div><div id="skip"></div><div id="fast"></div></div>
<script>window.ANIM = {meta: {duration: 8, slug: 'clip'}, cueList: [], cues: {}, words: []};
window.REAL = {clips: {demo: {n: 4, fps: 1}}};
window.drawn = {};  // last frame file drawn on each canvas
const draw = CanvasRenderingContext2D.prototype.drawImage;
CanvasRenderingContext2D.prototype.drawImage = function (im, ...rest) {
  window.drawn[this.canvas.parentElement.id] = im.src.split('/').pop(); return draw.call(this, im, ...rest); };
</script>
<script src="GSAP"></script><script src="PLAYER"></script><script src="ICONS"></script><script src="MODERN"></script>
<script>
Modern.clip('#plain', 'demo', 0);
Modern.clip('#skip', 'demo', 0, { from: 2 });
Modern.clip('#fast', 'demo', 0, { speed: 2, from: 1 });
</script></body></html>"""


class ModernClipTests(unittest.TestCase):
    def test_from_and_speed_pick_the_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            frames = Path(tmp) / "assets/demo"
            frames.mkdir(parents=True)
            for i, colour in enumerate(("red", "green", "blue", "white"), 1):
                Image.new("RGB", (4, 4), colour).save(frames / f"f{i:03d}.jpg")
            page_file = Path(tmp) / "index.html"
            page = PAGE
            for key, name in (("GSAP", "vendor/gsap.min.js"), ("PLAYER", "player.js"), ("ICONS", "icons.js"), ("MODERN", "modern.js")):
                page = page.replace(f'"{key}"', f'"{(ROOT / "_runtime" / name).as_uri()}"')
            page_file.write_text(page, encoding="utf-8")

            async def run():
                async with async_playwright() as p:
                    browser = await anim.launch_browser(p)
                    try:
                        tab = await browser.new_page()
                        await tab.goto(page_file.as_uri() + "?render")
                        await tab.wait_for_function("window.__ready === true")
                        await tab.evaluate("window.__seek(0.5)")
                        return await tab.evaluate("window.drawn")
                    finally:
                        await browser.close()

            # t = 0.5: plain is in second 0 (f001); from 2 is in second 2 (f003); speed 2 + from 1 is in second 2 (f003)
            self.assertEqual(asyncio.run(run()), {"plain": "f001.jpg", "skip": "f003.jpg", "fast": "f003.jpg"})


if __name__ == "__main__":
    unittest.main()
