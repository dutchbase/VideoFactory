"""HyperFrames sub-compositions: index.html mounts compositions/*.html with
data-composition-src. check, the tone gate (provenance labels) and the audio guard read every mounted file."""
import json, shutil, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tests"))
import anim
import check
import tone
from test_check_rules import SOUND_MD, cues_every, run_hf_check

FIXTURE = ROOT / "tests/fixtures/hf_compositions/04_scene"


def video(d, cue_list=None, duration=330.0, brand="videofactory"):
    """A long (5.5 min) HyperFrames video built from the fixture: a root with chapter compositions."""
    vdir = Path(d) / "v"
    shutil.copytree(FIXTURE, vdir / "04_scene")
    (vdir / "03_cues").mkdir()
    (vdir / "project.json").write_text(json.dumps({"engine": "hyperframes", "brand": brand, "format": "tall"}))
    cues = cue_list if cue_list is not None else cues_every(4.0, duration)
    (vdir / "03_cues/cues.json").write_text(json.dumps({"meta": {"duration": duration, "music": "file:bed.mp3"}, "cueList": cues}))
    (vdir / "04_scene/assets").mkdir()
    (vdir / "04_scene/assets/sound.md").write_text(SOUND_MD)
    return vdir


class Documents(unittest.TestCase):
    def test_fixture_reads_root_then_mounted_files_once(self):
        docs, problems = check.scene_documents(FIXTURE)
        self.assertEqual([n for n, _ in docs], ["index.html", "compositions/opening.html", "compositions/card.html", "compositions/cta.html"])
        self.assertEqual(problems, [])  # card.html mounted twice is one file; the commented-out old.html is not read

    def test_cycle_missing_and_outside(self):
        with tempfile.TemporaryDirectory() as d:
            scene = Path(d) / "04_scene"
            shutil.copytree(FIXTURE, scene)
            card = scene / "compositions/card.html"
            card.write_text(card.read_text().replace("<p>", '<div data-composition-src="compositions/opening.html"></div>'
                                                     '<div data-composition-src="compositions/gone.html"></div>'
                                                     '<div data-composition-src="../../secret.html"></div><p>'))
            (Path(d) / "secret.html").write_text("<p>outside</p>")
            docs, problems = check.scene_documents(scene)
            self.assertEqual(len(docs), 4)
            self.assertEqual(len(problems), 3, problems)
            self.assertIn("composition cycle: index.html -> compositions/opening.html -> compositions/card.html -> compositions/opening.html", problems)
            self.assertTrue(any("not found: compositions/gone.html" in p for p in problems))
            self.assertTrue(any("outside 04_scene" in p for p in problems))

    def test_self_reference_terminates(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "index.html").write_text('<div data-composition-src="index.html"></div>')
            docs, problems = check.scene_documents(Path(d))
            self.assertEqual(len(docs), 1)
            self.assertEqual(problems, ["composition cycle: index.html -> index.html"])

    def test_html_text_reads_template_fragments(self):
        self.assertEqual(tone.html_text((FIXTURE / "compositions/opening.html").read_text()), "Every folder is a workspace")


class ToneGate(unittest.TestCase):
    def test_screen_text_has_every_composition(self):
        with tempfile.TemporaryDirectory() as d:
            text = anim.screen_text(video(d))
            self.assertEqual(text["index.html"], "THE CARD")
            self.assertEqual(text["compositions/card.html"], "One card per step")
            self.assertIn("compositions/cta.html", text)

    def test_provenance_label_in_a_nested_composition_stops(self):
        with tempfile.TemporaryDirectory() as d:
            vdir = video(d)
            card = vdir / "04_scene/compositions/card.html"
            card.write_text(card.read_text().replace("<p>One card per step</p>", "<p>One card per step</p><small>Illustrated</small>"))
            with mock.patch("sys.stderr"), self.assertRaises(SystemExit):
                anim.tone_gate(vdir, anim.screen_text(vdir), False)


class HfCheck(unittest.TestCase):
    def test_long_video_with_compositions_passes(self):
        with tempfile.TemporaryDirectory() as d:
            r = run_hf_check(video(d))
            self.assertEqual(r["counters"]["no visual layer"], 0)  # the svg sits in compositions/opening.html
            self.assertEqual(r["counters"]["composition errors"], 0)
            self.assertEqual([r["counters"][k] for k in check.QUALITY_KEYS], [0, 0])
            self.assertEqual(r["info"]["sub-compositions read (info)"], 3)
            self.assertIn("composition errors", r["fail_keys"])

    def test_long_video_counts_quality_gaps(self):
        with tempfile.TemporaryDirectory() as d:  # chapter 2 (120 to 180 s) has no new cue
            cues = [c for c in cues_every(4.0, 330.0) if not 120 < c["start"] < 180]
            r = run_hf_check(video(d, cue_list=cues))
            self.assertEqual(r["counters"]["too few beats"], 1)
            self.assertTrue(any("120.0-180.0 s" in x for x in r["details"]))

    def test_root_alone_is_text_only(self):
        with tempfile.TemporaryDirectory() as d:
            vdir = video(d)
            (vdir / "04_scene/compositions/opening.html").unlink()
            r = run_hf_check(vdir)
            self.assertEqual(r["counters"]["no visual layer"], 1)
            self.assertEqual(r["counters"]["composition errors"], 1)
            self.assertIn("composition not found: compositions/opening.html (in index.html)", r["details"])


class AudioGuard(unittest.TestCase):
    def test_audio_in_a_composition_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            vdir = video(d)
            (vdir / "01_voice").mkdir()
            voice = vdir / "01_voice/voice.mp3"; voice.write_bytes(b"voice")
            (vdir / "04_scene/voice").symlink_to("../01_voice", target_is_directory=True)
            cues = json.loads((vdir / "03_cues/cues.json").read_text())
            with mock.patch.object(anim, "has_audio", return_value=False):
                anim.check_hf_audio(vdir, voice, cues)  # the fixture: one voice in the root, nothing in compositions
                cta = vdir / "04_scene/compositions/cta.html"
                cta.write_text(cta.read_text().replace("</p>", '</p><audio src="assets/bed.mp3"></audio>'))
                with self.assertRaisesRegex(ValueError, "separate tracks"):
                    anim.check_hf_audio(vdir, voice, cues)


if __name__ == "__main__":
    unittest.main()
