"""Every block demo runs in Chromium without page errors; blocks use brand vars only; two chats stay separate."""
import json, re, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import libcore as C

ROOT = Path(__file__).resolve().parent.parent
BLOCKS = ROOT / "library" / "blocks"
EXPECTED = {"core", "chat", "cursor", "tip", "stamp", "panel", "checklist", "end-card", "phone", "browser"}
COLOUR = re.compile(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?(?:[0-9a-fA-F]{2})?\b|\brgba?\(|\bhsla?\(")


def meta(bid):
    return C.frontmatter((BLOCKS / bid / "block.md").read_text(encoding="utf-8"))


class BlockFiles(unittest.TestCase):
    def test_expected_blocks_exist(self):
        self.assertLessEqual(EXPECTED, {p.parent.name for p in BLOCKS.glob("*/block.md")})

    def test_blocks_use_brand_vars_only(self):
        for f in list(BLOCKS.glob("*/*.css")) + list(BLOCKS.glob("*/*.js")) + list(BLOCKS.glob("*/demo*.html")):
            self.assertIsNone(COLOUR.search(f.read_text(encoding="utf-8")), f"hard colour in {f.relative_to(ROOT)}")

    def test_block_files_exist(self):
        for bid in EXPECTED:
            m = meta(bid)
            for f in m["files"]:
                self.assertTrue((BLOCKS / bid / f).is_file(), f"{bid}: {f}")
            for dep in m["depends"]:
                self.assertTrue((BLOCKS / dep / "block.md").is_file(), f"{bid} depends on missing {dep}")


class BlockDemos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop()

    def load(self, path, t):
        page = self.browser.new_page(viewport={"width": 1080, "height": 1920})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(path.as_uri())
        page.wait_for_function("!!(window.__timelines && window.__timelines.main)", timeout=10000)  # a GSAP timeline is thenable
        page.evaluate("t => { window.__timelines.main.seek(t); }", t)  # return nothing: a timeline is thenable
        return page, errors

    def test_block_demos_load(self):
        for demo in sorted(BLOCKS.glob("*/demo*.html")):
            with self.subTest(demo=demo.parent.name + "/" + demo.name):
                page, errors = self.load(demo, meta(demo.parent.name)["preview_at"])
                self.assertEqual(errors, [])
                page.close()

    def test_two_chat_instances(self):
        page, errors = self.load(BLOCKS / "chat" / "demo.html", 1.3)
        typed = page.evaluate("""() => [...document.querySelectorAll('.b-chat')].map(c =>
            [...c.querySelectorAll('.b-chat-input .b-ch')].filter(s => getComputedStyle(s).display !== 'none').map(s => s.textContent).join(''))""")
        self.assertEqual(errors, [])
        self.assertEqual(len(typed), 2)
        self.assertTrue(typed[0] and typed[1] and typed[0] != typed[1], typed)
        page.close()

    def test_browser_url_domain_only(self):
        page, errors = self.load(BLOCKS / "browser" / "demo.html", 1.0)
        self.assertEqual(errors, [])
        self.assertEqual(page.inner_text(".b-browser-url"), "chatgpt.com")  # demo url has a path and a query
        page.close()


class Gallery(unittest.TestCase):
    def test_gallery_has_card_per_block(self):
        import library as LIBR
        out = LIBR.blocks_gallery()
        html = out.read_text(encoding="utf-8")
        for e in LIBR.index():
            if e["kind"] == "block":
                self.assertIn(e["ref"], html)
                self.assertTrue((BLOCKS / e["name"] / "preview.png").is_file(), e["ref"])

    def test_studio_serves_gallery(self):
        from studio import server
        self.assertTrue(server._trusted("library/blocks/GALLERY.html"))
        self.assertTrue(server._trusted("library/blocks/chat/preview.png"))
        self.assertFalse(server._trusted("library/blocks/../../.env"))


if __name__ == "__main__":
    unittest.main()
