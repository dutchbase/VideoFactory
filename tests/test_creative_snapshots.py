"""Synthetic source files exercise the video-owned creative boundary."""

import json
import os
import argparse
import asyncio
import shutil
import subprocess
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

from studio import workspace as ws


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'videos/demo').mkdir(parents=True)
        (self.root / 'videos/demo/project.json').write_text(json.dumps({'brand': 'videofactory', 'style': 'ink', 'renderer': 'modern', 'format': 'wide'}))
        style = self.root / 'styles/ink'
        (style / 'template').mkdir(parents=True)
        (style / 'style.md').write_text('---\nid: "ink"\ntitle: "Ink"\nbase_kit: "modern"\nrenderer: "modern"\nsupported_formats: ["wide"]\n---\nInk.')
        (style / 'materials.md').write_text('# Materials\n')
        (style / 'template/index.html').write_text('<script src="../../../_runtime/modern.js"></script>')
        (self.root / '_runtime').mkdir()
        (self.root / '_runtime/modern.js').write_text('window.Modern = {};')
        (self.root / '_runtime/character.js').write_text('window.Character = {};')

    def test_approval_is_required(self):
        with self.assertRaises(ws.WorkspaceError) as raised:
            ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])
        self.assertEqual(raised.exception.code, 'blocked')

    def test_withdrawn_approval_blocks_prepared_proposal(self):
        with patch('studio.creative.creative_review_state', return_value={'state': 'approved', 'ready': True, 'fingerprint': 'reviewed'}):
            proposal = ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])
        with patch('studio.creative.creative_review_state', return_value={'state': 'draft', 'ready': True, 'fingerprint': 'reviewed'}):
            with self.assertRaises(ws.WorkspaceError) as raised:
                ws.apply_creative_snapshot(self.root, 'demo', 'ink', [], proposal['revision'], True)
        self.assertEqual(raised.exception.code, 'blocked')

    def test_legacy_style_removal_is_not_a_live_file(self):
        first = ws.apply_style(self.root, 'demo', 'ink', None)
        ws.apply_style(self.root, 'demo', 'ink', first['revision'], True)
        (self.root / 'styles/ink/template/index.html').unlink()
        update = ws.apply_style(self.root, 'demo', 'ink', None)
        ws.apply_style(self.root, 'demo', 'ink', update['revision'], True)
        snapshot = json.loads((self.root / 'videos/demo/style/snapshot.json').read_text())
        self.assertTrue(all(value is not None for value in snapshot['files'].values()))

    def test_old_null_style_deletion_marker_can_be_repaired(self):
        first = ws.apply_style(self.root, 'demo', 'ink', None)
        ws.apply_style(self.root, 'demo', 'ink', first['revision'], True)
        path = self.root / 'videos/demo/style/snapshot.json'
        old = json.loads(path.read_text())
        old['files']['videos/demo/style/deleted.css'] = None
        path.write_text(json.dumps(old))
        proposal = ws.apply_style(self.root, 'demo', 'ink', None)
        ws.apply_style(self.root, 'demo', 'ink', proposal['revision'], True)
        self.assertNotIn('videos/demo/style/deleted.css', json.loads(path.read_text())['files'])

    def test_new_video_uses_style_renderer(self):
        templates = Path(__file__).resolve().parents[1] / '_templates'
        shutil.copytree(templates / 'video', self.root / '_templates/video')
        shutil.copytree(templates.parent / 'brands', self.root / 'brands')
        shutil.copytree(templates / 'scene-modern-wide', self.root / '_templates/scene-modern-wide')
        ws.create_video(self.root, 'modern-demo', {'audience': 'students', 'video_type': 'explainer',
            'language': 'English', 'outcome': 'understand the lesson'}, 'wide', style_id='ink', brand='videofactory')
        self.assertIn('runtime/modern.js', (self.root / 'videos/videofactory/modern-demo/04_scene/index.html').read_text())

    @patch('studio.creative.creative_review_state', return_value={'state': 'approved', 'ready': True, 'fingerprint': 'reviewed'})
    def test_workspace_new_keeps_original_renderer_after_catalog_change(self, review):
        templates = Path(__file__).resolve().parents[1] / '_templates'
        shutil.copytree(templates / 'video', self.root / '_templates/video')
        shutil.copytree(templates.parent / 'brands', self.root / 'brands')
        shutil.copytree(templates / 'scene-modern-wide', self.root / '_templates/scene-modern-wide')
        ws.create_video(self.root, 'workspace-modern', {'audience': 'students', 'video_type': 'explainer',
            'language': 'English', 'outcome': 'understand the lesson'}, 'wide', style_id='ink', brand='videofactory')
        metadata = json.loads((self.root / 'videos/videofactory/workspace-modern/project.json').read_text())
        self.assertEqual(metadata['renderer'], 'modern')
        self.assertEqual(metadata['brand'], 'videofactory')
        html = (self.root / 'videos/videofactory/workspace-modern/04_scene/index.html').read_text()
        self.assertNotIn('{{BRAND}}', html)
        self.assertIn('brand/tokens.js', html)
        self.assertEqual(os.readlink(self.root / 'videos/videofactory/workspace-modern/04_scene/brand').split('/')[-2:], ['brands', 'videofactory'])
        path = self.root / 'styles/ink/style.md'
        path.write_text(path.read_text().replace('renderer: "modern"', 'renderer: "other"'))
        with self.assertRaises(ws.WorkspaceError) as raised:
            ws.propose_creative_snapshot(self.root, 'workspace-modern', 'ink', [])
        self.assertEqual(raised.exception.code, 'blocked')

    @patch('studio.creative.creative_review_state', return_value={'state': 'approved', 'ready': True, 'fingerprint': 'reviewed'})
    def test_cli_new_keeps_original_renderer_after_catalog_change(self, review):
        import anim
        templates = Path(__file__).resolve().parents[1] / '_templates'
        shutil.copytree(templates / 'video', self.root / '_templates/video')
        shutil.copytree(templates.parent / 'brands', self.root / 'brands')
        shutil.copytree(templates / 'scene-modern-wide', self.root / '_templates/scene-modern-wide')
        with patch.object(anim, 'ROOT', self.root), patch.object(anim, 'VIDEOS', self.root / 'videos'), \
             patch.object(anim, 'TEMPLATE', self.root / '_templates/video'):
            anim.cmd_new(argparse.Namespace(slug='cli-modern', voice=None, format='wide', style='ink', src=None, brand='videofactory'))
        metadata = json.loads((self.root / 'videos/videofactory/cli-modern/project.json').read_text())
        self.assertEqual((metadata['style'], metadata['renderer']), ('ink', 'modern'))
        path = self.root / 'styles/ink/style.md'
        path.write_text(path.read_text().replace('renderer: "modern"', 'renderer: "other"'))
        with self.assertRaises(ws.WorkspaceError) as raised:
            ws.propose_creative_snapshot(self.root, 'cli-modern', 'ink', [])
        self.assertEqual(raised.exception.code, 'blocked')

    @patch('studio.creative.creative_review_state', return_value={'state': 'approved', 'ready': True, 'fingerprint': 'reviewed'})
    def test_legacy_scene_uses_owned_engine_signature_or_blocks(self, review):
        video = self.root / 'videos/demo'
        (video / 'project.json').write_text('{"brand":"videofactory"}')
        scene = video / '04_scene'
        scene.mkdir()
        (scene / 'index.html').write_text('<div id="stage" data-width="1920" data-height="1080"></div>'
            '<script src="../../../_runtime/modern.js"></script>')
        self.assertFalse(ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])['applied'])
        path = self.root / 'styles/ink/style.md'
        path.write_text(path.read_text().replace('renderer: "modern"', 'renderer: "other"'))
        with self.assertRaises(ws.WorkspaceError) as mismatch:
            ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])
        self.assertEqual(mismatch.exception.code, 'blocked')
        path.write_text(path.read_text().replace('renderer: "other"', 'renderer: "modern"'))
        (scene / 'index.html').write_text('<div id="stage" data-width="1920" data-height="1080"></div>'
            '<script src="../../../_runtime/player.js"></script>')
        with self.assertRaises(ws.WorkspaceError) as ambiguous:
            ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])
        self.assertEqual(ambiguous.exception.code, 'blocked')

    @patch('studio.creative.creative_review_state', return_value={'state': 'approved', 'ready': True, 'fingerprint': 'reviewed'})
    def test_snapshot_owns_fonts_vendor_and_scene_runtime(self, review):
        from studio.workspace import creative_scene_html
        source_root = Path(__file__).resolve().parents[1]
        (self.root / 'videos/demo/project.json').write_text(json.dumps({'brand': 'videofactory', 'style': 'ink', 'renderer': 'modern', 'format': 'wide'}))
        shutil.copytree(source_root / '_runtime/fonts', self.root / '_runtime/fonts')
        for name in ('player.js', 'lib.js'):
            shutil.copy2(source_root / '_runtime' / name, self.root / '_runtime' / name)
        (self.root / '_runtime/addon.js').write_text("import './addon-part.js';")
        (self.root / '_runtime/addon-part.js').write_text('window.addonPart = true;')
        (self.root / '_runtime/vendor').mkdir()
        shutil.copy2(source_root / '_runtime/vendor/lottie_canvas.min.js',
                     self.root / '_runtime/vendor/lottie_canvas.min.js')
        scene = self.root / 'videos/demo/04_scene'
        scene.mkdir()
        (self.root / 'styles/ink/template/index.html').write_text('''<link href="../../../_runtime/fonts/fonts.css" rel="stylesheet">
<script src="../../../_runtime/lib.js"></script><script src="../../../_runtime/addon.js"></script>''')
        (scene / 'index.html').write_text('''<link href="../../../_runtime/fonts/fonts.css" rel="stylesheet">
<script src="../../../_runtime/player.js"></script><script src="../../../_runtime/lib.js"></script>
<script src="../../../_runtime/addon.js"></script>''')
        proposal = ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])
        ws.apply_creative_snapshot(self.root, 'demo', 'ink', [], proposal['revision'], True)
        owned = self.root / 'videos/demo/creative'
        self.assertTrue((owned / 'deps/_runtime/fonts/inter/Inter[opsz,wght].ttf').is_file())
        self.assertTrue((owned / 'deps/_runtime/vendor/lottie_canvas.min.js').is_file())
        self.assertEqual((owned / 'deps/_runtime/addon-part.js').read_text(), 'window.addonPart = true;')
        font = self.root / '_runtime/fonts/inter/Inter[opsz,wght].ttf'
        copied_font = (owned / 'deps/_runtime/fonts/inter/Inter[opsz,wght].ttf').read_bytes()
        font.unlink()
        self.assertEqual((owned / 'deps/_runtime/fonts/inter/Inter[opsz,wght].ttf').read_bytes(), copied_font)
        html = creative_scene_html(self.root, 'demo')
        self.assertIn('../creative/deps/_runtime/lib.js', html)
        self.assertIn('../creative/deps/_runtime/fonts/fonts.css', html)
        self.assertNotIn('../../../_runtime/', html)

    @patch('studio.creative.creative_review_state', return_value={'state': 'approved', 'ready': True, 'fingerprint': 'reviewed'})
    def test_authored_scene_script_reads_owned_shared_image_after_source_changes(self, review):
        from studio.server import make_server
        scene = self.root / 'videos/demo/04_scene'
        scene.mkdir()
        (scene / 'index.html').write_text('<script src="../../../_runtime/modern.js"></script><script src="../../../_runtime/addon.js"></script><script src="scene.js"></script>')
        (self.root / '_runtime/addon.js').write_text("import './addon-part.js';")
        (self.root / '_runtime/addon-part.js').write_text('window.addonPart = true;')
        source = self.root / 'library/materials/photo/picture.png'
        source.parent.mkdir(parents=True)
        Image.new('RGBA', (8, 8), 'red').save(source)
        original = source.read_bytes()
        (scene / 'scene.js').write_text("window.picture = Modern.image('../../../library/materials/photo/picture.png');")
        proposal = ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])
        ws.apply_creative_snapshot(self.root, 'demo', 'ink', [], proposal['revision'], True)
        source.unlink()
        (self.root / '_runtime/addon-part.js').unlink()
        self.assertEqual((self.root / 'videos/demo/creative/deps/_runtime/addon-part.js').read_text(), 'window.addonPart = true;')
        server = make_server(self.root, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f'http://127.0.0.1:{server.server_port}'
            with urlopen(base + '/videos/demo/04_scene/scene.js') as response:
                served = response.read().decode()
            self.assertIn('../creative/deps/library/materials/photo/picture.png', served)
            self.assertNotIn('../../../library/materials/photo/picture.png', served)
            with urlopen(base + '/videos/demo/creative/deps/library/materials/photo/picture.png') as response:
                self.assertEqual(response.read(), original)
            (scene / 'scene.js').write_text("window.picture = Modern.image('../../../library/materials/photo/new.png');")
            with self.assertRaises(HTTPError) as blocked:
                urlopen(base + '/videos/demo/04_scene/scene.js')
            self.assertEqual(blocked.exception.code, 409)
        finally:
            server.shutdown(); server.server_close(); thread.join()

    @unittest.skipUnless(os.environ.get('ANIM_GUI_TEST') == '1', 'contained browser proof is opt-in')
    @patch('studio.creative.creative_review_state', return_value={'state': 'approved', 'ready': True, 'fingerprint': 'reviewed'})
    def test_authored_scene_script_renders_copied_image_in_browser(self, review):
        from playwright.async_api import async_playwright
        from studio.server import make_server
        scene = self.root / 'videos/demo/04_scene'
        scene.mkdir()
        (scene / 'index.html').write_text('<canvas id="stage" width="8" height="8"></canvas><script src="scene.js"></script>')
        (scene / 'scene.js').write_text("const image = new Image(); image.src = '../../../library/materials/photo/picture.png'; "
                                        "image.onload = () => {document.querySelector('#stage').getContext('2d').drawImage(image, 0, 0); window.done = true};")
        source = self.root / 'library/materials/photo/picture.png'
        source.parent.mkdir(parents=True)
        Image.new('RGBA', (8, 8), 'red').save(source)
        proposal = ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])
        ws.apply_creative_snapshot(self.root, 'demo', 'ink', [], proposal['revision'], True)
        source.unlink()
        server = make_server(self.root, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            async def render():
                async with async_playwright() as playwright:
                    browser = await playwright.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
                    page = await browser.new_page()
                    requests = []
                    errors = []
                    page.on('request', lambda request: requests.append(request.url))
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
                    await page.goto(f'http://127.0.0.1:{server.server_port}/videos/demo/04_scene/index.html')
                    try:
                        await page.wait_for_function('window.done === true', timeout=5000)
                    except Exception:
                        self.fail(f'Image did not render: requests={requests}, errors={errors}')
                    pixel = await page.evaluate("Array.from(document.querySelector('#stage').getContext('2d').getImageData(0, 0, 1, 1).data)")
                    await browser.close()
                    return pixel, requests
            pixel, requests = asyncio.run(render())
            self.assertEqual(pixel, [255, 0, 0, 255])
            self.assertTrue(any('/creative/deps/library/materials/photo/picture.png' in url for url in requests))
            self.assertFalse(any('/library/materials/photo/picture.png' in url and '/creative/' not in url for url in requests))
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_character_variant_must_match_style(self):
        from studio.characters import snapshot_variant_for_style
        with patch('studio.characters._registered_variant', return_value={'style_id': 'another-style'}):
            with self.assertRaises(ws.WorkspaceError) as blocked:
                snapshot_variant_for_style(self.root, 'tutor', 'ink', 'ink')
        self.assertEqual(blocked.exception.code, 'blocked')

    @patch('studio.creative.creative_review_state', return_value={'state': 'approved', 'ready': True, 'fingerprint': 'reviewed'})
    def test_owned_preview_allows_opaque_read_without_private_paths(self, review):
        from studio.server import make_server
        proposal = ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])
        ws.apply_creative_snapshot(self.root, 'demo', 'ink', [], proposal['revision'], True)
        server = make_server(self.root, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f'http://127.0.0.1:{server.server_port}'
            with urlopen(base + '/api/bootstrap') as response:
                token = json.load(response)['token']
            def post(body):
                request = Request(base + '/api/videos/demo/creative', data=json.dumps(body).encode(),
                    headers={'Content-Type': 'application/json', 'X-Studio-Token': token}, method='POST')
                with urlopen(request) as response: return json.load(response)
            proposal = post({'style_id': 'ink', 'characters': []})
            self.assertFalse(proposal['applied'])
            self.assertTrue(post({'style_id': 'ink', 'characters': [], 'expected_revision': proposal['revision'], 'confirm': True})['applied'])
            with urlopen(Request(base + '/videos/demo/creative/snapshot.json', headers={'Origin': 'null'})) as response:
                self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'null')
                self.assertEqual(json.load(response)['style_id'], 'ink')
            with self.assertRaises(HTTPError) as denied:
                urlopen(base + '/videos/demo/creative/_auth/secret.json')
            self.assertEqual(denied.exception.code, 404)
            denied.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    @patch('studio.creative.creative_review_state', return_value={'state': 'approved', 'ready': True, 'fingerprint': 'reviewed'})
    def test_copies_and_protects_owned_files(self, review):
        proposal = ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])
        self.assertTrue(proposal['changes'])
        applied = ws.apply_creative_snapshot(self.root, 'demo', 'ink', [], proposal['revision'], True)
        self.assertTrue(applied['applied'])
        owned = self.root / 'videos/demo/creative'
        snapshot = json.loads((owned / 'snapshot.json').read_text())
        self.assertTrue(all(value for value in snapshot['files'].values()))
        html = (owned / 'style/template/index.html').read_text()
        self.assertIn('deps/_runtime/modern.js', html)
        self.assertNotIn('../../../_runtime', html)
        (self.root / '_runtime/modern.js').write_text('changed')
        self.assertEqual((owned / 'deps/_runtime/modern.js').read_text(), 'window.Modern = {};')
        (owned / 'style/template/index.html').write_text('manual edit')
        with self.assertRaises(ws.WorkspaceError) as raised:
            ws.apply_creative_snapshot(self.root, 'demo', 'ink', [],
                ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])['revision'], True)
        self.assertEqual(raised.exception.code, 'conflict')

    @patch('studio.creative.creative_review_state', return_value={'state': 'approved', 'ready': True, 'fingerprint': 'reviewed'})
    def test_stale_revision_and_removal(self, review):
        proposal = ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])
        (self.root / 'styles/ink/style.md').write_text((self.root / 'styles/ink/style.md').read_text() + '\nChanged')
        with self.assertRaises(ws.WorkspaceError):
            ws.apply_creative_snapshot(self.root, 'demo', 'ink', [], proposal['revision'], True)
        fresh = ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])
        ws.apply_creative_snapshot(self.root, 'demo', 'ink', [], fresh['revision'], True)
        (self.root / 'styles/ink/template/index.html').unlink()
        removal = ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])
        self.assertTrue(any(c['after'] is None for c in removal['changes']))
        ws.apply_creative_snapshot(self.root, 'demo', 'ink', [], removal['revision'], True)
        snapshot = json.loads((self.root / 'videos/demo/creative/snapshot.json').read_text())
        self.assertTrue(all(value is not None for value in snapshot['files'].values()))

    @patch('studio.creative.creative_review_state', return_value={'state': 'approved', 'ready': True, 'fingerprint': 'reviewed'})
    def test_removed_local_file_and_failed_swap_keep_prior_snapshot(self, review):
        proposal = ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])
        ws.apply_creative_snapshot(self.root, 'demo', 'ink', [], proposal['revision'], True)
        owned = self.root / 'videos/demo/creative'
        original = (owned / 'snapshot.json').read_bytes()
        (owned / 'style/template/index.html').unlink()
        protected = ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])
        self.assertTrue(protected['protected'])
        with self.assertRaises(ws.WorkspaceError):
            ws.apply_creative_snapshot(self.root, 'demo', 'ink', [], protected['revision'], True)
        (owned / 'style/template/index.html').write_text('<script src="../../deps/_runtime/modern.js"></script>')
        self.assertEqual(ws._file_hash(owned / 'style/template/index.html'), json.loads(original)['files']['videos/demo/creative/style/template/index.html'])
        (self.root / 'styles/ink/style.md').write_text((self.root / 'styles/ink/style.md').read_text() + '\nupdate')
        update = ws.propose_creative_snapshot(self.root, 'demo', 'ink', [])
        real_replace = os.replace
        def failed_swap(source, target):
            if Path(source).name.startswith('.studio-creative-') and not Path(source).name.startswith('.studio-creative-backup-') and Path(target) == owned:
                raise OSError('synthetic swap failure')
            return real_replace(source, target)
        with patch('studio.workspace.os.replace', side_effect=failed_swap), self.assertRaises(OSError):
            ws.apply_creative_snapshot(self.root, 'demo', 'ink', [], update['revision'], True)
        self.assertEqual((owned / 'snapshot.json').read_bytes(), original)
        self.assertFalse(list((self.root / 'videos/demo').glob('.studio-creative-*')))

    @patch('studio.characters.snapshot_variant_for_style', return_value={'style_id': 'ink'})
    @patch('studio.creative.creative_review_state', return_value={'state': 'approved', 'ready': True, 'fingerprint': 'reviewed'})
    @patch('studio.character_motion.compile_character_pack')
    def test_character_art_and_manifest_are_video_owned(self, compile_pack, review, variant):
        art = self.root / 'characters/tutor/art.png'
        art.parent.mkdir(parents=True)
        Image.new('RGBA', (8, 8), (255, 0, 0, 255)).save(art)
        pack = self.root / 'characters/tutor/03_animation/ink'
        pack.mkdir(parents=True)
        for name in ('assets', 'rig', 'motions'):
            (pack / f'{name}.json').write_text('{}')
        part = {'path': 'characters/tutor/art.png', 'sha256': ws._file_hash(art),
                'crop': [0, 0, 8, 8], 'at': [4, 4], 'anchor': [4, 4], 'layer': 0}
        compile_pack.return_value = {'canvas': [8, 8], 'views': {
            view: {'parts': {'body': part}, 'rig': {'draw_order': ['body'], 'expressions': {}, 'mouths': {}, 'props': {}}}
            for view in ('front', 'three-quarter-right')},
            'actions': {'idle': {'duration': 4, 'loop': True, 'expression': 'neutral', 'requires_prop': False, 'tracks': {}}}}
        selected = [{'character_id': 'tutor', 'variant_id': 'ink', 'actions': ['idle']}]
        proposed = ws.propose_creative_snapshot(self.root, 'demo', 'ink', selected)
        ws.apply_creative_snapshot(self.root, 'demo', 'ink', selected, proposed['revision'], True)
        owned = self.root / 'videos/demo/creative'
        manifest = json.loads((owned / 'characters/tutor/ink/manifest.json').read_text())
        part = manifest['views']['front']['parts']['body']
        self.assertTrue(part['path'].startswith('videos/demo/creative/'))
        self.assertTrue(part['url'].startswith('../creative/'))
        self.assertEqual(ws._file_hash(self.root / part['path']), part['sha256'])
        art.write_bytes(b'changed')
        self.assertEqual(ws._file_hash(self.root / part['path']), part['sha256'])
        scene_revision = ws.gate_fingerprint(self.root, 'demo', 'scene')
        (self.root / part['path']).write_bytes(b'video-owned local edit')
        self.assertNotEqual(ws.gate_fingerprint(self.root, 'demo', 'scene'), scene_revision)

    @patch('studio.characters.snapshot_variant_for_style', return_value={'style_id': 'ink'})
    @patch('studio.creative.creative_review_state', return_value={'state': 'approved', 'ready': True, 'fingerprint': 'reviewed'})
    @patch('studio.character_motion.compile_character_pack')
    def test_hyphenated_character_and_variant_ids_have_distinct_manifests(self, compile_pack, review, variant):
        import anim
        for ident, variant_id, color in [('tutor-main', 'ink', 'red'), ('tutor', 'main-ink', 'blue')]:
            art = self.root / f'characters/{ident}/art.png'
            art.parent.mkdir(parents=True)
            Image.new('RGBA', (8, 8), color).save(art)
            pack = self.root / f'characters/{ident}/03_animation/{variant_id}'
            pack.mkdir(parents=True)
            for name in ('assets', 'rig', 'motions'): (pack / f'{name}.json').write_text('{}')
        def compiled(root, ident, variant_id):
            art = self.root / f'characters/{ident}/art.png'
            part = {'path': art.relative_to(self.root).as_posix(), 'sha256': ws._file_hash(art),
                    'crop': [0, 0, 8, 8], 'at': [4, 4], 'anchor': [4, 4], 'layer': 0}
            return {'canvas': [8, 8], 'views': {view: {'parts': {'body': part}, 'rig': {}}
                    for view in ('front', 'three-quarter-right')}, 'actions': {'idle': {'duration': 1}}}
        compile_pack.side_effect = compiled
        selected = [{'character_id': ident, 'variant_id': variant_id, 'actions': ['idle']}
                    for ident, variant_id in [('tutor-main', 'ink'), ('tutor', 'main-ink')]]
        proposal = ws.propose_creative_snapshot(self.root, 'demo', 'ink', selected)
        ws.apply_creative_snapshot(self.root, 'demo', 'ink', selected, proposal['revision'], True)
        snapshot = json.loads((self.root / 'videos/demo/creative/snapshot.json').read_text())
        self.assertEqual(len({choice['manifest'] for choice in snapshot['characters']}), 2)
        for choice in snapshot['characters']:
            manifest = json.loads((self.root / 'videos/demo' / choice['manifest']).read_text())
            art = manifest['views']['front']['parts']['body']
            self.assertEqual((self.root / art['path']).read_bytes(),
                             (self.root / f"characters/{choice['character_id']}/art.png").read_bytes())
        old_root = anim.ROOT
        try:
            anim.ROOT = self.root
            self.assertEqual(len(anim.creative_snapshot(self.root / 'videos/demo')['characters']), 2)
        finally:
            anim.ROOT = old_root

    @unittest.skipUnless(os.environ.get('ANIM_GUI_TEST') == '1', 'contained browser proof is opt-in')
    @patch('studio.characters.snapshot_variant_for_style', return_value={'style_id': 'ink'})
    @patch('studio.creative.creative_review_state', return_value={'state': 'approved', 'ready': True, 'fingerprint': 'reviewed'})
    @patch('studio.character_motion.compile_character_pack')
    def test_synthetic_normal_check_stills_render(self, compile_pack, review, variant):
        import anim
        from PIL import ImageDraw

        runtime = self.root / '_runtime'
        source_runtime = Path(anim.__file__).resolve().parent / '_runtime'
        for name in ('player.js', 'textcheck.js'):
            shutil.copy2(source_runtime / name, runtime / name)
        art = self.root / 'characters/tutor/synthetic-atlas.png'
        art.parent.mkdir(parents=True)
        image = Image.new('RGBA', (128, 64))
        pen = ImageDraw.Draw(image)
        names = ['body', 'head', 'hair', 'arm-left', 'arm-right'] + [f'face-{x}' for x in
            ('neutral', 'blink', 'happy', 'puzzled', 'surprised', 'disappointed')] + [f'mouth-{x}' for x in ('closed', 'half', 'open')] + ['book', 'tablet']
        for index in range(len(names) * 2):
            x, y = index % 16 * 8, index // 16 * 8
            pen.rectangle((x, y, x + 7, y + 7), fill=(210, 30 + index, 40, 255))
        image.save(art)
        sha = ws._file_hash(art)
        views = {}
        for view_index, view in enumerate(('front', 'three-quarter-right')):
            parts = {name: {'path': art.relative_to(self.root).as_posix(), 'sha256': sha,
                'crop': [(index + view_index * len(names)) % 16 * 8, (index + view_index * len(names)) // 16 * 8, 8, 8],
                'at': [24 + index % 3 * 2, 24 + index % 4 * 2], 'anchor': [4, 4], 'layer': index}
                for index, name in enumerate(names)}
            views[view] = {'parts': parts, 'rig': {'draw_order': names,
                'expressions': {x: f'face-{x}' for x in ('neutral', 'blink', 'happy', 'puzzled', 'surprised', 'disappointed')},
                'mouths': {x: f'mouth-{x}' for x in ('closed', 'half', 'open')}, 'props': {'book': 'book', 'tablet': 'tablet'}}}
        idle = {'duration': 4, 'loop': True, 'expression': 'neutral', 'requires_prop': False,
                'tracks': {'body': [{'t': 0, 'x': 0, 'y': 0, 'rotation': 0}, {'t': 4, 'x': 0, 'y': 0, 'rotation': 0}]}}
        compile_pack.return_value = {'canvas': [64, 64], 'views': views, 'actions': {'idle': idle}}
        pack = self.root / 'characters/tutor/03_animation/ink'
        pack.mkdir(parents=True)
        for name in ('assets', 'rig', 'motions'):
            (pack / f'{name}.json').write_text('{}')
        choice = [{'character_id': 'tutor', 'variant_id': 'ink', 'actions': ['idle']}]

        video = self.root / 'videos/demo'
        for directory in ('01_voice', '02_transcript', '03_cues', '04_scene', '05_render'):
            (video / directory).mkdir()
        (video / '04_scene/index.html').write_text('''<!doctype html><link rel="icon" href="data:,"><div id="stage" data-width="320" data-height="180"></div>
<script src="../03_cues/cues.js"></script><script src="../../../_runtime/player.js"></script><script src="scene.js"></script>''')
        (video / '04_scene/scene.js').write_text('''const canvas = document.createElement('canvas');
canvas.width = 320; canvas.height = 180; document.getElementById('stage').append(canvas);
const ctx = canvas.getContext('2d');
P.onFrame(t => { ctx.fillStyle = '#fafafa'; ctx.fillRect(0, 0, 320, 180);
  ctx.save(); ctx.translate(90, 40); ctx.scale(2, 2);
  const result = P.drawCharacter(ctx, {id:'tutor', variant:'ink', actions:{intro:'idle'}, view:'front',
    expression:'happy', expressions:{later:'neutral'}, prop:'book', props:{later:'tablet'}});
  window.__lastCharacter = result;
  if (!result.available) console.error('character unavailable: ' + result.reason);
  ctx.restore(); });''')
        (video / '03_cues/cues.md').write_text('## intro @0\nSynthetic character motion.\n## later @1.5\nChange pose.\n')
        (video / '02_transcript/words.json').write_text(json.dumps({'duration': 2,
            'voice': 'voice.wav', 'words': [{'text': 'Synthetic', 'start': 0, 'end': 0.4}]}))
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2',
                        str(video / '01_voice/voice.wav')], check=True)
        proposal = ws.propose_creative_snapshot(self.root, 'demo', 'ink', choice)
        ws.apply_creative_snapshot(self.root, 'demo', 'ink', choice, proposal['revision'], True)
        old_root, old_videos, old_server = anim.ROOT, anim.VIDEOS, anim._creative_http
        anim.ROOT, anim.VIDEOS, anim._creative_http = self.root, self.root / 'videos', None
        try:
            anim.cmd_cues(argparse.Namespace(slug='demo', threshold=0.75))
            async def cue_defaults():
                from playwright.async_api import async_playwright
                async with async_playwright() as playwright:
                    browser, page, _, _ = await anim.open_page(playwright, anim.scene_url(video))
                    before = await page.evaluate('window.__lastCharacter')
                    await page.evaluate('window.__seek(1.6)')
                    after = await page.evaluate('window.__lastCharacter')
                    await browser.close()
                    return before, after
            before, after = asyncio.run(cue_defaults())
            self.assertEqual((before['expression'], before['prop']), ('happy', 'book'))
            self.assertEqual((after['expression'], after['prop']), ('neutral', 'tablet'))
            check = anim.run_check(video)
            self.assertTrue(all(v == 0 for v in check['counters'].values()), check['details'])
            anim.cmd_stills(argparse.Namespace(slug='demo', skip_tone=True, hold=0.5, at=None))
            still = Image.open(next((video / '05_render/stills').glob('*.png'))).convert('RGB')
            self.assertLess(still.getpixel((138, 90))[1], 200)
            anim.cmd_render(argparse.Namespace(slug='demo', skip_tone=True, fps=6, start=None, end=None,
                workers=1, crf=28, quality=85, blur=1, skip_check=False, no_master=False, lufs=-14, phone=False))
            self.assertTrue((video / '05_render/demo.mp4').is_file())
            delivery = (video / '05_render/check-video.md').read_text()
            self.assertIn('format:', delivery)
            self.assertIn('loudness:', delivery)
            self.assertIn('(ok)', delivery)
            self.assertTrue(all(v == 0 for v in anim.run_check(video)['counters'].values()))
        finally:
            if anim._creative_http:
                anim._creative_http.shutdown()
                anim._creative_http.server_close()
            anim.ROOT, anim.VIDEOS, anim._creative_http = old_root, old_videos, old_server


if __name__ == '__main__': unittest.main()
