"""Variant A (template reel, no voice) sound mix: effects without word timings are allowed only when project.json
declares no voice AND the voice track is digital silence. Voiced projects keep the strict check. No rendering:
only numpy arrays and short WAV files in a temp dir (decoded by ffmpeg)."""
import json, sys, tempfile, unittest, wave
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.argv = sys.argv[:1]
import anim
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_runtime"))
import synth

SR = 44100


def fx_track(seconds=1.0):
    e = np.zeros(int(SR * seconds))
    e[1000:3000] = 0.3
    return e


def noisy_wav(path: Path, seconds=1.0):
    rng = np.random.default_rng(1)
    data = (rng.uniform(-0.2, 0.2, int(SR * seconds)) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())


class Windows(unittest.TestCase):
    def test_voiced_projects_still_need_word_timings(self):
        voice = np.full(SR, 0.1)
        with self.assertRaisesRegex(ValueError, "corrected word timings"):
            anim.limit_sfx(voice, fx_track(), [], SR)
        with self.assertRaisesRegex(ValueError, "silent voice track"):
            anim.limit_sfx(voice, fx_track(), [], SR, no_voice=True)  # declared no voice, but the track has sound
        with self.assertRaisesRegex(ValueError, "corrected word timings"):
            anim.limit_sfx(np.zeros(SR), fx_track(), [], SR)  # silence alone is not enough: the project must declare it

    def test_silent_no_voice_passes_unchanged(self):
        e = fx_track()
        out = anim.limit_sfx(np.zeros(SR), e, [], SR, no_voice=True)
        np.testing.assert_array_equal(out, e)  # nothing to protect: effects are never raised or cut
        r = anim.check_sfx(np.zeros(SR), e, [], SR, 0, 1, no_voice=True)
        self.assertEqual((r["status"], r["violations"], r["measured_windows"], r["minimum_db"]), ("passed", 0, 0, None))

    def test_voiced_with_timings_unchanged(self):
        voice, e = np.full(SR, 0.1), fx_track()
        a = anim.limit_sfx(voice, e, [(0.0, 0.5)], SR)
        self.assertLess(np.abs(a[1000:3000]).max(), 0.3)  # still ducked under speech
        self.assertEqual(anim.check_sfx(voice, a, [(0.0, 0.5)], SR, 0, 1)["status"], "passed")


class PrepareEffects(unittest.TestCase):
    def make(self, meta, voice):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        for sub in ("01_voice", "02_transcript", "03_cues", "05_render"):
            (d / sub).mkdir()
        (d / "project.json").write_text(json.dumps(meta))
        (d / "03_cues/cues.json").write_text(json.dumps({"meta": {"duration": 1.0}, "cueList": [{"start": 0.05, "sfx": ["pop"]}], "words": []}))
        (d / "03_cues/cues.md").write_text("# Cues\n")
        path = d / "01_voice/voice.wav"
        synth.write_wav(path, np.zeros(SR)) if voice == "silent" else noisy_wav(path)
        return d, path

    def test_declared_no_voice(self):
        d, _ = self.make({"template": "carousel-reel", "template_voice": "none"}, "silent")
        self.assertTrue(anim.declared_no_voice(d))
        for meta in ({"template": "carousel-reel", "template_voice": "short"}, {"engine": "hyperframes"}):
            (d / "project.json").write_text(json.dumps(meta))
            self.assertFalse(anim.declared_no_voice(d))

    def test_variant_a_mix_passes(self):
        d, voice = self.make({"template": "carousel-reel", "template_voice": "none"}, "silent")
        r = anim.prepare_effects(d, voice, fx_track(), d / "05_render/fx.wav", 0.0, 1.0)
        self.assertEqual((r["status"], r["violations"], r["measured_windows"]), ("passed", 0, 0))
        self.assertIn("no_voice", r)
        self.assertRegex(r["effect_track_sha256"], r"^[0-9a-f]{64}$")

    def test_voiced_project_without_timings_still_fails(self):
        d, voice = self.make({"engine": "hyperframes"}, "noise")
        with self.assertRaisesRegex(ValueError, "corrected word timings"):
            anim.prepare_effects(d, voice, fx_track(), d / "05_render/fx.wav", 0.0, 1.0)
        d, voice = self.make({"engine": "hyperframes"}, "silent")  # silent track but not a declared no-voice project
        with self.assertRaisesRegex(ValueError, "corrected word timings"):
            anim.prepare_effects(d, voice, fx_track(), d / "05_render/fx.wav", 0.0, 1.0)

    def test_declared_no_voice_with_sound_fails(self):
        d, voice = self.make({"template": "carousel-reel", "template_voice": "none"}, "noise")
        with self.assertRaisesRegex(ValueError, "not silent"):
            anim.prepare_effects(d, voice, fx_track(), d / "05_render/fx.wav", 0.0, 1.0)


if __name__ == "__main__":
    unittest.main()
