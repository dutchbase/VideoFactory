import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import anim
from studio.workspace import gate_fingerprint, review_state


class HandoffTests(unittest.TestCase):
    def test_studio_job_cli_waits_for_owned_worker(self):
        output = io.StringIO()
        queued = {'id': 'job-1', 'state': 'queued'}
        done = {'id': 'job-1', 'state': 'succeeded', 'exit_code': 0}
        with patch('studio.jobs.start_job', return_value=queued), \
             patch('studio.jobs.job_detail', side_effect=[queued, done]) as detail, \
             contextlib.redirect_stdout(output):
            anim.cmd_studio_job(SimpleNamespace(action='research-init', slug='demo', options=None,
                                                expected=None, request_id='job-1'))
        self.assertEqual(detail.call_count, 2)
        self.assertIn('"succeeded"', output.getvalue())

    def test_ready_prints_exact_review_url_without_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stage = root / 'videos/demo/01_voice'
            stage.mkdir(parents=True)
            (stage.parent / 'project.json').write_text('{"brand": "videofactory"}')
            (stage / 'brief.md').write_text('Audience: managers\nVideo type: explainer\nLanguage: English\nOne outcome: understand it\n')
            fingerprint = gate_fingerprint(root, 'demo', 'brief')
            output = io.StringIO()
            with patch.object(anim, 'ROOT', root), contextlib.redirect_stdout(output):
                anim.cmd_review(SimpleNamespace(slug='demo', gate='brief', ready=True,
                                                approve=False, changes=False, accept=False,
                                                expected=fingerprint, port=8765))
            self.assertIn('http://127.0.0.1:8765/videos/demo/review/brief', output.getvalue())
            self.assertEqual(review_state(root, 'demo', 'brief')['state'], 'awaiting-review')

    def test_review_prints_current_fingerprint(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stage = root / 'videos/demo/01_voice'
            stage.mkdir(parents=True)
            (stage.parent / 'project.json').write_text('{"brand": "videofactory"}')
            (stage / 'brief.md').write_text('Audience: managers\n')
            output = io.StringIO()
            with patch.object(anim, 'ROOT', root), contextlib.redirect_stdout(output):
                anim.cmd_review(SimpleNamespace(slug='demo', gate='brief', ready=False,
                                                approve=False, changes=False, accept=False,
                                                expected=None, port=8765))
            self.assertIn(f"fingerprint: {gate_fingerprint(root, 'demo', 'brief')}", output.getvalue())

    def test_stale_ready_does_not_change_review_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stage = root / 'videos/demo/01_voice'
            stage.mkdir(parents=True)
            (stage.parent / 'project.json').write_text('{"brand": "videofactory"}')
            (stage / 'brief.md').write_text('Audience: managers\nVideo type: explainer\nLanguage: English\nOne outcome: understand it\n')
            with patch.object(anim, 'ROOT', root), self.assertRaises(Exception):
                anim.cmd_review(SimpleNamespace(slug='demo', gate='brief', ready=True,
                                                approve=False, changes=False, accept=False,
                                                expected='old', port=8765))
            self.assertFalse((root / 'videos/demo/REVIEW.md').exists())
