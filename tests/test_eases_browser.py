"""Measured eases (_shared/motion.md): same curve in the canvas player (P.ease) and the HyperFrames bridge (window.Eases)."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMES = ("crashIn", "whip", "softLand", "accelExit")
SETUP = ("window.ANIM = {meta: {duration: 1}, cueList: [], cues: {}, words: []};"
         "window.BrandTokens = {ink: '#111', ramp: ['#000', '#111', '#222', '#333', '#444', '#555', '#666', '#777'],"
         " dim: '#888', line: '#999', green: '#0a0', font: 'sans-serif', head: 'sans-serif'};")


class Eases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()
        cls.page = cls.browser.new_page()
        cls.page.set_content('<div id="stage" data-width="1920" data-height="1080"></div>')
        cls.page.add_script_tag(content=SETUP)
        for f in ("player.js", "hf-bridge.js"):
            cls.page.add_script_tag(path=str(ROOT / "_runtime" / f))

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def sample(self, obj, name, xs):
        return self.page.evaluate(f"xs => xs.map(x => {obj}[{name!r}](x))", xs)

    def test_endpoints_and_clamp(self):
        for obj in ("P.ease", "Eases"):
            for n in NAMES:
                self.assertEqual(self.sample(obj, n, [-0.5, 0, 1, 1.5]), [0, 0, 1, 1], f"{obj}.{n}")

    def test_shapes(self):
        xs = [i / 100 for i in range(101)]
        self.assertGreater(max(self.sample("P.ease", "crashIn", xs)), 1.1)  # passes its mark
        self.assertLess(self.sample("P.ease", "accelExit", [0.5])[0], 0.5)  # accelerates away
        self.assertGreater(self.sample("P.ease", "whip", [0.5])[0], 0.5)  # decelerates
        self.assertGreater(self.sample("P.ease", "softLand", [0.5])[0], 0.5)

    def test_engines_match(self):  # Review Focus 5
        xs = [0.1, 0.5, 0.9]
        for n in NAMES:
            for a, b in zip(self.sample("P.ease", n, xs), self.sample("Eases", n, xs)):
                self.assertAlmostEqual(a, b, places=12, msg=n)


if __name__ == "__main__":
    unittest.main()
