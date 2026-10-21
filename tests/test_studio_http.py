import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import quote

from studio.server import make_server
from studio.permissions import grant


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'videos/demo/01_voice').mkdir(parents=True)
        (self.root / 'videos/demo/project.json').write_text('{"brand": "videofactory"}')
        (self.root / 'videos/demo/01_voice/script.md').write_text('First', encoding='utf-8')
        (self.root / 'videos/demo/01_voice/voice.mp3').write_bytes(b'0123456789')
        (self.root / 'videos/demo/03_cues').mkdir()
        (self.root / 'videos/demo/03_cues/cues.js').write_text('window.CUES = [];')
        (self.root / '_runtime/fonts/inter').mkdir(parents=True)
        (self.root / '_runtime/fonts/inter/Inter[opsz,wght].ttf').write_bytes(b'font')
        (self.root / '_auth').mkdir()
        (self.root / '_auth/session.json').write_text('secret')
        (self.root / '.env').write_text('KEY=secret')
        (self.root / 'studio/web').mkdir(parents=True)
        (self.root / 'studio/web/index.html').write_text('<html><body>Studio</body></html>')
        (self.root / 'videos/demo/01_voice/escape.mp3').symlink_to(self.root / '_auth/session.json')
        self.server = make_server(self.root, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'
        with self.request('/api/bootstrap') as response:
            bootstrap = json.load(response)
        self.session = 'c' * 32 + '.' + bootstrap['session_nonce']
        grant(self.root, 'video:videofactory/demo', 'each-stage', session_id=self.session)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, path, method='GET', data=None, headers=None):
        headers = dict(headers or {})
        if method != 'GET' and headers.get('X-Studio-Token'):
            headers['X-VF-Session-ID'] = self.session
        request = Request(self.base + path, data=json.dumps(data).encode() if data is not None else None,
                          headers=headers, method=method)
        return urlopen(request)

    def test_unread_body_does_not_corrupt_next_request(self):
        import http.client
        with self.request('/api/bootstrap') as response:
            token = json.load(response)['token']
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        headers = {'X-Studio-Token': token, 'Content-Type': 'application/json'}
        headers['X-VF-Session-ID'] = self.session
        connection.request('POST', '/api/jobs/no-such-job/cancel', body='{}', headers=headers)
        connection.getresponse().read()
        connection.request('GET', '/api/videos')
        self.assertEqual(connection.getresponse().status, 200)
        connection.close()

    def test_request_run_requires_token(self):
        with self.assertRaises(HTTPError) as error:
            self.request('/api/requests/req-one/run', 'POST', {'mode': 'auto'})
        self.assertEqual(error.exception.code, 403)

    def test_request_run_route_starts_auto(self):
        from unittest.mock import patch
        import sys
        from studio import agent_runs
        with self.request('/api/bootstrap') as response:
            token = json.load(response)['token']
        headers = {'X-Studio-Token': token, 'Content-Type': 'application/json'}
        headers['X-VF-Session-ID'] = self.session
        self.request('/api/requests', 'POST', {'slug': 'demo', 'kind': 'script', 'instructions': 'Write it.', 'fingerprint': '', 'request_id': 'req-one'}, headers).close()
        with patch.object(agent_runs, 'agent_argv', return_value=[sys.executable, '-c', 'print(1)']):
            with self.request('/api/requests/req-one/run', 'POST', {'mode': 'auto'}, headers) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(json.load(response)['run']['mode'], 'auto')
        with self.request('/api/requests/req-one/log') as response:
            status = json.load(response)
            self.assertIn('log', status)
            self.assertIn(status['state'], ('running', 'succeeded'))

    def test_list_and_unauthorized_write(self):
        with self.request('/api/videos') as response:
            self.assertEqual(response.status, 200)
            self.assertIsInstance(json.load(response), list)
        with self.assertRaises(HTTPError) as error:
            self.request('/api/files', 'PUT', {'path': 'videos/demo/01_voice/script.md', 'text': 'Changed', 'expected_revision': ''})
        self.assertEqual(error.exception.code, 403)

    def test_private_and_encoded_paths(self):
        for path in ('/_auth/session.json', '/.env', '/media/_auth/session.json',
                     '/media/videos/%2e%2e/.env', '/media/videos/demo/01_voice/escape.mp3'):
            with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                self.request(path)
            self.assertEqual(error.exception.code, 404)

    def test_range_and_head(self):
        path = '/media/videos/demo/01_voice/voice.mp3'
        with self.request(path, headers={'Range': 'bytes=3-5'}) as response:
            self.assertEqual(response.status, 206)
            self.assertEqual(response.read(), b'345')
        with self.request(path, headers={'Range': 'bytes=-3'}) as response:
            self.assertEqual(response.read(), b'789')
        with self.request(path, headers={'Range': 'bytes=7-'}) as response:
            self.assertEqual(response.read(), b'789')
        with self.assertRaises(HTTPError) as error:
            self.request(path, headers={'Range': 'bytes=99-'})
        self.assertEqual(error.exception.code, 416)
        with self.request(path, method='HEAD') as response:
            self.assertEqual(response.headers['Content-Length'], '10')

    def test_forged_origin_and_host(self):
        with self.assertRaises(HTTPError) as error:
            self.request('/api/bootstrap', headers={'Origin': 'http://evil.test'})
        self.assertEqual(error.exception.code, 403)
        with self.assertRaises(HTTPError) as error:
            self.request('/api/videos', headers={'Host': 'evil.test'})
        self.assertEqual(error.exception.code, 403)

    def test_conflict_and_unknown_route(self):
        with self.request('/api/bootstrap') as response:
            token = json.load(response)['token']
        relative = 'videos/demo/01_voice/script.md'
        with self.request('/api/files?path=' + relative) as response:
            revision = json.load(response)['revision']
        (self.root / relative).write_text('Agent edit')
        with self.assertRaises(HTTPError) as error:
            self.request('/api/files', 'PUT', {'path': relative, 'text': 'Manual edit', 'expected_revision': revision},
                         {'X-Studio-Token': token, 'Content-Type': 'application/json'})
        self.assertEqual(error.exception.code, 409)
        self.assertEqual((self.root / relative).read_text(), 'Agent edit')
        with self.assertRaises(HTTPError) as error:
            self.request('/api/no-such-route')
        self.assertEqual(error.exception.code, 404)
        self.assertEqual(json.load(error.exception)['error']['code'], 'missing')

    def test_download_is_attachment_and_deep_link_is_shell(self):
        document = self.root / 'videos/demo/05_render/DESCRIPTION.md'
        document.parent.mkdir()
        document.write_text('Description')
        with self.request('/download/videos/demo/05_render/DESCRIPTION.md') as response:
            self.assertTrue(response.headers['Content-Disposition'].startswith('attachment;'))
            self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        with self.request('/videos/demo/review/script') as response:
            self.assertEqual(response.status, 200)
            self.assertIn(b'<html', response.read().lower())

    def test_upload_without_token_writes_nothing(self):
        request = Request(self.base + '/api/materials/upload', data=b'not-an-image', method='POST',
                          headers={'X-Material-Filename': 'asset.png', 'X-Material-Metadata': '{}'})
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 403)
        self.assertFalse((self.root / 'library/materials').exists())

    def test_unscoped_upload_is_blocked(self):
        with self.request('/api/bootstrap') as response:
            token = json.load(response)['token']
        filename = 'scène-€.png'
        metadata = {'id': 'unicode-source', 'title': 'Scène €', 'description': 'Café 😀',
                    'kind': 'graphic', 'source': 'upload', 'rights': 'owned'}
        headers = {'X-Studio-Token': token, 'X-Material-Filename': quote(filename, safe=''),
                   'X-Material-Filename-Encoding': 'uri',
                   'X-Material-Metadata': json.dumps(metadata, ensure_ascii=True)}
        headers['X-VF-Session-ID'] = self.session
        request = Request(self.base + '/api/materials/upload', data=b'image', method='POST', headers=headers)
        with self.assertRaises(HTTPError) as blocked:
            urlopen(request)
        self.assertEqual(blocked.exception.code, 403)
        self.assertFalse((self.root / 'library/materials/unicode-source').exists())
        for encoded, encoding in (('bad%ZZ.png', 'uri'), ('asset.png', 'unknown')):
            with self.subTest(encoded=encoded), self.assertRaises(HTTPError) as error:
                req = Request(self.base + '/api/materials/upload', data=b'image', method='POST',
                              headers={**headers, 'X-Material-Filename': encoded,
                                       'X-Material-Filename-Encoding': encoding})
                urlopen(req)
            self.assertEqual(error.exception.code, 403)

    def test_sandboxed_preview_can_load_cues_and_fonts_but_not_api(self):
        headers = {'Origin': 'null'}
        with self.request('/videos/demo/03_cues/cues.js', headers=headers) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'null')
        with self.request('/_runtime/fonts/inter/Inter%5Bopsz%2Cwght%5D.ttf', headers=headers) as response:
            self.assertEqual(response.read(), b'font')
        with self.request('/videos/demo/01_voice/voice.mp3', headers=headers) as response:
            self.assertEqual(response.read(), b'0123456789')
        with self.assertRaises(HTTPError) as error:
            self.request('/api/bootstrap', headers=headers)
        self.assertEqual(error.exception.code, 403)

    def test_style_template_sample_is_trusted_static_only(self):
        template = self.root / 'styles/ink/template'
        template.mkdir(parents=True)
        (template / 'index.html').write_text('<html><script src="scene.js"></script></html>')
        (template / 'scene.js').write_text('window.sample = true;')
        with self.request('/styles/ink/template/index.html', headers={'Origin': 'null'}) as response:
            self.assertEqual(response.status, 200)
        with self.request('/styles/ink/template/scene.js', headers={'Origin': 'null'}) as response:
            self.assertIn(b'sample', response.read())
        with self.assertRaises(HTTPError) as error:
            self.request('/styles/ink/style.md', headers={'Origin': 'null'})
        self.assertEqual(error.exception.code, 403)
