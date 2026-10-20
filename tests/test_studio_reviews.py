import tempfile
import unittest
from pathlib import Path

from studio.workspace import WorkspaceError, gate_fingerprint, mark_ready, decide_review, review_state, skip_research, set_voice_selection, create_material, link_material


class ReviewTests(unittest.TestCase):
    def _approve(self, root, gate):
        fingerprint = gate_fingerprint(root, 'demo', gate)
        mark_ready(root, 'demo', gate, fingerprint)
        decide_review(root, 'demo', gate, 'approved', 'Reviewer', '', fingerprint)

    def test_approval_is_of_saved_revision_and_upstream(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for ident in ('demo', 'silent-first-scene'):
                project = root / 'videos' / ident
                project.mkdir(parents=True, exist_ok=True)
                (project / 'project.json').write_text('{"brand": "videofactory"}')
            stage = root / 'videos/demo/01_voice'
            stage.mkdir(parents=True, exist_ok=True)
            (stage / 'brief.md').write_text('Audience: managers\nVideo type: explainer\nLanguage: English\nOne outcome: understand the workflow\n')
            (stage / 'script.md').write_text('```\nHello there.\n```\n')
            for gate in ('brief', 'script'):
                fingerprint = gate_fingerprint(root, 'demo', gate)
                mark_ready(root, 'demo', gate, fingerprint)
                decide_review(root, 'demo', gate, 'approved', 'Reviewer', '', fingerprint)
            self.assertEqual(review_state(root, 'demo', 'script')['state'], 'approved')
            (stage / 'script.md').write_text('```\nA changed opening.\n```\n')
            self.assertEqual(review_state(root, 'demo', 'script')['state'], 'stale')
            stale = gate_fingerprint(root, 'demo', 'script')
            (stage / 'script.md').write_text('A second change')
            with self.assertRaises(WorkspaceError):
                mark_ready(root, 'demo', 'script', stale)

    def test_ready_is_not_approval_and_legacy_prose_survives(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for ident in ('demo', 'silent-first-scene'):
                project = root / 'videos' / ident
                project.mkdir(parents=True, exist_ok=True)
                (project / 'project.json').write_text('{"brand": "videofactory"}')
            stage = root / 'videos/demo/01_voice'
            stage.mkdir(parents=True, exist_ok=True)
            (stage / 'brief.md').write_text('Audience: managers\nType: course\nLanguage: en\nOne outcome: learn\n')
            review = root / 'videos/demo/REVIEW.md'
            review.write_text('# Old note\nApproved by someone in 2020.\n')
            mark_ready(root, 'demo', 'brief', gate_fingerprint(root, 'demo', 'brief'))
            self.assertEqual(review_state(root, 'demo', 'brief')['state'], 'awaiting-review')
            self.assertIn('Old note', review.read_text())

    def test_unfilled_template_brief_is_not_ready(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for ident in ('demo', 'silent-first-scene'):
                project = root / 'videos' / ident
                project.mkdir(parents=True, exist_ok=True)
                (project / 'project.json').write_text('{"brand": "videofactory"}')
            stage = root / 'videos/demo/01_voice'
            stage.mkdir(parents=True, exist_ok=True)
            (stage / 'brief.md').write_text('# Brief\n- Type: course | ad\n- Language: en | nl\n- Audience:\n- One outcome:\n- Call to action: later\n')
            state = review_state(root, 'demo', 'brief')
            self.assertEqual(review_state(root, 'demo', 'research')['state'], 'not-applicable')
            self.assertFalse(state['ready'])
            self.assertIn('audience', state['missing'])
            self.assertIn('outcome', state['missing'])
            (stage / 'brief.md').write_text('Audience: managers\nType: course\nLanguage: en\nOne outcome: learn\n')
            self._approve(root, 'brief')
            (stage / 'script.md').write_text('# Narration draft\n```\nReplace this with the script.\n```\n')
            self.assertIn('script.md', review_state(root, 'demo', 'script')['missing'])

    def test_research_skip_needs_reason(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for ident in ('demo', 'silent-first-scene'):
                project = root / 'videos' / ident
                project.mkdir(parents=True, exist_ok=True)
                (project / 'project.json').write_text('{"brand": "videofactory"}')
            (root / 'videos/demo').mkdir(parents=True, exist_ok=True)
            with self.assertRaises(WorkspaceError):
                skip_research(root, 'demo', '', 'Reviewer')

    def test_source_change_stales_script_without_deleting_export(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for ident in ('demo', 'silent-first-scene'):
                project = root / 'videos' / ident
                project.mkdir(parents=True, exist_ok=True)
                (project / 'project.json').write_text('{"brand": "videofactory"}')
            voice = root / 'videos/demo/01_voice'
            voice.mkdir(parents=True, exist_ok=True)
            (voice / 'brief.md').write_text('Audience: managers\nType: course\nLanguage: en\nOne outcome: learn\n')
            (voice / 'script.md').write_text('Hello there.')
            material = root / 'library/materials/logo'
            material.mkdir(parents=True, exist_ok=True)
            (material / 'material.md').write_text('Source notes')
            (root / 'videos/demo/materials.md').write_text('## Linked materials\n```json\n["logo"]\n```\n')
            export = root / 'videos/demo/05_render/final.mp4'
            export.parent.mkdir(parents=True, exist_ok=True)
            export.write_bytes(b'old export')
            self._approve(root, 'brief')
            self._approve(root, 'script')
            (material / 'material.md').write_text('Changed source notes')
            self.assertEqual(review_state(root, 'demo', 'script')['state'], 'stale')
            self.assertEqual(export.read_bytes(), b'old export')

    def test_linked_local_source_bytes_stale_script(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for ident in ('demo', 'silent-first-scene'):
                project = root / 'videos' / ident
                project.mkdir(parents=True, exist_ok=True)
                (project / 'project.json').write_text('{"brand": "videofactory"}')
            voice = root / 'videos/demo/01_voice'
            voice.mkdir(parents=True, exist_ok=True)
            (voice / 'brief.md').write_text('Audience: managers\nType: course\nLanguage: en\nOne outcome: learn\n')
            (voice / 'script.md').write_text('A sourced statement.')
            source = root / 'library/ref.txt'
            source.parent.mkdir()
            source.write_text('Original source')
            item = create_material(root, {'title': 'Reference', 'description': 'Reviewer evidence', 'kind': 'document', 'source': 'library/ref.txt', 'rights': 'User supplied'})
            link_material(root, 'video', 'demo', item['id'])
            self._approve(root, 'brief')
            self._approve(root, 'script')
            source.write_text('Changed source')
            self.assertEqual(review_state(root, 'demo', 'script')['state'], 'stale')

    def test_stale_compiler_blocks_storyboard(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for ident in ('demo', 'silent-first-scene'):
                project = root / 'videos' / ident
                project.mkdir(parents=True, exist_ok=True)
                (project / 'project.json').write_text('{"brand": "videofactory"}')
            cues = root / 'videos/silent-first-scene/03_cues'
            cues.mkdir(parents=True, exist_ok=True)
            (cues / 'cues.json').write_text('{}')
            (cues / 'cues.js').write_text('x')
            (cues / 'cues.md').write_text('## intro @0\nA real beat.')
            self.assertIn('stale cues.json', review_state(root, 'silent-first-scene', 'cues')['missing'])

    def test_imported_voice_omits_test_take_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for ident in ('demo', 'silent-first-scene'):
                project = root / 'videos' / ident
                project.mkdir(parents=True, exist_ok=True)
                (project / 'project.json').write_text('{"brand": "videofactory"}')
            voice = root / 'videos/demo/01_voice'
            voice.mkdir(parents=True, exist_ok=True)
            (voice / 'brief.md').write_text('Audience: managers\nType: course\nLanguage: en\nOne outcome: learn\n')
            (voice / 'script.md').write_text('Hello there.')
            (voice / 'voice.wav').write_bytes(b'fake audio')
            self._approve(root, 'brief')
            self._approve(root, 'script')
            self.assertTrue(review_state(root, 'demo', 'voice')['ready'])

    def test_scene_requires_zero_check_and_render_uses_real_thumbnail_name(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for ident in ('demo', 'silent-first-scene'):
                project = root / 'videos' / ident
                project.mkdir(parents=True, exist_ok=True)
                (project / 'project.json').write_text('{"brand": "videofactory"}')
            base = root / 'videos/silent-first-scene'
            (base / '03_cues').mkdir(parents=True, exist_ok=True)
            (base / '03_cues/cues.md').write_text('## intro @0\nBeat')
            (base / '03_cues/cues.json').write_text('{}')
            (base / '03_cues/cues.js').write_text('x')
            (base / '04_scene').mkdir()
            (base / '04_scene/scene.js').write_text('function scene(t) {}')
            (base / '04_scene/index.html').write_text('<div></div>')
            (base / '05_render/stills').mkdir(parents=True, exist_ok=True)
            (base / '05_render/stills/intro.png').write_bytes(b'png')
            self.assertIn('zero-counter check.md', review_state(root, 'silent-first-scene', 'scene')['missing'])
            (base / '05_render/check.md').write_text('page errors  0\ncue warnings  0\nclock use  0\nnondeterministic frames  0\ntext cut off  0\ntext overlaps  0\ntext too short to read  0\n')
            self.assertNotIn('zero-counter check.md', review_state(root, 'silent-first-scene', 'scene')['missing'])
            self.assertEqual(review_state(root, 'silent-first-scene', 'voice')['state'], 'not-applicable')
            self.assertEqual(review_state(root, 'silent-first-scene', 'transcript')['state'], 'not-applicable')
            self.assertEqual(review_state(root, 'silent-first-scene', 'brief')['state'], 'not-applicable')
            self.assertEqual(review_state(root, 'silent-first-scene', 'script')['state'], 'not-applicable')

    def test_generated_final_voice_uses_take_triples_without_voice_text_sidecar(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for ident in ('demo', 'silent-first-scene'):
                project = root / 'videos' / ident
                project.mkdir(parents=True, exist_ok=True)
                (project / 'project.json').write_text('{"brand": "videofactory"}')
            voice = root / 'videos/demo/01_voice'
            takes = voice / 'takes'
            takes.mkdir(parents=True, exist_ok=True)
            (voice / 'brief.md').write_text('Audience: managers\nType: course\nLanguage: en\nOne outcome: learn\n')
            (voice / 'script.md').write_text('Hello there.')
            self._approve(root, 'brief')
            self._approve(root, 'script')
            (takes / '01.mp3').write_bytes(b'audio')
            (takes / '01.txt').write_text('Hello there.')
            (takes / '01.json').write_text('{"body": {"text": "Hello there."}}')
            script_revision = gate_fingerprint(root, 'demo', 'script')
            set_voice_selection(root, 'demo', 'voice_test', '01_voice/takes/01.mp3', script_revision)
            self.assertTrue(review_state(root, 'demo', 'voice-test')['ready'])
            self._approve(root, 'voice-test')
            (voice / 'voice.mp3').write_bytes(b'assembled audio')
            set_voice_selection(root, 'demo', 'voice', '01_voice/voice.mp3', script_revision)
            self.assertTrue(review_state(root, 'demo', 'voice')['ready'])


class HyperframesReviewTests(unittest.TestCase):
    def test_scene_gate_for_hyperframes_needs_index_html_not_scene_js(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for ident in ('demo', 'silent-first-scene'):
                project = root / 'videos' / ident
                project.mkdir(parents=True, exist_ok=True)
                (project / 'project.json').write_text('{"brand": "videofactory"}')
            base = root / 'videos/silent-first-scene'
            (base / '03_cues').mkdir(parents=True, exist_ok=True)
            (base / 'project.json').write_text('{"engine": "hyperframes", "brand": "videofactory"}')
            (base / '04_scene').mkdir()
            (base / '05_render/stills').mkdir(parents=True, exist_ok=True)
            (base / '05_render/stills/intro.png').write_bytes(b'png')
            missing = review_state(root, 'silent-first-scene', 'scene')['missing']
            self.assertIn('index.html', missing)
            (base / '04_scene/index.html').write_text('<div></div>')
            (base / '05_render/check.md').write_text('lint errors  0\nvideo vs voice length  0\nno visual layer  0\npage errors  n/a (hyperframes)\n')
            missing = review_state(root, 'silent-first-scene', 'scene')['missing']
            self.assertNotIn('scene.js', missing)
            self.assertNotIn('index.html', missing)
            self.assertNotIn('zero-counter check.md', missing)
