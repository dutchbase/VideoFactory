import json
import tempfile
import unittest
from pathlib import Path
from studio.project_paths import ProjectPathError, resolve_project, project_id, iter_projects, settings_snapshot

class ProjectPathsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "videos").mkdir()
    def project(self, brand, slug, legacy=False):
        path = self.root / "videos" / ("" if legacy else brand) / slug
        path.mkdir(parents=True)
        (path / "project.json").write_text(json.dumps({"brand": brand}))
        return path
    def test_same_slug_is_scoped_and_unscoped_is_ambiguous(self):
        one = self.project("videofactory", "demo")
        two = self.project("other", "demo")
        self.assertEqual(resolve_project(self.root, "videofactory/demo"), one)
        self.assertEqual(resolve_project(self.root, "other/demo"), two)
        with self.assertRaises(ProjectPathError): resolve_project(self.root, "demo")
        self.assertEqual(len(list(iter_projects(self.root))), 2)
    def test_legacy_unique_and_traversal(self):
        path = self.project("videofactory", "demo", True)
        self.assertEqual(resolve_project(self.root, "demo"), path)
        self.assertEqual(project_id(self.root, path), "videofactory/demo")
        for identity in ("../demo", "/demo", "videofactory/../demo", "videofactory//demo"):
            with self.assertRaises(ProjectPathError): resolve_project(self.root, identity)
    def test_brand_mismatch_is_rejected(self):
        path = self.project("videofactory", "demo")
        (path / "project.json").write_text('{"brand":"other"}')
        with self.assertRaises(ProjectPathError): resolve_project(self.root, "videofactory/demo")
    def test_symlink_project_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            path = Path(outside)
            (path / "project.json").write_text('{"brand":"videofactory"}')
            (self.root / "videos/escape").symlink_to(path, target_is_directory=True)
            with self.assertRaises(ProjectPathError): resolve_project(self.root, "escape")

    def test_adapted_asset_can_only_be_used_by_target_brand(self):
        import library
        from studio.asset_adaptation import adapt_asset
        from unittest.mock import patch
        source = self.root / "brands/other/library/source.svg"
        source.parent.mkdir(parents=True)
        source.write_text('<svg fill="{{TOKEN:color}}"/>')
        record = adapt_asset(self.root, "brands/other/library/source.svg", "other", "videofactory", rights="own", changes="target color",
                             tokens={"color":"red"}, source_kind="vector",
                             validation={"target_brand":"videofactory","evidence":["checked target color"],"identity_removed":True,"claims_verified":True})
        target = self.project("videofactory", "target")
        other = self.project("other", "other")
        with patch.object(library.C, "ROOT", self.root), patch.object(library, "LIB", self.root / "library"):
            library.use(target, "adaptation:" + record["id"])
            with self.assertRaises(FileNotFoundError): library.use(other, "adaptation:" + record["id"])
        self.assertIn("red", (target / "04_scene/assets/adaptations" / (record["id"] + ".svg")).read_text())

    def test_snapshot_does_not_follow_later_brand_edits(self):
        path = self.project("other", "demo")
        voice = self.root / "brands/other/voice.md"
        voice.parent.mkdir(parents=True)
        voice.write_text("---\nvoice_id: first\n---\n")
        self.assertEqual(settings_snapshot(self.root, path)["voice"]["voice_id"], "first")
        voice.write_text("---\nvoice_id: second\n---\n")
        self.assertEqual(settings_snapshot(self.root, path)["voice"]["voice_id"], "first")
        self.assertEqual(settings_snapshot(self.root, self.project("videofactory", "empty"))["voice"], {})
    def test_library_prefers_owned_and_excludes_other_motion(self):
        import library
        from unittest.mock import patch
        owned = self.root / "brands/videofactory/library/graphics/demo"
        shared = self.root / "library/graphics/demo"
        for folder, color in ((owned, "red"), (shared, "blue")):
            folder.mkdir(parents=True)
            (folder / "mark.svg").write_text(f'<svg fill="{color}"/>')
            (folder / "mark.meta.json").write_text('{"license":"CC0-1.0","source":"own"}')
        project = self.project("videofactory", "assets")
        with patch.object(library.C, "ROOT", self.root), patch.object(library, "LIB", self.root / "library"):
            self.assertEqual(len(library.find("mark", brand="videofactory")), 1)
            library.use(project, "graphic:demo/mark")
        self.assertIn("red", (project / "04_scene/assets/graphics/demo/mark.svg").read_text())

if __name__ == "__main__": unittest.main()
