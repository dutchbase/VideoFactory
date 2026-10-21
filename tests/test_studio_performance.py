"""Overview caches must stay cheap and separate from decision authority."""
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from studio import creative, jobs, readcache, workspace as ws
from studio.permissions import grant
from tests import test_studio_http as http_fixture


class OverviewHttpTests(unittest.TestCase):
    setUp = http_fixture.HttpTests.setUp
    tearDown = http_fixture.HttpTests.tearDown
    request = http_fixture.HttpTests.request
    def test_shell_and_summary_do_not_run_full_checks(self):
        with patch.object(ws, 'video_detail', side_effect=AssertionError('video detail')), \
             patch.object(ws, 'list_materials', side_effect=AssertionError('library')), \
             patch.object(ws, 'list_styles', side_effect=AssertionError('styles')):
            with self.request('/api/bootstrap?view=shell') as response:
                self.assertEqual(set(json.load(response)), {'token', 'session_nonce', 'jobs', 'requests', 'brands'})
        with patch.object(ws, 'review_state', side_effect=AssertionError('review')), \
             patch.object(ws, '_own_paths', side_effect=AssertionError('evidence scan')):
            with self.request('/api/videos?view=summary') as response:
                rows = json.load(response)
                self.assertEqual(rows[0]['reviews']['script']['state'], 'unchecked')
                self.assertEqual(rows[0]['reviews']['research']['recorded_state'], 'not-applicable')
            with self.request('/api/videos/demo?view=shell') as response:
                self.assertIn('script', json.load(response)['files'])

    def test_selected_review_retains_next_agent_action_without_loading_all_reviews(self):
        with self.request('/api/videos/demo/reviews/brief') as response:
            self.assertFalse(json.load(response)['next_unwritten'])
        (self.root / 'videos/demo/01_voice/script.md').write_text('Replace this with the script')
        with self.request('/api/videos/demo/reviews/brief') as response:
            self.assertTrue(json.load(response)['next_unwritten'])

    def test_material_pages_search_and_direct_ids(self):
        for i in range(51):
            ws.create_material(self.root, {'id': f'm-{i}', 'title': f'Item {i}', 'description': 'needle' if i == 50 else 'plain',
                'kind': 'image' if i == 50 else 'reference', 'source': 'https://example.org', 'rights': 'owned'})
        with self.request('/api/materials?view=summary') as response:
            page = json.load(response)
            self.assertEqual((len(page['items']), page['total']), (48, 51))
        with self.request('/api/materials?view=summary&offset=48') as response:
            self.assertEqual(len(json.load(response)['items']), 3)
        with self.request('/api/materials?view=summary&q=needle&kind=image') as response:
            self.assertEqual(json.load(response)['items'][0]['id'], 'm-50')
        with patch.object(ws, '_inventory', side_effect=AssertionError('inventory')):
            with self.request('/api/materials/item?id=m-50') as response:
                self.assertEqual(json.load(response)['id'], 'm-50')
            with self.request('/api/materials?ids=m-50,m-1') as response:
                self.assertEqual(len(json.load(response)), 2)
            with self.request('/api/materials?ids=m-50,missing') as response:
                rows = json.load(response)
                self.assertEqual(rows[0]['id'], 'm-50')
                self.assertIn('error', rows[1])
        with self.request('/api/materials') as response:
            self.assertIsInstance(json.load(response), list)
        with self.request('/api/materials/files?view=summary&kind=mp3&q=voice') as response:
            self.assertEqual([r['name'] for r in json.load(response)['items']], ['voice.mp3'])


class OverviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        path = self.root / 'videos/demo/01_voice/script.md'
        path.parent.mkdir(parents=True)
        path.write_text('Original script')
        (path.parent.parent / 'project.json').write_text('{"brand": "videofactory"}')
        self.script = path
        self.addCleanup(readcache.invalidate, self.root)

    def test_creative_summary_uses_recorded_events_without_full_checks(self):
        folder = self.root / 'styles/ink'
        folder.mkdir(parents=True)
        (folder / 'style.md').write_text('---\nid: "ink"\ntitle: "Ink style"\n---\n')
        events = [{'gate': 'brief', 'kind': 'ready', 'fingerprint': 'old', 'at': ws._now()}]
        (folder / 'REVIEW.md').write_text(creative._HEADING + '\n```json\n' + json.dumps(events) + '\n```\n')
        with patch.object(creative, 'creative_detail', side_effect=AssertionError('detail')), \
             patch.object(creative, 'creative_review_state', side_effect=AssertionError('checks')):
            row = creative.review_summaries(self.root)[0]
        self.assertEqual(row['title'], 'Ink style')
        self.assertEqual(row['reviews']['brief']['recorded_state'], 'awaiting-review')
        self.assertEqual(row['reviews']['brief']['state'], 'unchecked')

    def test_request_memo_keys_include_workspace_subject_and_gate(self):
        for slug in ('other',):
            path = self.root / f'videos/{slug}/01_voice/script.md'
            path.parent.mkdir(parents=True)
            path.write_text('Different script')
            (path.parent.parent / 'project.json').write_text('{"brand": "videofactory"}')
        with ws.read_scope(), patch.object(ws, '_readiness', wraps=ws._readiness) as checks:
            one = ws.review_state(self.root, 'demo', 'script')
            self.assertIs(one, ws.review_state(self.root, 'demo', 'script'))
            self.assertIs(one, ws.review_state(root=self.root, slug='demo', gate='script'))
            self.assertNotEqual(one['fingerprint'], ws.review_state(self.root, 'other', 'script')['fingerprint'])
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = root / 'videos/demo/01_voice/script.md'
                path.parent.mkdir(parents=True)
                path.write_text('Another workspace')
                (path.parent.parent / 'project.json').write_text('{"brand": "videofactory"}')
                self.assertNotEqual(one['fingerprint'], ws.review_state(root, 'demo', 'script')['fingerprint'])
            self.assertEqual(sum(call.args[2] == 'script' for call in checks.call_args_list), 3)

    def test_expiry_external_edit_and_studio_invalidation(self):
        meta = self.root / 'videos/demo/project.json'
        meta.write_text('{"brand": "videofactory","title":"Before"}')
        with patch.object(readcache, 'monotonic', return_value=10):
            self.assertEqual(ws.list_videos(self.root, summary=True)[0]['title'], 'Before')
        meta.write_text('{"brand": "videofactory","title":"External"}')
        with patch.object(readcache, 'monotonic', return_value=14):
            self.assertEqual(ws.list_videos(self.root, summary=True)[0]['title'], 'Before')
        with patch.object(readcache, 'monotonic', return_value=15):
            self.assertEqual(ws.list_videos(self.root, summary=True)[0]['title'], 'External')
            meta.write_text('{"brand": "videofactory","title":"Studio"}')
            ws.save_text(self.root, 'videos/demo/01_voice/script.md', 'Saved', ws.read_file(self.root, 'videos/demo/01_voice/script.md')['revision'])
            self.assertEqual(ws.list_videos(self.root, summary=True)[0]['title'], 'Studio')

    def test_concurrent_reads_share_one_refresh_and_write_discards_inflight(self):
        started, release = threading.Event(), threading.Event()
        calls = []
        def read():
            calls.append(1)
            started.set()
            self.assertTrue(release.wait(2))
            return len(calls)
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(readcache.cached, self.root, 'test', read) for _ in range(4)]
            self.assertTrue(started.wait(2))
            release.set()
            self.assertEqual([f.result() for f in futures], [1]*4)
        self.assertEqual(len(calls), 1)
        readcache.invalidate(self.root)
        def invalidated():
            readcache.invalidate(self.root)
            return 'old'
        self.assertEqual(readcache.cached(self.root, 'test', invalidated), 'old')
        self.assertEqual(readcache.cached(self.root, 'test', lambda: 'new'), 'new')

    def test_cached_overview_cannot_authorize_changed_revision(self):
        canonical = self.root / 'videos/videofactory/demo'
        canonical.parent.mkdir(parents=True)
        self.script.parent.parent.rename(canonical)
        self.script = canonical / '01_voice/script.md'
        slug = 'videofactory/demo'
        fingerprint = ws.gate_fingerprint(self.root, slug, 'script')
        ws._write_event(self.root, slug, {'gate': 'script', 'kind': 'ready', 'fingerprint': fingerprint, 'at': ws._now()})
        summary = ws.list_videos(self.root, summary=True)
        self.assertEqual(summary[0]['reviews']['script']['recorded_state'], 'awaiting-review')
        self.script.write_text('Changed outside Studio')
        self.assertNotEqual(fingerprint, ws.gate_fingerprint(self.root, slug, 'script'))
        self.assertIs(summary, ws.list_videos(self.root, summary=True))
        with self.assertRaises(ws.WorkspaceError) as error:
            ws.decide_review(self.root, slug, 'script', 'approved', 'Reviewer', '', fingerprint)
        self.assertEqual(error.exception.code, 'conflict')
        grant(self.root, 'video:' + slug, 'full')
        with self.assertRaisesRegex(ws.WorkspaceError, 'separate approval'):
            jobs.start_job(self.root, 'voice-test', slug, {'confirmation_fingerprint': fingerprint}, fingerprint, 'stale-voice')

    def test_inventory_expiry_shares_files_and_observes_external_additions(self):
        with patch.object(readcache, 'monotonic', return_value=10), patch.object(ws, '_inventory', wraps=ws._inventory) as scan:
            self.assertEqual(ws.inventory_page(self.root, 'materials', {})['total'], 0)
            self.assertEqual(ws.inventory_page(self.root, 'files', {})['total'], 1)
            self.assertEqual(scan.call_count, 1)
        asset = self.root / 'videos/demo/04_scene/assets/new.png'
        asset.parent.mkdir(parents=True)
        asset.write_bytes(b'new')
        with patch.object(readcache, 'monotonic', return_value=15):
            self.assertEqual(ws.inventory_page(self.root, 'materials', {})['total'], 1)
        for i in range(140):
            readcache.cached(self.root, ('bounded', i), lambda: i)
        self.assertLessEqual(len(readcache._entries), readcache._LIMIT)

    def test_inventory_and_direct_lookup_reject_private_and_symlink_files(self):
        assets = self.root / 'videos/demo/04_scene/assets'
        assets.mkdir(parents=True)
        (assets / 'ok.png').write_bytes(b'png')
        (assets / '.private.png').write_bytes(b'private')
        (assets / '_auth').mkdir()
        (assets / '_auth/session.png').write_bytes(b'secret')
        (assets / 'link.png').symlink_to(assets / '_auth/session.png')
        rows = ws.inventory_page(self.root, 'materials', {})['items']
        self.assertEqual([r['id'] for r in rows], ['videos/demo/04_scene/assets/ok.png'])
        with patch.object(ws, 'list_public_files', side_effect=AssertionError('walk')):
            self.assertEqual(ws.material_detail(self.root, rows[0]['id'])['origin'], 'video-asset')
        for name in ('.private.png', '_auth/session.png', 'link.png', '../project.json'):
            with self.subTest(name=name), self.assertRaises(ws.WorkspaceError):
                ws.material_detail(self.root, f'videos/demo/04_scene/assets/{name}')
        with self.assertRaises(ws.WorkspaceError):
            ws.save_text(self.root, 'videos/demo/03_cues/cues.js', 'generated', None)
