"""Render startup and worker failure checks using a throwaway scene."""

import argparse
import asyncio
import json
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from playwright.async_api import async_playwright

import anim


PAGE = """<!doctype html><canvas width=320 height=180></canvas><script>
const g = document.querySelector('canvas').getContext('2d');
window.__size = {w:320,h:180}; window.__ready = true;
window.__seek = t => {
  if (location.search.includes('fail') && t >= 4) throw Error('fixture seek failure');
  g.fillStyle = '#123'; g.fillRect(0,0,320,180);
  g.fillStyle = '#fed'; g.fillRect(Math.floor(t*10),30,50,50);
};
</script>"""


class RenderBrowserTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.video = self.root / "fixture"
        for stage in ("01_voice", "03_cues", "04_scene", "05_render"):
            (self.video / stage).mkdir(parents=True)
        (self.video / "03_cues/cues.js").write_text("")
        (self.video / "03_cues/cues.json").write_text(json.dumps({"meta": {"duration": 8}, "cueList": []}))
        (self.video / "04_scene/index.html").write_text(PAGE)
        with wave.open(str(self.video / "01_voice/voice.wav"), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(8000)
            wav.writeframes(b"\0\0" * 8000 * 8)

    def args(self, workers):
        return argparse.Namespace(slug="fixture", blur=1, skip_tone=True, start="0", end="8",
                                  skip_check=False, fps=2, workers=workers, crf=25, quality=80,
                                  no_master=True, lufs=-14, phone=False)

    def test_asset_rejection_fails_startup_and_closes_browser(self):
        page = self.video / "04_scene/index.html"
        page.write_text("<script>window.__assetError='missing image'</script>")

        async def run():
            async with async_playwright() as p:
                with self.assertRaisesRegex(RuntimeError, "missing image"):
                    await anim.open_page(p, page.as_uri())

        asyncio.run(run())

    def test_one_and_four_workers_complete(self):
        with patch.object(anim, "VIDEOS", self.root):
            for workers in (1, 4):
                with self.subTest(workers=workers):
                    anim.cmd_render(self.args(workers))
                    self.assertTrue((self.video / "05_render/fixture_0-8s.mp4").is_file())
                    self.assertFalse((self.video / "05_render/_segments").exists())
                    meta = json.loads((self.video / "05_render/fixture_0-8s.render.json").read_text())
                    self.assertEqual((meta["width"], meta["height"], meta["fps"], meta["workers"]),
                                     (320, 180, 2, workers))
                    self.assertTrue(meta["browser_version"])

    def test_worker_failure_cancels_and_removes_segments(self):
        page = self.video / "04_scene/index.html"
        page.write_text(PAGE.replace("location.search.includes('fail')", "true"))
        with patch.object(anim, "VIDEOS", self.root):
            with self.assertRaisesRegex(Exception, "fixture seek failure"):
                anim.cmd_render(self.args(4))
        self.assertFalse((self.video / "05_render/_segments").exists())
        self.assertFalse((self.video / "05_render/fixture_0-8s.mp4").exists())

    def test_concat_failure_preserves_previous_export_and_cleans_segments(self):
        final = self.video / "05_render/fixture_0-8s.mp4"
        final.write_bytes(b"previous approved export")
        with patch.object(anim, "VIDEOS", self.root), patch.object(anim.subprocess, "run",
                side_effect=subprocess.CalledProcessError(1, "ffmpeg")):
            with self.assertRaises(subprocess.CalledProcessError):
                anim.cmd_render(self.args(1))
        self.assertEqual(final.read_bytes(), b"previous approved export")
        self.assertFalse((self.video / "05_render/_segments").exists())

    def test_postprocess_failure_keeps_new_export_metadata(self):
        with patch.object(anim, "VIDEOS", self.root), patch.object(anim, "audio_peak",
                side_effect=RuntimeError("postprocess failed")):
            with self.assertRaisesRegex(RuntimeError, "postprocess failed"):
                anim.cmd_render(self.args(1))
        final = self.video / "05_render/fixture_0-8s.mp4"
        self.assertTrue(final.is_file())
        meta = json.loads(final.with_suffix(".render.json").read_text())
        self.assertEqual((meta["frames"], meta["workers"]), (16, 1))


if __name__ == "__main__":
    unittest.main()
