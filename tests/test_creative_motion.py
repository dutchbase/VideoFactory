"""Synthetic character art exercises pack trust boundaries and controlled motion."""

import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw

from studio import workspace as ws
from studio.character_motion import compile_character_pack, export_character_frames, prepare_animation, motion_template
from studio.characters import character_capabilities


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.pack = self.root / 'characters/tutor/03_animation/line'
        self.pack.mkdir(parents=True)
        art = self.root / 'characters/tutor/generated/variant-fixture/sheet.png'
        art.parent.mkdir(parents=True)
        atlas = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(atlas)
        for index in range(16):
            x, y = index % 8 * 8, index // 8 * 8
            draw.rectangle((x, y, x + 7, y + 7), fill=(10 + index * 12, 40, 160, 255))
            draw.rectangle((x, y + 16, x + 7, y + 23), fill=(10 + index * 12, 80, 120, 255))
        atlas.save(art)
        self.art = art.relative_to(self.root).as_posix()
        self.sha = ws._file_hash(art)
        self.variant = {'id': 'line', 'style_id': 'line', 'artwork': {'path': self.art, 'sha256': self.sha,
                        'views': ['front', 'three-quarter-right']}}
        parts = {}
        for index, name in enumerate(('body', 'head', 'hair', 'arm-left', 'arm-right', 'face', 'face-blink',
                                      'face-happy', 'face-puzzled', 'face-surprised', 'face-disappointed',
                                      'mouth-closed', 'mouth-half', 'mouth-open', 'book', 'tablet')):
            at = {'body': [32, 40], 'head': [32, 25], 'hair': [32, 17], 'arm-left': [22, 38],
                  'arm-right': [42, 38], 'book': [50, 37], 'tablet': [50, 37], 'face-puzzled': [38, 25]}.get(name, [32, 25] if name.startswith('face') else [32, 31])
            parts[name] = {'path': self.art, 'sha256': self.sha, 'crop': [index % 8 * 8, index // 8 * 8, 8, 8],
                           'at': at, 'anchor': [4, 4], 'layer': index}
        angled = {name: {**part, 'crop': [part['crop'][0], part['crop'][1] + 16, 8, 8]}
                  for name, part in parts.items()}
        assets = {'schema': 1, 'canvas': [64, 64], 'views': {'front': parts, 'three-quarter-right': angled}}
        rig = {'schema': 1, 'views': {view: {'draw_order': list(parts),
            'expressions': {key: ('face' if key == 'neutral' else 'face-' + key)
                            for key in ('neutral', 'blink', 'happy', 'puzzled', 'surprised', 'disappointed')},
            'mouths': {key: 'mouth-' + key for key in ('closed', 'half', 'open')},
            'props': {'book': 'book', 'tablet': 'tablet'}} for view in assets['views']}}
        actions = {name: motion_template(name) for name in
                   ('idle', 'blink', 'talk', 'point', 'present', 'wave', 'sit', 'stand', 'computer',
                    'happy', 'puzzled', 'surprised', 'disappointed', 'hold-prop', 'present-prop')}
        for name, value in [('assets', assets), ('rig', rig), ('motions', {'schema': 1, 'actions': actions})]:
            (self.pack / (name + '.json')).write_text(json.dumps(value))

    def compiled(self):
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}):
            return compile_character_pack(self.root, 'tutor', 'line')

    def test_capabilities_only_claim_valid_authored_actions(self):
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}), \
             patch('studio.characters.creative_review_state', return_value={'state': 'draft'}):
            result = character_capabilities(self.root, 'tutor', 'line')
            self.assertIsNone(result['error'])
            self.assertEqual(result['supported']['views'], ['front', 'three-quarter-right'])
            self.assertIn('idle', result['authored']['actions'])
            self.assertEqual(next(item for item in result['supported']['actions'] if item['id'] == 'idle')['review'], 'draft')
            self.assertFalse(any(next(item for item in result['supported']['actions'] if item['id'] == 'idle')['exports'].values()))
            path = self.pack / 'assets.json'
            assets = json.loads(path.read_text())
            assets['views']['front']['body']['crop'] = [60, 60, 8, 8]
            path.write_text(json.dumps(assets))
            result = character_capabilities(self.root, 'tutor', 'line')
            self.assertTrue(result['error'])
            self.assertEqual(result['supported']['actions'], [])
            self.assertIn('idle', result['authored']['actions'])

    def test_invalid_active_native_keeps_saved_clip_discoverable(self):
        native = self.pack / 'native'
        pointer = native / 'renders/front/idle/neutral/current.json'
        pointer.parent.mkdir(parents=True)
        pointer.write_text('{}')
        (native / 'manifest.json').write_text('{broken')
        candidate = self.pack / 'native-candidate'
        candidate.mkdir()
        (candidate / 'manifest.json').write_text('{broken')
        (candidate / 'new-evidence.txt').write_text('revised')
        prior = {'path': 'characters/tutor/03_animation/line/native/renders/front/idle/neutral/old',
                 'preview': 'characters/tutor/03_animation/line/native/renders/front/idle/neutral/old/preview.mp4'}
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}), \
             patch('studio.characters.creative_review_state', return_value={'state': 'stale'}), \
             patch('studio.native_pipeline.render_status', return_value={'current': False, 'clip': prior, 'error': 'source needs repair'}):
            result = character_capabilities(self.root, 'tutor', 'line')['native']
        self.assertTrue(result['registered'])
        self.assertFalse(result['available'])
        self.assertFalse(result['source_matches'])
        self.assertTrue(result['error'])
        self.assertEqual(result['bindings'][0]['render']['clip'], prior)

    def test_review_fingerprint_ignores_in_progress_export_directories(self):
        from studio.creative import creative_fingerprint
        temporary = self.pack / 'frames/idle/.export-in-progress'
        temporary.mkdir(parents=True)
        (temporary / '0000.png').write_bytes(b'partial')
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}):
            fingerprint = creative_fingerprint(self.root, 'character', 'tutor', 'animation:line:idle')
            (temporary / '0000.png').write_bytes(b'changed partial')
            self.assertEqual(creative_fingerprint(self.root, 'character', 'tutor', 'animation:line:idle'), fingerprint)

    def test_native_registration_adds_rig_gate_and_stales_action_on_source_change(self):
        import shutil
        from studio.creative import _previous, _readiness, _write_event, creative_fingerprint
        from studio.native_character import write_render_manifest
        source = Path(__file__).resolve().parents[1] / 'studio/native_pilot'
        native = self.pack / 'native'
        native.mkdir()
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}):
            before = creative_fingerprint(self.root, 'character', 'tutor', 'animation:line:idle')
            self.assertEqual(_previous('character', 'animation:line:idle', self.pack.parents[1]), 'identity')
        for name in ('switch-gesture.sif', 'face-open.png', 'face-closed.png', 'arm.png'):
            shutil.copy2(source / name, native / name)
        write_render_manifest(native / 'switch-gesture.sif', native / 'manifest.json',
                              settings={'fps': 24, 'frame_count': 240},
                              capabilities_result={'renderer': {'pinned': True, 'png_target': True}},
                              controls={'expression': ['eyes-open', 'eyes-closed']})
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}):
            after = creative_fingerprint(self.root, 'character', 'tutor', 'animation:line:idle')
            self.assertNotEqual(before, after)
            self.assertEqual(_previous('character', 'animation:line:idle', self.pack.parents[1]), 'rig:line')
            with patch('studio.creative.creative_review_state', return_value={'state': 'approved'}), \
                 patch('studio.characters._registered_variant', return_value=self.variant):
                ready, missing = _readiness(self.root, 'character', 'tutor', 'rig:line')
                self.assertFalse(ready)
                self.assertIn('pinned Synfig 1.4.5 with PNG output', missing)
                self.assertTrue(any('evidence registry' in item for item in missing))
                (native / 'face-open.png').write_bytes(b'changed')
                ready, missing = _readiness(self.root, 'character', 'tutor', 'rig:line')
                self.assertFalse(ready)
            self.assertNotEqual(after, creative_fingerprint(self.root, 'character', 'tutor', 'animation:line:idle'))
            _write_event(self.pack.parents[1], 'character', {'gate': 'rig:line', 'kind': 'ready',
                         'fingerprint': 'old', 'at': '2026-10-10T00:00:00Z'})
            (native / 'manifest.json').unlink()
            self.assertEqual(_previous('character', 'animation:line:idle', self.pack.parents[1]), 'identity')
            self.assertEqual(before, creative_fingerprint(self.root, 'character', 'tutor', 'animation:line:idle'))

    def test_native_candidate_does_not_change_existing_canvas_action_fingerprint(self):
        from studio.creative import _previous, creative_fingerprint
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}):
            before = creative_fingerprint(self.root, 'character', 'tutor', 'animation:line:idle')
            candidate = self.pack / 'native-candidate'
            candidate.mkdir()
            (candidate / 'manifest.json').write_text('{"schema":1}')
            self.assertEqual(_previous('character', 'animation:line:idle', self.pack.parents[1]), 'identity')
            self.assertEqual(before, creative_fingerprint(self.root, 'character', 'tutor', 'animation:line:idle'))

    def test_activated_native_action_needs_current_clips_in_both_views(self):
        from studio.creative import _files, _readiness
        (self.pack / 'native').mkdir()
        (self.pack / 'native/manifest.json').write_text('{"schema":1}')
        clips = {}
        for view in ('front', 'three-quarter-right'):
            output = self.pack / 'native/renders' / view / 'idle/neutral/hash'
            (output / 'frames').mkdir(parents=True)
            (output / 'preview.mp4').write_bytes(b'preview')
            (output / 'frames/0000.png').write_bytes(b'frame')
            (output / 'render.json').write_text(json.dumps({'frames': [{'file': '0000.png'}]}))
            clips[view] = {'current': True, 'clip': {'path': output.relative_to(self.root).as_posix()}}
        with patch('studio.native_pipeline.render_status', side_effect=lambda _root, _id, _variant, view, *_: clips[view]), \
             patch('studio.creative.creative_review_state', return_value={'state': 'approved'}):
            files = _files(self.pack.parents[1], 'character', 'animation:line:idle')
            self.assertEqual(sum(path.name == 'preview.mp4' for path in files), 2)
            self.assertTrue(_readiness(self.root, 'character', 'tutor', 'animation:line:idle')[0])
            clips['three-quarter-right'] = {'current': False, 'clip': clips['three-quarter-right']['clip']}
            ready, missing = _readiness(self.root, 'character', 'tutor', 'animation:line:idle')
            self.assertFalse(ready)
            self.assertIn('current native idle clip for three-quarter-right', missing)

    def test_rig_evidence_requires_current_distinct_images_for_both_views(self):
        from studio.creative import _validate_rig_evidence
        native = self.pack / 'native'
        native.mkdir()
        (native / 'manifest.json').write_text('{"schema":1}', encoding='utf-8')
        roles = ('neutral', 'blink', 'mouth_contact_sheet', 'head_movement',
                 'elbows_bent', 'hands_crossing_torso')
        views = {}
        for view in ('front', 'three-quarter-right'):
            images = {}
            for number, role in enumerate(roles):
                path = native / f'{view}-{role}.png'
                Image.new('RGBA', (128, 128), (number * 25, 20, 70, 255)).save(path)
                images[role] = {'path': path.name, 'sha256': ws._file_hash(path)}
            views[view] = {'mouth_states': list('ABCDEFGHX'), 'images': images}
        evidence = {'schema': 1, 'source_sha256': ws._file_hash(native / 'manifest.json'),
                    'views': views}
        (native / 'rig-review.json').write_text(json.dumps(evidence), encoding='utf-8')
        registration = {'projects': {'front': {}, 'three-quarter-right': {}},
                        'controls': {'mouth_shapes': list('ABCDEFGHX')}}
        _validate_rig_evidence(native, registration)
        (native / 'manifest.json').write_text('{"schema":1,"changed":true}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'current native source'):
            _validate_rig_evidence(native, registration)
        (native / 'manifest.json').write_text('{"schema":1}', encoding='utf-8')
        (native / 'front-blink.png').write_bytes(b'stale')
        with self.assertRaisesRegex(ValueError, 'stale'):
            _validate_rig_evidence(native, registration)
        Image.new('RGBA', (128, 128), (10, 20, 70, 255)).save(native / 'front-blink.png')
        evidence['views']['front']['images']['blink']['sha256'] = ws._file_hash(native / 'front-blink.png')
        evidence['views']['front']['images']['blink']['path'] = '../elsewhere.png'
        (native / 'rig-review.json').write_text(json.dumps(evidence), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            _validate_rig_evidence(native, registration)

    def test_compiler_rejects_unregistered_art_and_bad_crops(self):
        manifest = self.compiled()
        self.assertEqual(manifest['canvas'], [64, 64])
        self.assertEqual(manifest['renderer_revision'], 2)
        self.assertEqual(manifest['engine_sha256'], ws._file_hash(Path(__file__).resolve().parents[1] / '_runtime/character.js'))
        self.assertIn('wave', manifest['actions'])
        path = self.pack / 'assets.json'
        data = json.loads(path.read_text())
        data['views']['front']['body']['crop'] = [60, 60, 8, 8]
        path.write_text(json.dumps(data))
        with self.assertRaises(ws.WorkspaceError): self.compiled()
        data['views']['front']['body']['crop'] = [0, 0, 8, 8]
        data['views']['front']['body']['path'] = 'library/random.png'
        path.write_text(json.dumps(data))
        with self.assertRaises(ws.WorkspaceError): self.compiled()

    def test_idle_accepts_only_authored_face_and_rest_mouth(self):
        motions_path = self.pack / 'motions.json'
        rig_path = self.pack / 'rig.json'
        motions = json.loads(motions_path.read_text())
        motions['actions'] = {'idle': motions['actions']['idle']}
        motions_path.write_text(json.dumps(motions))
        rig = json.loads(rig_path.read_text())
        for view in rig['views'].values():
            view['expressions'] = {name: value for name, value in view['expressions'].items()
                                   if name in ('neutral', 'blink')}
            view['mouths'] = {'closed': view['mouths']['closed']}
        rig_path.write_text(json.dumps(rig))
        self.assertEqual(list(self.compiled()['actions']), ['idle'])
        rig['views']['front']['expressions'].pop('blink')
        rig_path.write_text(json.dumps(rig))
        self.assertEqual(list(self.compiled()['actions']), ['idle'])
        motions['actions']['blink'] = motion_template('blink')
        motions_path.write_text(json.dumps(motions))
        with self.assertRaises(ws.WorkspaceError): self.compiled()

    def test_compiler_preserves_optional_destination_size_and_legacy_parts(self):
        self.assertNotIn('size', self.compiled()['views']['front']['parts']['head'])
        substitute = self.root / self.art
        ws.create_material(self.root, {'id': 'substitute', 'title': 'Fixture prop',
            'description': 'Synthetic prop art for boundary test', 'kind': 'image',
            'source': self.art, 'rights': 'User supplied', 'tags': []})
        path = self.pack / 'assets.json'
        original = json.loads(path.read_text())
        original['views']['front']['head']['size'] = [12.5, 16]
        original['views']['front']['book'].update(path=self.art,
            sha256=ws._file_hash(substitute), material_id='substitute', size=[10, 12])
        path.write_text(json.dumps(original))
        manifest = self.compiled()
        self.assertEqual(manifest['views']['front']['parts']['head']['size'], [12.5, 16])
        self.assertEqual(manifest['views']['front']['parts']['book']['size'], [10, 12])

        for size in ([0, 8], [2049, 8], [True, 8], [1, float('inf')], [float('nan'), 8], [10**400, 8]):
            with self.subTest(size=size):
                invalid = json.loads(json.dumps(original))
                invalid['views']['front']['head']['size'] = size
                path.write_text(json.dumps(invalid))
                with self.assertRaises(ws.WorkspaceError): self.compiled()
        unknown = json.loads(json.dumps(original))
        unknown['views']['front']['head']['unexpected'] = True
        path.write_text(json.dumps(unknown))
        with self.assertRaises(ws.WorkspaceError): self.compiled()

    def test_compiler_validates_normalized_clip_polygons_and_field_combinations(self):
        substitute = self.root / self.art
        ws.create_material(self.root, {'id': 'substitute', 'title': 'Fixture prop',
            'description': 'Synthetic prop art for boundary test', 'kind': 'image',
            'source': self.art, 'rights': 'User supplied', 'tags': []})
        path = self.pack / 'assets.json'
        original = json.loads(path.read_text())
        triangle = [[0, 0], [1, 0], [0, 1]]
        tiny = float.fromhex('0x0.0000000000001p-1022')
        tiny_triangle = [[0, 0], [tiny, 0], [0, tiny]]
        maximum = triangle * 42 + [[0, 0], [1, 0]]
        original['views']['front']['head'].update(size=[16, 12], clip=triangle)
        original['views']['front']['arm-left']['clip'] = triangle
        original['views']['front']['hair']['clip'] = tiny_triangle
        original['views']['front']['book'].update(path=self.art, sha256=ws._file_hash(substitute),
            material_id='substitute', clip=triangle)
        original['views']['front']['tablet'].update(path=self.art, sha256=ws._file_hash(substitute),
            material_id='substitute', size=[12, 10], clip=maximum)
        path.write_text(json.dumps(original))
        manifest = self.compiled()
        parts = manifest['views']['front']['parts']
        self.assertEqual(parts['head']['clip'], triangle)
        self.assertEqual(parts['arm-left']['clip'], triangle)
        self.assertNotIn('size', parts['book'])
        self.assertEqual(parts['tablet']['clip'], maximum)
        self.assertEqual(parts['hair']['clip'], tiny_triangle)

        invalid_clips = [
            None, [], [[0, 0], [1, 0]], [[0, 0], [1, 0], [2, 0]],
            [[0, 0], [0.5, 0.5], [1, 1]], [[-0.1, 0], [1, 0], [0, 1]],
            [[0, 0], [1.1, 0], [0, 1]], [[10**400, 0], [1, 0], [0, 1]],
            [[float('nan'), 0], [1, 0], [0, 1]], [[float('inf'), 0], [1, 0], [0, 1]],
            [[True, 0], [1, 0], [0, 1]], [[0, 0, 0], [1, 0], [0, 1]], triangle * 43,
        ]
        for clip in invalid_clips:
            with self.subTest(clip=clip):
                invalid = json.loads(json.dumps(original))
                invalid['views']['front']['head']['clip'] = clip
                path.write_text(json.dumps(invalid))
                with self.assertRaises(ws.WorkspaceError): self.compiled()

    def test_core_parts_cannot_become_optional_roles_or_material_props(self):
        path = self.pack / 'rig.json'
        rig = json.loads(path.read_text())
        rig['views']['front']['expressions']['neutral'] = 'body'
        path.write_text(json.dumps(rig))
        with self.assertRaises(ws.WorkspaceError): self.compiled()
        rig['views']['front']['expressions']['neutral'] = 'face'
        rig['views']['front']['props']['body-swap'] = 'body'
        path.write_text(json.dumps(rig))
        with self.assertRaises(ws.WorkspaceError): self.compiled()
        substitute = self.root / 'library/substitute.png'
        substitute.parent.mkdir(parents=True)
        Image.new('RGBA', (8, 8), (255, 0, 0, 255)).save(substitute)
        ws.create_material(self.root, {'id': 'substitute', 'title': 'Fixture prop', 'description': 'Synthetic prop art for boundary test',
                                            'kind': 'image', 'source': 'library/substitute.png', 'rights': 'User supplied', 'tags': []})
        assets_path = self.pack / 'assets.json'
        assets = json.loads(assets_path.read_text())
        assets['views']['front']['body'].update(path='library/substitute.png', sha256=ws._file_hash(substitute),
                                               material_id='substitute', crop=[0, 0, 8, 8])
        assets_path.write_text(json.dumps(assets))
        with self.assertRaises(ws.WorkspaceError): self.compiled()

    def test_malformed_rig_values_return_workspace_error(self):
        path = self.pack / 'rig.json'
        original = json.loads(path.read_text())
        for edit in ('props-list', 'draw-order-list', 'expression-list'):
            rig = json.loads(json.dumps(original))
            if edit == 'props-list': rig['views']['front']['props'] = []
            elif edit == 'draw-order-list': rig['views']['front']['draw_order'][0] = []
            else: rig['views']['front']['expressions']['neutral'] = []
            path.write_text(json.dumps(rig))
            with self.subTest(edit=edit), self.assertRaises(ws.WorkspaceError): self.compiled()

    def test_compiler_preserves_expression_part_groups_and_legacy_strings(self):
        assets_path, rig_path = self.pack / 'assets.json', self.pack / 'rig.json'
        assets = json.loads(assets_path.read_text())
        rig = json.loads(rig_path.read_text())
        extra_names = ['face-extra', *[f'spare-{index}' for index in range(8)]]
        for view, parts in assets['views'].items():
            for name in extra_names:
                parts[name] = {**parts['face-blink'], 'layer': len(parts)}
            rig['views'][view]['draw_order'] = sorted(parts, key=lambda name: parts[name]['layer'])
            expressions = rig['views'][view]['expressions']
            expressions['blink'] = ['face-blink', 'face-extra']
            expressions['happy'] = ['face-happy']
            expressions['puzzled'] = ['face-puzzled', *extra_names[1:8]]
        assets_path.write_text(json.dumps(assets))
        rig_path.write_text(json.dumps(rig))

        manifest = self.compiled()
        expressions = manifest['views']['front']['rig']['expressions']
        self.assertEqual(expressions['neutral'], 'face')
        self.assertEqual(expressions['disappointed'], 'face-disappointed')
        self.assertEqual(expressions['blink'], ['face-blink', 'face-extra'])
        self.assertEqual(expressions['happy'], ['face-happy'])
        self.assertEqual(expressions['puzzled'], ['face-puzzled', *extra_names[1:8]])

        invalid_values = [
            [], ['face-blink'] * 2, ['face-blink', 'face-happy'],
            ['face-blink', 'mouth-closed'], ['face-blink', 'book'],
            ['face-blink', 'body'], ['face-blink', 'unknown-part'],
            ['face-blink', []], ['face-blink', None], ['face-blink', True],
            ['face-blink', *extra_names[:8]],
        ]
        for value in invalid_values:
            invalid = json.loads(json.dumps(rig))
            invalid['views']['front']['expressions']['blink'] = value
            rig_path.write_text(json.dumps(invalid))
            with self.subTest(expression=value), self.assertRaises(ws.WorkspaceError): self.compiled()

        for group, key in (('mouths', 'closed'), ('props', 'book')):
            invalid = json.loads(json.dumps(rig))
            invalid['views']['front'][group][key] = [invalid['views']['front'][group][key]]
            rig_path.write_text(json.dumps(invalid))
            with self.subTest(group=group), self.assertRaises(ws.WorkspaceError): self.compiled()

    def test_rig_change_invalidates_existing_character_export(self):
        from studio import character_motion
        def render(root, manifest, action, view, fps, output, prop):
            for number in range(int(manifest['actions'][action]['duration'] * fps)):
                Image.new('RGBA', tuple(manifest['canvas']), (10, 20, 30, 0)).save(output / f'{number:04d}.png')
        rig_path = self.pack / 'rig.json'
        original = rig_path.read_bytes()
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}), \
             patch('studio.character_motion.creative_review_state', return_value={'state': 'approved'}), \
             patch('studio.character_motion._render_frames', side_effect=render):
            export_character_frames(self.root, 'tutor', 'line', 'idle', 'front')
            self.assertTrue(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'idle', 'front'))
            rig = json.loads(original)
            expressions = rig['views']['front']['expressions']
            expressions['neutral'], expressions['happy'] = expressions['happy'], expressions['neutral']
            rig_path.write_text(json.dumps(rig))
            self.assertFalse(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'idle', 'front'))
            rig_path.write_bytes(original)
            self.assertTrue(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'idle', 'front'))

    def test_sit_and_stand_templates_hold_distinct_end_poses(self):
        self.assertTrue(all(all(frame[key] == 0 for key in ('x', 'y', 'rotation'))
                            for track in motion_template('idle')['tracks'].values() for frame in track))
        sit, stand = motion_template('sit'), motion_template('stand')
        self.assertFalse(sit['loop'])
        self.assertFalse(stand['loop'])
        self.assertEqual(sit['tracks']['body'][0]['y'], 0)
        self.assertGreater(sit['tracks']['body'][-1]['y'], 0)
        self.assertEqual(stand['tracks']['body'][0]['y'], sit['tracks']['body'][-1]['y'])
        self.assertEqual(stand['tracks']['body'][-1]['y'], 0)

    def test_missing_action_and_view_are_explicit(self):
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}):
            with self.assertRaises(ws.WorkspaceError):
                compile_character_pack(self.root, 'tutor', 'line', action='dance')
            with self.assertRaises(ws.WorkspaceError):
                compile_character_pack(self.root, 'tutor', 'line', view='left')

    def test_animation_art_request_attaches_both_canonical_and_variant_references(self):
        reference = {'appearance': {'hair': 'brown'}, 'material_ids': {'sheet': 'canonical-sheet', 'in-scene': 'canonical-scene'}}
        variant = {**self.variant, 'generation_id': 'variant-fixture', 'identity_revision': 'rev',
                   'monochrome_exception': False}
        with patch('studio.character_motion._registered_variant', return_value=variant), \
             patch('studio.character_motion._registered_reference', return_value=reference), \
             patch('studio.character_motion.creative_review_state', return_value={'state': 'approved', 'fingerprint': 'rev'}), \
             patch('studio.character_motion.ws._style_revision', return_value='style-rev'), \
             patch('studio.character_motion.prepare_generation', side_effect=lambda root, request: request):
            request = prepare_animation(self.root, 'tutor', 'line', 'wave')
        self.assertEqual(request['purpose'], 'character-animation')
        self.assertEqual(request['context']['variant_id'], 'line')
        self.assertEqual({r['material_id'] for r in request['references']},
                         {'canonical-sheet', 'canonical-scene', 'tutor-variant-fixture-variant'})
        self.assertTrue(request['transparent'])
        self.assertEqual(request['motion_template'], motion_template('wave'))

    def test_export_requires_contained_browser_and_preserves_old_index(self):
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}), \
             patch('studio.character_motion.creative_review_state', return_value={'state': 'approved'}), \
             patch('studio.character_motion._render_frames', side_effect=ws.WorkspaceError('blocked', 'browser unavailable')):
            prior = self.pack / 'frames/idle/front/index.json'
            prior.parent.mkdir(parents=True)
            prior.write_text('previous')
            with self.assertRaises(ws.WorkspaceError):
                export_character_frames(self.root, 'tutor', 'line', 'idle', 'front')
            self.assertEqual(prior.read_text(), 'previous')

    def test_required_prop_is_export_state_and_stales_different_selection(self):
        from studio import character_motion
        def render(root, manifest, action, view, fps, output, prop):
            for number in range(int(manifest['actions'][action]['duration'] * fps)):
                Image.new('RGBA', tuple(manifest['canvas']), (10, 20, 30, 0)).save(output / f'{number:04d}.png')
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}), \
             patch('studio.character_motion.creative_review_state', return_value={'state': 'approved'}), \
             patch('studio.character_motion._render_frames', side_effect=render):
            with self.assertRaises(ws.WorkspaceError):
                export_character_frames(self.root, 'tutor', 'line', 'hold-prop', 'front')
            index = export_character_frames(self.root, 'tutor', 'line', 'hold-prop', 'front', prop='book')
            self.assertEqual(index['prop'], 'book')
            self.assertTrue(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'hold-prop', 'front', prop='book'))
            self.assertFalse(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'hold-prop', 'front', prop='other'))

    def test_registration_failure_restores_previous_frames_and_preview(self):
        from studio import character_motion
        def render(root, manifest, action, view, fps, output, prop):
            for number in range(int(manifest['actions'][action]['duration'] * fps)):
                Image.new('RGBA', tuple(manifest['canvas']), (10, 20, 30, 0)).save(output / f'{number:04d}.png')
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}), \
             patch('studio.character_motion.creative_review_state', return_value={'state': 'approved'}), \
             patch('studio.character_motion._render_frames', side_effect=render):
            export_character_frames(self.root, 'tutor', 'line', 'idle', 'front')
            index = self.pack / 'frames/idle/front/index.json'
            preview = self.pack / 'preview/idle/front.png'
            before = index.read_bytes(), preview.read_bytes()
            motions = json.loads((self.pack / 'motions.json').read_text())
            motions['actions']['idle']['expression'] = 'happy'
            (self.pack / 'motions.json').write_text(json.dumps(motions))
            real_write = ws._atomic_write
            def fail_preview(path, data):
                if path == preview: raise OSError('synthetic preview write failure')
                return real_write(path, data)
            with patch('studio.character_motion.ws._atomic_write', side_effect=fail_preview), self.assertRaises(OSError):
                export_character_frames(self.root, 'tutor', 'line', 'idle', 'front')
            self.assertEqual((index.read_bytes(), preview.read_bytes()), before)
            real_replace = os.replace
            def fail_move(source, destination):
                if Path(source) == preview: raise OSError('synthetic preview move failure')
                return real_replace(source, destination)
            with patch('studio.character_motion.os.replace', side_effect=fail_move), self.assertRaises(OSError):
                export_character_frames(self.root, 'tutor', 'line', 'idle', 'front')
            self.assertEqual((index.read_bytes(), preview.read_bytes()), before)

    def test_action_review_requires_the_same_prop_in_both_views(self):
        from studio.creative import _readiness
        def render(root, manifest, action, view, fps, output, prop):
            for number in range(int(manifest['actions'][action]['duration'] * fps)):
                Image.new('RGBA', tuple(manifest['canvas']), (10, 20, 30, 0)).save(output / f'{number:04d}.png')
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}), \
             patch('studio.character_motion.creative_review_state', return_value={'state': 'approved'}), \
             patch('studio.creative.creative_review_state', return_value={'state': 'approved'}), \
             patch('studio.character_motion._render_frames', side_effect=render):
            export_character_frames(self.root, 'tutor', 'line', 'hold-prop', 'front', prop='book')
            export_character_frames(self.root, 'tutor', 'line', 'hold-prop', 'three-quarter-right', prop='tablet')
            ready, missing = _readiness(self.root, 'character', 'tutor', 'animation:line:hold-prop')
            self.assertFalse(ready)
            self.assertIn('same selected prop in both views', missing)
            export_character_frames(self.root, 'tutor', 'line', 'hold-prop', 'three-quarter-right', prop='book')
            ready, missing = _readiness(self.root, 'character', 'tutor', 'animation:line:hold-prop')
            self.assertTrue(ready, missing)

    def test_action_export_tracks_exact_sources_and_unrelated_actions(self):
        from studio import character_motion
        def render(root, manifest, action, view, fps, output, prop):
            for number in range(int(manifest['actions'][action]['duration'] * fps)):
                Image.new('RGBA', tuple(manifest['canvas']), (10, 20, 30, 0)).save(output / f'{number:04d}.png')
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}), \
             patch('studio.character_motion.creative_review_state', return_value={'state': 'approved'}), \
             patch('studio.character_motion._render_frames', side_effect=render):
            front = export_character_frames(self.root, 'tutor', 'line', 'idle', 'front')
            export_character_frames(self.root, 'tutor', 'line', 'idle', 'three-quarter-right')
            wave = export_character_frames(self.root, 'tutor', 'line', 'wave', 'front')
            self.assertEqual(len(wave['frames']), 60)
            self.assertTrue(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'idle', 'front'))
            self.assertEqual(front, export_character_frames(self.root, 'tutor', 'line', 'idle', 'front'))
            motion_path = self.pack / 'motions.json'
            motions = json.loads(motion_path.read_text())
            motions['actions']['wave']['expression'] = 'happy'
            motion_path.write_text(json.dumps(motions))
            self.assertTrue(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'idle', 'front'))
            motions['actions']['idle']['expression'] = 'happy'
            motion_path.write_text(json.dumps(motions))
            self.assertFalse(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'idle', 'front'))
            motions['actions']['idle']['expression'] = 'neutral'
            motion_path.write_text(json.dumps(motions))
            assets_path = self.pack / 'assets.json'
            original_assets = assets_path.read_bytes()
            assets = json.loads(assets_path.read_text())
            assets['views']['front']['head']['size'] = [10, 10]
            assets_path.write_text(json.dumps(assets))
            self.assertFalse(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'idle', 'front'))
            assets_path.write_bytes(original_assets)
            self.assertTrue(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'idle', 'front'))
            assets = json.loads(original_assets)
            assets['views']['front']['head']['clip'] = [[0, 0], [1, 0], [0, 1]]
            assets_path.write_text(json.dumps(assets))
            self.assertFalse(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'idle', 'front'))
            assets_path.write_bytes(original_assets)
            self.assertTrue(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'idle', 'front'))
            (self.pack / 'frames/idle/front/0000.png').write_bytes(b'changed')
            self.assertFalse(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'idle', 'front'))

    def test_legacy_frame_export_signature_is_stale_after_renderer_revision(self):
        import hashlib
        from studio import character_motion
        def render(root, manifest, action, view, fps, output, prop):
            for number in range(int(manifest['actions'][action]['duration'] * fps)):
                Image.new('RGBA', tuple(manifest['canvas']), (0, 0, 0, 0)).save(output / f'{number:04d}.png')
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}), \
             patch('studio.character_motion.creative_review_state', return_value={'state': 'approved'}), \
             patch('studio.character_motion._render_frames', side_effect=render):
            index = export_character_frames(self.root, 'tutor', 'line', 'idle', 'front', fps=1)
            manifest = compile_character_pack(self.root, 'tutor', 'line', action='idle')
            legacy_revision = hashlib.sha256((manifest['source_revision'] + '\0').encode()).hexdigest()
            index['source_revision'] = legacy_revision
            (self.pack / 'frames/idle/front/index.json').write_text(json.dumps(index))
            self.assertFalse(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'idle', 'front'))

    def test_http_exposes_motion_template_and_keeps_export_token_guard(self):
        from studio.server import make_server
        server = make_server(self.root, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f'http://127.0.0.1:{server.server_port}'
        url = base + '/api/characters/tutor/variants/line/actions/wave/template'
        self.assertEqual(json.load(urlopen(url)), motion_template('wave'))
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}), \
             patch('studio.characters.creative_review_state', return_value={'state': 'draft'}):
            capabilities = json.load(urlopen(base + '/api/characters/tutor/variants/line/capabilities'))
        self.assertEqual(capabilities['renderer'], 'canvas')
        self.assertIn('wave', [action['id'] for action in capabilities['supported']['actions']])
        request = Request(base + '/api/characters/tutor/variants/line/actions/wave/export',
                          data=b'{"view":"front"}', headers={'Content-Type': 'application/json'})
        with self.assertRaises(HTTPError) as error: urlopen(request)
        self.assertEqual(error.exception.code, 403)

    @unittest.skipUnless(os.environ.get('CHARACTER_BROWSER_TEST') == '1', 'contained browser proof is opt-in')
    def test_contained_browser_export_canvas_edges_remain_transparent(self):
        from studio import character_motion
        assets_path = self.pack / 'assets.json'
        assets = json.loads(assets_path.read_text())
        assets['canvas'] = [768, 1240]
        assets_path.write_text(json.dumps(assets))
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}), \
             patch('studio.character_motion.creative_review_state', return_value={'state': 'approved'}):
            index = export_character_frames(self.root, 'tutor', 'line', 'idle', 'front', fps=1)
            self.assertEqual(len(index['frames']), 4)
            self.assertTrue(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'idle', 'front', fps=1))
            first = self.pack / 'frames/idle/front/0000.png'
            with Image.open(first) as image:
                self.assertEqual(image.size, (768, 1240))
                self.assertEqual(image.getpixel((767, 0)), (0, 0, 0, 0))
                self.assertEqual(image.getpixel((0, 1239)), (0, 0, 0, 0))

    @unittest.skipUnless(os.environ.get('CHARACTER_BROWSER_TEST') == '1', 'contained browser proof is opt-in')
    def test_contained_browser_frames_are_transparent_layered_looping_and_stable(self):
        from studio import character_motion
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}), \
             patch('studio.character_motion.creative_review_state', return_value={'state': 'approved'}):
            index = export_character_frames(self.root, 'tutor', 'line', 'idle', 'front')
            self.assertEqual(len(index['frames']), 120)
            self.assertTrue(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'idle', 'front'))
            first = self.pack / 'frames/idle/front/0000.png'
            with Image.open(first) as image:
                self.assertEqual(image.mode, 'RGBA')
                self.assertEqual(image.getpixel((0, 0))[3], 0)
                self.assertEqual(image.getpixel((32, 31))[:3], (10 + 11 * 12, 40, 160))
                self.assertEqual(image.getpixel((32, 40))[:3], (10, 40, 160))
            again = export_character_frames(self.root, 'tutor', 'line', 'idle', 'front')
            self.assertEqual(index, again)
            other = export_character_frames(self.root, 'tutor', 'line', 'idle', 'three-quarter-right')
            self.assertEqual(len(other['frames']), 120)
            self.assertTrue(character_motion.animation_export_valid(self.root, 'tutor', 'line', 'idle', 'three-quarter-right'))

    @unittest.skipUnless(os.environ.get('CHARACTER_BROWSER_TEST') == '1', 'contained browser proof is opt-in')
    def test_contained_browser_required_prop_export_has_alpha_and_pixels(self):
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}), \
             patch('studio.character_motion.creative_review_state', return_value={'state': 'approved'}):
            held = export_character_frames(self.root, 'tutor', 'line', 'hold-prop', 'front', prop='book')
            self.assertEqual((held['prop'], len(held['frames'])), ('book', 60))
            with Image.open(self.pack / 'frames/hold-prop/front/0000.png') as image:
                self.assertEqual(image.getpixel((0, 0))[3], 0)
                locations = [(x, y) for y in range(64) for x in range(64)
                             if image.getpixel((x, y)) == (10 + 14 * 12, 40, 160, 255)]
                self.assertTrue(locations, 'selected prop pixels must appear in the transparent export')

    @unittest.skipUnless(os.environ.get('CHARACTER_BROWSER_TEST') == '1', 'contained browser proof is opt-in')
    def test_contained_browser_head_attachments_and_transition_end_pose(self):
        from playwright.sync_api import sync_playwright
        from studio import jobs
        from studio.character_motion import ENGINE
        from studio.server import make_server
        motions = json.loads((self.pack / 'motions.json').read_text())
        motions['actions']['puzzled']['tracks']['head'][1]['rotation'] = 0.65
        (self.pack / 'motions.json').write_text(json.dumps(motions))
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}):
            manifest = compile_character_pack(self.root, 'tutor', 'line')
        server = make_server(self.root, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        box = None
        try:
            box, endpoint = jobs._contained_browser()
            with sync_playwright() as playwright:
                browser = playwright.chromium.connect_over_cdp(endpoint)
                page = browser.new_page(viewport={'width': 64, 'height': 64})
                page.goto(f'http://127.0.0.1:{server.server_port}/api/bootstrap')
                page.set_content('<canvas width="64" height="64"></canvas>')
                page.add_script_tag(content=Path(os.environ.get('CHARACTER_ENGINE_SOURCE') or ENGINE).read_text())
                page.evaluate('async m => { window.actor = await Character.load(m); }', manifest)
                script = '''({action,time}) => {
                  const canvas = document.querySelector('canvas'), ctx = canvas.getContext('2d');
                  ctx.clearRect(0,0,64,64);
                  const state = window.actor.draw(ctx,time,{action,view:'front',speechLevel:0});
                  const bytes = ctx.getImageData(0,0,64,64).data;
                  function box(red) { let xs=[], ys=[]; for(let y=0;y<64;y++) for(let x=0;x<64;x++) {
                    const i=(y*64+x)*4; if(bytes[i]===red && bytes[i+1]===40 && bytes[i+2]===160 && bytes[i+3]===255) {xs.push(x);ys.push(y)} }
                    return xs.length ? [Math.min(...xs),Math.min(...ys),Math.max(...xs),Math.max(...ys)] : null; }
                  return {state, hair:box(34), face:box(106), mouth:box(142), png:canvas.toDataURL()};
                }'''
                before = page.evaluate(script, {'action': 'puzzled', 'time': 0})
                tilted = page.evaluate(script, {'action': 'puzzled', 'time': 1})
                self.assertNotEqual(before['hair'][0], tilted['hair'][0])
                self.assertNotEqual(before['face'][1], tilted['face'][1])
                self.assertNotEqual(before['mouth'][0], tilted['mouth'][0])
                sit_end = page.evaluate(script, {'action': 'sit', 'time': 2})
                sit_later = page.evaluate(script, {'action': 'sit', 'time': 20})
                stand_start = page.evaluate(script, {'action': 'stand', 'time': 0})
                stand_end = page.evaluate(script, {'action': 'stand', 'time': 2})
                stand_later = page.evaluate(script, {'action': 'stand', 'time': 20})
                self.assertEqual(sit_end['png'], sit_later['png'])
                self.assertEqual(sit_end['png'], stand_start['png'])
                self.assertNotEqual(stand_start['png'], stand_end['png'])
                self.assertEqual(stand_end['png'], stand_later['png'])
                browser.close()
        finally:
            if box: jobs._stop_box(box)
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()

    @unittest.skipUnless(os.environ.get('CHARACTER_BROWSER_TEST') == '1', 'contained browser proof is opt-in')
    def test_contained_browser_scales_part_to_destination_size_and_anchor(self):
        from playwright.sync_api import sync_playwright
        from studio import jobs
        from studio.character_motion import ENGINE
        from studio.server import make_server
        assets_path = self.pack / 'assets.json'
        assets = json.loads(assets_path.read_text())
        head = assets['views']['front']['head']
        head.update(size=[16, 12], anchor=[3, 5])
        assets_path.write_text(json.dumps(assets))
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}):
            manifest = compile_character_pack(self.root, 'tutor', 'line')
        manifest['views']['front']['rig']['draw_order'] = ['head']
        server = make_server(self.root, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        box = None
        try:
            box, endpoint = jobs._contained_browser()
            with sync_playwright() as playwright:
                browser = playwright.chromium.connect_over_cdp(endpoint)
                page = browser.new_page(viewport={'width': 64, 'height': 64})
                page.goto(f'http://127.0.0.1:{server.server_port}/api/bootstrap')
                page.set_content('<canvas width="64" height="64"></canvas>')
                page.add_script_tag(content=Path(os.environ.get('CHARACTER_ENGINE_SOURCE') or ENGINE).read_text())
                page.evaluate('async m => { window.actor = await Character.load(m); }', manifest)
                bounds = page.evaluate('''() => {
                  const canvas = document.querySelector('canvas'), ctx = canvas.getContext('2d');
                  window.actor.draw(ctx, 0, {action:'idle', view:'front', speechLevel:0});
                  const pixels = ctx.getImageData(0, 0, 64, 64).data, xs = [], ys = [];
                  for (let y = 0; y < 64; y++) for (let x = 0; x < 64; x++) {
                    const i = (y * 64 + x) * 4;
                    if (pixels[i+3] > 0) {
                      xs.push(x); ys.push(y);
                    }
                  }
                  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
                }''')
                self.assertEqual(bounds, [29, 20, 44, 31])
                browser.close()
        finally:
            if box: jobs._stop_box(box)
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()

    @unittest.skipUnless(os.environ.get('CHARACTER_BROWSER_TEST') == '1', 'contained browser proof is opt-in')
    def test_contained_browser_clips_scaled_rotated_part_without_leaking_path_or_clip(self):
        from playwright.sync_api import sync_playwright
        from studio import jobs
        from studio.character_motion import ENGINE
        from studio.server import make_server
        assets_path = self.pack / 'assets.json'
        assets = json.loads(assets_path.read_text())
        assets['views']['front']['head'].update(size=[16, 12], anchor=[3, 5],
            clip=[[0, 0], [1, 0], [0, 1]])
        assets['views']['front']['body']['at'] = [40, 30]
        assets_path.write_text(json.dumps(assets))
        motions_path = self.pack / 'motions.json'
        motions = json.loads(motions_path.read_text())
        motions['actions']['stand']['tracks']['head'] = [
            {'t': 0, 'x': 0, 'y': 0, 'rotation': 0},
            {'t': 2, 'x': 0, 'y': 0, 'rotation': 0.5},
        ]
        motions_path.write_text(json.dumps(motions))
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}):
            manifest = compile_character_pack(self.root, 'tutor', 'line')
        manifest['views']['front']['rig']['draw_order'] = ['head', 'body']
        server = make_server(self.root, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        box = None
        try:
            box, endpoint = jobs._contained_browser()
            with sync_playwright() as playwright:
                browser = playwright.chromium.connect_over_cdp(endpoint)
                page = browser.new_page(viewport={'width': 64, 'height': 64})
                page.goto(f'http://127.0.0.1:{server.server_port}/api/bootstrap')
                page.set_content('<canvas width="64" height="64"></canvas>')
                page.add_script_tag(content=Path(os.environ.get('CHARACTER_ENGINE_SOURCE') or ENGINE).read_text())
                page.evaluate('async m => { window.actor = await Character.load(m); }', manifest)
                render = '''({time, bypassClip}) => {
                  const canvas = document.querySelector('canvas'), ctx = canvas.getContext('2d');
                  ctx.clearRect(0, 0, 64, 64);
                  ctx.beginPath(); ctx.rect(1, 1, 4, 4);
                  const before = ctx.isPointInPath(2, 2) && !ctx.isPointInPath(8, 8);
                  const hadOwnClip = Object.prototype.hasOwnProperty.call(ctx, 'clip');
                  const originalClip = ctx.clip;
                  if (bypassClip) ctx.clip = () => {};
                  try {
                    window.actor.draw(ctx, time, {action:'stand', view:'front', speechLevel:0});
                  } finally {
                    if (bypassClip) {
                      if (hadOwnClip) ctx.clip = originalClip;
                      else delete ctx.clip;
                    }
                  }
                  const pixels = ctx.getImageData(0, 0, 64, 64).data, xs = [], ys = [];
                  for (let y = 0; y < 64; y++) for (let x = 0; x < 64; x++) {
                    const i = (y * 64 + x) * 4;
                    if (pixels[i] > 16 && pixels[i+1] === 40 && pixels[i+2] === 160 && pixels[i+3] === 255) {
                      xs.push(x); ys.push(y);
                    }
                  }
                  const inside = Array.from(ctx.getImageData(32, 25, 1, 1).data);
                  const outside = Array.from(ctx.getImageData(40, 31, 1, 1).data);
                  const excluded = Array.from(ctx.getImageData(43, 24, 1, 1).data);
                  const after = ctx.isPointInPath(2, 2) && !ctx.isPointInPath(8, 8);
                  return {box:[Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)],
                    inside, outside, excluded, pathUnchanged:before && after};
                }'''
                unclipped = page.evaluate(render, {'time':0, 'bypassClip':True})
                straight = page.evaluate(render, {'time':0, 'bypassClip':False})
                rotated = page.evaluate(render, {'time':2, 'bypassClip':False})
                self.assertEqual(unclipped['excluded'][3], 255, unclipped)
                self.assertEqual(straight['excluded'], [0, 0, 0, 0], straight)
                self.assertNotEqual(straight['box'], rotated['box'])
                self.assertEqual(straight['inside'], [22, 40, 160, 255], straight)
                self.assertEqual(rotated['inside'], [22, 40, 160, 255])
                self.assertEqual(straight['outside'], [10, 40, 160, 255])
                self.assertEqual(rotated['outside'], [10, 40, 160, 255])
                self.assertTrue(straight['pathUnchanged'] and rotated['pathUnchanged'])
                browser.close()
        finally:
            if box: jobs._stop_box(box)
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()

    @unittest.skipUnless(os.environ.get('CHARACTER_BROWSER_TEST') == '1', 'contained browser proof is opt-in')
    def test_contained_browser_draws_expression_groups_and_inherits_head_rotation(self):
        from playwright.sync_api import sync_playwright
        from studio import jobs
        from studio.character_motion import ENGINE
        from studio.server import make_server
        left_color, right_color = (241, 30, 230, 255), (30, 241, 230, 255)
        with Image.open(self.root / self.art) as source:
            atlas = source.convert('RGBA')
        draw = ImageDraw.Draw(atlas)
        for y in (32, 48):
            draw.rectangle((0, y, 7, y + 7), fill=left_color)
            draw.rectangle((8, y, 15, y + 7), fill=right_color)
        atlas.save(self.root / self.art)
        self.sha = ws._file_hash(self.root / self.art)
        self.variant['artwork']['sha256'] = self.sha

        assets_path = self.pack / 'assets.json'
        assets = json.loads(assets_path.read_text())
        for view, parts in assets['views'].items():
            for part in parts.values(): part['sha256'] = self.sha
            y = 32 if view == 'front' else 48
            parts['lid-left'] = {'path': self.art, 'sha256': self.sha, 'crop': [0, y, 8, 8],
                'at': [29, 23], 'anchor': [4, 2], 'size': [8, 4], 'layer': 16}
            parts['lid-right'] = {'path': self.art, 'sha256': self.sha, 'crop': [8, y, 8, 8],
                'at': [35, 23], 'anchor': [4, 2], 'size': [8, 4], 'layer': 17}
        assets_path.write_text(json.dumps(assets))
        rig_path = self.pack / 'rig.json'
        rig = json.loads(rig_path.read_text())
        for view, mapping in rig['views'].items():
            mapping['expressions']['blink'] = ['lid-left', 'lid-right']
            mapping['draw_order'] = sorted(assets['views'][view],
                key=lambda name: assets['views'][view][name]['layer'])
        rig_path.write_text(json.dumps(rig))
        motions_path = self.pack / 'motions.json'
        motions = json.loads(motions_path.read_text())
        motions['actions']['puzzled']['tracks']['head'][1]['rotation'] = 0.65
        motions_path.write_text(json.dumps(motions))
        with patch('studio.character_motion._registered_variant', return_value=self.variant), \
             patch('studio.character_motion._registered_reference', return_value={}):
            manifest = compile_character_pack(self.root, 'tutor', 'line')

        server = make_server(self.root, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        box = None
        try:
            box, endpoint = jobs._contained_browser()
            with sync_playwright() as playwright:
                browser = playwright.chromium.connect_over_cdp(endpoint)
                page = browser.new_page(viewport={'width': 64, 'height': 64})
                page.goto(f'http://127.0.0.1:{server.server_port}/api/bootstrap')
                page.set_content('<canvas width="64" height="64"></canvas>')
                page.add_script_tag(content=Path(os.environ.get('CHARACTER_ENGINE_SOURCE') or ENGINE).read_text())
                page.evaluate('async m => { window.actor = await Character.load(m); }', manifest)
                render = '''({time, expression}) => {
                  const canvas = document.querySelector('canvas'), ctx = canvas.getContext('2d');
                  ctx.clearRect(0, 0, 64, 64);
                  const state = window.actor.draw(ctx, time,
                    {action:'puzzled', view:'front', expression, speechLevel:0});
                  const pixels = ctx.getImageData(0, 0, 64, 64).data;
                  function bounds(r, g, b) {
                    const xs = [], ys = [];
                    for (let y = 0; y < 64; y++) for (let x = 0; x < 64; x++) {
                      const i = (y * 64 + x) * 4;
                      if (pixels[i] === r && pixels[i+1] === g && pixels[i+2] === b && pixels[i+3] === 255) {
                        xs.push(x); ys.push(y);
                      }
                    }
                    return xs.length ? [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)] : null;
                  }
                  return {state, left:bounds(241,30,230), right:bounds(30,241,230)};
                }'''
                straight = page.evaluate(render, {'time':0, 'expression':'blink'})
                tilted = page.evaluate(render, {'time':1, 'expression':'blink'})
                hidden = page.evaluate(render, {'time':1, 'expression':'happy'})
                self.assertEqual(straight['state']['expression'], 'blink')
                self.assertIsNotNone(straight['left'], straight)
                self.assertIsNotNone(straight['right'], straight)
                self.assertNotEqual(straight['left'], tilted['left'])
                self.assertNotEqual(straight['right'], tilted['right'])
                self.assertIsNone(hidden['left'], hidden)
                self.assertIsNone(hidden['right'], hidden)
                faces = page.evaluate('''() => [0, 3.16, 3.30].map(time => ({
                  automatic: window.actor.draw(document.querySelector('canvas').getContext('2d'), time,
                    {action:'idle', view:'front', speechLevel:0}).expression,
                  override: window.actor.draw(document.querySelector('canvas').getContext('2d'), time,
                    {action:'idle', view:'front', expression:'neutral', speechLevel:0}).expression
                }))''')
                self.assertEqual(faces, [{'automatic':'neutral', 'override':'neutral'},
                                         {'automatic':'blink', 'override':'neutral'},
                                         {'automatic':'neutral', 'override':'neutral'}])
                browser.close()
        finally:
            if box: jobs._stop_box(box)
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()


if __name__ == '__main__': unittest.main()
