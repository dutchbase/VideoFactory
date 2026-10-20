"""Run with STUDIO_BROWSER_TESTS=1 inside omabox; uses only disposable files."""
import asyncio
import json
import os
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from playwright.async_api import async_playwright, expect
from studio import workspace as ws
from studio.server import make_server


@unittest.skipUnless(os.environ.get('STUDIO_BROWSER_TESTS') == '1', 'run inside omabox explicitly')
class StudioBrowserTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(Path(__file__).resolve().parents[1] / 'studio/web', self.root / 'studio/web')
        self.script = self.root / 'videos/demo/01_voice/script.md'
        self.script.parent.mkdir(parents=True)
        self.script.write_text('Original script')
        (self.script.parent.parent / 'project.json').write_text(json.dumps({'title': '<script>Demo</script>'}))
        self.material = ws.create_material(self.root, {'id': 'source', 'title': 'Source', 'description': 'Evidence', 'kind': 'reference', 'source': 'https://example.org', 'rights': 'owned'})
        ws.link_material(self.root, 'video', 'demo', self.material['id'])
        self.server = make_server(self.root, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch()
        self.page = await self.browser.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('dialog', lambda dialog: dialog.accept())

    async def asyncTearDown(self):
        await self.browser.close()
        await self.playwright.stop()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()
        self.assertEqual(self.errors, [])

    async def test_settings_is_shell_only_and_navigation_ignores_old_reads(self):
        urls = []
        self.page.on('request', lambda request: urls.append(request.url))
        await self.page.goto(self.base + '/settings')
        await expect(self.page.locator('h1')).to_have_text('Settings and agent handoff')
        self.assertEqual([u.split('/api/')[1] for u in urls if '/api/' in u], ['bootstrap?view=shell'])
        started = asyncio.Event()
        async def slow(route):
            started.set()
            await asyncio.sleep(.3)
            try:
                await route.continue_()
            except Exception:
                pass  # The route's read was cancelled by navigation.
        await self.page.route('**/api/videos?view=summary', slow)
        await self.page.locator('[data-nav="videos"]').click()
        await asyncio.wait_for(started.wait(), 2)
        await self.page.get_by_role('link', name='Settings and agent guide', exact=True).click()
        await expect(self.page.locator('h1')).to_have_text('Settings and agent handoff')
        await asyncio.sleep(.4)
        await expect(self.page.locator('h1')).to_have_text('Settings and agent handoff')

    async def test_review_survives_failed_sources_polling_conflict_and_narrow_navigation(self):
        await self.page.set_viewport_size({'width': 390, 'height': 844})
        async def failed(route):
            await route.fulfill(status=500, json={'error': {'message': 'Source offline'}})
        await self.page.route('**/api/materials?ids=*', failed)
        finished = asyncio.Event()
        async def bootstrap(route):
            response = await route.fetch()
            data = await response.json()
            data['requests'] = [{'id': 'req-test', 'slug': 'demo', 'kind': 'script', 'state': 'running'}]
            await route.fulfill(json=data)
        async def agent_log(route):
            await finished.wait()
            await route.fulfill(json={'state': 'succeeded', 'log': 'Saved by agent'})
        await self.page.route('**/api/bootstrap?view=shell', bootstrap)
        await self.page.route('**/api/requests/req-test/log', agent_log)
        await self.page.goto(self.base + '/videos/demo/review/script')
        editor = self.page.get_by_role('textbox', name='Script source', exact=True)
        await expect(editor).to_have_value('Original script')
        await expect(self.page.locator('#review-count')).to_be_hidden()
        await expect(self.page.locator('h1')).to_have_text('<script>Demo</script> · Script')
        self.assertEqual(await self.page.locator('#main script').count(), 0)
        await editor.fill('Retained draft')
        await editor.focus()
        await self.page.evaluate('fetch("/api/jobs")')
        finished.set()
        await expect(self.page.get_by_role('button', name='Open updated review', exact=True)).to_be_visible()
        await expect(editor).to_be_focused()
        await expect(editor).to_have_value('Retained draft')
        await self.page.get_by_role('button', name='Details', exact=True).click()
        await expect(self.page.get_by_text('Source offline', exact=True)).to_be_visible()
        await self.page.unroute('**/api/materials?ids=*', failed)
        await self.page.get_by_role('button', name='Retry section', exact=True).click()
        await expect(self.page.locator('.details-drawer .material-link-copy strong')).to_have_text('Source')
        await self.page.get_by_role('button', name='Close', exact=True).click()
        self.script.write_text('External revision')
        await self.page.get_by_role('button', name='Save draft', exact=True).click()
        await expect(self.page.get_by_role('heading', name='Save conflict · your draft is retained')).to_be_visible()
        await expect(self.page.get_by_role('textbox', name='Script source', exact=True)).to_have_value('Retained draft')
        await self.page.locator('[data-nav="videos"]').click()
        await expect(self.page.locator('h1')).to_have_text('Videos')
        await self.page.go_back()
        await expect(self.page.get_by_role('textbox', name='Script source', exact=True)).to_have_value('Retained draft')
        self.assertLessEqual(await self.page.evaluate('document.documentElement.scrollWidth'), 390)

    async def test_write_completes_after_navigation_and_draft_is_preserved(self):
        await self.page.goto(self.base + '/videos/demo/review/script')
        editor = self.page.get_by_role('textbox', name='Script source', exact=True)
        await expect(editor).to_have_value('Original script')
        self.script.write_text('Fresh content')
        await self.page.get_by_role('link', name='Settings and agent guide', exact=True).click()
        await expect(self.page.locator('h1')).to_have_text('Settings and agent handoff')
        await self.page.go_back()
        await expect(editor).to_have_value('Fresh content')
        await editor.fill('Saved while navigating')
        started = asyncio.Event()
        async def slow_write(route):
            if route.request.method == 'PUT':
                started.set()
                await asyncio.sleep(.25)
            await route.continue_()
        await self.page.route('**/api/files', slow_write)
        await self.page.get_by_role('button', name='Save draft', exact=True).click()
        await asyncio.wait_for(started.wait(), 2)
        await editor.fill('Typed during save')
        await self.page.get_by_role('link', name='Settings and agent guide', exact=True).click()
        await expect(self.page.locator('h1')).to_have_text('Settings and agent handoff')
        for _ in range(30):
            if self.script.read_text() == 'Saved while navigating':
                break
            await asyncio.sleep(.05)
        self.assertEqual(self.script.read_text(), 'Saved while navigating')
        await expect(self.page.locator('h1')).to_have_text('Settings and agent handoff')

        await self.page.go_back()
        await expect(editor).to_have_value('Typed during save')

    async def test_library_pages_and_lazy_file_inventory_keep_form_inputs(self):
        for i in range(50):
            ws.create_material(self.root, {'id': f'item-{i:02}', 'title': f'Item {i}', 'description': 'needle' if i == 49 else 'plain', 'kind': 'image' if i == 49 else 'reference', 'source': 'https://example.org', 'rights': 'owned'})
        urls = []
        self.page.on('request', lambda request: urls.append(request.url))
        await self.page.goto(self.base + '/library')
        await expect(self.page.locator('.material-tile')).to_have_count(48)
        self.assertFalse(any('/api/materials/files' in u for u in urls))
        await self.page.get_by_role('button', name='Load next 3 records', exact=True).click()
        await expect(self.page.locator('.material-tile')).to_have_count(51)
        await self.page.get_by_role('searchbox', name='Search title, description, type, or linked item', exact=True).fill('needle')
        await expect(self.page.locator('.material-tile')).to_have_count(1)
        await expect(self.page.locator('.material-tile h3')).to_have_text('Item 49')
        await self.page.locator('#library-add').get_by_label('Title', exact=True).first.fill('Unsubmitted material')
        await self.page.get_by_text('Describe an existing file', exact=True).click()
        await expect(self.page.get_by_role('combobox', name='Public workspace file', exact=True)).to_be_visible()
        self.assertTrue(any('/api/materials/files?view=summary' in u for u in urls))
        await expect(self.page.locator('#library-add').get_by_label('Title', exact=True).first).to_have_value('Unsubmitted material')
        await self.page.goto(self.base + '/library?material=item-49')
        await expect(self.page.locator('.material-tile')).to_have_count(1)
        await expect(self.page.locator('.material-tile h3')).to_have_text('Item 49')

    async def test_brief_keeps_approve_and_run_agent_for_unwritten_script(self):
        self.script.write_text('')
        await self.page.goto(self.base + '/videos/demo/review/brief')
        await expect(self.page.get_by_role('button', name='Approve & run agent', exact=True)).to_be_disabled()
