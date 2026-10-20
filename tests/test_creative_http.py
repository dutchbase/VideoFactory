import json
import base64
import random
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from studio.server import make_server
from studio import workspace as ws
from PIL import Image


class CreativeHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'studio/web').mkdir(parents=True)
        (self.root / 'studio/web/index.html').write_text('<html>Studio</html>')
        self.server = make_server(self.root, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'
        with self.call('/api/bootstrap') as response:
            self.token = json.load(response)['token']

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def call(self, path, method='GET', body=None, *, token=True):
        headers = {'Content-Type': 'application/json'}
        if token: headers['X-Studio-Token'] = self.token if hasattr(self, 'token') else ''
        return urlopen(Request(self.base + path, data=json.dumps(body).encode() if body is not None else None,
                               headers=headers, method=method))

    def test_end_to_end_style_workshop_and_review_link(self):
        with self.call('/api/style-families') as response:
            self.assertEqual(json.load(response), [])
        with self.call('/api/creative', 'POST', {'type': 'style', 'id': 'warm-line', 'prompt': 'Warm tutor scenes',
                                                'metadata': {'title': 'Warm Line'}}, token=True) as response:
            self.assertEqual(response.status, 201)
            detail = json.load(response)
        with self.call('/api/requests') as response:
            request = json.load(response)[0]
        self.assertEqual(request['subject'], {'type': 'style', 'id': 'warm-line'})
        with self.call('/api/creative/style/warm-line/answers', 'PUT',
                       {'answers': {'look': 'Warm line art'}, 'brief': 'Warm line art and motion for tutors.',
                        'expected_revision': detail['revision']}) as response:
            detail = json.load(response)
        fingerprint = detail['reviews']['brief']['fingerprint']
        with self.call('/api/creative/style/warm-line/reviews/brief/ready', 'POST', {'expected_revision': fingerprint}) as response:
            ready = json.load(response)
        self.assertEqual(ready['state'], 'awaiting-review')
        self.assertEqual(ready['review_url'], self.base + '/creative/style/warm-line/review/brief')
        with self.call('/creative/style/warm-line/review/brief') as response:
            self.assertEqual(response.status, 200)
        with self.call('/api/creative/style/warm-line/reviews/brief') as response:
            self.assertEqual(json.load(response)['state'], 'awaiting-review')
        with self.call('/api/creative/style/warm-line/reviews/brief/decision', 'POST',
                       {'expected_revision': fingerprint, 'decision': 'approved', 'reviewer': 'Reviewer', 'note': ''}) as response:
            self.assertEqual(json.load(response)['state'], 'approved')
        with self.call('/api/creative/style/warm-line/reviews/brief/ready', 'POST',
                       {'expected_revision': fingerprint}) as response:
            self.assertEqual(json.load(response)['state'], 'approved')
        with self.call('/api/styles') as response:
            self.assertEqual(len(json.load(response)), 1)

    def test_token_stale_revision_and_private_path_denial(self):
        with self.assertRaises(HTTPError) as error:
            self.call('/api/creative', 'POST', {'type': 'character', 'id': 'tutor', 'prompt': 'A tutor',
                                                'metadata': {'title': 'Teacher'}}, token=False)
        self.assertEqual(error.exception.code, 403)
        with self.call('/api/creative', 'POST', {'type': 'character', 'id': 'tutor', 'prompt': 'A tutor',
                                                'metadata': {'title': 'Teacher'}}) as response:
            detail = json.load(response)
        with self.assertRaises(HTTPError) as error:
            self.call('/api/creative/character/tutor/answers', 'PUT', {'answers': {'a': 'b'}, 'expected_revision': 'old'})
        self.assertEqual(error.exception.code, 409)
        with self.assertRaises(HTTPError) as error:
            self.call('/api/creative/character/%2e%2e/answers')
        self.assertEqual(error.exception.code, 404)
        with self.assertRaises(HTTPError) as error:
            self.call('/media/characters/tutor/_auth/secret.png')
        self.assertEqual(error.exception.code, 404)
        with self.call('/api/creative/character/tutor') as response:
            self.assertEqual(json.load(response)['revision'], detail['revision'])

    def test_style_template_reference_can_be_fingerprinted(self):
        template = self.root / '_templates/scene-modern-wide/index.html'
        template.parent.mkdir(parents=True)
        template.write_text('<html>Authored source</html>')
        with self.call('/api/creative', 'POST', {'type': 'style', 'id': 'warm-modern', 'prompt': 'Warm modern scenes',
                                                'metadata': {'title': 'Warm Modern', 'references': [
                                                    '_templates/scene-modern-wide/index.html']}}) as response:
            detail = json.load(response)
        self.assertEqual(detail['reviews']['materials']['state'], 'draft')
        before = detail['reviews']['materials']['fingerprint']
        template.write_text('<html>Revised authored source</html>')
        with self.call('/api/creative/style/warm-modern/reviews/materials') as response:
            self.assertNotEqual(json.load(response)['fingerprint'], before)

    def test_declared_source_download_is_scoped_and_never_serves_private_files(self):
        runtime = self.root / '_runtime/modern.js'
        template = self.root / '_templates/scene-modern-wide/index.html'
        private = self.root / '_runtime/private.js'
        for path, body in ((runtime, 'modern source'), (template, '<html>scene source</html>'), (private, 'private source')):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
        ws.create_style(self.root, 'ink', 'Ink', references=['_runtime/modern.js', '_templates/scene-modern-wide/index.html'])
        for relative, expected in (('_runtime/modern.js', b'modern source'),
                                   ('_templates/scene-modern-wide/index.html', b'<html>scene source</html>')):
            with self.call('/source/' + relative) as response:
                self.assertEqual(response.read(), expected)
                self.assertIn('attachment', response.headers['Content-Disposition'])
            with self.assertRaises(HTTPError) as error:
                self.call('/download/' + relative)
            self.assertEqual(error.exception.code, 404)
        for relative in ('_runtime/private.js', '_templates/scene-modern-wide/missing.js',
                         '_runtime/_auth/secret.js', '_templates/scene-modern-wide/%2e%2e/index.html'):
            with self.assertRaises(HTTPError) as error:
                self.call('/source/' + relative)
            self.assertIn(error.exception.code, (400, 404))

    def test_full_brainstormform_result_preserves_notes_and_typed_values(self):
        with self.call('/api/creative', 'POST', {'type': 'character', 'id': 'tutor', 'prompt': 'A tutor',
                                                'metadata': {'title': 'Teacher'}}) as response:
            detail = json.load(response)
        result = {'sessionId': 'bf-123', 'submittedAt': '2026-10-09T12:00:00Z', 'durationMs': 12345,
                  'answers': {'actions': {'type': 'multi', 'value': ['wave', 'point']},
                              'has_props': {'type': 'boolean', 'value': False},
                              'energy': {'type': 'number', 'value': 0}},
                  'notes': {'actions': 'Right hand'}, 'skipped': [], 'unanswered': [], 'hidden': ['optional']}
        with self.call('/api/creative/character/tutor/answers', 'PUT',
                       {**result, 'brief': 'Teacher at a desk.', 'expected_revision': detail['revision']}) as response:
            updated = json.load(response)
        self.assertTrue(updated['reviews']['brief']['ready'])
        self.assertEqual(json.loads((self.root / 'characters/tutor/01_design/answers.json').read_text()), result)

    def test_setting_adapters_keep_browser_work_out_of_server(self):
        with self.call('/api/creative', 'POST', {'type': 'style', 'id': 'classroom', 'prompt': 'Warm classroom',
                                                'metadata': {'title': 'Classroom', 'setting': 'A recurring classroom',
                                                             'supported_formats': ['wide']}}):
            pass
        with self.call('/api/creative/style/classroom/materials-plan') as response:
            plan = json.load(response)
        self.assertEqual(plan['setting'], 'A recurring classroom')
        with self.assertRaises(HTTPError) as error:
            self.call('/api/creative/style/classroom/website-reference', 'POST',
                      {'evidence': {'url': 'http://127.0.0.1/'}, 'expected_revision': plan['input_revision']}, token=False)
        self.assertEqual(error.exception.code, 403)
        with self.assertRaises(HTTPError) as error:
            self.call('/api/creative/style/classroom/website-reference', 'POST',
                      {'evidence': {'url': 'http://127.0.0.1/'}, 'expected_revision': plan['input_revision']})
        self.assertEqual(error.exception.code, 400)
        with self.assertRaises(HTTPError) as error:
            self.call('/api/creative/style/classroom/sample/wide', 'POST', {})
        self.assertEqual(error.exception.code, 409)
        with self.call('/api/creative/style/classroom/sample/wide') as response:
            self.assertEqual(json.load(response)['state'], 'missing')

    def test_generation_routes_keep_review_and_transport_guards(self):
        with self.call('/api/creative', 'POST', {'type': 'character', 'id': 'tutor', 'prompt': 'A tutor',
                                                'metadata': {'title': 'Teacher'}}) as response:
            detail = json.load(response)
        with self.call('/api/creative/character/tutor/answers', 'PUT',
                       {'answers': {'look': 'Warm and professional'}, 'brief': 'A warm professional teacher.',
                        'expected_revision': detail['revision']}) as response:
            detail = json.load(response)
        revision = detail['reviews']['brief']['fingerprint']
        with self.call('/api/creative/character/tutor/reviews/brief/ready', 'POST', {'expected_revision': revision}): pass
        with self.call('/api/creative/character/tutor/reviews/brief/decision', 'POST',
                       {'expected_revision': revision, 'decision': 'approved', 'reviewer': 'Reviewer', 'note': ''}): pass
        request = {'id': 'test-batch', 'subject_type': 'character', 'subject_id': 'tutor', 'purpose': 'character-concepts',
                   'prompt': 'Three concepts', 'references': [], 'transparent': False, 'image_count': 3,
                   'input_revision': revision, 'transport': 'native'}
        with self.assertRaises(HTTPError) as error:
            self.call('/api/generations', 'POST', request, token=False)
        self.assertEqual(error.exception.code, 403)
        with self.call('/api/generations', 'POST', request) as response:
            self.assertEqual(json.load(response)['state'], 'awaiting-batch-approval')
        with self.call('/api/generations') as response:
            self.assertEqual(json.load(response)[0]['id'], 'test-batch')
        with self.assertRaises(HTTPError) as error:
            self.call('/api/generations/test-batch/run', 'POST', {})
        self.assertEqual(error.exception.code, 409)
        with self.call('/api/generations/test-batch/approve', 'POST', {'reviewer': 'Reviewer'}) as response:
            self.assertEqual(json.load(response)['state'], 'approved')
        with self.call('/api/generations/test-batch/run', 'POST', {}) as response:
            self.assertIn('handoff', json.load(response))
        with self.assertRaises(HTTPError) as error:
            self.call('/api/generations/test-batch/outputs', 'POST', {'outputs': [], 'provenance': {}})
        self.assertEqual(error.exception.code, 400)

    def test_native_output_http_accepts_large_real_bytes_but_keeps_other_json_small(self):
        from studio import generation
        from studio.server import JSON_LIMIT, NATIVE_OUTPUT_LIMIT
        with self.call('/api/creative', 'POST', {'type': 'style', 'id': 'large-art', 'prompt': 'A style',
                                                'metadata': {'title': 'Large art'}}) as response:
            detail = json.load(response)
        with self.call('/api/creative/style/large-art/answers', 'PUT',
                       {'answers': {'look': 'Large raster'}, 'brief': 'Large raster artwork.',
                        'expected_revision': detail['revision']}) as response:
            detail = json.load(response)
        revision = detail['reviews']['brief']['fingerprint']
        with self.call('/api/creative/style/large-art/reviews/brief/ready', 'POST', {'expected_revision': revision}): pass
        with self.call('/api/creative/style/large-art/reviews/brief/decision', 'POST',
                       {'expected_revision': revision, 'decision': 'approved', 'reviewer': 'Reviewer', 'note': ''}): pass
        with self.call('/api/generations', 'POST', {'id': 'large-batch', 'subject_type': 'style',
            'subject_id': 'large-art', 'purpose': 'style-material', 'prompt': 'Synthetic fixture art only',
            'references': [], 'transparent': True, 'image_count': 1, 'input_revision': revision,
            'transport': 'native'}): pass
        with self.call('/api/generations/large-batch/approve', 'POST', {'reviewer': 'Reviewer'}): pass
        output = self.root / 'styles/large-art/generated/large-batch/image.png'
        output.parent.mkdir(parents=True)
        Image.frombytes('RGBA', (1024, 1024), random.Random(7).randbytes(1024 * 1024 * 4)).save(output)
        self.assertGreater(output.stat().st_size, 1_500_000)
        relative = output.relative_to(self.root).as_posix()
        body = {'outputs': [relative], 'provenance': {'provider': 'openai', 'transport': 'native',
            'coordinator': 'Synthetic HTTP fixture', 'image_tool_used': True,
            'tool_results': [{'image_url': 'data:image/png;base64,' + base64.b64encode(output.read_bytes()).decode()}]}}
        self.assertGreater(len(json.dumps(body)), 2 * 1024 * 1024)
        with self.call('/api/generations/large-batch/outputs', 'POST', body) as response:
            self.assertEqual(json.load(response)['state'], 'completed')
        with self.assertRaises(HTTPError) as ordinary:
            urlopen(Request(self.base + '/api/creative',
                data=b'{"type":"style","id":"too-large","prompt":"tiny","metadata":{"title":"Large"}}', method='POST',
                headers={'X-Studio-Token': self.token, 'Content-Type': 'application/json',
                         'Content-Length': str(JSON_LIMIT + 1)}))
        self.assertEqual(ordinary.exception.code, 400)
        self.assertFalse((self.root / 'styles/too-large').exists())
        with self.assertRaises(HTTPError) as oversized:
            urlopen(Request(self.base + '/api/generations/large-batch/outputs', data=b'{}', method='POST',
                headers={'X-Studio-Token': self.token, 'Content-Type': 'application/json',
                         'Content-Length': str(NATIVE_OUTPUT_LIMIT + 1)}))
        self.assertEqual(oversized.exception.code, 400)
        self.assertEqual(len(generation.generation_detail(self.root, 'large-batch')['outputs']), 1)


if __name__ == '__main__':
    unittest.main()
