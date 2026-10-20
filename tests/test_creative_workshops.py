import json
import tempfile
import unittest
from PIL import Image
from unittest.mock import patch
from pathlib import Path

from studio import generation, jobs, workspace as ws
from studio.characters import (prepare_character_identity, prepare_character_variant, register_character_candidates,
                               register_character_identity, register_character_variant, select_character_candidate)
from studio.creative import (create_creative, creative_detail, creative_fingerprint,
                             decide_creative, mark_creative_ready, save_workshop_answers)


class CreativeWorkshopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def test_prompt_creates_honest_question_wait_and_legacy_requests_survive(self):
        detail = create_creative(self.root, 'style', 'warm-line', 'Warm, clear tutor scenes',
                                 {'title': 'Warm Line', 'base_kit': 'modern'})
        self.assertEqual(detail['workshop']['state'], 'waiting-for-agent')
        self.assertEqual(detail['reviews']['brief']['state'], 'draft')
        self.assertEqual((self.root / 'styles/warm-line/01_brief/prompt.md').read_text(), 'Warm, clear tutor scenes\n')
        request = jobs.list_requests(self.root)[0]
        self.assertEqual(request['subject'], {'type': 'style', 'id': 'warm-line'})
        self.assertEqual(request['kind'], 'style-discovery')
        self.assertEqual(request['state'], 'waiting-for-agent')
        self.assertEqual(request['input_revision'], creative_fingerprint(self.root, 'style', 'warm-line', 'brief'))
        (self.root / 'videos/videofactory/legacy').mkdir(parents=True)
        (self.root / 'videos/videofactory/legacy/project.json').write_text('{"brand":"videofactory"}')
        old = jobs.create_request(self.root, 'videofactory/legacy', 'script', 'Write the script', None, 'legacy-req')
        self.assertEqual(old['slug'], 'videofactory/legacy')
        self.assertNotIn('subject', old)

    def test_saved_answers_and_brief_are_ready_but_not_approved_and_stale_edits_block(self):
        create_creative(self.root, 'character', 'tutor', 'Cheerful professional woman tutor', {'title': 'Teacher'})
        detail = creative_detail(self.root, 'character', 'tutor')
        with self.assertRaises(ws.WorkspaceError) as error:
            mark_creative_ready(self.root, 'character', 'tutor', 'brief', detail['reviews']['brief']['fingerprint'])
        self.assertEqual(error.exception.code, 'blocked')
        saved = save_workshop_answers(self.root, 'character', 'tutor', {'audience': 'New creators'},
                                      brief='A cheerful tutor in a useful course scene.',
                                      form_url='https://example.org/forms/tutor', expected_revision=detail['revision'])
        self.assertEqual(saved['workshop']['state'], 'answers-saved')
        revision = saved['reviews']['brief']['fingerprint']
        ready = mark_creative_ready(self.root, 'character', 'tutor', 'brief', revision)
        self.assertEqual(ready['state'], 'awaiting-review')
        self.assertNotEqual(ready['state'], 'approved')
        with self.assertRaises(ws.WorkspaceError) as error:
            decide_creative(self.root, 'character', 'tutor', 'brief', 'approved', 'Reviewer', '', 'stale')
        self.assertEqual(error.exception.code, 'conflict')
        approved = decide_creative(self.root, 'character', 'tutor', 'brief', 'approved', 'Reviewer', '', revision)
        self.assertEqual(approved['state'], 'approved')
        (self.root / 'characters/tutor/01_design/brief.md').write_text('Changed after approval')
        self.assertEqual(creative_detail(self.root, 'character', 'tutor')['reviews']['brief']['state'], 'stale')

    def test_ready_and_repeated_approval_cannot_demote_or_duplicate_current_decision(self):
        detail = create_creative(self.root, 'style', 'warm-line', 'Warm scenes', {'title': 'Warm Line'})
        saved = save_workshop_answers(self.root, 'style', 'warm-line', {'look': 'Warm line art'},
                                      brief='Warm line art with restrained motion.', expected_revision=detail['revision'])
        revision = saved['reviews']['brief']['fingerprint']
        mark_creative_ready(self.root, 'style', 'warm-line', 'brief', revision)
        approved = decide_creative(self.root, 'style', 'warm-line', 'brief', 'approved', 'Reviewer', '', revision)
        count = len(approved['history'])
        again = mark_creative_ready(self.root, 'style', 'warm-line', 'brief', revision)
        self.assertEqual((again['state'], len(again['history'])), ('approved', count))
        repeated = decide_creative(self.root, 'style', 'warm-line', 'brief', 'approved', 'Reviewer', '', revision)
        self.assertEqual((repeated['state'], len(repeated['history'])), ('approved', count))
        (self.root / 'styles/warm-line/01_brief/brief.md').write_text('A newly saved direction.\n')
        current = creative_detail(self.root, 'style', 'warm-line')['reviews']['brief']
        self.assertEqual(current['state'], 'stale')
        self.assertEqual(mark_creative_ready(self.root, 'style', 'warm-line', 'brief', current['fingerprint'])['state'], 'awaiting-review')

    def test_downstream_gate_needs_current_upstream_approval_and_real_outputs(self):
        create_creative(self.root, 'style', 'warm-line', 'Warm scenes', {'title': 'Warm Line'})
        first = creative_detail(self.root, 'style', 'warm-line')
        save_workshop_answers(self.root, 'style', 'warm-line', {'look': 'Warm line art'},
                              brief='Warm line art with restrained motion.', expected_revision=first['revision'])
        fingerprint = creative_fingerprint(self.root, 'style', 'warm-line', 'brief')
        mark_creative_ready(self.root, 'style', 'warm-line', 'brief', fingerprint)
        decide_creative(self.root, 'style', 'warm-line', 'brief', 'approved', 'Reviewer', '', fingerprint)
        with self.assertRaises(ws.WorkspaceError) as error:
            mark_creative_ready(self.root, 'style', 'warm-line', 'materials', creative_fingerprint(self.root, 'style', 'warm-line', 'materials'))
        self.assertEqual(error.exception.code, 'blocked')
        (self.root / 'styles/warm-line/materials.md').write_text('# Materials\n\nA classroom setting, drawn as a reusable environment.\n')
        revision = creative_fingerprint(self.root, 'style', 'warm-line', 'materials')
        self.assertEqual(mark_creative_ready(self.root, 'style', 'warm-line', 'materials', revision)['state'], 'awaiting-review')
        (self.root / 'styles/warm-line/01_brief/brief.md').write_text('A changed direction.')
        with self.assertRaises(ws.WorkspaceError) as error:
            decide_creative(self.root, 'style', 'warm-line', 'materials', 'approved', 'Reviewer', '', revision)
        self.assertEqual(error.exception.code, 'conflict')

    def test_private_paths_and_invalid_subjects_are_denied(self):
        for subject_type, ident in [('video', 'x'), ('style', '../secret'), ('character', '_auth')]:
            with self.subTest(subject_type=subject_type, ident=ident), self.assertRaises(ws.WorkspaceError):
                create_creative(self.root, subject_type, ident, 'Prompt', {'title': 'Title'})
        with self.assertRaises(ws.WorkspaceError):
            ws.safe_path(self.root, 'characters/x/_auth/secret', write=True)

    def test_linked_art_and_style_reference_revisions_are_fingerprinted(self):
        source = self.root / '_shared/guide.md'
        source.parent.mkdir()
        source.write_text('First direction')
        create_creative(self.root, 'style', 'warm-line', 'Warm scenes',
                        {'title': 'Warm Line', 'references': ['_shared/guide.md']})
        before = creative_fingerprint(self.root, 'style', 'warm-line', 'materials')
        source.write_text('Changed direction')
        self.assertNotEqual(before, creative_fingerprint(self.root, 'style', 'warm-line', 'materials'))
        create_creative(self.root, 'character', 'tutor', 'A tutor', {'title': 'Teacher'})
        art = self.root / 'characters/tutor/02_identity/sheet.png'
        art.write_bytes(b'first')
        (art.parent / 'scene.png').write_bytes(b'scene')
        (art.parent / 'reference-set.json').write_text(json.dumps({'sheet': 'characters/tutor/02_identity/sheet.png',
                                                                  'in_scene': 'characters/tutor/02_identity/scene.png'}))
        before = creative_fingerprint(self.root, 'character', 'tutor', 'identity')
        art.write_bytes(b'second')
        self.assertNotEqual(before, creative_fingerprint(self.root, 'character', 'tutor', 'identity'))

    def test_typed_request_rechecks_its_input_before_claim(self):
        create_creative(self.root, 'character', 'tutor', 'A tutor', {'title': 'Teacher'})
        revision = creative_fingerprint(self.root, 'character', 'tutor', 'brief')
        request = jobs.create_request(self.root, None, 'creative-material', 'Describe the tutor props', None,
                                      'material-1', subject={'type': 'character', 'id': 'tutor'}, input_revision=revision)
        self.assertEqual(request['subject']['type'], 'character')
        (self.root / 'characters/tutor/character.md').write_text('Changed identity input')
        with self.assertRaises(ws.WorkspaceError) as error:
            jobs.claim_request(self.root, 'material-1', 'agent')
        self.assertEqual(error.exception.code, 'conflict')
        self.assertEqual(jobs.list_requests(self.root)[0]['state'], 'waiting-for-agent')

    def test_brainstormform_json_keeps_typed_values_and_requires_finished_session(self):
        create_creative(self.root, 'character', 'tutor', 'A tutor', {'title': 'Teacher'})
        draft = {'sessionId': 'bf-123', 'answers': {'actions': {'type': 'multi', 'value': ['wave', 'point']},
                                                  'has_desk': {'type': 'boolean', 'value': False},
                                                  'energy': {'type': 'scale', 'value': 0}},
                 'notes': {'actions': 'Wave with the right hand'}, 'unanswered': [], 'hidden': []}
        revision = creative_detail(self.root, 'character', 'tutor')['revision']
        saved = save_workshop_answers(self.root, 'character', 'tutor', draft, brief='Teacher at a desk.', expected_revision=revision)
        self.assertEqual(json.loads((self.root / 'characters/tutor/01_design/answers.json').read_text()), draft)
        self.assertFalse(saved['reviews']['brief']['ready'])
        complete = {**draft, 'submittedAt': '2026-10-09T12:00:00Z', 'durationMs': 12345}
        saved = save_workshop_answers(self.root, 'character', 'tutor', complete, expected_revision=saved['revision'])
        self.assertEqual(saved['workshop']['state'], 'answers-saved')
        self.assertTrue(saved['reviews']['brief']['ready'])

    def test_style_asset_and_template_edits_stale_current_approvals(self):
        create_creative(self.root, 'style', 'warm', 'Warm style', {'title': 'Warm', 'supported_formats': ['wide']})
        detail = creative_detail(self.root, 'style', 'warm')
        save_workshop_answers(self.root, 'style', 'warm', {'look': 'Warm line art'}, brief='Warm line art for tutors.', expected_revision=detail['revision'])
        brief = creative_fingerprint(self.root, 'style', 'warm', 'brief')
        mark_creative_ready(self.root, 'style', 'warm', 'brief', brief)
        decide_creative(self.root, 'style', 'warm', 'brief', 'approved', 'Reviewer', '', brief)
        folder = self.root / 'styles/warm'
        (folder / 'materials.md').write_text('# Materials\n\nA quiet classroom scene drawn for this course.\n')
        asset = folder / '02_assets/classroom.png'
        asset.parent.mkdir(exist_ok=True)
        asset.write_bytes(b'first asset')
        materials = creative_fingerprint(self.root, 'style', 'warm', 'materials')
        mark_creative_ready(self.root, 'style', 'warm', 'materials', materials)
        decide_creative(self.root, 'style', 'warm', 'materials', 'approved', 'Reviewer', '', materials)
        sample = folder / '03_sample/wide/index.html'
        sample.parent.mkdir(parents=True)
        sample.write_text('<html>Actual sample</html>')
        template = folder / 'template/scene.js'
        template.parent.mkdir()
        template.write_text('first')
        # This test isolates review invalidation; rendered-media validity is tested separately.
        with patch('studio.references.sample_valid', return_value=True):
            sample_revision = creative_fingerprint(self.root, 'style', 'warm', 'sample')
            mark_creative_ready(self.root, 'style', 'warm', 'sample', sample_revision)
            decide_creative(self.root, 'style', 'warm', 'sample', 'approved', 'Reviewer', '', sample_revision)
            template.write_text('second')
            self.assertEqual(creative_detail(self.root, 'style', 'warm')['reviews']['sample']['state'], 'stale')
            template.write_text('first')
            self.assertEqual(creative_detail(self.root, 'style', 'warm')['reviews']['sample']['state'], 'approved')
            decide_creative(self.root, 'style', 'warm', 'brief', 'changes-requested', 'Reviewer', 'Revise the direction', brief)
            reviews = creative_detail(self.root, 'style', 'warm')['reviews']
            self.assertNotEqual(reviews['materials']['state'], 'approved')
            self.assertNotEqual(reviews['sample']['state'], 'approved')
            decide_creative(self.root, 'style', 'warm', 'brief', 'approved', 'Reviewer', 'Direction accepted', brief)
            self.assertEqual(creative_detail(self.root, 'style', 'warm')['reviews']['sample']['state'], 'approved')
            asset.write_bytes(b'second asset')
            reviews = creative_detail(self.root, 'style', 'warm')['reviews']
            self.assertEqual(reviews['materials']['state'], 'stale')
            self.assertEqual(reviews['sample']['state'], 'stale')

    def test_unregistered_character_art_and_fake_frames_cannot_be_approved(self):
        create_creative(self.root, 'character', 'tutor', 'A tutor', {'title': 'Teacher'})
        detail = creative_detail(self.root, 'character', 'tutor')
        save_workshop_answers(self.root, 'character', 'tutor', {'goal': 'Teach new VAs'}, brief='Teacher in a course.', expected_revision=detail['revision'])
        folder = self.root / 'characters/tutor'
        for gate in ('brief', 'design', 'identity'):
            if gate == 'design':
                batch = generation.prepare_generation(self.root, {'id': 'concepts-fixture', 'subject_type': 'character',
                    'subject_id': 'tutor', 'purpose': 'character-concepts', 'prompt': 'Synthetic fixture concepts',
                    'references': [], 'transparent': True, 'image_count': 3,
                    'input_revision': creative_fingerprint(self.root, 'character', 'tutor', 'brief')})
                outputs = []
                for index in range(3):
                    image = self.root / batch['output_dir'] / f'{index}.png'
                    image.parent.mkdir(parents=True, exist_ok=True)
                    Image.new('RGBA', (8, 8), (index, 0, 0, 0)).save(image)
                    outputs.append({'path': image.relative_to(self.root).as_posix(), 'sha256': ws._file_hash(image)})
                batch.update(state='completed', outputs=outputs)
                generation._save(self.root, batch)
                register_character_candidates(self.root, 'tutor', batch['id'], batch['input_revision'])
                select_character_candidate(self.root, 'tutor', 'concept-1', creative_fingerprint(self.root, 'character', 'tutor', 'design'))
            if gate == 'identity':
                batch = prepare_character_identity(self.root, 'tutor')
                outputs = []
                for index, name in enumerate(('sheet', 'scene')):
                    image = self.root / batch['output_dir'] / f'{name}.png'
                    image.parent.mkdir(parents=True, exist_ok=True)
                    Image.new('RGBA', (8, 8), (0, index, 0, 0)).save(image)
                    outputs.append({'path': image.relative_to(self.root).as_posix(), 'sha256': ws._file_hash(image)})
                batch.update(state='completed', outputs=outputs)
                generation._save(self.root, batch)
                register_character_identity(self.root, 'tutor', batch['id'],
                    {'hair': 'fixture curls', 'eyes': 'fixture eyes', 'face': 'fixture face',
                     'proportions': 'fixture proportions', 'clothing': 'fixture blazer'}, batch['input_revision'])
            revision = creative_fingerprint(self.root, 'character', 'tutor', gate)
            mark_creative_ready(self.root, 'character', 'tutor', gate, revision)
            decide_creative(self.root, 'character', 'tutor', gate, 'approved', 'Reviewer', '', revision)
        art = self.root / '_shared/hand.png'
        art.parent.mkdir()
        art.write_bytes(b'first art')
        ws.create_style(self.root, 'classic', 'Classic', 'modern')
        variant_batch = prepare_character_variant(self.root, 'tutor', 'classic', 'classic', 'Synthetic fixture variant')
        variant_art = self.root / variant_batch['output_dir'] / 'sheet.png'
        variant_art.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGBA', (8, 8), (0, 0, 1, 0)).save(variant_art)
        variant_batch.update(state='completed', outputs=[{'path': variant_art.relative_to(self.root).as_posix(),
                                                          'sha256': ws._file_hash(variant_art)}])
        generation._save(self.root, variant_batch)
        reference = json.loads((folder / '02_identity/reference-set.json').read_text())
        register_character_variant(self.root, 'tutor', 'classic',
            {'generation_id': variant_batch['id'], 'style_id': 'classic', 'views': ['front', 'three-quarter-right'],
             'appearance': reference['appearance'], 'monochrome_exception': False},
            creative_fingerprint(self.root, 'character', 'tutor', 'identity'))
        pack = folder / '03_animation/classic'
        (pack / 'assets.json').write_text(json.dumps({'layers': [{'path': '_shared/hand.png'}]}))
        (pack / 'rig.json').write_text('{}')
        (pack / 'motions.json').write_text(json.dumps({'actions': {'wave': {}}}))
        preview = pack / 'preview/wave/clip.png'
        preview.parent.mkdir(parents=True)
        preview.write_bytes(b'preview')
        frame = pack / 'frames/wave/000.png'
        frame.parent.mkdir(parents=True)
        frame.write_bytes(b'first frame')
        gate = 'animation:classic:wave'
        revision = creative_fingerprint(self.root, 'character', 'tutor', gate)
        self.assertFalse(creative_detail(self.root, 'character', 'tutor')['reviews'][gate]['ready'])
        with self.assertRaises(ws.WorkspaceError):
            mark_creative_ready(self.root, 'character', 'tutor', gate, revision)


if __name__ == '__main__':
    unittest.main()
