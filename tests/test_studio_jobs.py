import tempfile
import sys
import time
import json
import asyncio
from contextlib import contextmanager
from unittest.mock import patch, AsyncMock, Mock
import unittest
from pathlib import Path

from studio.jobs import build_argv, create_request, claim_request, finish_request, start_job, job_detail, cancel_job, recover_jobs, _run_job
from studio.workspace import WorkspaceError
import anim
import capture


class JobTests(unittest.TestCase):
    def test_native_render_rejects_unapproved_or_changed_rig(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            options = {'variant': 'original-look', 'view': 'front', 'action': 'idle', 'expression': 'neutral'}
            self.assertEqual(build_argv(root, 'native-render', 'tutor', options)[1:3], ['-m', 'studio.native_pipeline'])
            with patch('studio.creative.creative_review_state', return_value={'state': 'awaiting-review', 'fingerprint': 'current'}):
                with self.assertRaisesRegex(WorkspaceError, 'Approve the current native rig'):
                    start_job(root, 'native-render', 'tutor', options, 'current', 'native-one')
            with patch('studio.creative.creative_review_state', return_value={'state': 'approved', 'fingerprint': 'current'}):
                with self.assertRaisesRegex(WorkspaceError, 'revision changed'):
                    start_job(root, 'native-render', 'tutor', options, 'stale', 'native-two')
            with self.assertRaises(WorkspaceError):
                build_argv(root, 'native-render', 'tutor', options | {'view': '../escape'})

    def wait_job(self, root, ident):
        for _ in range(200):
            detail = job_detail(root, ident)
            if detail['state'] not in ('queued', 'running', 'cancelling'):
                return detail
            time.sleep(.01)
        self.fail('job did not finish')

    def test_fixed_argv(self):
        root = Path('/tmp/studio-fixture')
        self.assertEqual(build_argv(root, 'cues', 'demo', {}),
                         [str(root / '.venv/bin/python'), str(root / 'anim.py'), 'cues', 'demo'])
        for action, slug, options in [('shell', 'demo', {}), ('cues', '../escape', {}),
                                      ('render', 'demo', {'skip_check': True})]:
            with self.subTest(action=action), self.assertRaises(WorkspaceError):
                build_argv(root, action, slug, options)

    def test_request_waits_for_a_real_agent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'videos/demo').mkdir(parents=True)
            (root / 'videos/demo/project.json').write_text(json.dumps({'brand': 'videofactory'}))
            request = create_request(root, 'demo', 'script', 'Draft opening', '', 'same-key')
            self.assertEqual(request['state'], 'waiting-for-agent')
            self.assertEqual(create_request(root, 'demo', 'script', 'Draft opening', '', 'same-key')['id'], request['id'])
            claimed = claim_request(root, request['id'], 'codex')
            self.assertEqual(claimed['state'], 'running')
            with self.assertRaises(WorkspaceError):
                finish_request(root, request['id'], {'state': 'succeeded', 'note': 'Done', 'outputs': []})
            self.assertEqual(finish_request(root, request['id'], {'state': 'failed'})['state'], 'failed')

    def test_paid_action_requires_current_confirmation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'videos/demo').mkdir(parents=True)
            (root / 'videos/demo/project.json').write_text(json.dumps({'brand': 'videofactory'}))
            with self.assertRaises(WorkspaceError):
                start_job(root, 'voice', 'demo', {}, '', 'voice-key')

    def test_duplicate_job_is_one_process_and_cancellation_is_terminal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'videos/demo').mkdir(parents=True)
            (root / 'videos/demo/project.json').write_text(json.dumps({'brand': 'videofactory'}))
            python = root / '.venv/bin/python'
            python.parent.mkdir(parents=True)
            python.symlink_to(sys.executable)
            (root / 'anim.py').write_text('import time\nprint("running", flush=True)\ntime.sleep(30)\n')
            first = start_job(root, 'research-init', 'demo', {}, None, 'same-key')
            self.assertEqual(start_job(root, 'research-init', 'demo', {}, None, 'same-key')['id'], first['id'])
            for _ in range(100):
                if job_detail(root, first['id'])['state'] == 'running': break
                time.sleep(.01)
            self.assertEqual(job_detail(root, first['id'])['state'], 'running')
            cancel_job(root, first['id'])
            for _ in range(100):
                if job_detail(root, first['id'])['state'] == 'cancelled': break
                time.sleep(.01)
            self.assertEqual(job_detail(root, first['id'])['state'], 'cancelled')
            self.assertIsNotNone(job_detail(root, first['id'])['error'])

    def test_parallel_record_saves_leave_a_complete_record(self):
        from concurrent.futures import ThreadPoolExecutor
        from studio.jobs import _save, _read
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '.studio/jobs/concurrent.json'
            def write(index):
                _save(path, {'id': 'concurrent', 'index': index, 'payload': 'x' * 10000})
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(write, range(64)))
            self.assertIn(_read(path)['index'], range(64))

    def test_zero_exit_without_output_fails_and_log_redacts_key(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'videos/demo').mkdir(parents=True)
            (root / 'videos/demo/project.json').write_text(json.dumps({'brand': 'videofactory'}))
            python = root / '.venv/bin/python'
            python.parent.mkdir(parents=True)
            python.symlink_to(sys.executable)
            (root / '.env').write_text('API_KEY=fake-secret-value\n')
            (root / 'anim.py').write_text('print("fake-secret-value", flush=True)\n')
            job = start_job(root, 'research-init', 'demo', {}, None, 'no-output')
            detail = self.wait_job(root, job['id'])
            self.assertEqual(detail['state'], 'failed')
            self.assertEqual(detail['exit_code'], 0)
            self.assertIn('[redacted]', detail['log'])
            self.assertNotIn('fake-secret-value', detail['log'])

    def test_restart_marks_orphan_interrupted(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shelf = root / '.studio/jobs'
            shelf.mkdir(parents=True)
            (shelf / 'orphan.json').write_text(json.dumps({'id': 'orphan', 'slug': 'demo', 'action': 'check',
                                                           'state': 'running', 'pid': 999999, 'process_start': 'old'}))
            recover_jobs(root)
            self.assertEqual(job_detail(root, 'orphan')['state'], 'interrupted')

    def test_worker_workspace_error_is_recorded_terminal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shelf = root / '.studio/jobs'
            shelf.mkdir(parents=True)
            (shelf / 'blocked.json').write_text(json.dumps({'id': 'blocked', 'slug': 'demo', 'action': 'check',
                                                            'options': {}, 'state': 'queued', 'pid': None}))
            @contextmanager
            def denied(*args, **kwargs):
                raise WorkspaceError('busy', 'Another video is under production.')
                yield
            with patch('studio.jobs.workspace_lock', denied):
                _run_job(root, 'blocked')
            detail = job_detail(root, 'blocked')
            self.assertEqual(detail['state'], 'failed')
            self.assertIn('Another video', detail['error'])


class ContainedBrowserTests(unittest.TestCase):
    def test_cdp_failure_never_launches_host_browser(self):
        chromium = Mock()
        chromium.connect_over_cdp = AsyncMock(side_effect=RuntimeError('box unavailable'))
        p = Mock(chromium=chromium)
        with patch.dict('os.environ', {'ANIM_CDP_URL': 'http://127.0.0.1:9222'}):
            with self.assertRaisesRegex(RuntimeError, 'box unavailable'):
                asyncio.run(anim.launch_browser(p))
            with self.assertRaisesRegex(RuntimeError, 'box unavailable'):
                asyncio.run(capture.open_context(p, {}, None))
        chromium.launch.assert_not_called()
