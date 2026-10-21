"""Character records use synthetic fixture art; no real concept is generated here."""

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image

from studio import workspace as ws
from studio import jobs
from studio.characters import (character_detail, create_character, list_characters,
                               prepare_character_identity, register_character_candidates,
                               register_character_identity, register_character_variant,
                               select_character_candidate, prepare_character_variant)
from studio.creative import creative_fingerprint, creative_review_state, decide_creative, mark_creative_ready, save_workshop_answers
from studio.generation import prepare_generation, generation_detail
from studio.server import make_server
from studio.permissions import grant


class CharacterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def image(self, path, color):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGBA', (8, 8), (*color, 0)).save(target)
        return path

    def approve(self, gate):
        revision = creative_fingerprint(self.root, 'character', 'tutor', gate)
        mark_creative_ready(self.root, 'character', 'tutor', gate, revision)
        decide_creative(self.root, 'character', 'tutor', gate, 'approved', 'Reviewer', '', revision)

    def created(self):
        create_character(self.root, 'tutor', 'A cheerful tutor', {'title': 'Tutor'})
        grant(self.root, 'character:tutor', 'full')
        detail = character_detail(self.root, 'tutor')
        save_workshop_answers(self.root, 'character', 'tutor', {'subject': 'Cheerful professional woman tutor'},
                              brief='Stylized realistic, professionally dressed, not fully human-looking.', expected_revision=detail['revision'])
        self.approve('brief')

    def completed_batch(self, purpose, paths, references=None, batch_id=None):
        from studio import generation
        gate = {'character-concepts': 'brief', 'character-identity': 'design'}[purpose]
        ident = batch_id or purpose + '-fixture'
        request = prepare_generation(self.root, {'id': ident, 'subject_type': 'character', 'subject_id': 'tutor',
            'purpose': purpose, 'prompt': 'Synthetic fixture art only', 'references': references or [],
            'transparent': True, 'image_count': len(paths), 'input_revision': creative_fingerprint(self.root, 'character', 'tutor', gate)})
        request['state'] = 'completed'
        request['outputs'] = [{'path': path, 'sha256': ws._file_hash(self.root / path)} for path in paths]
        generation._save(self.root, request)  # clearly labelled synthetic fixture; never a production transport
        return ident

    def concepts(self):
        paths = [self.image(f'characters/tutor/generated/character-concepts-fixture/{n}.png', (n, 0, 0)) for n in range(3)]
        batch = self.completed_batch('character-concepts', paths)
        register_character_candidates(self.root, 'tutor', batch, creative_fingerprint(self.root, 'character', 'tutor', 'brief'))
        return paths

    def test_candidate_registration_rejects_art_outside_approved_batch_folder(self):
        self.created()
        paths = [self.image(f'characters/tutor/generated/character-concepts-fixture/{n}.png', (n, 0, 0)) for n in range(3)]
        batch = self.completed_batch('character-concepts', paths)
        record = generation_detail(self.root, batch)
        foreign = self.image('characters/tutor/01_design/foreign.png', (0, 1, 0))
        record['outputs'][0] = {'path': foreign, 'sha256': ws._file_hash(self.root / foreign)}
        from studio import generation
        generation._save(self.root, record)
        with self.assertRaises(ws.WorkspaceError):
            register_character_candidates(self.root, 'tutor', batch,
                                          creative_fingerprint(self.root, 'character', 'tutor', 'brief'))
        self.assertFalse((self.root / 'characters/tutor/01_design/candidates.json').exists())

    def test_catalog_preview_uses_saved_art_in_identity_then_concept_order(self):
        self.created()
        initial = next(row for row in list_characters(self.root) if row['id'] == 'tutor')
        self.assertIsNone(initial['preview'])
        self.assertEqual(initial['brief_state'], 'approved')
        paths = self.concepts()
        row = next(row for row in list_characters(self.root) if row['id'] == 'tutor')
        self.assertEqual((row['preview']['path'], row['preview']['kind']), (paths[0], 'concept'))
        select_character_candidate(self.root, 'tutor', 'concept-2',
                                   creative_fingerprint(self.root, 'character', 'tutor', 'design'))
        row = next(row for row in list_characters(self.root) if row['id'] == 'tutor')
        self.assertEqual(row['preview']['path'], paths[1])
        self.approve('design')
        request = prepare_character_identity(self.root, 'tutor')
        images = [self.image(f'characters/tutor/generated/{request["id"]}/{name}.png', (0, n + 3, 0))
                  for n, name in enumerate(('sheet', 'scene'))]
        request['state'] = 'completed'
        request['outputs'] = [{'path': path, 'sha256': ws._file_hash(self.root / path)} for path in images]
        from studio import generation
        generation._save(self.root, request)
        register_character_identity(self.root, 'tutor', request['id'],
            {'hair': 'Curls', 'eyes': 'Brown', 'face': 'Oval', 'proportions': 'Tall', 'clothing': 'Blazer'},
            creative_fingerprint(self.root, 'character', 'tutor', 'design'))
        row = next(row for row in list_characters(self.root) if row['id'] == 'tutor')
        self.assertEqual((row['preview']['path'], row['preview']['kind']), (images[1], 'in-scene'))
        (self.root / images[1]).unlink()
        row = next(row for row in list_characters(self.root) if row['id'] == 'tutor')
        self.assertEqual((row['preview']['path'], row['preview']['kind']), (images[0], 'sheet'))

    def test_catalog_preview_skips_malformed_private_and_missing_art(self):
        self.created()
        paths = self.concepts()
        registry = self.root / 'characters/tutor/01_design/candidates.json'
        records = json.loads(registry.read_text())
        records[0]['path'] = 'characters/tutor/_auth/private.png'
        records[1]['path'] = 'characters/tutor/generated/missing.png'
        registry.write_text(json.dumps(records))
        row = next(row for row in list_characters(self.root) if row['id'] == 'tutor')
        self.assertEqual(row['preview']['path'], paths[2])
        registry.write_text('{bad json')
        row = next(row for row in list_characters(self.root) if row['id'] == 'tutor')
        self.assertIsNone(row['preview'])

    def test_new_character_profile_and_discovery_request_share_current_revision(self):
        detail = create_character(self.root, 'tutor', 'A cheerful tutor', {'title': 'Tutor'})
        self.assertEqual(set(detail['profile']['appearance']), {'hair', 'eyes', 'face', 'proportions'})
        self.assertTrue(all(value is None for value in detail['profile']['appearance'].values()))
        self.assertEqual(jobs.list_requests(self.root)[0]['input_revision'], detail['reviews']['brief']['fingerprint'])

    def test_three_real_candidates_and_selection_are_required_before_design_review(self):
        self.created()
        paths = self.concepts()
        self.assertFalse(creative_review_state(self.root, 'character', 'tutor', 'design')['ready'])
        revision = creative_fingerprint(self.root, 'character', 'tutor', 'design')
        selected = select_character_candidate(self.root, 'tutor', 'concept-2', revision)
        self.assertEqual(sum(item['selected'] for item in selected['candidates']), 1)
        self.approve('design')
        (self.root / paths[1]).write_bytes(b'broken')
        self.assertNotEqual(creative_review_state(self.root, 'character', 'tutor', 'design')['state'], 'approved')

    def test_unregistered_manifests_never_become_review_ready_and_bad_shapes_fail_detail(self):
        self.created()
        folder = self.root / 'characters/tutor/01_design'
        paths = [self.image(f'characters/tutor/01_design/candidates/{n}.png', (n, 0, 0)) for n in range(3)]
        (folder / 'candidates.json').write_text(json.dumps([
            {'id': f'concept-{n}', 'path': path, 'sha256': ws._file_hash(self.root / path), 'selected': n == 0}
            for n, path in enumerate(paths)]))
        self.assertFalse(creative_review_state(self.root, 'character', 'tutor', 'design')['ready'])
        (folder / 'candidates.json').write_text('["a", "b", "c"]')
        with self.assertRaises(ws.WorkspaceError) as error:
            character_detail(self.root, 'tutor')
        self.assertEqual(error.exception.code, 'invalid')

    def test_private_batch_invalidation_stales_approved_design_and_duplicate_bitmap_is_rejected(self):
        self.created()
        paths = [self.image(f'characters/tutor/generated/character-concepts-fixture/{n}.png', (n, 0, 0)) for n in range(3)]
        batch = self.completed_batch('character-concepts', paths)
        record = generation_detail(self.root, batch)
        record['outputs'][2] = record['outputs'][0].copy()
        from studio import generation
        generation._save(self.root, record)
        with self.assertRaises(ws.WorkspaceError):
            register_character_candidates(self.root, 'tutor', batch,
                                          creative_fingerprint(self.root, 'character', 'tutor', 'brief'))
        record['outputs'][2] = {'path': paths[2], 'sha256': ws._file_hash(self.root / paths[2])}
        generation._save(self.root, record)
        register_character_candidates(self.root, 'tutor', batch,
                                      creative_fingerprint(self.root, 'character', 'tutor', 'brief'))
        select_character_candidate(self.root, 'tutor', 'concept-1',
                                   creative_fingerprint(self.root, 'character', 'tutor', 'design'))
        self.approve('design')
        record['state'] = 'partial'
        generation._save(self.root, record)
        state = creative_review_state(self.root, 'character', 'tutor', 'design')
        self.assertEqual((state['state'], state['ready']), ('stale', False))

    def test_malformed_reference_record_returns_explicit_invalid(self):
        self.approved_identity()
        (self.root / 'characters/tutor/02_identity/reference-set.json').write_text('null')
        with self.assertRaises(ws.WorkspaceError) as error:
            character_detail(self.root, 'tutor')
        self.assertEqual(error.exception.code, 'invalid')

    def test_identity_readiness_requires_batch_reference_to_selected_concept(self):
        self.approved_identity()
        reference = character_detail(self.root, 'tutor')['reference_set']
        from studio import generation
        record = generation_detail(self.root, reference['generation_id'])
        record['resolved_references'] = []
        generation._save(self.root, record)
        state = creative_review_state(self.root, 'character', 'tutor', 'identity')
        self.assertEqual((state['state'], state['ready']), ('stale', False))

    def approved_identity(self):
        self.created()
        self.concepts()
        with self.assertRaises(ws.WorkspaceError):
            prepare_character_identity(self.root, 'tutor')
        revision = creative_fingerprint(self.root, 'character', 'tutor', 'design')
        select_character_candidate(self.root, 'tutor', 'concept-1', revision)
        self.approve('design')
        request = prepare_character_identity(self.root, 'tutor')
        self.assertEqual(request['state'], 'awaiting-batch-approval')
        paths = [self.image(f'characters/tutor/generated/{request["id"]}/{name}.png', (0, n, 0))
                 for n, name in enumerate(('sheet', 'scene'))]
        request['state'] = 'completed'
        request['outputs'] = [{'path': path, 'sha256': ws._file_hash(self.root / path)} for path in paths]
        from studio import generation
        generation._save(self.root, request)
        constraints = {'hair': 'Chosen curls', 'eyes': 'Chosen brown', 'face': 'Chosen oval',
                       'proportions': 'Chosen proportions', 'clothing': 'Chosen blazer'}
        register_character_identity(self.root, 'tutor', request['id'], constraints,
                                    creative_fingerprint(self.root, 'character', 'tutor', 'design'))
        self.assertTrue(creative_review_state(self.root, 'character', 'tutor', 'identity')['ready'])
        self.assertEqual(character_detail(self.root, 'tutor')['reviews']['identity']['state'], 'draft')
        self.approve('identity')
        return constraints

    def test_identity_requires_approved_selected_concept_and_both_artworks(self):
        self.approved_identity()

    def test_identity_route_is_explicit_and_preserved_in_batch(self):
        self.created()
        self.concepts()
        select_character_candidate(self.root, 'tutor', 'concept-1',
                                   creative_fingerprint(self.root, 'character', 'tutor', 'design'))
        self.approve('design')
        request = prepare_character_identity(self.root, 'tutor', transport='native')
        self.assertEqual(request['transport'], 'native')
        self.assertEqual(request['image_model'], 'unknown')
        self.assertFalse(request['transparent'])

    def test_changes_requested_identity_can_be_refined_without_rewriting_selected_concept(self):
        self.approved_identity()
        old = character_detail(self.root, 'tutor')['reference_set']
        current = creative_fingerprint(self.root, 'character', 'tutor', 'identity')
        decide_creative(self.root, 'character', 'tutor', 'identity', 'changes-requested', 'Reviewer', 'Refine face', current)
        request = prepare_character_identity(self.root, 'tutor')
        paths = [self.image(f'characters/tutor/generated/{request["id"]}/{name}.png', (0, n + 3, 0))
                 for n, name in enumerate(('sheet', 'scene'))]
        request['state'] = 'completed'
        request['outputs'] = [{'path': path, 'sha256': ws._file_hash(self.root / path)} for path in paths]
        from studio import generation
        generation._save(self.root, request)
        refined = register_character_identity(self.root, 'tutor', request['id'],
            {**old['appearance'], 'face': 'Refined chosen oval'},
            creative_fingerprint(self.root, 'character', 'tutor', 'design'))
        self.assertEqual(refined['reference_set']['candidate_sha256'], old['candidate_sha256'])
        self.assertEqual(refined['reviews']['identity']['state'], 'stale')

    def test_changes_requested_identity_rejects_stale_registry_before_material_writes(self):
        self.approved_identity()
        revision = creative_fingerprint(self.root, 'character', 'tutor', 'identity')
        decide_creative(self.root, 'character', 'tutor', 'identity', 'changes-requested', 'Reviewer', 'Refine face', revision)
        current = ws._file_hash(self.root / 'characters/tutor/02_identity/reference-set.json')
        request = prepare_character_identity(self.root, 'tutor')
        paths = [self.image(f'characters/tutor/generated/{request["id"]}/{name}.png', (0, n + 5, 0))
                 for n, name in enumerate(('sheet', 'scene'))]
        request['state'] = 'completed'
        request['outputs'] = [{'path': path, 'sha256': ws._file_hash(self.root / path)} for path in paths]
        from studio import generation
        generation._save(self.root, request)
        locks = character_detail(self.root, 'tutor')['reference_set']['appearance']
        canonical = (self.root / 'characters/tutor/02_identity/reference-set.json').read_bytes()
        design = creative_fingerprint(self.root, 'character', 'tutor', 'design')
        with self.assertRaises(ws.WorkspaceError):
            register_character_identity(self.root, 'tutor', request['id'], locks, design,
                                        replace_revision='0' * 64, confirm_replace=True)
        for name in ('sheet', 'in-scene'):
            self.assertFalse((self.root / f'library/materials/tutor-{request["id"]}-{name}').exists())
        self.assertEqual((self.root / 'characters/tutor/02_identity/reference-set.json').read_bytes(), canonical)
        result = register_character_identity(self.root, 'tutor', request['id'], locks, design,
                                             replace_revision=current, confirm_replace=True)
        self.assertEqual(result['reference_set']['generation_id'], request['id'])

    def test_changed_brief_can_replace_candidates_only_with_current_registry_confirmation(self):
        self.created()
        self.concepts()
        old = character_detail(self.root, 'tutor')['candidates']
        old_revision = ws._file_hash(self.root / 'characters/tutor/01_design/candidates.json')
        detail = character_detail(self.root, 'tutor')
        save_workshop_answers(self.root, 'character', 'tutor', {'subject': 'A newly directed tutor'},
                              brief='A newly directed professional tutor.', expected_revision=detail['revision'])
        self.approve('brief')
        paths = [self.image(f'characters/tutor/generated/new-concepts/{n}.png', (n, 9, 0)) for n in range(3)]
        batch = self.completed_batch('character-concepts', paths, batch_id='new-concepts')
        revision = creative_fingerprint(self.root, 'character', 'tutor', 'brief')
        with self.assertRaises(ws.WorkspaceError):
            register_character_candidates(self.root, 'tutor', batch, revision)
        with self.assertRaises(ws.WorkspaceError):
            register_character_candidates(self.root, 'tutor', batch, revision,
                                          replace_revision='0' * 64, confirm_replace=True)
        replaced = register_character_candidates(self.root, 'tutor', batch, revision,
                                                 replace_revision=old_revision, confirm_replace=True)
        self.assertEqual(replaced['candidates'][0]['generation_id'], batch)
        self.assertTrue((self.root / old[0]['path']).is_file())
        self.assertEqual(replaced['reviews']['design']['state'], 'draft')
        self.assertFalse(replaced['reviews']['design']['ready'])

    def test_new_selected_concept_can_replace_stale_identity_with_current_confirmation(self):
        locks = self.approved_identity()
        old = character_detail(self.root, 'tutor')['reference_set']
        old_revision = ws._file_hash(self.root / 'characters/tutor/02_identity/reference-set.json')
        select_character_candidate(self.root, 'tutor', 'concept-2',
                                   creative_fingerprint(self.root, 'character', 'tutor', 'design'))
        self.approve('design')
        self.assertEqual(creative_review_state(self.root, 'character', 'tutor', 'identity')['state'], 'stale')
        request = prepare_character_identity(self.root, 'tutor')
        paths = [self.image(f'characters/tutor/generated/{request["id"]}/{name}.png', (0, n + 9, 0))
                 for n, name in enumerate(('sheet', 'scene'))]
        request['state'] = 'completed'
        request['outputs'] = [{'path': path, 'sha256': ws._file_hash(self.root / path)} for path in paths]
        from studio import generation
        generation._save(self.root, request)
        revision = creative_fingerprint(self.root, 'character', 'tutor', 'design')
        with self.assertRaises(ws.WorkspaceError):
            register_character_identity(self.root, 'tutor', request['id'], locks, revision)
        with self.assertRaises(ws.WorkspaceError):
            register_character_identity(self.root, 'tutor', request['id'], locks, revision,
                                        replace_revision='0' * 64, confirm_replace=True)
        replaced = register_character_identity(self.root, 'tutor', request['id'], locks, revision,
                                               replace_revision=old_revision, confirm_replace=True)
        self.assertEqual(replaced['reference_set']['candidate_id'], 'concept-2')
        self.assertTrue((self.root / old['sheet']).is_file())
        self.assertEqual(replaced['reviews']['identity']['state'], 'stale')

    def test_variant_binds_master_identity_and_stales_on_art_change(self):
        constraints = self.approved_identity()
        ws.create_style(self.root, 'ink', 'Ink', 'modern')
        ws.create_style(self.root, 'modern', 'Modern', 'modern')
        revision = creative_fingerprint(self.root, 'character', 'tutor', 'identity')
        manifest = {'style_id': 'ink', 'views': ['front', 'three-quarter-right'],
                    'appearance': constraints, 'monochrome_exception': False}
        with self.assertRaises(ws.WorkspaceError):
            register_character_variant(self.root, 'tutor', 'ink', manifest, revision)
        request = prepare_character_variant(self.root, 'tutor', 'ink', 'ink', 'Make one matching ink-style sheet')
        self.assertEqual(request['context']['variant_id'], 'ink')
        self.assertEqual(request['context']['style_id'], 'ink')
        artwork = self.image(f'characters/tutor/generated/{request["id"]}/sheet.png', (0, 0, 1))
        request['state'] = 'completed'
        request['outputs'] = [{'path': artwork, 'sha256': ws._file_hash(self.root / artwork)}]
        from studio import generation
        generation._save(self.root, request)
        with self.assertRaises(ws.WorkspaceError):
            register_character_variant(self.root, 'tutor', 'wrong', {**manifest, 'generation_id': request['id']}, revision)
        with self.assertRaises(ws.WorkspaceError):
            register_character_variant(self.root, 'tutor', 'ink', {**manifest, 'style_id': 'modern', 'generation_id': request['id']}, revision)
        completed = threading.Event()
        outcome = []
        def register_waiting():
            try:
                outcome.append(register_character_variant(self.root, 'tutor', 'ink',
                    {**manifest, 'generation_id': request['id']}, revision))
            except Exception as exc:
                outcome.append(exc)
            finally:
                completed.set()
        with ws.workspace_lock(self.root):
            worker = threading.Thread(target=register_waiting)
            worker.start()
            self.assertFalse(completed.wait(0.15))
        worker.join(timeout=2)
        self.assertTrue(completed.is_set())
        if isinstance(outcome[0], Exception): raise outcome[0]
        variant = outcome[0]
        self.assertEqual(variant['identity_revision'], revision)
        self.assertEqual(variant['artwork']['sha256'], ws._file_hash(self.root / artwork))
        self.assertEqual(character_detail(self.root, 'tutor')['variants'][0]['state'], 'draft')
        self.assertEqual(len(request['resolved_references']), 2)
        old_variant_revision = ws._file_hash(self.root / 'characters/tutor/03_animation/ink/variant.json')
        replacement = prepare_character_variant(self.root, 'tutor', 'ink', 'ink', 'Refresh the synthetic variant')
        newer_art = self.image(f'characters/tutor/generated/{replacement["id"]}/sheet.png', (0, 0, 9))
        replacement['state'] = 'completed'
        replacement['outputs'] = [{'path': newer_art, 'sha256': ws._file_hash(self.root / newer_art)}]
        generation._save(self.root, replacement)
        with self.assertRaises(ws.WorkspaceError):
            register_character_variant(self.root, 'tutor', 'ink', {**manifest, 'generation_id': replacement['id']}, revision)
        with self.assertRaises(ws.WorkspaceError):
            register_character_variant(self.root, 'tutor', 'ink', {**manifest, 'generation_id': replacement['id']}, revision,
                                       replace_revision='0' * 64, confirm_replace=True)
        refreshed = register_character_variant(self.root, 'tutor', 'ink', {**manifest, 'generation_id': replacement['id']}, revision,
                                               replace_revision=old_variant_revision, confirm_replace=True)
        self.assertEqual(refreshed['artwork']['sha256'], ws._file_hash(self.root / newer_art))
        self.assertTrue((self.root / artwork).is_file())
        self.assertTrue((self.root / f'characters/tutor/history/variant/{old_variant_revision}.json').is_file())
        self.assertEqual(creative_review_state(self.root, 'character', 'tutor', 'identity')['state'], 'approved')
        from studio.character_motion import prepare_animation
        animation = prepare_animation(self.root, 'tutor', 'ink', 'wave', transport='native')
        self.assertEqual(animation['state'], 'awaiting-batch-approval')
        self.assertEqual(animation['transport'], 'native')
        self.assertEqual(len(animation['resolved_references']), 3)
        self.assertEqual(animation['context']['variant_id'], 'ink')
        api_variant = prepare_character_variant(self.root, 'tutor', 'api-ink', 'ink',
            'Transparent two-view art', transport='openai-api', image_model='gpt-image-1.5', max_paid_spend='1.00')
        self.assertEqual((api_variant['transport'], api_variant['requested_image_model'], api_variant['transparent']),
                         ('openai-api', 'gpt-image-1.5', True))
        with self.assertRaises(ws.WorkspaceError):
            register_character_variant(self.root, 'tutor', 'wrong', {**manifest, 'appearance': {**constraints, 'eyes': 'blue'}}, revision)
        style_path = self.root / 'styles/ink/style.md'
        original_style = style_path.read_bytes()
        style_path.write_bytes(original_style + b'\nChanged style intent\n')
        self.assertEqual(character_detail(self.root, 'tutor')['variants'][0]['state'], 'stale')
        style_path.write_bytes(original_style)
        reference = json.loads((self.root / 'characters/tutor/02_identity/reference-set.json').read_text())
        (self.root / reference['sheet']).write_bytes(b'changed')
        self.assertEqual(creative_review_state(self.root, 'character', 'tutor', 'identity')['state'], 'stale')
        self.assertEqual(character_detail(self.root, 'tutor')['variants'][0]['state'], 'stale')
        with self.assertRaises(ws.WorkspaceError):
            prepare_character_variant(self.root, 'tutor', 'ink', 'ink', 'Changed art')


if __name__ == '__main__':
    unittest.main()


class CharacterHttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'studio/web').mkdir(parents=True)
        (self.root / 'studio/web/index.html').write_text('<html>Studio</html>')
        self.server = make_server(self.root, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'
        bootstrap = json.load(urlopen(self.base + '/api/bootstrap'))
        self.token = bootstrap['token']
        self.session = 'b' * 32 + '.' + bootstrap['session_nonce']

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def call(self, path, method='GET', body=None, token=True):
        if token and method != 'GET':
            from studio.permissions import grant
            if path == '/api/characters': scope = 'character:' + str((body or {}).get('id', ''))
            elif path.startswith('/api/characters/'):
                scope = 'character:' + path.split('/')[3]
            else: scope = None
            if scope: grant(self.root, scope, 'each-stage', session_id=self.session)
        return urlopen(Request(self.base + path, method=method,
            data=json.dumps(body).encode() if body is not None else None,
            headers={'Content-Type': 'application/json', 'X-Studio-Token': self.token if token else '', 'X-VF-Session-ID': self.session}))

    def test_character_routes_keep_drafts_and_require_revision_on_selection(self):
        with self.call('/api/characters') as response:
            self.assertEqual(json.load(response), [])
        with self.assertRaises(HTTPError) as error:
            self.call('/api/characters', 'POST', {'id': 'tutor', 'prompt': 'A tutor', 'metadata': {'title': 'Teacher'}}, False)
        self.assertEqual(error.exception.code, 403)
        with self.call('/api/characters', 'POST', {'id': 'tutor', 'prompt': 'A tutor', 'metadata': {'title': 'Teacher'}}) as response:
            self.assertEqual(response.status, 201)
            self.assertEqual(json.load(response)['profile']['identity'], 'draft')
        with self.call('/api/characters/tutor') as response:
            self.assertEqual(json.load(response)['candidates'], [])
        with self.assertRaises(HTTPError) as error:
            self.call('/api/characters/tutor/candidate', 'PUT', {'candidate_id': 'concept-1', 'expected_revision': 'stale'})
        self.assertEqual(error.exception.code, 409)

    def test_file_api_cannot_write_generated_character_manifests(self):
        with self.call('/api/characters', 'POST', {'id': 'tutor', 'prompt': 'A tutor', 'metadata': {'title': 'Tutor'}}):
            pass
        for path in ('characters/tutor/01_design/candidates.json', 'characters/tutor/02_identity/reference-set.json',
                     'characters/tutor/03_animation/ink/variant.json'):
            with self.assertRaises(HTTPError) as error:
                self.call('/api/files', 'PUT', {'path': path, 'text': '{}', 'expected_revision': None})
            self.assertEqual(error.exception.code, 400)
        (self.root / 'characters/tutor/01_design/candidates.json').write_text('null')
        with self.assertRaises(HTTPError) as error:
            self.call('/api/characters/tutor')
        self.assertEqual(error.exception.code, 400)
