import json, subprocess, sys, tempfile, unittest, wave
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import libcore as L
import stock as S
import library as LIB
import anim

FIX = Path(__file__).parent / "fixtures" / "openverse_audio.json"


def track(id, secs, lic="cc0"):
    return {"id": id, "title": "T " + id, "license": lic, "duration": secs * 1000, "url": f"https://cdn/{id}.mp3",
            "creator": "Zed", "foreign_landing_url": f"https://freesound.org/{id}"}


def fake(results, calls=None):
    def fetch(url, headers):
        if calls is not None:
            calls.append(url)
        if url.endswith(".mp3"):
            return b"ID3audio"
        return json.dumps({"results": results}).encode()
    return fetch


class MusicSearch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = S.CACHE
        S.CACHE = Path(self.tmp.name)

    def tearDown(self):
        S.CACHE = self.old
        self.tmp.cleanup()

    def test_real_fixture_maps(self):
        items = S.search("openverse", "ambient", "audio", fetch=lambda u, h: FIX.read_bytes())
        self.assertTrue(items)
        self.assertTrue(all(i["kind"] == "audio" and i["license"] == "CC0-1.0" and i["duration"] >= 30 for i in items))
        L.check_license(items[0]["license"])

    def test_short_and_non_cc0_are_dropped(self):
        items = S.search("openverse", "x", "audio", fetch=fake([track("a", 5), track("b", 90, "by"), track("c", 90)]))
        self.assertEqual([i["id"] for i in items], ["c"])

    def test_empty_result(self):
        self.assertEqual(S.search("openverse", "zzzz", "audio", fetch=fake([])), [])

    def test_audio_and_provider_must_match(self):
        with self.assertRaises(ValueError):
            S.search("pexels", "x", "audio", fetch=fake([]))
        with self.assertRaises(ValueError):
            S.search("openverse", "x", "video", fetch=fake([]))

    def test_download_and_use_log_licence(self):
        fetch = fake([track("c", 90)])
        item = S.search("openverse", "x", "audio", fetch=fetch)[0]
        vdir = Path(self.tmp.name) / "videos" / "videofactory" / "demo"
        vdir.mkdir(parents=True)
        (vdir / "project.json").write_text(json.dumps({"brand": "videofactory"}))
        lines = LIB.use(vdir, item["ref"], fetch=fetch)
        dest = vdir / "04_scene" / "assets" / "music-openverse-c.mp3"
        self.assertEqual(dest.read_bytes(), b"ID3audio")
        self.assertIn("CC0-1.0", (vdir / "04_scene" / "assets" / "library.md").read_text(encoding="utf-8"))
        self.assertNotIn("endorse", " ".join(lines).lower())


def sine(path, secs):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency=440:duration={secs}", str(path)], check=True)


def wav_seconds(p):
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


class BedFromFile(unittest.TestCase):
    def test_short_loops_long_trims(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for secs in (1, 30):
                src, out = d / f"in{secs}.mp3", d / f"out{secs}.wav"
                sine(src, secs)
                anim.bed_from_file(src, 10, 0.2, out)
                self.assertTrue(10 <= wav_seconds(out) <= 11.1, wav_seconds(out))  # covers the video, never longer than video + 1 s

    def test_missing_file_fails_loud(self):
        with self.assertRaises(SystemExit):
            anim.bed_from_file(Path("/nonexistent/x.mp3"), 10, 0.2, Path("/tmp/x.wav"))


if __name__ == "__main__":
    unittest.main()


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_runtime"))
import synth
import numpy as np


class NewSfx(unittest.TestCase):
    def test_new_effects_render(self):
        for n in ("riser", "impact", "click", "key"):
            s = synth.render_sfx(n)
            self.assertTrue(len(s) > 0 and np.max(np.abs(s)) <= 1.0, n)

    def test_riser_ends_on_cue(self):
        _, fx = synth.soundtrack(4.0, None, [(3.0, "riser")])
        e = np.abs(fx)
        self.assertLess(e[int(3.05 * synth.SR):].max(), 0.01)
        self.assertGreater(e[int(2.8 * synth.SR):int(3.0 * synth.SR)].max(), 0.05)

    def test_old_effects_unchanged(self):  # start-aligned exactly as before
        _, fx = synth.soundtrack(2.0, None, [(1.0, "pop")])
        exp, s, i = np.zeros_like(fx), synth.render_sfx("pop"), int(1.0 * synth.SR)
        exp[i:i + len(s)] = s
        np.testing.assert_array_equal(fx, exp)


class SfxBalance(unittest.TestCase):
    def test_soft_voice_and_overlapping_effects(self):
        voice = np.full(44100, .02)
        fx = np.full(44100, .8) + np.full(44100, .8)
        self.assertGreater(fx.max() * anim.FX_GAIN, voice.max())
        out = anim.limit_sfx(voice, fx, [(0, 1)], 44100)
        self.assertLessEqual(abs(out).max(), .02 * 10 ** (-anim.SFX_DISTANCE_DB / 20))
        np.testing.assert_array_equal(voice, np.full(44100, .02))

    def test_loud_voice_silence_stereo_and_impact(self):
        sr = 1000
        voice = np.full((1000, 2), .8)
        voice[200:400] = 0
        fx = np.full(1000, .01); fx[100] = 1
        out = anim.limit_sfx(voice, fx, [(0, 1)], sr)
        self.assertEqual(out[300], fx[300])  # a pause inside a word keeps the effect at its level
        self.assertLessEqual(out[100], .8 * 10 ** (-anim.SFX_DISTANCE_DB / 20))
        self.assertTrue(np.all(abs(out) <= abs(fx)))
        np.testing.assert_array_equal(out, anim.limit_sfx(voice, fx, [(0, 1)], sr))

    def test_empty_effects_and_word_edges(self):
        sr = 1000
        voice = np.full(1000, .02)
        np.testing.assert_array_equal(anim.limit_sfx(voice, np.zeros(1000), [], sr), np.zeros(1000))
        self.assertEqual(anim.limit_sfx(voice, np.array([]), [], sr).size, 0)
        fx = np.ones(1000)
        out = anim.limit_sfx(voice, fx, [(.2, .4)], sr)
        self.assertLessEqual(out[150:550].max(), .02 * 10 ** (-anim.SFX_DISTANCE_DB / 20))
        self.assertEqual(out[800], 1)
        np.testing.assert_array_equal(out[200:400], anim.limit_sfx(voice, fx, [(.2, .4)], sr)[200:400])

    def test_effect_on_a_word_stays_audible(self):
        # a stop consonant (30 ms of silence) inside a word must not mute the effect over it
        sr = 44100
        voice = np.zeros(sr * 2); voice[int(.5 * sr):int(1.5 * sr)] = .2
        voice[int(.5 * sr):int(.56 * sr)] *= np.linspace(0, 1, int(.06 * sr))  # soft onset
        voice[int(.9 * sr):int(.93 * sr)] = 0
        fx = np.zeros(sr * 2); fx[int(.5 * sr):int(1.0 * sr)] = .5
        out = anim.limit_sfx(voice, fx, [(.5, 1.5)], sr)
        rms = lambda a: float(np.sqrt(np.mean(a ** 2)))
        self.assertGreater(rms(out[int(.9 * sr):int(.93 * sr)]), .2 * 10 ** (-20 / 20))
        self.assertGreater(rms(out[int(.5 * sr):int(.56 * sr)]), .2 * 10 ** (-24 / 20))
        self.assertEqual(anim.check_sfx(voice, out, [(.5, 1.5)], sr, 0, 2)['violations'], 0)

    def test_effects_sit_3_db_under_the_voice(self):
        # the user's choice (2026-10-21): during speech effects stay 3 dB under the voice, not 12
        self.assertEqual(anim.SFX_DISTANCE_DB, 3)
        voice, fx = np.full(1000, .2), np.full(1000, .2 * 10 ** (-5 / 20))
        np.testing.assert_allclose(anim.limit_sfx(voice, fx, [(0, 1)], 1000), fx)
        self.assertEqual(anim.check_sfx(voice, fx, [(0, 1)], 1000, 0, 1)['violations'], 0)
        self.assertGreater(anim.check_sfx(voice, voice, [(0, 1)], 1000, 0, 1)['violations'], 0)

    def test_missing_timings_fail(self):
        with self.assertRaisesRegex(ValueError, 'word timings'):
            anim.limit_sfx(np.ones(100), np.ones(100), [], 1000)


class AudioExportChecks(unittest.TestCase):
    def test_written_stem_gain_one_and_fragment(self):
        with tempfile.TemporaryDirectory() as directory:
            vdir = Path(directory)
            for name in ('01_voice', '02_transcript', '03_cues', '05_render'):
                (vdir / name).mkdir()
            sr = 44100
            voice = np.full(sr * 2, .02); voice[sr:sr + sr // 2] = 0
            synth.write_wav(vdir / '01_voice/voice.wav', voice)
            words = [{'start': 0, 'end': .8}, {'start': 1.5, 'end': 2}]
            (vdir / '02_transcript/words.json').write_text(json.dumps({'words': words}))
            (vdir / '03_cues/cues.json').write_text(json.dumps({'words': words}))
            fx = np.full(sr * 2, .8) + np.full(sr * 2, .8)
            full = anim.prepare_effects(vdir, vdir / '01_voice/voice.wav', fx, vdir / '05_render/full.wav', 0, 2)
            cut = anim.prepare_effects(vdir, vdir / '01_voice/voice.wav', fx, vdir / '05_render/cut.wav', .4, 1.8)
            self.assertEqual(full['violations'], 0)
            self.assertGreaterEqual(full['minimum_db'], anim.SFX_DISTANCE_DB)
            self.assertEqual(cut['violations'], 0)
            np.testing.assert_array_equal(anim.decode_pcm(vdir / '05_render/full.wav'), anim.decode_pcm(vdir / '05_render/cut.wav'))

    def test_checker_detects_rms_and_peak_failures(self):
        voice = np.full(1000, .02)
        for fx in (np.full(1000, .8), np.r_[1., np.zeros(999)]):
            self.assertGreater(anim.check_sfx(voice, fx, [(0, 1)], 1000, 0, 1)['violations'], 0)

    def test_hyperframes_extra_audio_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            vdir = Path(directory); (vdir / '04_scene').mkdir(); (vdir / '01_voice').mkdir()
            voice = vdir / '01_voice/voice.wav'; voice.write_bytes(b'voice')
            index = vdir / '04_scene/index.html'
            index.write_text('<audio src="../01_voice/voice.wav"></audio>')
            anim.check_hf_audio(vdir, voice, {'meta': {}, 'cueList': []})
            for extra in ('<audio src="music.wav"></audio>', '<video src="clip.mp4"></video>', '<script>new Audio("fx.wav")</script>'):
                index.write_text('<audio src="../01_voice/voice.wav"></audio>' + extra)
                with self.assertRaisesRegex(ValueError, 'separate tracks'):
                    anim.check_hf_audio(vdir, voice, {'meta': {}, 'cueList': []})


class HyperframesVoiceCompatibility(unittest.TestCase):
    def test_existing_template_voice_remains_supported(self):
        from studio.workspace import stamp_hf_scene
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            vdir = Path(directory) / 'videos/videofactory/demo'  # the stamp links brand and runtime relative to videos/
            shutil.copytree(anim.ROOT / '_templates/scene-hf-wide', vdir / '04_scene')
            (vdir / '01_voice').mkdir(); voice = vdir / '01_voice/voice.wav'; voice.write_bytes(b'voice')
            stamp_hf_scene(vdir / '04_scene', 'videofactory', 'voice.wav')
            anim.check_hf_audio(vdir, voice, {'meta': {}, 'cueList': []})


class EncodedStereoEffects(unittest.TestCase):
    def test_stereo_wav_retains_channels_and_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'stereo.wav'
            fx = np.column_stack((np.full(4410, .02), np.full(4410, .04)))
            synth.write_wav(out, fx)
            with wave.open(str(out)) as wav:
                self.assertEqual(wav.getnchannels(), 2)
                self.assertEqual(wav.getnframes(), 4410)
            np.testing.assert_allclose(anim.decode_pcm(out), fx, atol=1/32767)


class HyperframesModuleAudio(unittest.TestCase):
    def test_module_and_remote_audio_scripts_cannot_bypass(self):
        with tempfile.TemporaryDirectory() as directory:
            vdir = Path(directory); (vdir / '04_scene').mkdir(); (vdir / '01_voice').mkdir()
            voice = vdir / '01_voice/voice.wav'; voice.write_bytes(b'voice')
            (vdir/'04_scene/extra.mjs').write_text('new Audio("music.wav").play();')
            index = vdir/'04_scene/index.html'
            for src in ('extra.mjs', 'https://example.com/extra.js'):
                index.write_text('<audio src="../01_voice/voice.wav"></audio><script type="module" src="'+src+'"></script>')
                with self.assertRaisesRegex(ValueError, 'separate tracks'):
                    anim.check_hf_audio(vdir,voice,{'meta':{},'cueList':[]})


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _clip(path, audio):
    """A 1 s 64x64 test clip, with or without an audio stream."""
    a = ["-f", "lavfi", "-i", "sine=frequency=440:duration=1"] if audio else []
    _ff("-f", "lavfi", "-i", "testsrc=size=64x64:rate=12:duration=1", *a, *(["-shortest"] if audio else []), str(path))


class HyperframesMix(unittest.TestCase):
    """HyperFrames videos get the same music bed and effects as canvas videos (mix_soundtrack)."""

    def _scene(self, directory):
        vdir = Path(directory); (vdir / '04_scene/assets').mkdir(parents=True); (vdir / '01_voice').mkdir()
        voice = vdir / '01_voice/voice.wav'; voice.write_bytes(b'voice')
        return vdir, voice

    def test_hyperframes_music_mixed(self):
        with tempfile.TemporaryDirectory() as directory:
            vdir, voice = self._scene(directory)
            (vdir / '04_scene/index.html').write_text('<audio src="../01_voice/voice.wav"></audio>')
            cues = {'meta': {'music': 'file:bed.mp3', 'music_gain': 0.2}, 'cueList': [{'start': 1.0, 'sfx': ['click']}]}
            anim.check_hf_audio(vdir, voice, cues)  # no error: the render mixes music and effects itself

    def test_hf_render_uses_mix_soundtrack(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as directory:
            vdir, voice = self._scene(directory)
            (vdir / '03_cues').mkdir()
            (vdir / '03_cues/cues.json').write_text(json.dumps({'meta': {'duration': 1.0}, 'cueList': []}))
            def fake_hf(*args, cwd):
                _clip(Path(args[args.index('-o') + 1]), audio=True)
                return subprocess.CompletedProcess(args, 0)
            a = type('A', (), dict(slug='x', start=None, end=None, blur=1, fps=12, skip_tone=True, skip_check=True))()
            with mock.patch.object(anim, 'hf', fake_hf), mock.patch.object(anim, 'tone_gate'), \
                 mock.patch.object(anim, 'screen_text', return_value={}), mock.patch.object(anim, 'find_voice', return_value=voice), \
                 mock.patch.object(anim, 'check_hf_audio'), mock.patch.object(anim, 'audio_sources', return_value={}), \
                 mock.patch.object(anim, 'mix_soundtrack', side_effect=lambda v, vo, args, out, t0, t1: (_clip(out, True), {})[1]) as mix, \
                 mock.patch.object(anim, 'after_render'), mock.patch.object(anim, 'probe_duration', return_value=1.0), mock.patch('sys.stdout'):
                anim.hf_render(a, vdir)
            args = mix.call_args.args
            self.assertEqual(args[2][0], '-i')
            self.assertEqual(args[3], vdir / '05_render/x.mp4')

    def test_hyperframes_video_without_audio_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            vdir, voice = self._scene(directory)
            _clip(vdir / '04_scene/assets/x.mp4', audio=False)
            (vdir / '04_scene/index.html').write_text('<audio src="../01_voice/voice.wav"></audio><video class="clip" src="assets/x.mp4"></video>')
            anim.check_hf_audio(vdir, voice, {'meta': {}, 'cueList': []})

    def test_hyperframes_video_with_audio_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            vdir, voice = self._scene(directory)
            _clip(vdir / '04_scene/assets/x.mp4', audio=True)
            (vdir / '04_scene/index.html').write_text('<audio src="../01_voice/voice.wav"></audio><video class="clip" src="assets/x.mp4"></video>')
            with self.assertRaisesRegex(ValueError, 'separate tracks'):
                anim.check_hf_audio(vdir, voice, {'meta': {}, 'cueList': []})

    def test_use_stock_video_strips_audio(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as directory:
            vdir = Path(directory) / 'v'; (vdir / '04_scene').mkdir(parents=True)
            (vdir / 'project.json').write_text(json.dumps({'engine': 'hyperframes', 'brand': 'videofactory'}))
            src = Path(directory) / 'stock.mp4'; _clip(src, audio=True)
            item = {'provider': 'pexels', 'id': '1', 'kind': 'video', 'license': 'Pexels', 'page_url': 'https://x', 'author': 'a'}
            with mock.patch.object(S, 'load_item', return_value=item), mock.patch.object(S, 'download', return_value=src):
                LIB.use(vdir, 'stock:pexels/video/1', 'bg', '0', '0:01')
            out = vdir / '04_scene/assets/bg.mp4'
            self.assertTrue(out.exists())
            self.assertFalse(anim.has_audio(out))
