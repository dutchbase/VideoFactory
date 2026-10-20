"""A jump back in time must give an entrance its start state again, also when a later timeline changes the same element."""
import asyncio
import tempfile
import unittest
from pathlib import Path

from playwright.async_api import async_playwright

import anim

ROOT = Path(__file__).resolve().parent.parent
PAGE = """<!doctype html><html><body><div id="stage" data-width="320" data-height="180"><b id="box">x</b></div>
<script>window.ANIM = {meta: {duration: 8, slug: 'seek'}, cueList: [], cues: {}, words: []};</script>
<script src="GSAP"></script><script src="PLAYER"></script>
<script>
const a = P.timeline(), b = P.timeline();
a.from('#box', {opacity: 0, duration: 0.5}, 1);   // the entrance, in the first timeline (like data-in)
b.to('#box', {opacity: 0.45, duration: 0.5}, 4);  // a later change, in the second timeline (like scene.js)
</script></body></html>"""


class PlayerSeekTests(unittest.TestCase):
    def test_jump_back_restores_the_entrance_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            page_file = Path(tmp) / "index.html"
            page_file.write_text(PAGE.replace("GSAP", (ROOT / "_runtime/vendor/gsap.min.js").as_uri())
                                 .replace("PLAYER", (ROOT / "_runtime/player.js").as_uri()), encoding="utf-8")

            async def run():
                async with async_playwright() as p:
                    browser = await anim.launch_browser(p)
                    try:
                        page = await browser.new_page()
                        await page.goto(page_file.as_uri() + "?render")
                        await page.wait_for_function("window.__ready === true")
                        out = []
                        for t in (0.2, 6, 0.2):
                            await page.evaluate(f"window.__seek({t})")
                            out.append(await page.evaluate("getComputedStyle(document.getElementById('box')).opacity"))
                        return out
                    finally:
                        await browser.close()

            self.assertEqual(asyncio.run(run()), ["0", "0.45", "0"])


if __name__ == "__main__":
    unittest.main()
