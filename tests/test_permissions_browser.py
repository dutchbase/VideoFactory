"""Opt-in browser proof for the Studio session permission control."""
import json
import os
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from playwright.async_api import async_playwright, expect
from studio.server import make_server


@unittest.skipUnless(os.environ.get("STUDIO_BROWSER_TESTS") == "1", "run in omabox")
class PermissionBrowserTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(Path(__file__).resolve().parents[1] / "studio/web", self.root / "studio/web")
        video = self.root / "videos/demo/clip"
        (video / "01_voice").mkdir(parents=True)
        (video / "project.json").write_text(json.dumps({"brand": "demo", "title": "Clip"}))
        (video / "01_voice/script.md").write_text("A script")
        self.server = make_server(self.root, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch()

    async def asyncTearDown(self):
        await self.browser.close()
        await self.playwright.stop()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    async def test_explicit_choice_revoke_and_fresh_context(self):
        context = await self.browser.new_context(viewport={"width": 390, "height": 844})
        page = await context.new_page()
        await page.goto(self.base + "/videos/demo/clip")
        bar = page.get_by_role("region", name="Session permission")
        await expect(bar).to_contain_text("No permission in this session")
        dialog = page.get_by_role("dialog")
        await expect(dialog.get_by_text("Do I have full permission for this session?")).to_be_visible()
        self.assertEqual(await dialog.get_by_label("materials", exact=True).count(), 0)
        await dialog.get_by_label("Review selected stages").focus()
        await page.keyboard.press("Space")
        await dialog.get_by_label("script", exact=True).focus()
        await page.keyboard.press("Space")
        await dialog.get_by_role("button", name="Save permission").click()
        await expect(bar).to_contain_text("selected stages")
        self.assertFalse(await page.evaluate("document.documentElement.scrollWidth > innerWidth"))
        await bar.get_by_role("button", name="Revoke permission").click()
        await expect(bar).to_contain_text("No permission in this session")
        await context.close()

        fresh = await self.browser.new_context(viewport={"width": 390, "height": 844})
        second = await fresh.new_page()
        await second.goto(self.base + "/videos/demo/clip")
        await expect(second.get_by_role("region", name="Session permission")).to_contain_text("No permission in this session")
        await expect(second.get_by_role("dialog").get_by_text("Do I have full permission for this session?")).to_be_visible()
        await fresh.close()

    async def test_shared_library_record_prompts_for_brand_permission(self):
        page = await self.browser.new_page()
        await page.goto(self.base + "/library")
        form = page.get_by_role("button", name="Save link record").locator("xpath=ancestor::form")
        await form.get_by_label("Title", exact=True).fill("Brand source")
        await form.get_by_label("Source URL").fill("https://example.org/source")
        await form.get_by_label("Description").fill("Source material for this brand")
        await form.get_by_label("Shared project owner").fill("brand:demo")
        await form.get_by_role("button", name="Save link record").click()
        dialog = page.get_by_role("dialog")
        await expect(dialog.get_by_text("Do I have full permission for this session?")).to_be_visible()
        await dialog.get_by_label("Full permission").check()
        await dialog.get_by_role("button", name="Save permission").click()
        await expect(page.get_by_text("Link saved", exact=True)).to_be_visible()
        self.assertTrue((self.root / "library/materials").is_dir())

    async def test_stock_download_asks_for_separate_brand_permission(self):
        page = await self.browser.new_page()
        await page.goto(self.base + "/videos/demo/clip")
        dialog = page.get_by_role("dialog")
        await expect(dialog.get_by_text("Scope: video:demo/clip.")).to_be_visible()
        await dialog.get_by_label("Full permission").check()
        await dialog.get_by_role("button", name="Save permission").click()
        await page.get_by_text("Open production actions", exact=True).click()
        await page.get_by_label("Production action").select_option("stock-get")
        await page.get_by_label("Stock reference").fill("stock:pexels/photo/1")
        await page.get_by_role("button", name="Run action").click()
        await expect(dialog.get_by_text("Scope: brand:demo.", exact=False)).to_be_visible()
