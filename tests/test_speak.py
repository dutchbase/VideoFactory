import argparse
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import anim


class SpeakTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.stage = self.root / 'videos/demo/01_voice'
        self.stage.mkdir(parents=True)
        (self.root / '_shared').mkdir()
        (self.stage.parent / 'project.json').write_text('{"brand":"videofactory"}')
        self.cfg = dict(voice_id='JBFqnCBsd6RMkjVDRZzb', model='eleven_v4', stability='natural', similarity_boost='0.75', format='mp3_44100_128')
        self.script('Hello there. ' * 30)
        self.args = argparse.Namespace(slug='demo', chunk=None, dry_run=False, check=False, stability=None, skip_tone=False, confirm_script='a' * 64)
        for name, value in [('ROOT', self.root), ('VIDEOS', self.root / 'videos')]:
            p = patch.object(anim, name, value); p.start(); self.addCleanup(p.stop)
        self.api = patch.object(anim, 'eleven', return_value=b'audio').start()
        self.key = patch.object(anim, 'eleven_key', return_value='secret').start()
        self.tone = patch.object(anim, 'tone_gate').start()
        self.confirm = patch.object(anim, 'require_script_confirmation').start()
        self.run = patch.object(anim.subprocess, 'run', side_effect=self.ffmpeg).start()
        patch.object(anim, 'probe_duration', return_value=1).start()
        self.addCleanup(patch.stopall)

    def script(self, text):
        (self.stage / 'script.md').write_text('```\n' + text + '\n```')

    def ffmpeg(self, args, **kwargs):
        Path(args[-1]).write_bytes(b'final')

    def speak(self):
        with patch.object(anim, 'voice_config', return_value=self.cfg), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            anim.cmd_speak(self.args)

    def test_factory_defaults(self):
        with patch.object(anim, 'ROOT', Path(anim.__file__).parent):
            with tempfile.TemporaryDirectory() as directory:
                project = Path(directory)
                (project / "project.json").write_text('{"brand":"videofactory"}')
                cfg = anim.voice_config(project)
        # the voice in brands/videofactory/voice.md
        self.assertEqual(cfg, self.cfg)

    def test_payload_and_tags(self):
        text = '[whispers] Hello there. ' * 20
        self.script(text)
        self.speak()
        body = self.api.call_args.args[2]
        self.assertEqual(body, dict(text=text.strip(), model_id='eleven_v4', voice_settings=dict(stability=0.5, similarity_boost=0.75)))
        self.assertNotIn('[whispers]', self.tone.call_args.args[1]['script'])
        self.assertIn('Hello there.', self.tone.call_args.args[1]['script'])
        self.assertEqual((self.stage / 'takes/01.txt').read_text(), text.strip())

    def test_legacy_payload(self):
        self.cfg['model'] = 'eleven_multilingual_v2'
        self.speak()
        self.assertEqual(self.api.call_args.args[2]['voice_settings'], {'stability': 0.5})

    def test_invalid_inputs_before_auth(self):
        for field, value in [('stability', 'bad'), ('similarity_boost', 'nan'), ('similarity_boost', '1.1'), ('similarity_boost', 'no'), ('format', 'pcm_44100'), ('voice_id', ''), ('model', '')]:
            with self.subTest(field=field, value=value):
                old = self.cfg[field]; self.cfg[field] = value
                try:
                    with self.assertRaises(SystemExit): self.speak()
                finally:
                    self.cfg[field] = old
        for text in ['', '[whispers]', 'x' * 10001]:
            self.script(text)
            with self.assertRaises(SystemExit): self.speak()
        self.script('Hello.')
        for chunk in [0, -1, 2]:
            self.args.chunk = chunk
            with self.assertRaises(SystemExit): self.speak()
        self.key.assert_not_called()
        self.api.assert_not_called()

    def test_dry_run_is_read_only(self):
        self.args.dry_run = True
        before = sorted(self.root.rglob('*'))
        self.speak()
        self.key.assert_not_called(); self.api.assert_not_called(); self.run.assert_not_called()
        self.assertEqual(before, sorted(self.root.rglob('*')))
        self.confirm.assert_not_called()

    def test_unconfirmed_generation_stops_before_auth(self):
        self.confirm.side_effect = SystemExit(1)
        with self.assertRaises(SystemExit):
            self.speak()
        self.key.assert_not_called()
        self.api.assert_not_called()

    def test_first_fenced_block_is_the_only_narration(self):
        text = '# Draft\n```\nSpoken words only.\n```\n\nVisual: show a folder.\n```json\n{}\n```'
        self.assertEqual(anim.script_chunks(text), ['Spoken words only.'])

    def test_dry_run_check_combination_stops_before_auth(self):
        self.args.dry_run = self.args.check = True
        self.api.side_effect = [b'[ {"model_id":"eleven_v4", "can_do_text_to_speech":true} ]', b'{"name":"Lauren"}', b'{}']
        with self.assertRaises(SystemExit): self.speak()
        self.key.assert_not_called()
        self.api.assert_not_called()
        self.assertFalse((self.stage / 'takes').exists())

    def test_check_model_capability(self):
        self.args.check = True
        for models in [[], [{'model_id': 'eleven_v4', 'can_do_text_to_speech': False}]]:
            self.api.return_value = json.dumps(models).encode()
            with self.assertRaises(SystemExit): self.speak()
        self.api.side_effect = [json.dumps([{'model_id':'eleven_v4','can_do_text_to_speech':True}]).encode(), b'{"name":"Lauren","high_quality_base_model_ids":["old"]}', b'{}']
        self.speak()
        self.assertTrue(all(len(c.args) == 2 for c in self.api.call_args_list))
        self.run.assert_not_called()

    def test_spoken_tone_still_checked(self):
        self.tone.side_effect = SystemExit(1)
        with self.assertRaises(SystemExit): self.speak()
        self.api.assert_not_called()

    def test_matching_takes_reused_and_settings_invalidate(self):
        self.speak()
        self.api.reset_mock()
        self.speak()
        self.api.assert_not_called()
        for field, value in [('model', 'eleven_multilingual_v2'), ('voice_id', 'other'), ('stability', 'robust'), ('model', 'eleven_v4'), ('similarity_boost', '0.6'), ('format', 'mp3_44100_192')]:
            self.cfg[field] = value
            self.api.reset_mock(); self.speak()
            self.assertEqual(self.api.call_count, 1, field)
        self.script('Changed words. ' * 30)
        self.api.reset_mock(); self.speak()
        self.assertEqual(self.api.call_count, 1)
        meta = json.loads((self.stage / 'takes/01.json').read_text())
        self.assertEqual(meta['body'], self.api.call_args.args[2])
        self.assertNotIn('secret', json.dumps(meta))

    def test_missing_or_malformed_metadata_is_stale(self):
        self.speak()
        meta = self.stage / 'takes/01.json'
        for value in [None, '{bad', '[]']:
            if value is None: meta.unlink(missing_ok=True)
            else: meta.write_text(value)
            self.api.reset_mock(); self.speak()
            self.assertEqual(self.api.call_count, 1)

    def test_full_run_records_voice_selection(self):
        self.speak()
        meta = json.loads((self.stage.parent / 'project.json').read_text())
        self.assertEqual(meta['voice'], {'path': '01_voice/voice.mp3', 'origin': 'generated', 'script_fingerprint': 'a' * 64})
        self.assertEqual(meta['voice_test']['path'], '01_voice/takes/01.mp3')

    def test_partial_reroll_never_mixes_settings(self):
        self.script('First paragraph. ' * 20 + '\n\n' + 'Second paragraph. ' * 20)
        self.speak()
        (self.stage / 'voice.mp3').write_bytes(b'previous')
        self.cfg['voice_id'] = 'other'
        self.args.chunk = 1
        self.api.reset_mock(); self.run.reset_mock()
        self.speak()
        self.assertEqual(self.api.call_count, 1)
        self.run.assert_not_called()
        self.assertEqual((self.stage / 'voice.mp3').read_bytes(), b'previous')
        self.args.chunk = None
        self.api.reset_mock(); self.speak()
        self.assertEqual(self.api.call_count, 1)
        self.assertEqual((self.stage / 'voice.mp3').read_bytes(), b'final')

    def test_failures_preserve_final_and_invalidate_interrupted_take(self):
        self.speak()
        final = self.stage / 'voice.mp3'
        final.write_bytes(b'previous')
        self.args.chunk = 1
        self.api.side_effect = SystemExit(1)
        with self.assertRaises(SystemExit): self.speak()
        self.assertEqual(final.read_bytes(), b'previous')
        self.api.side_effect = None
        def failed_ffmpeg(args, **kwargs):
            Path(args[-1]).write_bytes(b'partial audio')
            raise RuntimeError('ffmpeg failed')
        self.run.side_effect = failed_ffmpeg
        with self.assertRaises(RuntimeError): self.speak()
        self.assertEqual(final.read_bytes(), b'previous')
        real_write = Path.write_text
        def interrupted(path, *args, **kwargs):
            if path.suffix == '.txt': raise OSError('interrupted')
            return real_write(path, *args, **kwargs)
        with patch.object(Path, 'write_text', interrupted):
            with self.assertRaises(OSError): self.speak()
        self.assertFalse((self.stage / 'takes/01.json').exists())
        self.assertEqual(final.read_bytes(), b'previous')


if __name__ == '__main__':
    unittest.main()
