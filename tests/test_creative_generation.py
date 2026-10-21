import base64
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from studio import workspace as ws
from studio import generation
from studio.characters import register_character_candidates, register_character_identity, select_character_candidate
from studio.creative import (create_creative, creative_detail, creative_fingerprint,
                             decide_creative, mark_creative_ready, save_workshop_answers)
from studio.generation import (approve_generation, generation_detail, prepare_generation,
                               register_generated_outputs, run_generation, _run_codex)
from studio.permissions import grant


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        create_creative(self.root, 'character', 'tutor', 'A helpful tutor', {'title': 'Teacher'})
        grant(self.root, 'character:tutor', 'full')
        detail = creative_detail(self.root, 'character', 'tutor')
        save_workshop_answers(self.root, 'character', 'tutor', {'look': 'Professional'},
                              brief='Cheerful professional tutor.', expected_revision=detail['revision'])
        rev = creative_fingerprint(self.root, 'character', 'tutor', 'brief')
        mark_creative_ready(self.root, 'character', 'tutor', 'brief', rev)
        decide_creative(self.root, 'character', 'tutor', 'brief', 'approved', 'Reviewer', '', rev)

    def request(self, **changes):
        request = {'id': 'concepts-1', 'subject_type': 'character', 'subject_id': 'tutor',
                   'purpose': 'character-concepts', 'prompt': 'Three distinct tutor concepts',
                   'references': [], 'transparent': True, 'image_count': 3,
                   'input_revision': creative_fingerprint(self.root, 'character', 'tutor', 'brief')}
        result = {**request, **changes}
        if result.get('transport') == 'openai-api': result.setdefault('max_paid_spend', 3)
        return result

    def image(self, name, alpha=True):
        path = self.root / 'characters/tutor/generated/concepts-1' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGBA' if alpha else 'RGB', (8, 8), (0, 0, 0, 0) if alpha else (0, 0, 0)).save(path)
        return path.relative_to(self.root).as_posix()

    def tool_results(self, paths):
        return [{'image_url': 'data:image/png;base64,' + base64.b64encode((self.root / path).read_bytes()).decode()}
                for path in paths]

    def approve_design(self):
        batch = prepare_generation(self.root, self.request(id='concepts-fixture'))
        outputs = []
        for index in range(3):
            path = self.root / batch['output_dir'] / f'concept-{index}.png'
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new('RGBA', (8, 8), (index, 0, 0, 0)).save(path)
            outputs.append({'path': path.relative_to(self.root).as_posix(), 'sha256': ws._file_hash(path)})
        batch.update(state='completed', outputs=outputs)
        generation._save(self.root, batch)  # synthetic fixture batch; no external image call
        register_character_candidates(self.root, 'tutor', batch['id'], batch['input_revision'])
        select_character_candidate(self.root, 'tutor', 'concept-2', creative_fingerprint(self.root, 'character', 'tutor', 'design'))
        revision = creative_fingerprint(self.root, 'character', 'tutor', 'design')
        mark_creative_ready(self.root, 'character', 'tutor', 'design', revision)
        decide_creative(self.root, 'character', 'tutor', 'design', 'approved', 'Reviewer', '', revision)
        return outputs[1]['path']

    def material_for(self, ident, source):
        ws.create_material(self.root, {'id': ident, 'title': ident, 'description': 'Approved character art',
                                       'kind': 'image', 'source': source, 'rights': 'user-supplied', 'tags': []})
        return {'material_id': ident, 'role': 'canonical identity'}

    def test_provider_and_duplicate_id_rejected(self):
        with self.assertRaises(ws.WorkspaceError):
            prepare_generation(self.root, self.request(provider='anthropic'))
        prepare_generation(self.root, self.request())
        with self.assertRaises(ws.WorkspaceError):
            prepare_generation(self.root, self.request(prompt='Changed'))

    def test_batch_approval_and_stale_input_block_runner(self):
        prepared = prepare_generation(self.root, self.request())
        self.assertEqual(prepared['state'], 'awaiting-batch-approval')
        self.assertEqual(prepared['image_count'], 3)
        with self.assertRaises(ws.WorkspaceError):
            run_generation(self.root, 'concepts-1')
        approve_generation(self.root, 'concepts-1', 'Reviewer')
        (self.root / 'characters/tutor/01_design/brief.md').write_text('New direction')
        with self.assertRaises(ws.WorkspaceError):
            run_generation(self.root, 'concepts-1')

    def test_unpriced_cli_is_blocked_before_preflight(self):
        prepare_generation(self.root, self.request())
        approve_generation(self.root, 'concepts-1', 'Reviewer')
        with patch('studio.generation._codex_preflight') as preflight:
            with self.assertRaisesRegex(ws.WorkspaceError, 'maximum-cost quote'):
                run_generation(self.root, 'concepts-1')
            preflight.assert_not_called()
        self.assertEqual(generation_detail(self.root, 'concepts-1')['state'], 'approved')

    def test_unpriced_cli_keeps_existing_drafts(self):
        prepare_generation(self.root, self.request())
        approve_generation(self.root, 'concepts-1', 'Reviewer')
        first = self.image('first.png')
        with self.assertRaisesRegex(ws.WorkspaceError, 'maximum-cost quote'):
            run_generation(self.root, 'concepts-1')
        self.assertTrue((self.root / first).is_file())
        self.assertEqual(generation_detail(self.root, 'concepts-1')['outputs'], [])

    def test_unpriced_cli_cannot_start_paid_batch(self):
        prepare_generation(self.root, self.request())
        approve_generation(self.root, 'concepts-1', 'Reviewer')

        with self.assertRaisesRegex(ws.WorkspaceError, 'maximum-cost quote'):
            run_generation(self.root, 'concepts-1')
        self.assertEqual(generation_detail(self.root, 'concepts-1')['state'], 'approved')

    def test_api_route_requires_separate_billing_acknowledgement(self):
        prepare_generation(self.root, self.request(transport='openai-api', transparent=False))
        with self.assertRaises(ws.WorkspaceError):
            approve_generation(self.root, 'concepts-1', 'Reviewer')
        approved = approve_generation(self.root, 'concepts-1', 'Reviewer', billing_acknowledged=True)
        self.assertTrue(approved['billing_acknowledged'])

    def test_transparent_api_batch_requires_explicit_compatible_model(self):
        with self.assertRaises(ws.WorkspaceError):
            prepare_generation(self.root, self.request(transport='openai-api', image_model='gpt-image-2'))
        with self.assertRaises(ws.WorkspaceError):
            prepare_generation(self.root, self.request(transport='openai-api'))
        batch = prepare_generation(self.root, self.request(transport='openai-api', image_model='gpt-image-1.5'))
        self.assertEqual(batch['requested_image_model'], 'gpt-image-1.5')

    def test_public_registration_rejects_self_attested_cli_or_api_proof(self):
        for route in ('codex-cli', 'openai-api'):
            with self.subTest(route=route):
                ident = 'concepts-1' if route == 'codex-cli' else 'concepts-2'
                prepare_generation(self.root, self.request(id=ident, transport=route, transparent=False))
                approve_generation(self.root, ident, 'Reviewer', billing_acknowledged=route == 'openai-api')
                path = self.root / f'characters/tutor/generated/{ident}/fake.png'
                path.parent.mkdir(parents=True)
                Image.new('RGB', (8, 8), 'red').save(path)
                with self.assertRaises(ws.WorkspaceError):
                    register_generated_outputs(self.root, ident, [path.relative_to(self.root).as_posix()],
                                               {'provider': 'openai', 'transport': route,
                                                'coordinator': 'Codex CLI', 'image_tool_used': True})
                self.assertEqual(generation_detail(self.root, ident)['outputs'], [])

    def test_cli_requires_successful_exact_image_tool_event(self):
        record = prepare_generation(self.root, self.request())

        def fake_run(event):
            def invoke(args, **_):
                Path(args[args.index('--output-last-message') + 1]).write_text('{"outputs": []}')
                return subprocess.CompletedProcess(args, 0, json.dumps(event) + '\n', '')
            return invoke

        unrelated = {'type': 'item.completed', 'item': {'type': 'mcp_tool_call',
                     'name': 'unrelated_tool', 'arguments': {'text': 'imagegen'}, 'status': 'completed'}}
        with patch('studio.generation.subprocess.run', side_effect=fake_run(unrelated)):
            self.assertFalse(_run_codex(self.root, record, 'codex')['image_tool_used'])
        failed = {'type': 'item.completed', 'item': {'type': 'mcp_tool_call',
                  'server': 'image_gen', 'tool': 'imagegen', 'status': 'failed'}}
        with patch('studio.generation.subprocess.run', side_effect=fake_run(failed)):
            self.assertFalse(_run_codex(self.root, record, 'codex')['image_tool_used'])
        tool_error = {'type': 'item.completed', 'item': {'type': 'mcp_tool_call',
                      'server': 'image_gen', 'tool': 'imagegen', 'status': 'completed',
                      'result': {'isError': True}}}
        with patch('studio.generation.subprocess.run', side_effect=fake_run(tool_error)):
            self.assertFalse(_run_codex(self.root, record, 'codex')['image_tool_used'])
        success = {'type': 'item.completed', 'item': {'type': 'mcp_tool_call',
                   'server': 'image_gen', 'tool': 'imagegen', 'status': 'completed'}}
        with patch('studio.generation.subprocess.run', side_effect=fake_run(success)):
            self.assertTrue(_run_codex(self.root, record, 'codex')['image_tool_used'])

    def test_external_registrar_cannot_self_attest_cli_batch(self):
        prepare_generation(self.root, self.request())
        approve_generation(self.root, 'concepts-1', 'Reviewer')
        path = self.image('first.png')

        with self.assertRaises(ws.WorkspaceError):
            register_generated_outputs(self.root, 'concepts-1', [path],
                                       {'provider': 'openai', 'transport': 'codex-cli',
                                        'coordinator': 'Codex CLI', 'image_tool_used': True})

    def test_unpriced_cli_does_not_register_existing_files(self):
        prepare_generation(self.root, self.request())
        approve_generation(self.root, 'concepts-1', 'Reviewer')
        paths = [self.image(f'image-{index}.png') for index in range(4)]
        with self.assertRaisesRegex(ws.WorkspaceError, 'maximum-cost quote'):
            run_generation(self.root, 'concepts-1')
        self.assertEqual(generation_detail(self.root, 'concepts-1')['outputs'], [])

    def test_identity_requires_selected_concept_reference_and_variant_requires_sheet_and_scene(self):
        selected = self.approve_design()
        identity = self.request(id='identity-1', purpose='character-identity', image_count=2,
                                input_revision=creative_fingerprint(self.root, 'character', 'tutor', 'design'))
        with self.assertRaises(ws.WorkspaceError):
            prepare_generation(self.root, identity)
        self.material_for('selected', selected)
        ready = prepare_generation(self.root, {**identity, 'references': [{'material_id': 'selected', 'role': 'selected concept'}]})
        self.assertEqual(ready['state'], 'awaiting-batch-approval')

        sheet, scene = (self.root / ready['output_dir'] / name for name in ('sheet.png', 'scene.png'))
        for index, path in enumerate((sheet, scene)):
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new('RGBA', (8, 8), (index, 0, 0, 0)).save(path)
        ready.update(state='completed', outputs=[{'path': p.relative_to(self.root).as_posix(), 'sha256': ws._file_hash(p)}
                                                 for p in (sheet, scene)])
        generation._save(self.root, ready)
        register_character_identity(self.root, 'tutor', ready['id'],
            {'hair': 'fixture curls', 'eyes': 'fixture eyes', 'face': 'fixture face',
             'proportions': 'fixture proportions', 'clothing': 'fixture blazer'},
            ready['input_revision'])
        revision = creative_fingerprint(self.root, 'character', 'tutor', 'identity')
        mark_creative_ready(self.root, 'character', 'tutor', 'identity', revision)
        decide_creative(self.root, 'character', 'tutor', 'identity', 'approved', 'Reviewer', '', revision)
        ws.create_style(self.root, 'ink', 'Ink', 'modern')
        variant = self.request(id='variant-1', purpose='character-variant', image_count=1,
                               input_revision=revision,
                               context={'variant_id': 'ink', 'style_id': 'ink',
                                        'style_revision': ws._style_revision(self.root, 'ink'),
                                        'monochrome_exception': False})
        with self.assertRaises(ws.WorkspaceError):
            prepare_generation(self.root, variant)
        sheet_ref = self.material_for('sheet', sheet.relative_to(self.root).as_posix())
        with self.assertRaises(ws.WorkspaceError):
            prepare_generation(self.root, {**variant, 'references': [sheet_ref]})
        scene_ref = self.material_for('scene', scene.relative_to(self.root).as_posix())
        self.assertEqual(prepare_generation(self.root, {**variant, 'references': [sheet_ref, scene_ref]})['state'],
                         'awaiting-batch-approval')

    def test_native_registration_checks_tool_evidence_alpha_and_confinement(self):
        prepare_generation(self.root, self.request(transport='native'))
        approve_generation(self.root, 'concepts-1', 'Reviewer')
        opaque = self.image('opaque.png')
        Image.new('RGBA', (8, 8), (0, 0, 0, 255)).save(self.root / opaque)
        proof = {'provider': 'openai', 'transport': 'native', 'coordinator': 'Codex',
                 'image_tool_used': True, 'image_model': 'unknown'}
        with self.assertRaises(ws.WorkspaceError):
            register_generated_outputs(self.root, 'concepts-1', [opaque], {**proof, 'tool_results': self.tool_results([opaque])})
        transparent = self.image('draft.png')
        with self.assertRaises(ws.WorkspaceError):
            register_generated_outputs(self.root, 'concepts-1', ['characters/tutor/elsewhere.png'], proof)
        (self.root / 'characters/tutor/generated/concepts-1/link.png').symlink_to(self.root / opaque)
        with self.assertRaises(ws.WorkspaceError):
            register_generated_outputs(self.root, 'concepts-1',
                                       ['characters/tutor/generated/concepts-1/link.png'], proof)
        with self.assertRaises(ws.WorkspaceError):
            register_generated_outputs(self.root, 'concepts-1', [transparent], {**proof, 'image_tool_used': False})
        with self.assertRaises(ws.WorkspaceError):
            register_generated_outputs(self.root, 'concepts-1', [transparent], {**proof, 'tool_results': self.tool_results([opaque])})
        paths = [transparent, self.image('draft-2.png'), self.image('draft-3.png')]
        result = register_generated_outputs(self.root, 'concepts-1', paths, {**proof, 'tool_results': self.tool_results(paths)})
        self.assertEqual(result['state'], 'completed')
        self.assertEqual(result['outputs'][0]['dimensions'], [8, 8])

    def test_reference_hash_change_blocks_registration_and_partial_valid_drafts_survive(self):
        reference = self.root / 'library/materials/pose/ref.png'
        reference.parent.mkdir(parents=True)
        Image.new('RGB', (8, 8), 'red').save(reference)
        ws._atomic_write(reference.parent / 'material.md', ws._record({
            'id': 'pose', 'title': 'Pose', 'description': 'Teacher pose', 'kind': 'image',
            'source': 'upload', 'rights': 'user-supplied', 'tags': []}, '').encode())
        prepare_generation(self.root, self.request(transport='native', references=[{'material_id': 'pose', 'role': 'pose'}]))
        approve_generation(self.root, 'concepts-1', 'Reviewer')
        first = self.image('first.png')
        proof = {'provider': 'openai', 'transport': 'native', 'coordinator': 'Codex', 'image_tool_used': True}
        partial = register_generated_outputs(self.root, 'concepts-1', [first], {**proof, 'tool_results': self.tool_results([first])})
        self.assertEqual(partial['state'], 'partial')
        self.assertEqual(len(partial['outputs']), 1)
        Image.new('RGB', (8, 8), 'blue').save(reference)
        with self.assertRaises(ws.WorkspaceError):
            register_generated_outputs(self.root, 'concepts-1', [self.image('second.png')], proof)
        self.assertEqual(len(generation_detail(self.root, 'concepts-1')['outputs']), 1)


if __name__ == '__main__':
    unittest.main()
