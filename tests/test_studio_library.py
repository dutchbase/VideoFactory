import tempfile
import unittest
import io
import os
from pathlib import Path
from unittest.mock import patch

from studio.workspace import WorkspaceError, create_material, link_material, list_materials, save_style, apply_style, read_file, create_style, create_video


class LibraryTests(unittest.TestCase):
    def test_one_record_links_to_many_owners(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ('videos/a', 'videos/b', 'styles/ink'):
                (root / name).mkdir(parents=True)
                if name.startswith('videos/'):
                    (root / name / 'project.json').write_text('{"brand":"videofactory"}')
            item = create_material(root, {'title': 'Logo', 'description': 'User supplied', 'kind': 'image', 'source': 'upload', 'rights': 'user-supplied', 'tags': ['brand']}, content=b'PNG', filename='logo.png')
            for kind, ident in (('video', 'a'), ('video', 'b'), ('style', 'ink')):
                link_material(root, kind, ident, item['id'])
            self.assertEqual(len(list_materials(root, {})), 1)
            self.assertEqual(len(list_materials(root, {})[0]['linked_videos']), 2)

    def test_style_snapshot_does_not_track_later_recipe_edit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            style = root / 'styles/ink/style.md'
            style.parent.mkdir(parents=True)
            style.write_text('---\nid: "ink"\ntitle: "Ink"\nbase_kit: "modern"\n---\n\nDark lines.\n')
            (root / 'videos/a').mkdir(parents=True)
            (root / 'videos/a/project.json').write_text('{"brand":"videofactory"}')
            proposal = apply_style(root, 'a', 'ink', None)
            applied = apply_style(root, 'a', 'ink', proposal['revision'], confirm=True)
            snapshot = root / 'videos/a/style/style.md'
            self.assertEqual(snapshot.read_text(), style.read_text())
            save_style(root, 'ink', style.read_text().replace('Dark', 'Light'), read_file(root, 'styles/ink/style.md')['revision'])
            self.assertEqual(snapshot.read_text(), '---\nid: "ink"\ntitle: "Ink"\nbase_kit: "modern"\n---\n\nDark lines.\n')
            self.assertTrue(applied['applied'])

    def test_style_update_rejects_changed_source_and_rolls_back_swap_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            style = root / 'styles/ink/style.md'
            style.parent.mkdir(parents=True)
            style.write_text('---\nid: "ink"\ntitle: "Ink"\nbase_kit: "modern"\n---\n\nDark.\n')
            (root / 'videos/a').mkdir(parents=True)
            (root / 'videos/a/project.json').write_text('{"brand":"videofactory"}')
            first = apply_style(root, 'a', 'ink', None)
            apply_style(root, 'a', 'ink', first['revision'], confirm=True)
            prior = (root / 'videos/a/style/style.md').read_text()
            proposal = apply_style(root, 'a', 'ink', None)
            style.write_text(style.read_text().replace('Dark', 'Light'))
            with self.assertRaises(WorkspaceError):
                apply_style(root, 'a', 'ink', proposal['revision'], confirm=True)
            proposal = apply_style(root, 'a', 'ink', None)
            real_replace = os.replace

            def fail_swap(source, target):
                if Path(target) == root / 'videos/a/style' and Path(source).name.startswith('.studio-style-') and 'backup' not in Path(source).name:
                    raise OSError('disk failure')
                return real_replace(source, target)

            with patch('studio.workspace.os.replace', side_effect=fail_swap):
                with self.assertRaises(OSError):
                    apply_style(root, 'a', 'ink', proposal['revision'], confirm=True)
            self.assertEqual((root / 'videos/a/style/style.md').read_text(), prior)

    def test_removed_style_file_with_local_edit_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            recipe = root / 'styles/ink/style.md'
            recipe.parent.mkdir(parents=True)
            recipe.write_text('---\nid: "ink"\ntitle: "Ink"\nbase_kit: "modern"\n---\n\nDark.\n')
            shared_scene = root / 'styles/ink/template/scene.js'
            shared_scene.parent.mkdir()
            shared_scene.write_text('original scene')
            (root / 'videos/a').mkdir(parents=True)
            (root / 'videos/a/project.json').write_text('{"brand":"videofactory"}')
            first = apply_style(root, 'a', 'ink', None)
            apply_style(root, 'a', 'ink', first['revision'], confirm=True)
            local_scene = root / 'videos/a/style/template/scene.js'
            manifest = root / 'videos/a/style/snapshot.json'
            original_manifest = manifest.read_bytes()
            local_scene.write_text('local edit')
            shared_scene.unlink()
            proposal = apply_style(root, 'a', 'ink', None)
            self.assertTrue(any(change['path'] == 'videos/a/style/template/scene.js' and change['after'] is None for change in proposal['changes']))
            with self.assertRaises(WorkspaceError) as error:
                apply_style(root, 'a', 'ink', proposal['revision'], confirm=True)
            self.assertEqual(error.exception.code, 'conflict')
            self.assertEqual(local_scene.read_text(), 'local edit')
            self.assertEqual(manifest.read_bytes(), original_manifest)

    def test_unmodified_removed_style_file_is_deleted_after_confirm(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            recipe = root / 'styles/ink/style.md'
            recipe.parent.mkdir(parents=True)
            recipe.write_text('---\nid: "ink"\ntitle: "Ink"\nbase_kit: "modern"\n---\n\nDark.\n')
            shared_scene = root / 'styles/ink/template/scene.js'
            shared_scene.parent.mkdir()
            shared_scene.write_text('original scene')
            (root / 'videos/a').mkdir(parents=True)
            (root / 'videos/a/project.json').write_text('{"brand":"videofactory"}')
            first = apply_style(root, 'a', 'ink', None)
            apply_style(root, 'a', 'ink', first['revision'], confirm=True)
            shared_scene.unlink()
            proposal = apply_style(root, 'a', 'ink', None)
            self.assertTrue(any(change['path'] == 'videos/a/style/template/scene.js' and change['after'] is None for change in proposal['changes']))
            apply_style(root, 'a', 'ink', proposal['revision'], confirm=True)
            self.assertFalse((root / 'videos/a/style/template/scene.js').exists())

    def test_unknown_rights_stay_visible_on_reference_link(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'videos/a').mkdir(parents=True)
            (root / 'videos/a/project.json').write_text('{"brand":"videofactory"}')
            item = create_material(root, {'title': 'Unclear', 'description': 'test', 'kind': 'image', 'source': 'https://example.com/x', 'rights': 'unknown', 'tags': []})
            link_material(root, 'video', 'a', item['id'])
            self.assertEqual(list_materials(root, {})[0]['rights'], 'unknown')

    def test_new_video_snapshots_selected_recipe(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '_templates/video/01_voice').mkdir(parents=True)
            (root / '_templates/scene-modern-wide').mkdir(parents=True)
            (root / '_templates/video/01_voice/script.md').write_text('')
            (root / '_templates/video/01_voice/brief.md').write_text('# Brief\n')
            (root / '_templates/scene-modern-wide/index.html').write_text('<title>{{TITLE}}</title><script src="brand/tokens.js"></script>')
            (root / 'brands/videofactory').mkdir(parents=True)
            (root / 'brands/videofactory/tokens.js').write_text('')
            style = create_style(root, 'ink', 'Ink', 'modern')
            video = create_video(root, 'demo', {'audience': 'creators', 'video_type': 'course', 'language': 'en', 'outcome': 'learn'}, style_id='ink', brand='videofactory')
            self.assertEqual(video['style'], 'ink')
            self.assertTrue((root / 'videos/videofactory/demo/style/snapshot.json').is_file())

    def test_streamed_upload_failure_leaves_no_record(self):
        class Broken(io.BytesIO):
            def read(self, size=-1):
                raise OSError('disconnect')

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(WorkspaceError) as error:
                create_material(root, {'title': 'Clip', 'description': 'A clip', 'kind': 'video', 'source': 'upload', 'rights': 'user-supplied'}, Broken(b'x'), 'clip.mp4')
            self.assertEqual(error.exception.code, 'io')
            self.assertEqual(list_materials(root, {}), [])

    def test_collection_includes_generated_index_and_existing_video_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            icon = root / 'library/icons/mark.png'
            icon.parent.mkdir(parents=True)
            icon.write_bytes(b'png')
            (root / 'library/INDEX.json').write_text('[{"ref":"icon:mark","name":"mark","kind":"icon","license":"MIT","path":"icons/mark.png"}]')
            asset = root / 'videos/demo/04_scene/assets/logo.png'
            asset.parent.mkdir(parents=True)
            asset.write_bytes(b'png')
            records = list_materials(root, {})
            self.assertEqual({record['origin'] for record in records}, {'library-index', 'video-asset'})
            self.assertEqual(next(r for r in records if r['origin'] == 'video-asset')['linked_videos'], ['demo'])
