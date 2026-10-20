"""Opt-in contained-browser check for generation page controls."""

import json
import os
import threading
import unittest
from pathlib import Path
from urllib.request import urlopen

from studio import jobs
from studio.server import make_server


@unittest.skipUnless(os.environ.get('GENERATION_BROWSER_TEST') == '1', 'contained generation page proof is opt-in')
class GenerationPageTests(unittest.TestCase):
    def test_approval_controls_follow_saved_state_and_polling(self):
        from playwright.sync_api import sync_playwright

        server = make_server(Path(__file__).resolve().parents[1], 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        box = None
        try:
            base = f'http://127.0.0.1:{server.server_port}'
            with urlopen(base + '/api/bootstrap', timeout=60) as response:
                bootstrap = json.load(response)
            box, endpoint = jobs._contained_browser()
            with sync_playwright() as playwright:
                browser = playwright.chromium.connect_over_cdp(endpoint)
                page = browser.new_page()
                page.route('**/api/bootstrap', lambda route: route.fulfill(json=bootstrap))
                record = {'id': 'test-page-batch', 'purpose': 'character-animation', 'subject_type': 'character',
                          'subject_id': 'tutor', 'provider': 'openai', 'transport': 'native',
                          'state': 'completed', 'approved_by': 'Reviewer', 'approved_at': '2026-10-10T16:25:34Z',
                          'image_model': 'unknown', 'transparent': True, 'image_count': 1, 'prompt': 'Fixture prompt',
                          'context': {'variant_id': 'original-look'}, 'resolved_references': [], 'outputs': []}
                polls = {'count': 0}

                def batch(route):
                    polls['count'] += 1
                    result = {**record}
                    if record['state'] == 'running' and polls['count'] > 1: result['state'] = 'completed'
                    route.fulfill(json=result)

                page.route('**/api/generations/test-page-batch', batch)
                url = base + '/generations/test-page-batch'
                page.goto(url)
                page.get_by_text('Generation completed. Batch approval authorized generation', exact=False).wait_for()
                self.assertFalse(page.get_by_label('Batch reviewer').is_visible())
                self.assertFalse(page.get_by_role('button', name='Approve this batch').is_visible())
                self.assertFalse(page.get_by_text('Register native tool outputs', exact=True).is_visible())
                self.assertFalse(page.get_by_role('button', name='Show native handoff').is_visible())
                self.assertIn('Batch approved by Reviewer', page.locator('#main').inner_text())
                self.assertTrue(page.get_by_role('link', name='Inspect character rig and action reviews').is_visible())

                record['state'] = 'awaiting-batch-approval'
                page.reload()
                page.get_by_label('Batch reviewer').wait_for()
                self.assertTrue(page.get_by_role('button', name='Approve this batch').is_visible())
                self.assertFalse(page.get_by_label('I acknowledge OpenAI API billing for this exact batch').is_visible())
                self.assertFalse(page.get_by_text('Register native tool outputs', exact=True).is_visible())

                record['state'] = 'approved'
                page.reload()
                page.get_by_role('button', name='Show native handoff').wait_for()
                self.assertFalse(page.get_by_label('Batch reviewer').is_visible())
                self.assertTrue(page.get_by_text('Advanced · register native tool outputs').is_visible())

                record['state'] = 'superseded'
                record['superseded_by'] = 'replacement-batch'
                page.reload()
                page.get_by_role('link', name='Open replacement batch').wait_for()
                self.assertFalse(page.get_by_label('Batch reviewer').is_visible())
                self.assertFalse(page.get_by_text('Advanced · register native tool outputs').is_visible())

                record['transport'] = 'openai-api'
                record['state'] = 'awaiting-batch-approval'
                page.reload()
                page.get_by_label('I acknowledge OpenAI API billing for this exact batch').wait_for()
                self.assertTrue(page.get_by_label('Batch reviewer').is_visible())

                record['state'] = 'completed'
                page.reload()
                page.get_by_text('Generation completed. Batch approval authorized generation', exact=False).wait_for()
                self.assertFalse(page.get_by_label('Batch reviewer').is_visible())
                self.assertFalse(page.get_by_label('I acknowledge OpenAI API billing for this exact batch').is_visible())
                self.assertFalse(page.get_by_role('button', name='Run approved batch').is_visible())

                record['transport'] = 'native'
                record['state'] = 'running'
                polls['count'] = 0
                page.reload()
                page.get_by_text('Generation completed. Batch approval authorized generation', exact=False).wait_for(timeout=15000)
                self.assertFalse(page.get_by_label('Batch reviewer').is_visible())
                self.assertFalse(page.get_by_text('Register native tool outputs', exact=True).is_visible())
                browser.close()
        finally:
            if box: jobs._stop_box(box)
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()
