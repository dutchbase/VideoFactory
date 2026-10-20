"""Fixes from the Task 7 review and the whole-branch review (2026-10-13). Each test reproduces one finding."""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import anim, capture, check, libcore, privacy
from studio import workspace

ROOT = Path(__file__).resolve().parent.parent


class Crop(unittest.TestCase):
    def test_crop_box_clamped_to_viewport(self):  # ffmpeg would shift an outside box inward and take sidebar pixels
        self.assertEqual(capture.clamp_box({"x": 900, "y": -20, "width": 600, "height": 500}, 1280, 800),
                         {"x": 900, "y": 0, "width": 380, "height": 480})

    def test_empty_crop_box_refused(self):
        with self.assertRaisesRegex(RuntimeError, "crop"):
            capture.clamp_box({"x": 1300, "y": 10, "width": 200, "height": 200}, 1280, 800)


class Scan(unittest.TestCase):
    def test_tesseract_single_thread(self):  # parallel workers x tesseract threads overloaded the CPU
        seen = {}
        def fake_run(cmd, **kw):
            seen.update(kw.get("env") or {})
            return subprocess.CompletedProcess(cmd, 0, "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n", "")
        with mock.patch.object(privacy.subprocess, "run", fake_run):
            privacy.scan_image(ROOT / "library/blocks/chat/preview.png")
        self.assertEqual(seen.get("OMP_THREAD_LIMIT"), "1")

    def test_iban_followed_by_text(self):
        self.assertEqual(privacy.scan_text("NL91ABNA0417164300 EUR"), ["iban"])
        self.assertEqual(privacy.scan_text("Transfer to NL91ABNA0417164300 EUR 25"), ["iban"])

    def test_grouped_phone_numbers(self):
        for text in ("(415) 555-2671", "415-555-2671", "call 555 123 4567"):
            self.assertEqual(privacy.scan_text(text), ["phone"], text)
        for text in ("2026-10-13 12:30", "€ 19,95", "version 2.0.1"):
            self.assertEqual(privacy.scan_text(text), [], text)


class Templates(unittest.TestCase):
    def test_chatgpt_expect_is_logged_in_only(self):  # logged-out chatgpt.com also shows the composer
        opts, _ = capture.parse_steps((ROOT / "library/captures/chatgpt-chat.steps.txt").read_text())
        self.assertNotEqual(opts["expect"], "#prompt-textarea")
        self.assertIn("profile", opts["expect"])


class VisualLayer(unittest.TestCase):
    def test_core_only_is_text_only(self):  # core.js holds text helpers only
        self.assertEqual(check.no_visual_layer('<script src="blocks/core.js"></script>'), 1)
        self.assertEqual(check.no_visual_layer('<script src="blocks/core.js"></script><script src="blocks/chat.js"></script>'), 0)


class StudioGates(unittest.TestCase):
    def test_scene_gate_sees_visual_layer(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "check.md"
            f.write_text("lint errors  0\nvideo vs voice length  0\nno visual layer  1\n")
            self.assertFalse(workspace._scene_check_ok(f, "hyperframes"))
            f.write_text("lint errors  0\nvideo vs voice length  0\nno visual layer  0\n")
            self.assertTrue(workspace._scene_check_ok(f, "hyperframes"))

    def test_scene_gate_sees_invented_labels(self):  # older check.md files have no row and stay valid
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "check.md"
            hf = "lint errors  0\nvideo vs voice length  0\nno visual layer  0\n"
            canvas = "".join(f"{k}  0\n" for k in ("page errors", "cue warnings", "clock use", "nondeterministic frames",
                                                   "text cut off", "text overlaps", "text too short to read"))
            for engine, rows in (("hyperframes", hf), ("canvas", canvas)):
                f.write_text(rows + "invented labels  3\n")
                self.assertFalse(workspace._scene_check_ok(f, engine), engine)
                f.write_text(rows + "invented labels  0\n")
                self.assertTrue(workspace._scene_check_ok(f, engine), engine)
                f.write_text(rows)
                self.assertTrue(workspace._scene_check_ok(f, engine), engine)

    def test_video_gate_sees_flat_frames(self):  # a --skip-check render with flat frames must not pass the gate
        with tempfile.TemporaryDirectory() as d:
            vdir = Path(d); (vdir / "05_render").mkdir()
            f = vdir / "05_render/check-video.md"
            body = "- one-frame flashes (must be 0): 0\n{flat}- dead stretches over 3 s (stops the render): 0\n- format: h264 (ok)\n- loudness: no audio\n"
            f.write_text(body.format(flat="- flat frames, runs over 3 frames (stops the render): 2\n  - 0:02.00 - 0:02.20\n"))
            self.assertFalse(workspace._video_check_ok(f))
            f.write_text(body.format(flat="- flat frames, runs over 3 frames (stops the render): 0\n"))
            self.assertTrue(workspace._video_check_ok(f))
            f.write_text(body.format(flat=""))
            self.assertTrue(workspace._video_check_ok(f))

    def test_video_gate_sees_still_stretches(self):
        with tempfile.TemporaryDirectory() as d:
            vdir = Path(d); (vdir / "05_render").mkdir()
            f = vdir / "05_render/check-video.md"
            body = "- one-frame flashes (must be 0): 0\n- dead stretches over 3 s (stops the render): {n}\n- format: h264 (ok)\n- loudness: -14.0 LUFS, true peak -1.5 dBTP (target -14 LUFS, <= -1 dBTP: ok)\n"
            f.write_text(body.format(n=1))
            self.assertFalse(workspace._video_check_ok(f))
            (vdir / "project.json").write_text(json.dumps({"allow": ["still"]}))
            self.assertTrue(workspace._video_check_ok(f))
            (vdir / "project.json").write_text("{}")
            f.write_text(body.format(n=0))
            self.assertTrue(workspace._video_check_ok(f))


class Licence(unittest.TestCase):
    def test_own_is_not_a_download_licence(self):  # "own" let third-party downloads pass as own work
        with self.assertRaises(libcore.LicenseError):
            libcore.check_license("own")


class RenderSafety(unittest.TestCase):
    def test_mix_failure_keeps_previous_export(self):
        with tempfile.TemporaryDirectory() as d:
            vdir = Path(d); (vdir / "03_cues").mkdir(); (vdir / "01_voice").mkdir()
            (vdir / "03_cues/cues.json").write_text(json.dumps({"meta": {"duration": 1.0}, "cueList": []}))
            voice = vdir / "01_voice/voice.wav"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=duration=1", str(voice)], check=True)
            final = vdir / "final.mp4"; final.write_bytes(b"approved export")
            def ffmpeg_dies_mid_write(cmd, **kw):  # ffmpeg truncates its output file, then fails
                Path(cmd[-1]).write_bytes(b"")
                raise subprocess.CalledProcessError(1, cmd)
            with mock.patch.object(anim, "audio_sources", return_value={}), mock.patch.object(anim.subprocess, "run", ffmpeg_dies_mid_write), \
                 self.assertRaises(subprocess.CalledProcessError):
                anim.mix_soundtrack(vdir, voice, ["-i", str(vdir / "frames.mp4")], final, 0.0, 1.0)
            self.assertEqual(final.read_bytes(), b"approved export")

    def test_video_check_says_still_stops_render(self):
        with tempfile.TemporaryDirectory() as d:
            mp4 = Path(d) / "x.mp4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=gray:s=64x64:r=12:d=1", "-pix_fmt", "yuv420p", str(mp4)], check=True)
            anim.video_check(mp4, 12)
            self.assertIn("dead stretches over 3 s (stops the render)", (Path(d) / "check-video.md").read_text())


if __name__ == "__main__":
    unittest.main()
