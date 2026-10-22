"""Brand images: the size catalog, job folders, permission scope, the brief and final reviews, the AI picture purpose."""
import base64
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import anim
from studio import images
from studio import workspace as ws
from studio.creative import creative_review_state, decide_creative, mark_creative_ready
from studio.generation import approve_generation, prepare_generation, register_generated_outputs
from studio.permissions import _scope_path, grant

ROOT = Path(__file__).resolve().parents[1]
MAX_AGE_DAYS = 400  # a size row older than this needs a fresh check against the platform's help page


class SizeCatalogTests(unittest.TestCase):
    def test_catalog_loads_and_covers_the_common_platforms(self):
        catalog = images.load_sizes(ROOT)
        platforms = {row["platform"] for row in catalog["sizes"].values()}
        self.assertLessEqual({"Instagram", "Facebook", "LinkedIn", "X", "YouTube", "TikTok", "Pinterest"}, platforms)
        for ident in ("instagram-square", "instagram-portrait", "instagram-story", "linkedin-banner", "youtube-thumbnail",
                      "youtube-banner", "x-header", "web-og"):
            self.assertIn(ident, catalog["sizes"])
        self.assertEqual((catalog["sizes"]["linkedin-banner"]["w"], catalog["sizes"]["linkedin-banner"]["h"]), (1584, 396))
        self.assertEqual(catalog["sizes"]["youtube-thumbnail"]["ratio"], "16:9")
        for name in ("profile-all", "story-all", "banner-all", "feed-all", "instagram-all", "linkedin-all"):
            self.assertIn(name, catalog["sets"])

    def test_rows_are_recent_and_sourced(self):
        for row in images.load_sizes(ROOT)["sizes"].values():
            with self.subTest(size=row["id"]):
                self.assertTrue(row["source_url"].startswith("https://"))
                self.assertLess(images.checked_age_days(row), MAX_AGE_DAYS, "check this size against the platform again")

    def test_layout_classes(self):
        sizes = images.load_sizes(ROOT)["sizes"]
        self.assertEqual(sizes["instagram-profile"]["class"], "is-avatar")
        self.assertEqual(sizes["linkedin-company-logo"]["class"], "is-avatar")
        self.assertEqual(sizes["linkedin-banner"]["class"], "is-banner")
        self.assertEqual(sizes["youtube-banner"]["class"], "is-banner")  # the class follows the safe area, not the canvas
        self.assertEqual(sizes["instagram-square"]["class"], "is-square")
        self.assertEqual(sizes["pinterest-pin"]["class"], "is-portrait")
        self.assertEqual(images.ratio_class(1080, 1920), "is-tall")
        self.assertEqual(images.ratio_class(1200, 630), "is-wide")

    def test_sets_expand_in_order_without_repeats(self):
        rows = images.resolve_sizes(ROOT, "instagram-square, instagram-all")
        ids = [r["id"] for r in rows]
        self.assertEqual(ids[0], "instagram-square")
        self.assertEqual(len(ids), len(set(ids)))
        with self.assertRaises(images.ImageError):
            images.resolve_sizes(ROOT, "instagram-squared")

    def test_brief_words_ignore_bullets_and_comments(self):
        text = "- linkedin-banner - for the profile\n* x-header\n<!-- web-og -->\nprofile-all # every avatar"
        self.assertEqual(images.split_words(text), ["linkedin-banner", "x-header", "profile-all"])

    def test_bad_rows_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "_shared").mkdir()
            row = {"id": "a-b", "platform": "P", "use": "u", "w": 100, "h": 100, "shape": "rect",
                   "safe": {"top": 60, "right": 0, "bottom": 60, "left": 0}, "source_url": "https://x", "checked": "2026-01-01"}
            (root / images.SIZES_FILE).write_text(json.dumps({"sizes": [row], "sets": {}}))
            with self.assertRaises(images.ImageError):
                images.load_sizes(root)


class ImageJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "_shared").mkdir()
        shutil.copy(ROOT / images.SIZES_FILE, self.root / images.SIZES_FILE)
        brand = self.root / "brands/house"
        brand.mkdir(parents=True)
        (brand / "tokens.js").write_text("window.BrandTokens = {\n  id: 'house',\n};\n")
        env = patch.dict("os.environ", {"VF_SESSION_ID": "chat-one"})
        env.start()
        self.addCleanup(env.stop)
        root_patch = patch.object(anim, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)

    def command(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            anim._dispatch(anim.build_parser().parse_args(list(args)))
        return output.getvalue()

    def fill_brief(self):
        brief = self.root / "images/house/launch/01_brief/brief.md"
        text = brief.read_text().replace("<!-- One sentence", "People learn the product exists.\n<!-- One")
        brief.write_text(text.replace("<!-- The exact words", "Make videos from your voice\n<!-- The"))

    def pass_brief(self):
        state = creative_review_state(self.root, "image", "house/launch", "brief")
        mark_creative_ready(self.root, "image", "house/launch", "brief", state["fingerprint"])
        decide_creative(self.root, "image", "house/launch", "brief", "approved", "Reviewer", "", state["fingerprint"])

    def test_scope_path_and_bad_names(self):
        self.assertEqual(_scope_path(self.root, "image:house/launch"), self.root.resolve() / "images/house/.permissions/launch.json")
        for bad in ("image:house", "image:House/launch", "image:house/../x", "image:house/a/b"):
            with self.subTest(scope=bad), self.assertRaises(ValueError):
                _scope_path(self.root, bad)

    def test_new_needs_permission_and_a_known_brand(self):
        with self.assertRaises(ValueError):
            self.command("image", "new", "launch", "--brand", "house")
        grant(self.root, "image:house/launch", "full")
        grant(self.root, "image:nobrand/launch", "full")
        with self.assertRaises(SystemExit):
            self.command("image", "new", "launch", "--brand", "nobrand")
        output = self.command("image", "new", "launch", "--brand", "house", "--sizes", "linkedin-banner,profile-all", "--title", "A <b> title")
        self.assertIn("images/house/launch", output)
        job = self.root / "images/house/launch"
        self.assertEqual(json.loads((job / "project.json").read_text()), {"brand": "house", "kind": "image", "title": "A <b> title"})
        self.assertIn("- linkedin-banner\n- instagram-profile", (job / "01_brief/brief.md").read_text())
        self.assertIn("A &lt;b&gt; title", (job / "02_design/design.html").read_text())
        for link, target in (("brand", "brands/house"), ("runtime", "_runtime"), ("library", "library")):
            self.assertTrue((job / "02_design" / link).is_symlink())
            self.assertEqual((job / "02_design" / link).resolve(), (self.root / target).resolve())
        with self.assertRaises(SystemExit):
            self.command("image", "new", "launch", "--brand", "house")

    def test_brief_review_blocks_export_until_passed(self):
        grant(self.root, "image:house/launch", "each-stage")
        self.command("image", "new", "launch", "--brand", "house", "--sizes", "web-og")
        state = creative_review_state(self.root, "image", "house/launch", "brief")
        self.assertFalse(state["ready"])
        self.assertIn("brief section 'Message'", state["missing"])
        with self.assertRaises(ValueError):
            self.command("image", "export", "house/launch")
        self.fill_brief()
        state = creative_review_state(self.root, "image", "house/launch", "brief")
        self.assertTrue(state["ready"], state["missing"])
        mark_creative_ready(self.root, "image", "house/launch", "brief", state["fingerprint"])
        output = self.command("image", "review", "house/launch", "brief", "--approve", "--reviewer", "Ann", "--expected", state["fingerprint"])
        self.assertIn("brief: approved", output)
        brief = self.root / "images/house/launch/01_brief/brief.md"
        brief.write_text(brief.read_text() + "\nAn edit.\n")
        self.assertEqual(creative_review_state(self.root, "image", "house/launch", "brief")["state"], "stale")

    def test_unknown_size_in_brief_is_missing(self):
        grant(self.root, "image:house/launch", "full")
        self.command("image", "new", "launch", "--brand", "house", "--sizes", "web-og")
        self.fill_brief()
        brief = self.root / "images/house/launch/01_brief/brief.md"
        brief.write_text(brief.read_text().replace("- web-og", "- web-ogg"))
        self.assertTrue(any("web-ogg" in m for m in creative_review_state(self.root, "image", "house/launch", "brief")["missing"]))

    def test_final_gate_needs_a_current_clean_report(self):
        grant(self.root, "image:house/launch", "full")
        self.command("image", "new", "launch", "--brand", "house", "--sizes", "web-og")
        self.fill_brief()
        self.pass_brief()
        job = self.root / "images/house/launch"
        self.assertIn("exported images (python anim.py image export)", creative_review_state(self.root, "image", "house/launch", "final")["missing"])
        png = job / "03_export/web-og.png"
        Image.new("RGB", (1200, 630), "black").save(png)
        row = images.load_sizes(self.root)["sizes"]["web-og"]
        result = images.size_result(row, png, {"problems": [], "warnings": [], "texts": []}, [])
        report = images.write_report(job, [result], partial=False)
        self.assertTrue(report["ok"])
        self.assertTrue(creative_review_state(self.root, "image", "house/launch", "final")["ready"])
        (job / "02_design/design.js").write_text("// changed\n")
        self.assertIn("a new export: the design changed after the last export",
                      creative_review_state(self.root, "image", "house/launch", "final")["missing"])
        Image.new("RGB", (100, 100), "black").save(png)
        wrong = images.size_result(row, png, {"problems": [], "warnings": [], "texts": []}, [])
        self.assertIn("image is 100x100, not 1200x630", wrong["problems"])
        self.assertFalse(images.write_report(job, [wrong], partial=False)["ok"])

    def test_status_lists_jobs(self):
        grant(self.root, "image:house/launch", "full")
        self.command("image", "new", "launch", "--brand", "house", "--sizes", "web-og")
        output = self.command("image", "status")
        self.assertIn("house/launch", output)
        self.assertIn("draft", output)

    def test_own_picture_is_copied_and_logged(self):
        grant(self.root, "image:house/launch", "full")
        self.command("image", "new", "launch", "--brand", "house", "--sizes", "web-og")
        self.fill_brief()
        self.pass_brief()
        photo = self.root / "Team Photo.png"
        Image.new("RGB", (8, 8), "red").save(photo)
        self.command("image", "picture", "house/launch", str(photo))
        pictures = self.root / "images/house/launch/02_design/pictures"
        self.assertTrue((pictures / "team-photo.png").is_file())
        self.assertIn("team-photo.png: own file", (pictures / "SOURCES.md").read_text())

    def test_ai_picture_needs_the_passed_brief_and_lands_in_the_design(self):
        grant(self.root, "image:house/launch", "full")
        self.command("image", "new", "launch", "--brand", "house", "--sizes", "web-og")
        self.fill_brief()
        request = {"id": "launch-photo", "subject_type": "image", "subject_id": "house/launch", "purpose": "image-picture",
                   "prompt": "A calm desk with a microphone", "references": [], "transparent": False, "image_count": 1,
                   "transport": "native"}
        with self.assertRaises(ws.WorkspaceError):
            prepare_generation(self.root, {**request, "input_revision": creative_review_state(self.root, "image", "house/launch", "brief")["fingerprint"]})
        self.pass_brief()
        record = prepare_generation(self.root, {**request, "input_revision": creative_review_state(self.root, "image", "house/launch", "brief")["fingerprint"]})
        self.assertEqual(record["output_dir"], "images/house/launch/02_design/pictures/generated/launch-photo")
        approve_generation(self.root, "launch-photo", "Reviewer")
        path = self.root / record["output_dir"] / "photo.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (8, 8), "blue").save(path)
        relative = path.relative_to(self.root).as_posix()
        proof = {"provider": "openai", "transport": "native", "coordinator": "Claude", "image_tool_used": True,
                 "tool_results": [{"image_url": "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()}]}
        self.assertEqual(register_generated_outputs(self.root, "launch-photo", [relative], proof)["state"], "completed")
        self.assertIn(path, images.design_files(self.root / "images/house/launch"))


class CheckedDateTests(unittest.TestCase):
    def test_age(self):
        self.assertEqual(images.checked_age_days({"checked": "2026-01-01"}, date(2026, 1, 31)), 30)


if __name__ == "__main__":
    unittest.main()
