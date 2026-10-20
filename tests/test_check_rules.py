"""Project rules: no text-only video, no still stretch over 3 s, a music bed (warning only).
Quality bar (videofactory): sound design with licences, a hook cue by 2 s, a new cue every 5 s at most."""
import argparse, json, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import anim
import check

LINT = subprocess.CompletedProcess([], 0, json.dumps({"errorCount": 0, "warningCount": 0, "findings": []}), "")


def hf_video(directory, html, allow=None, music="file:bed.mp3", brand="videofactory", cue_list=None, duration=3.0, sound_md=None):
    vdir = Path(directory) / "v"
    (vdir / "04_scene").mkdir(parents=True); (vdir / "03_cues").mkdir()
    (vdir / "04_scene/index.html").write_text(html)
    pj = {"engine": "hyperframes", "brand": brand}
    if allow:
        pj["allow"] = allow
    (vdir / "project.json").write_text(json.dumps(pj))
    (vdir / "03_cues/cues.json").write_text(json.dumps({"meta": {"duration": duration, "music": music}, "cueList": cue_list or []}))
    if sound_md is not None:
        (vdir / "04_scene/assets").mkdir()
        (vdir / "04_scene/assets/sound.md").write_text(sound_md)
    return vdir


def run_hf_check(vdir):
    with mock.patch.object(anim, "hf", return_value=LINT), \
         mock.patch.object(check, "brand_counters", return_value={k: 0 for k in check.BRAND_KEYS}):
        return anim.hf_check(vdir)


TEXT_ONLY = '<div id="stage"><h1 class="clip">Text only</h1><script src="cues/cues.js"></script></div>'
WITH_BLOCK = '<div id="stage"><div class="clip"></div><script src="blocks/chat.js"></script></div>'


class VisualLayer(unittest.TestCase):
    def test_text_only_hf_scene_fails(self):
        with tempfile.TemporaryDirectory() as d:
            r = run_hf_check(hf_video(d, TEXT_ONLY))
            self.assertEqual(r["counters"]["no visual layer"], 1)
            self.assertIn("no visual layer", r["fail_keys"])

    def test_scene_with_block_passes(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run_hf_check(hf_video(d, WITH_BLOCK))["counters"]["no visual layer"], 0)

    def test_inline_svg_or_image_counts(self):
        for html in ('<svg viewBox="0 0 9 9"></svg>', '<img src="assets/a.jpg">', '<video class="clip" src="assets/b.mp4"></video>'):
            self.assertEqual(check.no_visual_layer(html), 0, html)

    def test_text_only_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run_hf_check(hf_video(d, TEXT_ONLY, allow=["text-only"]))["counters"]["no visual layer"], 0)


class Music(unittest.TestCase):
    def test_missing_music_warns(self):
        with tempfile.TemporaryDirectory() as d:
            r = run_hf_check(hf_video(d, WITH_BLOCK, music=None, brand="another-brand"))  # videofactory fails on it: QualityBar
            self.assertEqual(r["info"].get("music: none (warning)"), 1)
            self.assertFalse(any(r["counters"][k] for k in r["fail_keys"]))
            self.assertIn("music: none (warning)", (Path(d) / "v/05_render/check.md").read_text())

    def test_music_present_no_warning(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertNotIn("music: none (warning)", run_hf_check(hf_video(d, WITH_BLOCK))["info"])


def cues_every(step, duration, sfx=("whoosh",), first=0.0):
    out, t, k = [], first, 0
    while t < duration:
        out.append({"id": f"s{k}", "start": round(t, 2), "sfx": list(sfx) if k % 2 == 0 else []})
        t, k = t + step, k + 1
    return out


SOUND_MD = "# Sound\n- Music: openverse/audio/x, licence CC0-1.0\n- Effects: built-in (_shared/sound/), own synthesis\n"


class QualityBar(unittest.TestCase):
    def reel(self, d, **kw):
        args = dict(cue_list=cues_every(4.0, 36.0), duration=36.0, sound_md=SOUND_MD)
        args.update(kw)
        return run_hf_check(hf_video(d, WITH_BLOCK, **args))

    def test_full_reel_passes(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.reel(d)
            self.assertEqual([r["counters"][k] for k in check.QUALITY_KEYS], [0, 0])
            self.assertTrue(set(check.QUALITY_KEYS) <= set(r["fail_keys"]))
            self.assertTrue(set(check.QUALITY_KEYS) <= set(check.FAIL_KEYS))

    def test_missing_sound_design_counts_each_part(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.reel(d, music=None, cue_list=cues_every(4.0, 36.0, sfx=()), sound_md=None)
            self.assertEqual(r["counters"]["sound design missing"], 3)
            self.assertIn("sound design missing", (Path(d) / "v/05_render/check.md").read_text())

    def test_sound_file_without_licence(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self.reel(d, sound_md="# Sound\n- whoosh on cuts\n")["counters"]["sound design missing"], 1)

    def test_sparse_cues_and_late_hook(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self.reel(d, cue_list=cues_every(7.0, 36.0))["counters"]["too few beats"], 5)
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self.reel(d, cue_list=cues_every(4.0, 36.0, first=3.0))["counters"]["too few beats"], 1)
        with tempfile.TemporaryDirectory() as d:  # final CTA hold over 6 s
            self.assertEqual(self.reel(d, cue_list=cues_every(4.0, 28.0), duration=36.0)["counters"]["too few beats"], 1)

    def test_other_brand_and_exception_skip(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.reel(d, brand="another-brand", music=None, cue_list=[], sound_md=None)
            self.assertEqual([r["counters"][k] for k in check.QUALITY_KEYS], [0, 0])
        with tempfile.TemporaryDirectory() as d:
            r = self.reel(d, allow=["minimal"], music=None, cue_list=[], sound_md=None)
            self.assertEqual([r["counters"][k] for k in check.QUALITY_KEYS], [0, 0])

    def test_check_gate_stops(self):
        with tempfile.TemporaryDirectory() as d:
            vdir = hf_video(d, WITH_BLOCK, cue_list=cues_every(4.0, 36.0), duration=36.0, sound_md=None)
            with mock.patch.object(anim, "hf", return_value=LINT), \
                 mock.patch.object(check, "brand_counters", return_value={k: 0 for k in check.BRAND_KEYS}), \
                 mock.patch("sys.stdout"), mock.patch("sys.stderr"), self.assertRaises(SystemExit):
                anim.check_gate(vdir)

    def test_studio_scene_readiness(self):
        from studio import workspace
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "check.md"
            base = "lint errors  0\nvideo vs voice length  0\nno visual layer  0\n"
            f.write_text(base)
            self.assertTrue(workspace._scene_check_ok(f, "hyperframes"))  # older check.md without quality rows
            f.write_text(base + "sound design missing  0\ntoo few beats  2\n")
            self.assertFalse(workspace._scene_check_ok(f, "hyperframes"))
            f.write_text(base + "sound design missing  0\ntoo few beats  0\n")
            self.assertTrue(workspace._scene_check_ok(f, "hyperframes"))


class DeadStretch(unittest.TestCase):
    def after(self, vdir):
        a = argparse.Namespace(no_master=False, lufs=-14.0, start=None, end=None, skip_check=False, phone=False)
        vc = {"dead": [(1.0, 5.0)], "format_ok": True, "loudness_ok": True, "flashes": [], "flat": []}
        final = vdir / "05_render/v.mp4"; final.parent.mkdir(exist_ok=True); final.write_bytes(b"x")
        with mock.patch.object(anim, "master", return_value=(-14.0, -1.5)), mock.patch.object(anim, "video_check", return_value=vc), \
             mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            anim.after_render(a, vdir, final, 30, 0.0)

    def test_dead_stretch_fails(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                self.after(hf_video(d, WITH_BLOCK))

    def test_dead_stretch_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            self.after(hf_video(d, WITH_BLOCK, allow=["still"]))


class InventedLabels(unittest.TestCase):  # _shared/plan-check.md S2: production metadata on screen
    def test_flags_counters_and_metadata(self):
        hits = dict(check.invented_labels(["02 / 05", "01 — THE WAIT", "FILM 01", "00:01:24", "120 BPM", "1920x1080", "v1.2", "01:02:03:12"]))
        self.assertEqual(len(hits), 8, hits)
        self.assertEqual(hits["02 / 05"], "counter")
        self.assertEqual(hits["120 BPM"], "metadata")

    def test_keeps_real_text(self):  # Review Focus 1: real copy in any language
        self.assertEqual(check.invented_labels(["Step 1 of 3", "Step 2 of 4", "Lesson 2", "€49", "9:00–17:00", "1/3", "24/7",
                                                "3:45", "Hello world", "Scene 3 of the course", "2026"]), [])

    def test_keeps_scores_dates_timers_and_course_chapters(self):  # final review: real copy the first rules flagged
        self.assertEqual(check.invented_labels(["10 / 10", "12 / 24", "05/10", "01/12", "30-DAY GUARANTEE", "24-HOUR SUPPORT",
                                                "CHAPTER 3", "PART 2", "SHOT 5", "00", "03", "08:30:00", "1:30:00"]), [])

    def test_unique(self):
        self.assertEqual(len(check.invented_labels(["02 / 05"] * 30)), 1)

    def test_hyperframes_body_counts(self):  # Review Focus 4
        with tempfile.TemporaryDirectory() as d:
            r = run_hf_check(hf_video(d, '<div id="stage"><img src="a.png"><div class="clip">03 / 07</div></div>'))
            self.assertEqual(r["counters"]["invented labels"], 1)
            self.assertIn("invented labels", r["fail_keys"])

    def test_hyperframes_clean_body(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run_hf_check(hf_video(d, WITH_BLOCK))["counters"]["invented labels"], 0)


if __name__ == "__main__":
    unittest.main()
