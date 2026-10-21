"""Clip frame folders whose source video sits in the video folder are rebuilt on demand, so git can skip them:
register_clip notes the source path and width in real.js and lists the folder in 04_scene/assets/.gitignore;
ensure_clips (called by scene_url before stills, check and render) cuts missing frames again."""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import anim


def real(vdir):
    text = (vdir / "04_scene/assets/real.js").read_text()
    return json.loads(text[text.index("window.REAL = ") + 14:text.rindex(";")])


class ClipRebuild(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vdir = Path(self.tmp.name) / "videos/demo"
        (self.vdir / "04_scene/motion").mkdir(parents=True)
        (self.vdir / "04_scene/assets").mkdir()
        self.src = self.vdir / "04_scene/motion/clip.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=duration=1:size=320x180:rate=24",
                        "-pix_fmt", "yuv420p", str(self.src)], check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_local_source_is_noted_ignored_and_rebuilt(self):
        anim.register_clip(self.vdir, self.src, "spin", 0.0, 1.0, 12, 160)
        clip = real(self.vdir)["clips"]["spin"]
        self.assertEqual((clip["path"], clip["width"], clip["n"]), ("04_scene/motion/clip.mp4", 160, 12))
        self.assertIn("/spin/", (self.vdir / "04_scene/assets/.gitignore").read_text().splitlines())
        for frame in (self.vdir / "04_scene/assets/spin").glob("f*.jpg"):
            frame.unlink()
        anim.ensure_clips(self.vdir)
        self.assertEqual(len(list((self.vdir / "04_scene/assets/spin").glob("f*.jpg"))), 12)

    def test_outside_source_is_kept_in_git_and_not_rebuilt(self):
        with tempfile.TemporaryDirectory() as other:
            outside = Path(other) / "stock.mp4"
            outside.write_bytes(self.src.read_bytes())
            anim.register_clip(self.vdir, outside, "stock", 0.0, 1.0, 12, 160)
        self.assertNotIn("path", real(self.vdir)["clips"]["stock"])
        self.assertFalse((self.vdir / "04_scene/assets/.gitignore").exists())
        anim.ensure_clips(self.vdir)  # no source to cut from: nothing happens, no error
