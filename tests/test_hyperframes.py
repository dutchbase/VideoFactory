import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import anim  # noqa: E402


class HyperframesHelper(unittest.TestCase):
    def test_hf_missing_binary_dies(self):
        with mock.patch.object(anim, "HF_BIN", Path("/nonexistent/hyperframes")), mock.patch("sys.stderr"):
            with self.assertRaises(SystemExit):
                anim.hf("lint", cwd=ROOT)

    def test_hf_env_disables_telemetry(self):
        with tempfile.TemporaryDirectory() as d:
            fake = Path(d) / "hyperframes"
            fake.write_text("")
            done = subprocess.CompletedProcess([], 0, "", "")
            with mock.patch.object(anim, "HF_BIN", fake), \
                    mock.patch.object(anim.subprocess, "run", return_value=done) as run:
                out = anim.hf("lint", "--json", cwd=Path(d), capture=True)
        self.assertIs(out, done)
        args, kw = run.call_args
        self.assertEqual(args[0], [str(fake), "lint", "--json"])
        self.assertEqual(kw["env"]["HYPERFRAMES_NO_TELEMETRY"], "1")
        self.assertEqual(kw["env"]["DO_NOT_TRACK"], "1")
        self.assertEqual(kw["cwd"], d)
        self.assertTrue(kw["capture_output"])


class HyperframesNew(unittest.TestCase):
    """`anim.py new --engine hyperframes` in a scratch copy of videos/."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)  # links resolve like in the repo: videos/<slug>/04_scene/../../../brands
        for name in ("brands", "_runtime"):
            (base / name).symlink_to(ROOT / name)
        self.videos = base / "videos"
        self.videos.mkdir()
        self.patch = mock.patch.object(anim, "VIDEOS", self.videos)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def new(self, *argv):
        with mock.patch.object(sys, "argv", ["anim.py", "new", *argv]), \
                mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            anim.main()

    def test_wide(self):
        self.new("hf-wide", "--engine", "hyperframes", "--brand", "videofactory")
        d = self.videos / "videofactory" / "hf-wide"
        meta = json.loads((d / "project.json").read_text())
        self.assertEqual((meta["engine"], meta["brand"], meta["renderer"]), ("hyperframes", "videofactory", "hyperframes"))
        html = (d / "04_scene" / "index.html").read_text()
        self.assertIn('data-width="1920"', html)
        self.assertIn('src="brand/tokens.js"', html)
        self.assertIn('src="voice/voice.mp3"', html)
        self.assertNotIn("{{", html)
        self.assertEqual((d / "04_scene" / "brand").resolve(), (ROOT / "brands" / "videofactory").resolve())
        self.assertTrue((d / "04_scene" / "brand" / "tokens.js").is_file())
        self.assertTrue((d / "04_scene" / "runtime" / "hf-bridge.js").is_file())
        self.assertTrue((d / "04_scene" / "runtime" / "vendor" / "gsap.min.js").is_file())

    def test_tall(self):
        self.new("hf-tall", "--engine", "hyperframes", "--format", "tall", "--brand", "videofactory")
        html = (self.videos / "videofactory" / "hf-tall" / "04_scene" / "index.html").read_text()
        self.assertIn('data-height="1920"', html)
        self.assertEqual(json.loads((self.videos / "videofactory" / "hf-tall" / "project.json").read_text())["brand"], "videofactory")

    def test_wav_voice_sets_audio_src(self):
        wav = self.videos / "in.wav"
        wav.write_bytes(b"RIFF")
        self.new("hf-wav", str(wav), "--engine", "hyperframes", "--brand", "videofactory")
        self.assertIn('src="voice/voice.wav"', (self.videos / "videofactory" / "hf-wav" / "04_scene" / "index.html").read_text())

    def test_style_rejected(self):
        with self.assertRaises(SystemExit) as e:
            self.new("hf-style", "--engine", "hyperframes", "--style", "modern")
        self.assertNotEqual(e.exception.code, 0)
        self.assertFalse((self.videos / "videofactory" / "hf-style").exists())

    def test_canvas_default_writes_engine(self):
        self.new("cv", "--brand", "videofactory")
        self.assertEqual(json.loads((self.videos / "videofactory" / "cv" / "project.json").read_text())["engine"], "canvas")

    @unittest.skipUnless(anim.HF_BIN.is_file() and shutil.which("ffmpeg"), "hyperframes or ffmpeg not installed")
    def test_fresh_video_passes_lint(self):
        self.new("hf-lint", "--engine", "hyperframes", "--brand", "videofactory")
        d = self.videos / "videofactory" / "hf-lint"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=d=1",
                        str(d / "01_voice" / "voice.mp3")], check=True)
        out = anim.hf("lint", ".", "--json", cwd=d / "04_scene", capture=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        report = json.loads(out.stdout)
        self.assertEqual((report["errorCount"], report["warningCount"]), (0, 0), out.stdout)


class HyperframesCreateVideo(unittest.TestCase):
    def test_dashboard_path_accepts_engine(self):
        from studio import workspace as ws
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ("_templates", "brands"):
                (root / name).symlink_to(ROOT / name)
            (root / "_runtime").symlink_to(ROOT / "_runtime")
            brief = {"audience": "a", "video_type": "b", "language": "en", "outcome": "c"}
            with mock.patch.object(ws, "video_detail", return_value={}):
                ws.create_video(root, "hf-dash", brief, engine="hyperframes", brand="videofactory")
            meta = json.loads((root / "videos" / "videofactory" / "hf-dash" / "project.json").read_text())
            self.assertEqual((meta["engine"], meta["style"]), ("hyperframes", "none"))
            self.assertTrue((root / "videos" / "videofactory" / "hf-dash" / "04_scene" / "brand" / "tokens.js").is_file())
            with self.assertRaises(ws.WorkspaceError):
                ws.create_video(root, "hf-bad", brief, engine="hyperframes", style="modern")


class HyperframesDispatch(unittest.TestCase):
    """render / stills / check / preview pick the engine from project.json; canvas keeps the old path."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.videos = self.root / "videos"
        for name in ("_runtime", "tools", "brands", "FONT-SOURCES.json"):
            (self.root / name).symlink_to(ROOT / name, target_is_directory=True)
        self.root_patch = mock.patch.object(anim, "ROOT", self.root)
        self.root_patch.start()
        self.patch = mock.patch.object(anim, "VIDEOS", self.videos)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.root_patch.stop()
        self.tmp.cleanup()

    def video(self, slug, engine=None):
        v = self.videos / slug
        for d in ("01_voice", "03_cues", "04_scene", "05_render"):
            (v / d).mkdir(parents=True)
        meta = {"brand": "videofactory"} if engine is None else {"brand": "videofactory", "engine": engine}
        (v / "project.json").write_text(json.dumps(meta))
        (v / "01_voice" / "voice.wav").write_bytes(b"")
        (v / "04_scene" / "index.html").write_text('<html><audio src="../01_voice/voice.wav" data-start="0"></audio></html>')
        cues = [{"id": "a", "start": 0.0, "end": 2.0, "text": "", "note": ""},
                {"id": "b", "start": 2.0, "end": 4.0, "text": "", "note": ""}]
        (v / "03_cues" / "cues.json").write_text(json.dumps({"meta": {"duration": 4.0}, "cueList": cues}))
        return v

    def args(self, **kw):
        base = dict(slug="x", skip_tone=True, start=None, end=None, blur=1, skip_check=False, fps=30, hold=0.9, at=None,
                    no_master=False, lufs=-14.0, phone=False)
        base.update(kw)
        return mock.Mock(**base)

    def test_video_engine_default_canvas(self):
        self.assertEqual(anim.video_engine(self.video("old")), "canvas")
        self.assertEqual(anim.video_engine(self.video("new", "hyperframes")), "hyperframes")
        self.assertEqual(anim.video_engine(self.videos / "missing"), "canvas")

    def test_render_hyperframes_args(self):
        v = self.video("x", "hyperframes")

        def fake_hf(*args, cwd, capture=False):
            Path(args[2]).write_bytes(b"mp4")
            return subprocess.CompletedProcess(args, 0)
        probe = subprocess.CompletedProcess([], 0, json.dumps({"streams": [{"width": 1920, "height": 1080}]}), "")
        with mock.patch.object(anim, "hf", side_effect=fake_hf) as hf, \
                mock.patch.object(anim, "check_gate") as gate, mock.patch.object(anim, "after_render") as after, \
                mock.patch.object(anim, "probe_duration", return_value=4.0), \
                mock.patch.object(anim.subprocess, "run", return_value=probe), \
                mock.patch.object(anim.shutil, "which", return_value="/usr/bin/ffmpeg"), mock.patch("sys.stdout"), \
                mock.patch.object(anim, "mix_soundtrack", side_effect=lambda vd, vo, args, out, t0, t1: (out.write_bytes(b"mp4"), {})[1]) as mix:
            anim.cmd_render(self.args())
        final = v / "05_render" / "x.mp4"
        frames = v / "05_render" / ".x-frames.mp4"  # hyperframes draws the picture, mix_soundtrack adds voice, music and effects
        hf.assert_called_once_with("render", "-o", str(frames), "--fps", "30", "-q", "high", cwd=v / "04_scene")
        self.assertEqual(mix.call_args.args[2:4], (["-i", str(frames)], final))
        self.assertFalse(frames.exists())
        gate.assert_called_once_with(v)
        self.assertEqual(after.call_args.args[2], final)
        meta = json.loads((v / "05_render" / "x.render.json").read_text())
        self.assertEqual((meta["engine"], meta["frames"]), ("hyperframes", 120))

    def test_stills_hyperframes_keeps_cue_frames(self):
        v = self.video("x", "hyperframes")

        def fake_hf(*args, cwd, capture=False):
            Path(args[args.index("-o") + 1]).write_bytes(b"mp4")
            return subprocess.CompletedProcess(args, 0)

        def fake_ff(cmd, **kw):
            Path(cmd[-1]).write_text(cmd[cmd.index("-vf") + 1])
            return subprocess.CompletedProcess(cmd, 0)
        with mock.patch.object(anim, "hf", side_effect=fake_hf) as hf, mock.patch.object(anim, "write_contact"), \
                mock.patch.object(anim.subprocess, "run", side_effect=fake_ff), \
                mock.patch.object(anim, "write_sheets", return_value=1), mock.patch("sys.stdout"):
            anim.cmd_stills(self.args())
        draft = v / "05_render" / "_hf_stills.mp4"
        hf.assert_called_once_with("render", "-o", str(draft), "-q", "draft", "--fps", "30", "--quiet", cwd=v / "04_scene")
        stills = v / "05_render" / "stills"
        self.assertEqual(sorted(p.name for p in stills.iterdir()), ["000_a.png", "001_b.png"])
        # cue start + min(0.9, 0.6 * 2 s) = 0.9 s and 2.9 s -> frames 27 and 87 (0-based)
        self.assertEqual((stills / "000_a.png").read_text(), "select=eq(n\\,27)")
        self.assertEqual((stills / "001_b.png").read_text(), "select=eq(n\\,87)")
        self.assertFalse(draft.exists())

    def test_tone_gate_reads_hyperframes_html(self):
        v = self.video("x", "hyperframes")
        (v / "04_scene" / "index.html").write_text(
            '<html><head><title>simple</title></head><body><h1>It is easy to start.</h1>'
            '<script>const s = "quick";</script></body></html>')
        text = anim.screen_text(v)["index.html"]
        self.assertEqual(text, "It is easy to start.")
        with mock.patch("sys.stderr"), self.assertRaises(SystemExit):
            anim.tone_gate(v, anim.screen_text(v), False)

    def test_check_hyperframes_lint_counts(self):
        v = self.video("x", "hyperframes")
        lint = {"errorCount": 2, "warningCount": 1, "findings": [{"severity": "error", "code": "c1", "message": "m"}]}
        with mock.patch.object(anim, "hf", return_value=subprocess.CompletedProcess([], 1, json.dumps(lint), "")) as hf, \
                mock.patch.object(anim, "run_check") as canvas:
            r = anim.hf_check(v)
            with mock.patch("sys.stdout"), mock.patch("sys.stderr"), self.assertRaises(SystemExit):
                anim.check_gate(v)
        hf.assert_called_with("lint", "--json", cwd=v / "04_scene", capture=True)
        canvas.assert_not_called()
        self.assertEqual(r["counters"]["lint errors"], 2)
        self.assertIn("text overlaps", r["block"])
        self.assertIn("n/a (hyperframes)", r["block"])

    def test_check_hyperframes_length_counter(self):
        v = self.video("x", "hyperframes")
        (v / "05_render" / "x.mp4").write_bytes(b"")
        ok = subprocess.CompletedProcess([], 0, json.dumps({"errorCount": 0, "findings": []}), "")
        with mock.patch.object(anim, "hf", return_value=ok), \
                mock.patch.object(anim, "probe_duration", side_effect=lambda p: 4.8 if p.suffix == ".mp4" else 4.0):
            self.assertEqual(anim.hf_check(v)["counters"]["video vs voice length"], 1)

    def test_canvas_paths_unchanged(self):
        v = self.video("x")
        stop = RuntimeError("canvas path")
        with mock.patch.object(anim, "hf") as hf, mock.patch.object(anim, "scene_url", side_effect=stop) as url, \
                mock.patch.object(anim.shutil, "which", return_value="/usr/bin/ffmpeg"):
            for cmd in (anim.cmd_render, anim.cmd_stills):
                with self.assertRaises(RuntimeError):
                    cmd(self.args())
            with mock.patch.object(anim, "run_check", return_value={"counters": dict.fromkeys(__import__("check").FAIL_KEYS, 0), "details": [], "block": ""}) as rc, \
                    mock.patch("sys.stdout"):
                anim.check_gate(v)
            rc.assert_called_once_with(v, 6)
        hf.assert_not_called()
        self.assertEqual(url.call_count, 2)

    def test_preview_hyperframes_args(self):
        v = self.video("x", "hyperframes")
        with mock.patch.object(anim, "hf", return_value=subprocess.CompletedProcess([], 0)) as hf, mock.patch("sys.stdout"):
            anim.cmd_preview(mock.Mock(slug="x", port=4567, stop=False))
            hf.assert_called_once_with("preview", "--port", "4567", "--no-open", "--background", cwd=v / "04_scene")
            anim.cmd_preview(mock.Mock(slug="x", port=4567, stop=True))
            hf.assert_called_with("preview", "--stop", cwd=v / "04_scene")


if __name__ == "__main__":
    unittest.main()


class HyperframesThumbnail(unittest.TestCase):
    """`anim.py thumbnail` on a hyperframes video grabs a frame of the MP4 with ffmpeg."""

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs ffmpeg")
    def test_thumbnail_from_mp4(self):
        with tempfile.TemporaryDirectory() as d:
            videos = Path(d) / "videos"
            vdir = videos / "hf-thumb"
            (vdir / "05_render").mkdir(parents=True)
            (vdir / "project.json").write_text('{"brand": "videofactory", "engine": "hyperframes"}')
            subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=red:s=320x180:d=2",
                            str(vdir / "05_render" / "hf-thumb.mp4")], check=True)
            with mock.patch.object(anim, "ROOT", Path(d)), mock.patch.object(anim, "VIDEOS", videos), \
                    mock.patch.object(sys, "argv", ["anim.py", "thumbnail", "hf-thumb"]), mock.patch("sys.stdout"):
                anim.main()
            from PIL import Image
            png = vdir / "05_render" / "thumbnail-hf-thumb.png"
            self.assertTrue(png.is_file())
            with Image.open(png) as im:
                self.assertEqual(im.size, (1280, 720))
