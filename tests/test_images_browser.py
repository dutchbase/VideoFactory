"""Export one brand design at three very different sizes in Chromium: exact pixels, clean checks, no guide lines."""
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import anim
from studio import images
from studio.creative import creative_review_state, decide_creative, mark_creative_ready
from studio.permissions import grant

ROOT = Path(__file__).resolve().parents[1]
SIZES = "instagram-square,linkedin-banner,instagram-story,x-profile"


class ImageExportBrowserTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "_shared").mkdir()
        shutil.copy(ROOT / images.SIZES_FILE, self.root / images.SIZES_FILE)
        shutil.copytree(ROOT / "brands/videofactory", self.root / "brands/videofactory", symlinks=True)
        (self.root / "_runtime").symlink_to(ROOT / "_runtime")
        (self.root / "library").symlink_to(ROOT / "library")
        for p in (patch.dict("os.environ", {"VF_SESSION_ID": "browser"}), patch.object(anim, "ROOT", self.root)):
            p.start()
            self.addCleanup(p.stop)
        grant(self.root, "image:videofactory/launch", "full")
        self.command("image", "new", "launch", "--brand", "videofactory", "--sizes", SIZES, "--title", "Make videos from your voice")
        brief = self.root / "images/videofactory/launch/01_brief/brief.md"
        text = brief.read_text().replace("<!-- One sentence", "People learn the product exists.\n<!-- One")
        brief.write_text(text.replace("<!-- The exact words", "Make videos from your voice\n<!-- The"))
        state = creative_review_state(self.root, "image", "videofactory/launch", "brief")
        mark_creative_ready(self.root, "image", "videofactory/launch", "brief", state["fingerprint"])
        decide_creative(self.root, "image", "videofactory/launch", "brief", "approved", "Reviewer", "", state["fingerprint"])
        self.job = self.root / "images/videofactory/launch"

    def command(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            anim._dispatch(anim.build_parser().parse_args(list(args)))
        return output.getvalue()

    def test_export_sizes_checks_and_previews(self):
        self.command("image", "export", "videofactory/launch")
        report = json.loads((self.job / "03_export/report.json").read_text())
        self.assertTrue(report["ok"], report)
        catalog = images.load_sizes(self.root)["sizes"]
        for ident in SIZES.split(","):
            with Image.open(self.job / f"03_export/{ident}.png") as im:
                self.assertEqual(im.size, (catalog[ident]["w"], catalog[ident]["h"]))
        self.assertTrue(creative_review_state(self.root, "image", "videofactory/launch", "final")["ready"])

        self.command("image", "export", "videofactory/launch", "--guides", "--only", "linkedin-banner")
        final, preview = self.job / "03_export/linkedin-banner.png", self.job / "03_export/preview/linkedin-banner.png"
        self.assertNotEqual(final.read_bytes(), preview.read_bytes())  # only the preview has the safe-area lines
        self.assertTrue(json.loads((self.job / "03_export/report.json").read_text())["ok"])

    def test_text_outside_the_safe_area_fails(self):
        design = self.job / "02_design/design.html"
        design.write_text(design.read_text().replace('<section class="vf-frame">', '<section class="vf-frame" style="top:0;padding:0;justify-content:flex-start">'))
        with self.assertRaises(SystemExit):
            self.command("image", "export", "videofactory/launch", "--only", "instagram-story")
        report = json.loads((self.job / "03_export/report.json").read_text())
        self.assertFalse(report["ok"])
        self.assertTrue(any("outside the safe area" in p for p in report["sizes"][0]["problems"]))


if __name__ == "__main__":
    unittest.main()
