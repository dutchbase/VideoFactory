"""The curated Lottie shelf (library/lottie/) and the brand recolour of Lib.lottie(name, {colors: 'brand'}).

    .venv/bin/python -m unittest tests.test_lottie_brand
"""
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHELF = ROOT / "library" / "lottie"

try:
    import playwright.sync_api  # noqa: F401
    HAVE_PW = True
except ImportError:
    HAVE_PW = False


class Shelf(unittest.TestCase):
    def test_every_file_has_checked_rights(self):
        metas = sorted(SHELF.glob("*.meta.json"))
        self.assertGreaterEqual(len(metas), 40, "the curated shelf has about 45 animations")
        for m in metas:
            name = m.name[: -len(".meta.json")]
            with self.subTest(name):
                meta = json.loads(m.read_text(encoding="utf-8"))
                self.assertEqual(meta.get("license"), "Lottie-Simple")
                self.assertRegex(meta.get("page", ""), r"^https://lottiefiles\.com/free-animation/[\w-]+$")
                for k in ("creator", "title", "group"):
                    self.assertTrue(str(meta.get(k) or "").strip(), f"{k} is empty")
                self.assertTrue((SHELF / f"{name}.json").is_file())
                self.assertTrue((SHELF / f"{name}.js").is_file())
                self.assertLess((SHELF / f"{name}.json").stat().st_size, 1_000_000)

    def test_gallery_lists_every_animation(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("lottie_sheet", ROOT / "tools" / "lottie_sheet.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        text = mod.build().read_text(encoding="utf-8")
        self.assertIn("GENERATED", text.splitlines()[1])
        for m in SHELF.glob("*.meta.json"):
            self.assertIn(f'data-name="{m.name[: -len(".meta.json")]}"', text)


# Static fills and strokes, a keyframed fill, a gradient with alpha stops, a solid layer and a precomp layer.
SAMPLE = {
    "v": "5.7.0", "fr": 30, "ip": 0, "op": 30, "w": 100, "h": 100,
    "assets": [{"id": "p", "layers": [{"ty": 4, "shapes": [{"ty": "fl", "c": {"a": 0, "k": [0, 0, 1, 0.5]}}]}]}],
    "layers": [
        {"ty": 1, "sc": "#ffffff"},
        {"ty": 4, "shapes": [{"ty": "gr", "it": [
            {"ty": "fl", "c": {"a": 0, "k": [1, 1, 1, 1]}},
            {"ty": "st", "c": {"a": 0, "k": [0, 0, 0, 1]}},
            {"ty": "fl", "c": {"a": 0, "k": [0.4, 0.4, 0.4, 1]}},
            {"ty": "fl", "c": {"a": 0, "k": [1, 0.5, 0, 1]}},
            {"ty": "fl", "c": {"a": 0, "k": [0.2, 0.4, 0.9, 1]}},
            {"ty": "fl", "c": {"a": 0, "k": [0.1, 0.8, 0.4, 1]}},
            {"ty": "fl", "c": {"a": 0, "k": [0.9, 0.1, 0.1, 0.25]}},
            {"ty": "fl", "c": {"a": 0, "k": [0.05, 0.05, 0.2, 1]}},
            {"ty": "fl", "c": {"a": 1, "k": [{"t": 0, "s": [1, 0, 0, 1], "e": [0, 0.7, 0.2, 1]}, {"t": 30, "s": [0, 0.7, 0.2, 1]}]}},
            {"ty": "gf", "g": {"p": 2, "k": {"a": 0, "k": [0, 1, 1, 1, 1, 0.1, 0.5, 0.9, 0, 0.7, 1, 0.3]}}},
        ]}]},
        {"ty": 0, "refId": "p"},
    ],
}
BRAND = ["ink", "dim", "faint", "accent", "accent2", "green", "danger", "bg", "surface"]


@unittest.skipUnless(HAVE_PW, "playwright not installed (use .venv)")
class Recolour(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.tmp = tempfile.TemporaryDirectory()
        page = Path(cls.tmp.name) / "t.html"
        page.write_text(f'<!doctype html><meta charset=utf-8><script src="{(ROOT / "_runtime" / "lib.js").as_uri()}"></script>'
                        f'<script src="{(ROOT / "brands" / "videofactory" / "tokens.js").as_uri()}"></script>')
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()
        cls.pg = cls.browser.new_page()
        cls.pg.goto(page.as_uri())

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.tmp.cleanup()

    def run_js(self, body):
        return self.pg.evaluate("([data, body]) => new Function('data', body)(data)", [SAMPLE, body])

    def test_output_has_only_brand_colours(self):
        used = self.run_js("""
          const out = Lib.brandLottie(data, BrandTokens), seen = new Set();
          const hex = (v) => '#' + v.slice(0, 3).map((x) => Math.round(x * 255).toString(16).padStart(2, '0')).join('').toUpperCase();
          const walk = (n) => {
            if (Array.isArray(n)) return n.forEach(walk);
            if (!n || typeof n !== 'object') return;
            if (n.ty === 'fl' || n.ty === 'st') {
              const k = n.c.k;
              (typeof k[0] === 'object' ? k.flatMap((f) => [f.s, f.e].filter(Boolean)) : [k]).forEach((v) => seen.add(hex(v)));
            }
            if (n.ty === 'gf') for (let i = 0; i < n.g.p; i++) seen.add(hex(n.g.k.k.slice(i * 4 + 1, i * 4 + 4)));
            if (n.ty === 1) seen.add(n.sc.toUpperCase());
            Object.values(n).forEach(walk);
          };
          walk(out);
          return [...seen];""")
        allowed = set(self.pg.evaluate("(names) => names.map((n) => BrandTokens[n].toUpperCase())", BRAND))
        self.assertTrue(used)
        self.assertLessEqual(set(used), allowed)

    def test_deterministic_and_input_untouched(self):
        same, untouched = self.run_js("""
          const before = JSON.stringify(data);
          const a = Lib.brandLottie(data, BrandTokens), b = Lib.brandLottie(data, BrandTokens);
          return [JSON.stringify(a) === JSON.stringify(b), JSON.stringify(data) === before && a !== data];""")
        self.assertTrue(same)
        self.assertTrue(untouched)

    def test_mapping_rules(self):
        r = self.run_js("""
          const t = BrandTokens, out = Lib.brandLottie(data, t), hex = (v) => '#' + v.slice(0, 3).map((x) => Math.round(x * 255).toString(16).padStart(2, '0')).join('').toUpperCase();
          const it = out.layers[1].shapes[0].it, c = (i) => it[i].c.k;
          return { solid: out.layers[0].sc.toUpperCase(), white: hex(c(0)), black: hex(c(1)), mid: hex(c(2)), orange: hex(c(3)), blue: hex(c(4)),
            green: hex(c(5)), red: hex(c(6)), alpha: c(6)[3], navy: hex(c(7)), start: hex(it[8].c.k[0].s), end: hex(it[8].c.k[0].e), last: hex(it[8].c.k[1].s),
            stops: it[9].g.k.k, pre: hex(out.assets[0].layers[0].shapes[0].c.k), preAlpha: out.assets[0].layers[0].shapes[0].c.k[3],
            tok: Object.fromEntries(['ink', 'dim', 'faint', 'surface', 'accent', 'accent2', 'green', 'danger'].map((k) => [k, t[k].toUpperCase()])) };""")
        tok = r["tok"]
        self.assertEqual((r["solid"], r["white"]), (tok["ink"], tok["ink"]))
        self.assertEqual(r["black"], tok["surface"])
        self.assertEqual(r["mid"], tok["faint"])
        self.assertEqual((r["orange"], r["blue"], r["green"], r["red"]), (tok["accent"], tok["accent2"], tok["green"], tok["danger"]))
        self.assertEqual(r["alpha"], 0.25)
        self.assertEqual(r["navy"], tok["surface"])  # very dark colours join the darkest grey
        self.assertEqual((r["start"], r["end"], r["last"]), (tok["danger"], tok["green"], tok["green"]))
        self.assertEqual((r["pre"], r["preAlpha"]), (tok["accent2"], 0.5))
        self.assertEqual(len(r["stops"]), 12)
        self.assertEqual((r["stops"][0], r["stops"][4]), (0, 1))  # stop offsets stay
        self.assertEqual(r["stops"][8:], [0, 0.7, 1, 0.3])  # alpha stops stay
        self.assertNotEqual(r["stops"][1:4], r["stops"][5:8])  # two different stops stay apart

    def test_unknown_option_is_refused(self):
        msg = self.run_js("try { Lib.lottie('x', { colors: 'red' }); return ''; } catch (e) { return e.message; }")
        self.assertIn("colors must be 'brand'", msg)



if __name__ == "__main__":
    unittest.main()
