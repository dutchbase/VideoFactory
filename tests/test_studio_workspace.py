import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from studio.workspace import WorkspaceError, read_file, safe_path, save_text, list_videos


class WorkspaceTests(unittest.TestCase):
    def test_external_edit_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / 'videos/demo/01_voice/script.md'
            path.parent.mkdir(parents=True)
            path.write_text('First', encoding='utf-8')
            version = read_file(root, 'videos/demo/01_voice/script.md')['revision']
            path.write_text('Agent edit', encoding='utf-8')
            with self.assertRaises(WorkspaceError) as error:
                save_text(root, 'videos/demo/01_voice/script.md', 'Manual edit', version)
            self.assertEqual(error.exception.code, 'conflict')
            self.assertEqual(path.read_text(), 'Agent edit')

    def test_private_escaping_and_symlink_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '_auth').mkdir()
            (root / '_auth/session.json').write_text('{}')
            (root / 'videos').mkdir()
            (root / 'videos/link').symlink_to(root / '_auth', target_is_directory=True)
            for name in ('../.env', '.env', '_auth/session.json', '/etc/passwd',
                         'videos/link/session.json', 'videos/demo/../x'):
                with self.subTest(name=name), self.assertRaises(WorkspaceError):
                    safe_path(root, name)

    def test_scene_links_open_only_their_own_targets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            scene = root / 'videos/house/demo/04_scene'
            for name in ('_runtime', 'brands/house/logo', 'videos/house/demo/03_cues', '_auth'):
                (root / name).mkdir(parents=True, exist_ok=True)
            scene.mkdir(parents=True)
            for name in ('_runtime/modern.css', 'brands/house/tokens.js', 'brands/house/voice.md',
                         'brands/house/logo/mark.svg', 'videos/house/demo/03_cues/cues.js',
                         'videos/house/demo/03_cues/cues.md', '_auth/session.json'):
                (root / name).write_text('x')
            (scene / 'runtime').symlink_to('../../../../_runtime')
            (scene / 'brand').symlink_to('../../../../brands/house')
            (scene / 'cues').symlink_to('../03_cues')
            (scene / 'auth').symlink_to('../../../../_auth')
            for name, real in (('runtime/modern.css', '_runtime/modern.css'), ('brand/tokens.js', 'brands/house/tokens.js'),
                               ('brand/logo/mark.svg', 'brands/house/logo/mark.svg'), ('cues/cues.js', 'videos/house/demo/03_cues/cues.js')):
                with self.subTest(name=name):
                    self.assertEqual(safe_path(root, 'videos/house/demo/04_scene/' + name), (root / real).resolve())
            for name in ('brand/voice.md', 'cues/cues.md', 'auth/session.json', 'brand/../voice.md'):
                with self.subTest(name=name), self.assertRaises(WorkspaceError):
                    safe_path(root, 'videos/house/demo/04_scene/' + name)
            with self.assertRaises(WorkspaceError):
                safe_path(root, 'videos/house/demo/04_scene/runtime/modern.css', write=True)
            (scene / 'runtime').unlink()
            (scene / 'runtime').symlink_to('../../../../_auth')
            with self.assertRaises(WorkspaceError):
                safe_path(root, 'videos/house/demo/04_scene/runtime/session.json')

    def test_failed_replace_keeps_original_and_generated_file_is_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / 'videos/demo/01_voice/script.md'
            path.parent.mkdir(parents=True)
            path.write_text('original')
            version = read_file(root, 'videos/demo/01_voice/script.md')['revision']
            with patch('studio.workspace.os.replace', side_effect=OSError('disk')):
                with self.assertRaises(WorkspaceError):
                    save_text(root, 'videos/demo/01_voice/script.md', 'new', version)
            self.assertEqual(path.read_text(), 'original')
            cues = root / 'videos/demo/03_cues/cues.js'
            cues.parent.mkdir(parents=True)
            cues.write_text('const x = 1')
            with self.assertRaises(WorkspaceError):
                save_text(root, 'videos/demo/03_cues/cues.js', 'x', read_file(root, 'videos/demo/03_cues/cues.js')['revision'])

    def test_inventory_handles_empty_and_malformed_projects(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(list_videos(root), [])
            (root / 'videos/demo').mkdir(parents=True)
            self.assertEqual(list_videos(root), [])
            (root / 'videos/demo/project.json').write_text('{"brand": "videofactory"}')
            self.assertEqual(list_videos(root)[0]['slug'], 'videofactory/demo')

    def test_word_timing_validation_preserves_original(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / 'videos/demo/02_transcript/words.json'
            path.parent.mkdir(parents=True)
            path.write_text('{"duration": 2, "words": []}')
            revision = read_file(root, 'videos/demo/02_transcript/words.json')['revision']
            with self.assertRaises(WorkspaceError):
                save_text(root, 'videos/demo/02_transcript/words.json', '{"duration": 2, "words": [{"text": "x", "start": 2, "end": 1}]}', revision)
            self.assertEqual(path.read_text(), '{"duration": 2, "words": []}')


class AudioReviewTests(unittest.TestCase):
    def test_missing_failed_stale_and_current_audio_reports(self):
        import anim
        from studio.workspace import _readiness
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); vdir = root / 'videos/demo'
            (vdir / '05_render').mkdir(parents=True); (vdir / '01_voice').mkdir(); (vdir / '03_cues').mkdir()
            (vdir / 'project.json').write_text('{"brand": "videofactory"}')
            (vdir / '03_cues/cues.json').write_text('{"meta": {"duration": 1}, "cueList": []}')
            voice = vdir / '01_voice/voice.wav'; voice.write_bytes(b'voice')
            export = vdir / '05_render/demo.mp4'; export.write_bytes(b'export')
            report = dict(voice=str(voice), effects='none (not applicable)', start=0, end=1,
                          required_db=12, minimum_db=None, violations=0, measured_windows=0,
                          status='passed', sources=anim.audio_sources(vdir, voice))
            self.assertIn('current audio check', _readiness(root, 'demo', 'render')[1])
            anim.write_audio_check(vdir, export, report)
            self.assertNotIn('current audio check', _readiness(root, 'demo', 'render')[1])
            anim.write_audio_check(vdir, export, dict(report, end=.5))
            self.assertIn('current audio check', _readiness(root, 'demo', 'render')[1])
            anim.write_audio_check(vdir, export, report)
            voice.write_bytes(b'changed')
            self.assertIn('current audio check', _readiness(root, 'demo', 'render')[1])
            voice.write_bytes(b'voice')
            export.write_bytes(b'new export')
            self.assertIn('current audio check', _readiness(root, 'demo', 'render')[1])
            anim.write_audio_check(vdir, export, dict(report, status='failed', violations=1))
            self.assertIn('current audio check', _readiness(root, 'demo', 'render')[1])


    def test_separate_effect_stem_outside_speech_passes(self):
        import anim, json
        from _runtime import synth
        import numpy as np
        from studio.workspace import _readiness
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); vdir = root / 'videos/demo'
            for sub in ('01_voice', '02_transcript', '03_cues', '05_render'):
                (vdir / sub).mkdir(parents=True)
            (vdir / 'project.json').write_text('{"brand": "videofactory"}')
            voice = vdir / '01_voice/voice.wav'; synth.write_wav(voice, np.full(44100, .02))
            words = [{'start':0, 'end':.1}]
            for sub, name in (('02_transcript','words.json'), ('03_cues','cues.json')):
                (vdir / sub / name).write_text(json.dumps({'meta': {'duration':1},'words':words,'cueList':[{'start':.8,'sfx':['pop']}]}))
            fx=np.zeros(44100); fx[35280:]=.1
            report=anim.prepare_effects(vdir,voice,fx,vdir/'05_render/fx.wav',0,1)
            export=vdir/'05_render/demo.mp4'; export.write_bytes(b'export')
            anim.write_audio_check(vdir,export,report)
            self.assertNotIn('current audio check', _readiness(root,'demo','render')[1])
