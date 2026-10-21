import hashlib
import fcntl
import json
import os
import socket
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

from studio import workspace as ws
from studio.creative import (creative_fingerprint, creative_detail, create_creative, save_workshop_answers,
                             mark_creative_ready, decide_creative, creative_review_state)
from studio.references import (plan_style_materials, request_style_materials, save_website_reference,
                               prepare_style_sample, public_url, sample_valid, inspect_website)
from studio.references import sample_status
from studio.references import _pinned_fetch, _PinnedHTTPSConnection, _source_hashes, _sample_image, _register_sample


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        create_creative(self.root, 'style', 'classroom', 'A warm classroom',
                        {'title': 'Classroom', 'supported_formats': ['wide'],
                         'setting': 'A recurring classroom', 'environment': 'Warm wood and daylight',
                         'visual_instructions': 'Keep the teacher at screen left.'})

    def test_recipe_fields_and_material_plan(self):
        style = ws._style(self.root, 'classroom')
        self.assertEqual(style['setting'], 'A recurring classroom')
        plan = plan_style_materials(self.root, 'classroom')
        self.assertEqual(plan['setting'], style['setting'])
        self.assertEqual({x['route'] for x in plan['options']}, {'supplied', 'openai', 'licensed-stock'})
        self.assertTrue(all(x['description'] for x in plan['options']))
        self.assertEqual(plan['state'], 'waiting-for-agent')
        source = self.root / 'library/classroom.png'
        source.parent.mkdir()
        source.write_bytes(b'first')
        ws.create_material(self.root, {'id': 'classroom-art', 'title': 'Classroom art',
            'description': 'Reusable classroom background, behind the teacher.', 'kind': 'image',
            'source': 'library/classroom.png', 'rights': 'User supplied', 'tags': ['classroom']})
        ws.link_material(self.root, 'style', 'classroom', 'classroom-art')
        before = creative_fingerprint(self.root, 'style', 'classroom', 'materials')
        source.write_bytes(b'second')
        self.assertNotEqual(before, creative_fingerprint(self.root, 'style', 'classroom', 'materials'))

    def test_website_evidence_rejects_private_urls_and_unsafe_paths(self):
        for url in ('http://127.0.0.1/', 'http://localhost/', 'http://192.168.1.4/',
                    'file:///etc/passwd', 'https://user:pass@example.org/'):
            with self.subTest(url=url), self.assertRaises(ws.WorkspaceError):
                public_url(url)
        screenshot = self.root / 'styles/classroom/02_assets/website/original.png'
        screenshot.parent.mkdir(parents=True)
        Image.new('RGB', (128, 128), 'white').save(screenshot)
        evidence = {'url': 'https://example.org/', 'captured_at': '2026-10-09T12:00:00Z',
                    'screenshot': 'styles/classroom/02_assets/website/original.png',
                    'palette': [{'color': '#112233', 'source': 'computed background-color'}],
                    'fonts': [{'family': 'Arial', 'source': 'computed font-family'}],
                    'components': [{'name': 'primary button', 'description': 'round green button'}],
                    'logo_candidates': [{'url': 'https://example.org/logo.svg', 'rights': 'unknown'}]}
        bad = {**evidence, 'screenshot': '../_auth/secret.png'}
        with patch('studio.references.socket.getaddrinfo', return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', ('93.184.215.14', 443))]):
            with self.assertRaises(ws.WorkspaceError):
                save_website_reference(self.root, 'classroom', bad, creative_fingerprint(self.root, 'style', 'classroom', 'materials'))
            result = save_website_reference(self.root, 'classroom', evidence, creative_fingerprint(self.root, 'style', 'classroom', 'materials'))
        self.assertEqual(result['evidence']['logo_candidates'][0]['rights'], 'unknown')
        before = creative_fingerprint(self.root, 'style', 'classroom', 'materials')
        screenshot.write_bytes(b'changed')
        self.assertNotEqual(before, creative_fingerprint(self.root, 'style', 'classroom', 'materials'))

    def test_sample_claims_require_rendered_video(self):
        folder = self.root / 'styles/classroom/03_sample/wide'
        folder.mkdir(parents=True)
        (folder / 'index.html').write_text('<html>placeholder</html>')
        from studio.creative import creative_review_state
        self.assertIn('wide style sample', creative_review_state(self.root, 'style', 'classroom', 'sample')['missing'])
        with self.assertRaises(ws.WorkspaceError):
            prepare_style_sample(self.root, 'classroom', 'tall')
        lock_path = self.root / '.studio/sample-classroom-wide.lock'
        lock_path.parent.mkdir(exist_ok=True)
        with lock_path.open('a+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(sample_status(self.root, 'classroom', 'wide')['state'], 'rendering')
            with self.assertRaises(ws.WorkspaceError) as error:
                prepare_style_sample(self.root, 'classroom', 'wide')
            self.assertEqual(error.exception.code, 'busy')
            fcntl.flock(lock, fcntl.LOCK_UN)
        create_creative(self.root, 'style', 'unclaimed', 'No format claim', {'title': 'Unclaimed', 'supported_formats': []})
        self.assertIn('claimed style format', creative_review_state(self.root, 'style', 'unclaimed', 'sample')['missing'])

    def test_material_request_binds_current_style_sources(self):
        with self.assertRaises(ws.WorkspaceError):
            request_style_materials(self.root, 'classroom', 'openai', 'Draw a reusable room.')
        detail = creative_detail(self.root, 'style', 'classroom')
        save_workshop_answers(self.root, 'style', 'classroom', {'setting': 'A classroom'},
                              brief='Draw a classroom for course explainers.', expected_revision=detail['revision'])
        brief = creative_fingerprint(self.root, 'style', 'classroom', 'brief')
        mark_creative_ready(self.root, 'style', 'classroom', 'brief', brief)
        decide_creative(self.root, 'style', 'classroom', 'brief', 'approved', 'Fixture test', '', brief)
        revision = creative_fingerprint(self.root, 'style', 'classroom', 'materials')
        with self.assertRaises(ws.WorkspaceError):
            request_style_materials(self.root, 'classroom', 'openai', 'Draw a reusable room.', expected_revision='old')
        request = request_style_materials(self.root, 'classroom', 'openai', 'Draw a reusable room.', expected_revision=revision)
        self.assertEqual(request['input_revision'], creative_fingerprint(self.root, 'style', 'classroom', 'materials'))
        (self.root / 'styles/classroom/style.md').write_text((self.root / 'styles/classroom/style.md').read_text() + '\nChanged direction.\n')
        from studio import jobs
        with self.assertRaises(ws.WorkspaceError):
            jobs.claim_request(self.root, request['id'], 'agent')

    def test_pinned_fetch_uses_validated_address_for_actual_connection(self):
        calls = []
        class Response:
            status = 200
            def getheaders(self): return [('Content-Type', 'text/html')]
            def read(self, limit): return b'<html></html>'
        class Connection:
            def __init__(self, host, port, timeout): calls.append(('connect', host, port))
            def request(self, method, path, headers): calls.append(('request', method, path, headers['Host']))
            def getresponse(self): return Response()
            def close(self): pass
        with patch('studio.references.socket.getaddrinfo', return_value=[(2, 1, 6, '', ('93.184.215.14', 80))]), \
             patch('studio.references.http.client.HTTPConnection', Connection):
            status, headers, body = _pinned_fetch('http://example.org/path', {})
        self.assertEqual((status, body), (200, b'<html></html>'))
        self.assertEqual(calls, [('connect', '93.184.215.14', 80), ('request', 'GET', '/path', 'example.org')])
        class TLS:
            def wrap_socket(self, raw, server_hostname):
                calls.append(('sni', server_hostname))
                return raw
        with patch('studio.references.ssl.create_default_context', return_value=TLS()), \
             patch('studio.references.socket.create_connection', side_effect=lambda target, timeout: calls.append(('tls-connect', target)) or object()):
            _PinnedHTTPSConnection('example.org', '93.184.215.14', 443).connect()
        self.assertIn(('tls-connect', ('93.184.215.14', 443)), calls)
        self.assertIn(('sni', 'example.org'), calls)

    def test_sample_inputs_and_media_claims_must_match(self):
        root = self.root
        runtime = root / '_runtime/player.js'
        runtime.parent.mkdir()
        runtime.write_text('first runtime')
        template = root / 'styles/classroom/template/wide/index.html'
        template.parent.mkdir(parents=True)
        template.write_text('<div id="stage"></div>')
        folder = root / 'styles/classroom/03_sample/wide'
        folder.mkdir(parents=True)
        video = folder / 'sample.mp4'
        video.write_bytes(b'fixture video')
        sources = _source_hashes(root, 'classroom', 'wide', template, [])
        manifest = {'renderer': 'modern', 'format': 'wide', 'duration': 12, 'fps': 24, 'resources': [],
                    'materials_revision': creative_fingerprint(root, 'style', 'classroom', 'materials'),
                    'video_sha256': hashlib.sha256(video.read_bytes()).hexdigest(), 'sources': sources}
        (folder / 'sample.json').write_text(json.dumps(manifest))
        valid_stream = {'width': 960, 'height': 540, 'duration': '12.000000', 'nb_frames': '288', 'avg_frame_rate': '24/1'}
        with patch('studio.references.sample_probe', return_value=valid_stream), patch('studio.references._moving_frames', return_value=True):
            self.assertTrue(sample_valid(root, 'classroom', 'wide'))
            template.write_text('changed template')
            self.assertFalse(sample_valid(root, 'classroom', 'wide'))
            template.write_text('<div id="stage"></div>')
            runtime.write_text('changed runtime')
            self.assertFalse(sample_valid(root, 'classroom', 'wide'))
            runtime.write_text('first runtime')
            dependency = root / 'library/scene-art.png'
            dependency.parent.mkdir()
            dependency.write_bytes(b'first artwork')
            manifest['resources'] = ['library/scene-art.png']
            manifest['sources'] = _source_hashes(root, 'classroom', 'wide', template, manifest['resources'])
            (folder / 'sample.json').write_text(json.dumps(manifest))
            self.assertTrue(sample_valid(root, 'classroom', 'wide'))
            dependency.write_bytes(b'changed artwork')
            self.assertFalse(sample_valid(root, 'classroom', 'wide'))
            dependency.write_bytes(b'first artwork')
            for change in ({'duration': '24.000000', 'nb_frames': '576'}, {'avg_frame_rate': '30/1'}, {'nb_frames': '240'}):
                with patch('studio.references.sample_probe', return_value={**valid_stream, **change}):
                    self.assertFalse(sample_valid(root, 'classroom', 'wide'))

    def test_negated_rights_never_select_source_image(self):
        source = self.root / 'library/classroom.png'
        source.parent.mkdir()
        Image.new('RGB', (128, 128), 'white').save(source)
        for index, rights in enumerate(('No permission granted', 'not user supplied')):
            material_id = f'unsafe-{index}'
            ws.create_material(self.root, {'id': material_id, 'title': 'Source', 'description': 'Room backdrop',
                'kind': 'image', 'source': 'library/classroom.png', 'rights': rights, 'tags': []})
            ws.link_material(self.root, 'style', 'classroom', material_id)
        self.assertIsNone(_sample_image(self.root, ws._style(self.root, 'classroom')))

    def test_failed_rerender_preserves_prior_video_and_manifest(self):
        detail = creative_detail(self.root, 'style', 'classroom')
        save_workshop_answers(self.root, 'style', 'classroom', {'setting': 'Classroom'},
                              brief='Synthetic fixture for safe replacement.', expected_revision=detail['revision'])
        brief = creative_fingerprint(self.root, 'style', 'classroom', 'brief')
        mark_creative_ready(self.root, 'style', 'classroom', 'brief', brief)
        decide_creative(self.root, 'style', 'classroom', 'brief', 'approved', 'Fixture', '', brief)
        (self.root / 'styles/classroom/materials.md').write_text('A detailed synthetic classroom material description.')
        materials = creative_fingerprint(self.root, 'style', 'classroom', 'materials')
        mark_creative_ready(self.root, 'style', 'classroom', 'materials', materials)
        decide_creative(self.root, 'style', 'classroom', 'materials', 'approved', 'Fixture', '', materials)
        folder = self.root / 'styles/classroom/03_sample/wide'
        folder.mkdir(parents=True)
        (folder / 'sample.mp4').write_bytes(b'previous-video')
        (folder / 'sample.json').write_bytes(b'previous-manifest')
        async def fake_render(endpoint, html, target, dimensions):
            target.write_bytes(b'new invalid video')
            return {}
        with patch('studio.jobs._contained_browser', return_value=('box-1', 'cdp')), \
             patch('studio.jobs._stop_box'), patch('studio.references._render_sample', fake_render), \
             patch('studio.references.sample_valid', return_value=False):
            with self.assertRaises(ws.WorkspaceError):
                prepare_style_sample(self.root, 'classroom', 'wide')
        self.assertEqual((folder / 'sample.mp4').read_bytes(), b'previous-video')
        self.assertEqual((folder / 'sample.json').read_bytes(), b'previous-manifest')

    def test_registration_rolls_back_after_swap_or_manifest_write_failure(self):
        folder = self.root / 'styles/classroom/03_sample/wide'
        folder.mkdir(parents=True)
        previous = {folder / 'sample.mp4': b'old video', folder / 'sample.json': b'old manifest',
                    folder / 'index.html': b'old html'}
        from studio import references
        real_replace = references.os.replace
        for failure in ('validator', 'manifest-write'):
            with self.subTest(failure=failure):
                for path, data in previous.items(): path.write_bytes(data)
                staged_video = folder / '.new-video.mp4'; staged_video.write_bytes(b'new video')
                staged_manifest = folder / '.new-manifest.json'; staged_manifest.write_text('{}')
                staged_html = folder / '.new-source.html'; staged_html.write_text('new html')
                def replace(source, target):
                    if failure == 'manifest-write' and source == staged_manifest and target == folder / 'sample.json':
                        raise OSError('disk failure')
                    return real_replace(source, target)
                with patch('studio.references._sample_output_valid', return_value=True), \
                     patch('studio.references.sample_valid', return_value=False), \
                     patch('studio.references.os.replace', side_effect=replace):
                    with self.assertRaises((ws.WorkspaceError, OSError)):
                        _register_sample(self.root, 'classroom', 'wide', staged_video, staged_manifest,
                                         staged_html, creative_fingerprint(self.root, 'style', 'classroom', 'materials'), True)
                self.assertEqual({path: path.read_bytes() for path in previous}, previous)

    def test_inspection_rejects_concurrent_style_change(self):
        image = self.root / 'styles/classroom/materials.md'
        picture = Image.new('RGB', (128, 128), 'white')
        from io import BytesIO
        stream = BytesIO(); picture.save(stream, format='PNG')
        async def fake_page(endpoint, url):
            image.write_text('Changed while browser inspected the page.')
            return {'title': 'Example', 'palette': [], 'fonts': [], 'components': [], 'logo_candidates': []}, stream.getvalue(), url, {}
        with patch('studio.references.public_url', side_effect=lambda value: value), \
             patch('studio.jobs._contained_browser', return_value=('box-1', 'cdp')), \
             patch('studio.jobs._stop_box'), patch('studio.references._inspect_page', fake_page):
            with self.assertRaises(ws.WorkspaceError) as error:
                inspect_website(self.root, 'classroom', 'https://example.org/')
        self.assertEqual(error.exception.code, 'conflict')

    @unittest.skipUnless(os.getenv('RUN_CONTAINED_WEB'), 'contained public website proof')
    def test_contained_website_capture_keeps_original_evidence(self):
        with tempfile.TemporaryDirectory(prefix='.website-fixture-', dir=Path.cwd()) as temporary:
            root = Path(temporary)
            create_creative(root, 'style', 'fixture', 'Synthetic site extraction fixture', {'title': 'Fixture'})
            result = inspect_website(root, 'fixture', 'https://example.org/')
            self.assertEqual(result['evidence']['url'], 'https://example.org/')
            self.assertTrue((root / result['evidence']['screenshot']).is_file())
            self.assertEqual(result['evidence']['screenshot_sha256'],
                             hashlib.sha256((root / result['evidence']['screenshot']).read_bytes()).hexdigest())

    @unittest.skipUnless(os.getenv('RUN_CONTAINED_RENDER'), 'contained browser render proof')
    def test_contained_wide_and_tall_reels_are_real_synthetic_fixtures(self):
        with tempfile.TemporaryDirectory(prefix='.style-fixture-', dir=Path.cwd()) as temporary:
            root = Path(temporary)
            shutil.copytree(Path(__file__).parents[1] / '_runtime', root / '_runtime')
            renderer = os.getenv('RENDER_FAMILY', 'modern')
            create_creative(root, 'style', 'fixture', 'Synthetic classroom render fixture',
                            {'title': 'Synthetic fixture', 'supported_formats': ['wide', 'tall'],
                             'renderer': renderer, 'setting': 'Classroom', 'components': ['Welcome', 'Learn', 'Practice']})
            detail = creative_detail(root, 'style', 'fixture')
            save_workshop_answers(root, 'style', 'fixture', {'setting': 'Synthetic classroom'},
                                  brief='Synthetic test fixture for rendering.', expected_revision=detail['revision'])
            brief = creative_fingerprint(root, 'style', 'fixture', 'brief')
            mark_creative_ready(root, 'style', 'fixture', 'brief', brief)
            decide_creative(root, 'style', 'fixture', 'brief', 'approved', 'Fixture test', '', brief)
            (root / 'styles/fixture/materials.md').write_text('# Materials\n\nSynthetic authored classroom shapes used solely for render verification.\n')
            source = root / 'library/synthetic-classroom.png'
            source.parent.mkdir()
            Image.new('RGB', (320, 240), '#86b0a2').save(source)
            ws.create_material(root, {'id': 'synthetic-classroom', 'title': 'Synthetic classroom',
                'description': 'Fixture background used on the classroom board.', 'kind': 'image',
                'source': 'library/synthetic-classroom.png', 'rights': 'User supplied', 'tags': ['fixture']})
            ws.link_material(root, 'style', 'fixture', 'synthetic-classroom')
            materials = creative_fingerprint(root, 'style', 'fixture', 'materials')
            mark_creative_ready(root, 'style', 'fixture', 'materials', materials)
            decide_creative(root, 'style', 'fixture', 'materials', 'approved', 'Fixture test', '', materials)
            wide = prepare_style_sample(root, 'fixture', 'wide')
            self.assertEqual(json.loads((root / wide['manifest']).read_text())['image_source'], 'library/synthetic-classroom.png')
            if os.getenv('RUN_REPAIR_SMOKE'):
                self.assertTrue(sample_valid(root, 'fixture', 'wide'))
                return
            self.assertFalse(creative_review_state(root, 'style', 'fixture', 'sample')['ready'])
            prepare_style_sample(root, 'fixture', 'tall')
            self.assertTrue(sample_valid(root, 'fixture', 'wide'))
            self.assertTrue(sample_valid(root, 'fixture', 'tall'))
            self.assertTrue(creative_review_state(root, 'style', 'fixture', 'sample')['ready'])


if __name__ == '__main__':
    unittest.main()
