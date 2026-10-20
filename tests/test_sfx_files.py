"""Sound effect files in the mixer: [sfx: file:<name> [gain]] plays a CC0 or licensed file from
04_scene/assets/ (or library/sfx/); unknown effects stop check and render instead of being skipped silently."""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "_runtime")); sys.path.insert(0, str(ROOT / "tests"))
import anim
import check
import synth
from test_check_rules import LINT, SOUND_MD, WITH_BLOCK, cues_every, hf_video, run_hf_check

LICENSED = SOUND_MD + "- door.wav: https://freesound.org/s/1 (CC0 1.0), cue s0, a door on the cut\n"


def wav(path, seconds=0.2, rate=22050, channels=2, amp=0.9):
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}:sample_rate={rate}",
                    "-af", f"volume={amp}", "-ac", str(channels), str(path)], check=True)
    return path


class Parse(unittest.TestCase):
    def test_tokens(self):
        self.assertEqual(synth.parse_sfx("pop"), ("builtin", "pop", 1.0))
        self.assertEqual(synth.parse_sfx("whoosh 0.5"), ("builtin", "whoosh", 0.5))
        self.assertEqual(synth.parse_sfx("file:door.wav"), ("file", "door.wav", 1.0))
        self.assertEqual(synth.parse_sfx(" file:sfx/door-1.mp3 .8 "), ("file", "sfx/door-1.mp3", 0.8))

    def test_bad_tokens(self):
        for token in ("popp", "file:../x.wav", "file:/etc/x.wav", "file:notes.txt", "file:door.wav loud", "pop, tick"):
            with self.assertRaises(ValueError, msg=token):
                synth.parse_sfx(token)

    def test_cue_heading_keeps_file_tokens(self):
        cues = anim.parse_cues_md('## intro "hallo daar" [sfx: file:door.wav 0.5, pop]\n')
        self.assertEqual(cues[0]["sfx"], ["file:door.wav 0.5", "pop"])
        self.assertEqual(cues[0]["offset"], 0.0)  # the gain is not read as a cue offset


class Soundtrack(unittest.TestCase):
    def test_file_effect_placed_normalised_and_gained(self):
        clip = np.r_[np.zeros(10), np.full(100, 0.9), np.zeros(10)]
        _, fx = synth.soundtrack(2.0, None, [(1.0, "file:door.wav 0.5")], files={"door.wav": clip})
        i = int(1.0 * synth.SR)
        self.assertFalse(np.any(fx[:i]))
        self.assertAlmostEqual(float(np.max(np.abs(fx))), synth.FILE_PEAK * 0.5)
        self.assertAlmostEqual(float(fx[i + 10]), synth.FILE_PEAK * 0.5)

    def test_builtin_gain(self):
        _, a = synth.soundtrack(2.0, None, [(1.0, "pop")])
        _, b = synth.soundtrack(2.0, None, [(1.0, "pop 0.5")])
        np.testing.assert_allclose(b, a * 0.5)

    def test_unknown_effect_is_an_error(self):  # it used to be skipped silently
        with self.assertRaisesRegex(ValueError, "unknown sound effect"):
            synth.soundtrack(2.0, None, [(1.0, "popp")])
        with self.assertRaisesRegex(ValueError, "not loaded"):
            synth.soundtrack(2.0, None, [(1.0, "file:door.wav")])

    def test_effect_past_the_end_is_cut(self):
        _, fx = synth.soundtrack(1.0, None, [(5.0, "file:door.wav")], files={"door.wav": np.ones(10)})
        self.assertFalse(np.any(fx))


class Files(unittest.TestCase):
    def test_lookup_assets_then_library(self):
        with tempfile.TemporaryDirectory() as d:
            vdir, lib = Path(d) / "v", Path(d) / "lib"
            shared = wav(lib / "door.wav")
            with mock.patch.object(anim, "SFX_LIBRARY", lib):
                self.assertEqual(anim.sfx_file(vdir, "door.wav"), shared)
                own = wav(vdir / "04_scene/assets/door.wav")
                self.assertEqual(anim.sfx_file(vdir, "door.wav"), own)
                self.assertIsNone(anim.sfx_file(vdir, "bell.wav"))

    def test_decode_resamples_to_mono_44k(self):
        with tempfile.TemporaryDirectory() as d:
            vdir = Path(d) / "v"
            wav(vdir / "04_scene/assets/door.wav", seconds=0.5, rate=22050, channels=2)
            pcm = anim.load_sfx_files(vdir, [(1.0, "file:door.wav 0.5"), (2.0, "file:door.wav"), (3.0, "pop")])
            self.assertEqual(list(pcm), ["door.wav"])
            self.assertEqual(pcm["door.wav"].ndim, 1)
            self.assertAlmostEqual(len(pcm["door.wav"]) / synth.SR, 0.5, delta=0.02)

    def test_missing_file_or_unknown_name_stops(self):
        with tempfile.TemporaryDirectory() as d, mock.patch("sys.stderr"):
            with self.assertRaises(SystemExit):
                anim.load_sfx_files(Path(d), [(1.0, "file:door.wav")])
            with self.assertRaises(SystemExit):
                anim.load_sfx_files(Path(d), [(1.0, "popp")])


class Mix(unittest.TestCase):
    """mix_soundtrack puts the file effect on the effect stem at its cue, with the video's sfx: level."""

    def video(self, d, sfx):
        vdir = Path(d) / "v"
        (vdir / "03_cues").mkdir(parents=True); (vdir / "01_voice").mkdir()
        (vdir / "03_cues/cues.md").write_text('sfx: 0.4\n## a "hallo" [sfx: %s]\n' % sfx)
        (vdir / "03_cues/cues.json").write_text(json.dumps({"meta": {"duration": 3.0}, "cueList": [{"id": "a", "start": 1.0, "sfx": [sfx]}]}))
        voice = vdir / "01_voice/voice.wav"; voice.write_bytes(b"voice")
        return vdir, voice

    def test_file_effect_reaches_the_effect_stem(self):
        with tempfile.TemporaryDirectory() as d:
            vdir, voice = self.video(d, "file:door.wav")
            wav(vdir / "04_scene/assets/door.wav", seconds=0.2)
            seen = {}

            def stop(vd, vo, fx, out, t0, t1):
                seen["fx"] = fx
                raise RuntimeError("stop before the final mux")
            with mock.patch.object(anim, "prepare_effects", side_effect=stop), mock.patch.object(anim, "audio_sources", return_value={}), \
                 self.assertRaisesRegex(RuntimeError, "final mux"):
                anim.mix_soundtrack(vdir, voice, ["-i", "frames.mp4"], vdir / "out.mp4", 0.0, 3.0)
            fx, i = seen["fx"], int(1.0 * synth.SR)
            self.assertFalse(np.any(fx[:i - 1]))
            self.assertAlmostEqual(float(np.max(np.abs(fx[i:i + int(0.25 * synth.SR)]))), synth.FILE_PEAK * 0.4, places=2)

    def test_unknown_effect_stops_render_mix(self):
        for sfx in ("file:door.wav", "popp"):
            with tempfile.TemporaryDirectory() as d, mock.patch("sys.stderr"):
                vdir, voice = self.video(d, sfx)
                with mock.patch.object(anim, "prepare_effects") as prep, mock.patch.object(anim, "audio_sources", return_value={}), \
                     self.assertRaises(SystemExit):
                    anim.mix_soundtrack(vdir, voice, ["-i", "frames.mp4"], vdir / "out.mp4", 0.0, 3.0)
                prep.assert_not_called()

    def test_audio_sources_hash_the_effect_file(self):
        with tempfile.TemporaryDirectory() as d:
            vdir, voice = self.video(d, "file:door.wav 0.5")
            door = wav(vdir / "04_scene/assets/door.wav")
            self.assertIn(str(door.resolve()), anim.audio_sources(vdir, voice))


class Check(unittest.TestCase):
    def reel(self, d, sfx, sound_md=LICENSED, files=("door.wav",), **kw):
        vdir = hf_video(d, WITH_BLOCK, cue_list=cues_every(4.0, 36.0, sfx=sfx), duration=36.0, sound_md=sound_md, **kw)
        for name in files:
            wav(vdir / "04_scene/assets" / name)
        return run_hf_check(vdir)

    def test_licensed_file_effect_passes_and_counts_as_sound_design(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.reel(d, ("file:door.wav 0.6",))
            self.assertEqual([r["counters"][k] for k in check.SFX_KEYS + check.QUALITY_KEYS], [0, 0, 0, 0])
            self.assertTrue(set(check.SFX_KEYS) <= set(r["fail_keys"]) and set(check.SFX_KEYS) <= set(check.FAIL_KEYS))
            self.assertIn("sound effect unknown", (Path(d) / "v/05_render/check.md").read_text())

    def test_unknown_names_and_missing_files_count(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.reel(d, ("popp", "file:bell.wav", "whoosh"), files=())
            self.assertEqual(r["counters"]["sound effect unknown"], 2)
            self.assertTrue(any("popp" in x for x in r["details"]) and any("bell.wav" in x for x in r["details"]))

    def test_file_effect_needs_source_and_licence_line(self):
        for sound_md in (SOUND_MD, SOUND_MD + "- door.wav: a door (CC0)\n", SOUND_MD + "- door.wav: https://freesound.org/s/1\n"):
            with tempfile.TemporaryDirectory() as d:
                self.assertEqual(self.reel(d, ("file:door.wav",), sound_md=sound_md)["counters"]["sound effect unlicensed"], 1, sound_md)

    def test_every_brand(self):  # third-party audio needs its record whatever the brand
        with tempfile.TemporaryDirectory() as d:
            r = self.reel(d, ("file:door.wav",), sound_md=None, brand="example")
            self.assertEqual(r["counters"]["sound effect unlicensed"], 1)
            with mock.patch("sys.stdout"), mock.patch("sys.stderr"), mock.patch.object(anim, "hf", return_value=LINT), \
                 mock.patch.object(check, "brand_counters", return_value={k: 0 for k in check.BRAND_KEYS}), self.assertRaises(SystemExit):
                anim.check_gate(Path(d) / "v")

    def test_studio_scene_readiness(self):
        from studio import workspace
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "check.md"
            base = "lint errors  0\nvideo vs voice length  0\nno visual layer  0\n"
            f.write_text(base + "sound effect unknown  1\n")
            self.assertFalse(workspace._scene_check_ok(f, "hyperframes"))
            f.write_text(base + "sound effect unknown  0\nsound effect unlicensed  0\ncomposition errors  0\n")
            self.assertTrue(workspace._scene_check_ok(f, "hyperframes"))


if __name__ == "__main__":
    unittest.main()
