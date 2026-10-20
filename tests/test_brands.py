import json
import shutil
import subprocess
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import check  # noqa: E402


def new(slug, *extra):
    return subprocess.run([sys.executable, "anim.py", "new", slug, *extra], cwd=ROOT, capture_output=True, text=True)


class NewBrandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brand = ROOT / "brands" / "_test"
        cls.brand.mkdir()
        (cls.brand / "tokens.js").write_text(
            (ROOT / "brands/videofactory/tokens.js").read_text(encoding="utf-8").replace("id: 'videofactory'", "id: '_test'"), encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.brand, ignore_errors=True)
        try:
            (ROOT / "videos" / "_test").rmdir()  # the folder `anim.py new` made for the test brand
        except OSError:
            pass

    def slug(self):
        slug = "zz-brand-test-" + uuid.uuid4().hex[:8]
        self.addCleanup(shutil.rmtree, ROOT / "videos" / "_test" / slug, ignore_errors=True)
        return slug

    def test_new_with_brand(self):
        slug = self.slug()
        r = new(slug, "--brand", "_test", "--style", "modern")
        self.assertEqual(r.returncode, 0, r.stderr)
        v = ROOT / "videos" / "_test" / slug
        meta = json.loads((v / "project.json").read_text())
        self.assertEqual((meta["brand"], meta["style"]), ("_test", "modern"))
        html = (v / "04_scene/index.html").read_text()
        self.assertEqual((v / "04_scene/brand").resolve(), ROOT / "brands" / "_test")  # the scene links the brand folder
        self.assertIn("brand/tokens.js", html)
        self.assertNotIn("{{BRAND}}", html)
        self.assertLess(html.index("brand/tokens.js"), html.index("runtime/player.js"))

    def test_brand_is_required(self):
        slug = self.slug()
        self.assertNotEqual(new(slug).returncode, 0)

    def test_unknown_brand_dies(self):
        slug = self.slug()
        r = new(slug, "--brand", "nope")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("videofactory", r.stderr + r.stdout)  # the error lists the known brands
        self.assertFalse((ROOT / "videos" / "_test" / slug).exists())

    def test_path_trick_brand_dies(self):
        slug = self.slug()
        self.assertNotEqual(new(slug, "--brand", "../brands/videofactory").returncode, 0)
        self.assertFalse((ROOT / "videos" / "_test" / slug).exists())

    def test_unknown_style_dies(self):
        slug = self.slug()
        self.assertNotEqual(new(slug, "--style", "nope", "--brand", "_test").returncode, 0)
        self.assertFalse((ROOT / "videos" / "_test" / slug).exists())


class BrandCheckTests(unittest.TestCase):
    def setUp(self):
        self.dir = ROOT / "brands" / "_test"
        self.dir.mkdir()
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.house = (ROOT / "brands/videofactory/tokens.js").read_text(encoding="utf-8").replace("id: 'videofactory'", "id: '_test'")

    def run_check(self, text=None):
        if text is not None:
            (self.dir / "tokens.js").write_text(text, encoding="utf-8")
        return check.brand_counters(ROOT, "_test")

    def test_house_brand_all_zero(self):
        self.assertEqual(check.brand_counters(ROOT, "videofactory"), {k: 0 for k in check.BRAND_KEYS})

    def test_missing(self):
        self.assertEqual(self.run_check()["brand missing"], 1)

    def test_good_copy_is_zero(self):
        self.assertEqual(self.run_check(self.house), {k: 0 for k in check.BRAND_KEYS})

    def test_bad_font(self):
        r = self.run_check(self.house.replace('font: \'"Inter"', 'font: \'"Nope Sans"'))
        self.assertEqual(r["brand font unlicensed"], 1)
        r = self.run_check(self.house.replace('head: \'"Archivo"', 'head: \'"Nope Serif"'))
        self.assertEqual(r["brand font unlicensed"], 1)

    def test_generic_font_ignored(self):
        r = self.run_check(self.house.replace('font: \'"Inter", system-ui, sans-serif\'', "font: 'system-ui, sans-serif'"))
        self.assertEqual(r["brand font unlicensed"], 0)

    def test_low_contrast(self):
        r = self.run_check(self.house.replace("'#F5F2EA'", "'#2A2A2A'"))
        self.assertEqual(r["brand contrast"], 1)

    def test_grads_must_be_five_pairs(self):
        r = self.run_check(self.house.replace(",['#FF4D8D','#FF9A6B']", ""))
        self.assertEqual(r["brand grads"], 1)


if __name__ == "__main__":
    unittest.main()
