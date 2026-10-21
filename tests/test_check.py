import os, shutil, subprocess, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import check


def B(s, x0, y0, x1, y1): return {"s": s, "x0": x0, "y0": y0, "x1": x1, "y1": y1}


class Pure(unittest.TestCase):
    def test_overlap_found(self):
        self.assertEqual(check.overlaps([B("Jobs", 0, 0, 100, 40), B("Pay", 50, 10, 150, 50)]), [("Jobs", "Pay")])

    def test_small_touch_ignored(self):
        self.assertEqual(check.overlaps([B("A", 0, 0, 100, 40), B("B", 98, 0, 200, 40)]), [])

    def test_karaoke_substring_ignored(self):  # Review Focus 2
        self.assertEqual(check.overlaps([B("find your first job", 0, 0, 400, 40), B("first", 150, 0, 230, 40)]), [])

    def test_same_string_twice_ignored(self):  # fill + stroke of one label
        self.assertEqual(check.overlaps([B("Hi", 0, 0, 50, 20), B("Hi", 1, 0, 51, 20)]), [])

    def test_cut_off(self):
        self.assertTrue(check.cut_off(B("x", -20, 10, 50, 40), 1920, 1080))
        self.assertFalse(check.cut_off(B("x", 10, 10, 50, 40), 1920, 1080))
        self.assertFalse(check.cut_off(B("x", -500, 10, -400, 40), 1920, 1080))  # fully off = parked, not cut

    def test_read_floor(self):
        self.assertAlmostEqual(check.read_floor("Hi"), 0.7)
        self.assertAlmostEqual(check.read_floor("x" * 34), 0.25 + 2.0)

    def test_too_short(self):
        dt = 1 / 6
        s = [(k * dt, ["Find a job fast"] if 6 <= k < 8 else []) for k in range(30)]
        self.assertEqual([r[0] for r in check.too_short(s, dt, 30 * dt)], ["Find a job fast"])

    def test_typing_and_numbers_ignored(self):  # Review Focus 3
        dt = 1 / 6
        s = [(0, ["Hel", "12"]), (dt, ["Hello there", "13"])] + [(k * dt, ["Hello there"]) for k in range(2, 40)]
        self.assertEqual(check.too_short(s, dt, 40 * dt), [])

    def test_single_glyphs_ignored(self):  # scramble and decode effects flash one random glyph per span
        dt = 1 / 6
        s = [(k * dt, ["R", "#"] if k == 3 else []) for k in range(30)]
        self.assertEqual(check.too_short(s, dt, 30 * dt), [])

    def test_one_sample_rounding_forgiven(self):  # 4 samples at 6 fps = 0.67 s, true time up to 0.83 s
        dt = 1 / 6
        s = [(k * dt, ["work"] if 6 <= k < 10 else []) for k in range(30)]
        self.assertEqual(check.too_short(s, dt, 30 * dt), [])

    def test_deleting_text_ignored(self):  # backspace: each shorter string is a prefix of the one before
        dt = 1 / 6
        s = [(k * dt, ["visit example.com"]) for k in range(20)] + [(20 * dt, ["visit example.co"]), (21 * dt, ["visit example"])] \
            + [(k * dt, []) for k in range(22, 40)]
        self.assertEqual([r[0] for r in check.too_short(s, dt, 40 * dt)], [])

    def test_lasting_overlaps(self):  # a cross-fade is brief; an overlap that stays is a defect
        dt = 1 / 6
        seen = {("A", "B"): [k * dt for k in (10, 11)], ("C", "D"): [k * dt for k in (3, 4, 5, 6)]}
        self.assertEqual(check.lasting(seen, dt), [("C", "D")])

    def test_clock_use(self):
        self.assertEqual(check.clock_use("const r = Math.random(); // Date.now() in a comment\nsetTimeout(f, 9)"),
                         ["Math.random", "setTimeout"])

    def test_report_lists_every_counter(self):
        out = check.report({k: 0 for k in check.FAIL_KEYS}, {"unmapped text (info)": 3})
        for k in check.FAIL_KEYS:
            self.assertIn(k, out)


ROOT = Path(__file__).resolve().parent.parent


def anim(*args):
    # These synthetic scenes test check/render sensors. Their empty cue sheets
    # cannot pass a production review, so call the command handler directly.
    command = "import anim,sys; a=anim.build_parser().parse_args(sys.argv[1:]); a.fn(a)"
    return subprocess.run([sys.executable, "-c", command, *args], cwd=ROOT,
                          capture_output=True, text=True, env=os.environ.copy())


def count(out, key):
    """The number after `key` in a check counter block."""
    import re
    m = re.search(rf"^{re.escape(key)}\s+(\d+)$", out, re.M)
    return int(m.group(1)) if m else None


def make_scene(slug, draw):
    """A tiny canvas scene under videos/<slug>/ (8 s, no voice). draw: JS body run each frame with ctx and t."""
    import json, shutil
    v = ROOT / "videos" / slug
    shutil.rmtree(v, ignore_errors=True)
    (v / "03_cues").mkdir(parents=True)
    (v / "04_scene").mkdir(parents=True)
    cues = {"meta": {"duration": 8, "voice": None, "slug": slug, "music": None, "music_gain": 0.25}, "cueList": [], "cues": {}, "words": []}
    (v / "03_cues" / "cues.json").write_text(json.dumps(cues))
    (v / "03_cues" / "cues.js").write_text("window.ANIM = " + json.dumps(cues) + ";")
    (v / "project.json").write_text(json.dumps({"brand": "videofactory", "allow": ["minimal"]}))
    (v / "04_scene" / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><div id="stage" data-width="1920" data-height="1080"></div>'
        '<script src="../03_cues/cues.js"></script><script src="../../../_runtime/player.js"></script><script src="scene.js"></script>')
    (v / "04_scene" / "scene.js").write_text(
        "const c = document.createElement('canvas'); c.width = 1920; c.height = 1080; document.getElementById('stage').appendChild(c);\n"
        "const ctx = c.getContext('2d');\n"
        "P.onFrame((t) => { ctx.fillStyle = '#123'; ctx.fillRect(0, 0, 1920, 1080); ctx.fillStyle = '#fff'; ctx.font = '60px sans-serif';\n"
        + draw + "\n});\n")
    return v


class Fixture(unittest.TestCase):
    def tearDown(self):
        import shutil
        shutil.rmtree(ROOT / "videos" / "zz-check-test", ignore_errors=True)

    def test_texts_at_different_times_do_not_overlap(self):  # probe seeks must not leak into the first sample
        make_scene("zz-check-test", "if (t < 2) ctx.fillText('Alpha label', 100, 200); if (t >= 3 && t < 6) ctx.fillText('Beta label', 100, 200);")
        r = anim("check", "zz-check-test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(count(r.stdout, "text overlaps"), 0)

    def test_real_problems_are_counted(self):
        make_scene("zz-check-test", "ctx.fillText('Cut at the edge', -40, 300); ctx.fillText('One word', 600, 600); ctx.fillText('Two words', 620, 610);"
                                    "if (t > 4 && t < 4.3) ctx.fillText('Gone before you read it', 600, 900);")
        r = anim("check", "zz-check-test")
        self.assertNotEqual(r.returncode, 0)
        for key in ("text cut off", "text overlaps", "text too short to read"):
            self.assertEqual(count(r.stdout, key), 1, key)

    def test_invented_label_is_counted(self):  # _shared/plan-check.md S2
        make_scene("zz-check-test", "ctx.fillText('02 / 05', 600, 300); ctx.fillText('A real sentence', 600, 700);")
        r = anim("check", "zz-check-test")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(count(r.stdout, "invented labels"), 1, r.stdout)


class Fixes(unittest.TestCase):
    def tearDown(self):
        import shutil
        shutil.rmtree(ROOT / "videos" / "zz-check-test", ignore_errors=True)

    def test_offscreen_text_is_info_not_failure(self):  # Review Focus 1: canvas scenes draw text on detached canvases
        make_scene("zz-check-test", "const o = document.createElement('canvas'); o.width = 400; o.height = 100;"
                                    "const oc = o.getContext('2d'); oc.font = '60px sans-serif'; oc.fillStyle = '#fff';"
                                    "oc.fillText('Canvas words', -50, 60); ctx.drawImage(o, 0, 0);")
        r = anim("check", "zz-check-test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertGreaterEqual(count(r.stdout, "unmapped text (info)"), 1)

    def test_invisible_text_is_ignored(self):  # fillStyle with alpha 0 draws nothing
        make_scene("zz-check-test", "ctx.fillText('One word', 600, 600); ctx.fillStyle = 'rgba(255,255,255,0)'; ctx.fillText('Two words', 620, 610);")
        r = anim("check", "zz-check-test")
        self.assertEqual(count(r.stdout, "text overlaps"), 0, r.stdout)

    def test_flash_blocks_render_unless_skip_check(self):
        v = make_scene("zz-check-test", "if (t >= 2 && t < 2.03) { ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, 1920, 1080); }")
        (v / "01_voice").mkdir()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "8",
                        str(v / "01_voice" / "voice.wav")], check=True)
        r = anim("render", "zz-check-test", "--workers", "1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("one-frame flashes", r.stderr)
        r = anim("render", "zz-check-test", "--workers", "1", "--skip-check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("one-frame flashes (must be 0): 1", (v / "05_render" / "check-video.md").read_text())

    def test_flat_frames_block_render_unless_skip_check(self):  # Review Focus 2: a solid card held 6 frames
        v = make_scene("zz-check-test", "ctx.fillRect((t * 400) % 1600, 300, 300, 500);"
                                        "if (t >= 2 && t < 2.2) { ctx.fillStyle = '#f4ecd8'; ctx.fillRect(0, 0, 1920, 1080); }")
        (v / "01_voice").mkdir()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "8",
                        str(v / "01_voice" / "voice.wav")], check=True)
        r = anim("render", "zz-check-test", "--workers", "1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("flat frames", r.stderr)
        self.assertIn("--skip-check", r.stderr)
        r = anim("render", "zz-check-test", "--workers", "1", "--skip-check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("flat frames, runs over 3 frames (stops the render): 1", (v / "05_render" / "check-video.md").read_text())


class Video(unittest.TestCase):
    def test_flat_run_found(self):
        import numpy as np
        g = np.random.default_rng(1).integers(0, 255, (24, 9, 16), dtype=np.uint8); g[10:14] = 0
        self.assertEqual(check.flat_runs(g, 30), [(10 / 30, 14 / 30)])

    def test_three_flat_frames_pass(self):
        import numpy as np
        g = np.random.default_rng(1).integers(0, 255, (24, 9, 16), dtype=np.uint8); g[10:13] = 0
        self.assertEqual(check.flat_runs(g, 30), [])

    def test_flat_frame_zero_counts(self):  # banned default: an empty or black frame 0
        import numpy as np
        g = np.random.default_rng(1).integers(0, 255, (24, 9, 16), dtype=np.uint8); g[:5] = 0
        self.assertEqual(check.flat_runs(g, 30), [(0.0, 5 / 30)])

    def test_flat_cream_counts_like_black(self):
        import numpy as np
        g = np.random.default_rng(1).integers(0, 255, (24, 9, 16), dtype=np.uint8); g[20:] = 240
        self.assertEqual(check.flat_runs(g, 30), [(20 / 30, 24 / 30)])

    def test_flash(self):
        import numpy as np
        g = np.zeros((10, 9, 16), np.uint8); g[5] = 200
        self.assertEqual(check.flashes(g), [5])

    def test_cut_is_not_flash(self):
        import numpy as np
        g = np.zeros((10, 9, 16), np.uint8); g[5:] = 200
        self.assertEqual(check.flashes(g), [])

    def test_dead(self):
        import numpy as np
        g = np.zeros((30 * 5, 9, 16), np.uint8); g[:30] = np.arange(30)[:, None, None]
        self.assertEqual([round(a) for a in check.dead(g, 30)[0]], [1, 5])

    def test_parse_ebur128(self):
        err = "  Integrated loudness:\n    I:         -14.1 LUFS\n  True peak:\n    Peak:       -1.3 dBFS\n"
        self.assertEqual(check.ebur128(err), (-14.1, -1.3))

    def make_mp4(self, tmp, audio=True, tags=True):
        out = Path(tmp) / "t.mp4"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=320x180:d=4"]
        if audio:
            cmd += ["-f", "lavfi", "-i", "sine=f=440:d=4,volume=0.05", "-c:a", "aac"]
        if tags:  # as render writes it
            cmd += ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
        subprocess.run(cmd + ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-shortest", str(out)], check=True)
        return out

    def test_master_hits_target(self):  # Review Focus 5: a quiet, sparse mix is raised without clipping
        import tempfile
        import anim
        with tempfile.TemporaryDirectory() as tmp:
            i, tp = anim.master(self.make_mp4(tmp))
        self.assertTrue(-15 <= i <= -13, i)
        self.assertLessEqual(tp, -0.9)

    def test_master_hits_target_with_sharp_peaks(self):  # speech-like: quiet body, loud clicks (high crest factor)
        import tempfile
        import anim
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "p.mp4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=320x180:d=6",
                            "-f", "lavfi", "-i", "sine=f=220:d=6,volume=0.1",
                            "-f", "lavfi", "-i", "aevalsrc=if(lt(mod(t\\,0.5)\\,0.003)\\,0.95\\,0):d=6",
                            "-filter_complex", "[1:a][2:a]amix=inputs=2:normalize=0[a]", "-map", "0:v", "-map", "[a]",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out)], check=True)
            i, tp = anim.master(out)
        self.assertTrue(-15 <= i <= -13, i)
        self.assertLessEqual(tp, -0.9)

    def test_master_says_when_target_missed(self):  # -2 LUFS cannot fit under a -1 dBTP ceiling
        import contextlib, io, tempfile
        import anim
        with tempfile.TemporaryDirectory() as tmp:
            out = self.make_mp4(tmp)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                anim.master(out, -2.0)
            self.assertIn("target missed", buf.getvalue())
            self.assertFalse(anim.video_check(out, 25, -2.0)["loudness_ok"])

    def test_master_skips_silent_video(self):
        import tempfile
        import anim
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(anim.master(self.make_mp4(tmp, audio=False)))

    def test_video_check_finds_format_and_loudness(self):
        import tempfile
        import anim
        with tempfile.TemporaryDirectory() as tmp:
            f = self.make_mp4(tmp)
            anim.master(f)
            r = anim.video_check(f, 25)
        self.assertEqual(r["flashes"], [])
        self.assertTrue(r["format_ok"], r["format"])
        self.assertTrue(-15 <= r["lufs"] <= -13)


    def test_master_skips_digital_silence(self):  # a silent voice track measures -inf: nothing to raise
        import tempfile
        import anim
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "s.mp4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=320x180:d=2",
                            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", str(out)], check=True)
            self.assertIsNone(anim.master(out))

    def test_untagged_colour_is_flagged(self):
        import tempfile
        import anim
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(anim.video_check(self.make_mp4(tmp, tags=False), 25)["format_ok"])


class Blur(unittest.TestCase):
    def test_spread(self):
        s = check.subtimes(1.0, 4, 30, [])
        self.assertEqual(len(s), 4)
        self.assertAlmostEqual(sum(s) / 4, 1.0)
        self.assertAlmostEqual(max(s) - min(s), 0.5 / 30 * 3 / 4)

    def test_never_across_cut(self):
        self.assertTrue(all(x >= 2.0 for x in check.subtimes(2.0, 4, 30, [2.0])))
        self.assertTrue(all(x < 2.0 for x in check.subtimes(1.999, 4, 30, [2.0])))

    def test_one_is_plain(self):
        self.assertEqual(check.subtimes(3.0, 1, 30, []), [3.0])


class Scene(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = ROOT / "videos" / "silent-first-scene"
        shutil.copytree(ROOT / "tests/fixtures/silent-first-scene", cls.project)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.project, ignore_errors=True)

    def test_silent_scene_reads_zero(self):
        r = anim("check", "silent-first-scene")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(count(r.stdout, "nondeterministic frames"), 0)
        self.assertTrue((self.project / "05_render/check.md").exists())

    def test_partial_render_skips_check(self):  # Review Focus 4
        md = self.project / "05_render/check.md"
        before = md.stat().st_mtime if md.exists() else None
        r = anim("render", "silent-first-scene", "--start", "0", "--end", "1", "--workers", "1")
        try:
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(md.stat().st_mtime if md.exists() else None, before)
        finally:
            (self.project / "05_render/silent-first-scene_0-1s.mp4").unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
