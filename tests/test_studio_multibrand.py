import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from studio import jobs, workspace
from studio.production import production_lock
from studio.server import _VIDEO, _APP


class MultiBrandStudio(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for brand in ("one", "two"):
            project = self.root / "videos" / brand / "shared"
            (project / "01_voice").mkdir(parents=True)
            (project / "project.json").write_text(json.dumps({"brand": brand}))
            (project / "01_voice/script.md").write_text(brand)

    def test_nested_file_edits_are_isolated_and_leaf_is_ambiguous(self):
        name = "videos/one/shared/01_voice/script.md"
        saved = workspace.read_file(self.root, name)
        workspace.save_text(self.root, name, "updated", saved["revision"])
        self.assertEqual((self.root / "videos/two/shared/01_voice/script.md").read_text(), "two")
        with self.assertRaises(workspace.WorkspaceError):
            workspace.read_file(self.root, "videos/shared/01_voice/script.md")

    def test_routes_keep_brand_and_stage_separate(self):
        self.assertEqual(_VIDEO.fullmatch("/api/videos/one/shared/reviews/script").groups(), ("one/shared", "reviews/script"))
        self.assertEqual(_VIDEO.fullmatch("/api/videos/one/shared/production").groups(), ("one/shared", "production"))
        self.assertIsNotNone(_APP.fullmatch("/videos/one/shared/review/script"))

    def test_new_requires_explicit_brand(self):
        with self.assertRaises(workspace.WorkspaceError):
            jobs.build_argv(self.root, "new", "fresh", {"brief": {}})

    def test_cache_files_do_not_change_scene_fingerprint(self):
        folder = self.root / "videos/one/shared"
        (folder / "04_scene").mkdir()
        with patch.object(workspace, "_upstream", return_value=[]):
            before = workspace.gate_fingerprint(self.root, "one/shared", "scene")
            cache = folder / "04_scene/__pycache__"
            cache.mkdir()
            (cache / "scene.pyc").write_bytes(b"cache")
            self.assertEqual(before, workspace.gate_fingerprint(self.root, "one/shared", "scene"))

    def test_request_rejects_stale_input_even_when_output_ready(self):
        request = jobs.create_request(self.root, "one/shared", "script", "Write", "old", "stale")
        path = self.root / ".studio/requests/stale.json"
        request["state"] = "running"
        path.write_text(json.dumps(request))
        with patch.object(jobs, "gate_fingerprint", return_value="new"), self.assertRaises(workspace.WorkspaceError):
            jobs.finish_request(self.root, "stale", {"state": "succeeded"})

    def test_brand_assets_are_public_but_settings_are_private(self):
        brand = self.root / "brands/one"
        (brand / "library/motion").mkdir(parents=True)
        asset = brand / "library/motion/clip.mp4"
        asset.write_bytes(b"video")
        (brand / "voice.md").write_text("private")
        (self.root / "library").mkdir()
        (self.root / "library/motion").symlink_to("../brands/one/library/motion")
        self.assertEqual(workspace.safe_path(self.root, "library/motion/clip.mp4"), asset)
        self.assertEqual(workspace.safe_path(self.root, "brands/one/library/motion/clip.mp4"), asset)
        with self.assertRaises(workspace.WorkspaceError):
            workspace.safe_path(self.root, "brands/one/voice.md")
        self.assertEqual(workspace.inventory_page(self.root, "files", {"brand": "one"})["items"][0]["path"], "brands/one/library/motion/clip.mp4")

    def test_metadata_mismatch_is_rejected(self):
        (self.root / "videos/one/shared/project.json").write_text('{"brand":"two"}')
        with self.assertRaises(workspace.WorkspaceError):
            workspace.video_detail(self.root, "one/shared")

    def test_start_failure_is_saved_for_the_run_controls(self):
        settings = dict(brand="one", subject="A topic", intended_result="Understand", format="wide", language="en", review_mode="autonomous", selected_stages=[], max_paid_spend="0")
        with patch("studio.autonomous.run_video", side_effect=ValueError("engine unavailable")):
            try:
                jobs.start_managed_run(self.root, "one/shared", settings)
            except workspace.WorkspaceError:
                pass
            jobs._MANAGED[str(self.root.resolve())].join(timeout=5)
        records = jobs.managed_runs(self.root, "one/shared")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "failed")
        self.assertEqual(records[0]["error"], "engine unavailable")
        self.assertIn("builder_id", records[0])

    def test_direct_cli_writer_refuses_a_held_lease(self):
        import anim
        from types import SimpleNamespace
        from concurrent.futures import ThreadPoolExecutor
        from studio.production import ProductionBusy
        called = []
        args = SimpleNamespace(cmd="render", fn=lambda args: called.append(True))
        with patch.object(anim, "ROOT", self.root), production_lock(self.root, "studio"):
            with ThreadPoolExecutor(max_workers=1) as pool:
                with self.assertRaises(ProductionBusy):
                    pool.submit(anim._dispatch, args).result()
        self.assertEqual(called, [])

    def test_new_rejects_cross_brand_source_before_creation(self):
        import anim
        from types import SimpleNamespace
        args = SimpleNamespace(slug="new", brand="two", src="one/shared")
        with patch.object(anim, "ROOT", self.root), patch.object(anim, "VIDEOS", self.root / "videos"):
            with self.assertRaises(SystemExit):
                anim.cmd_new(args)
        self.assertFalse((self.root / "videos/two/new").exists())

    def test_cli_exposes_paid_recovery_controls(self):
        import anim
        import contextlib
        import io
        from unittest.mock import Mock
        quote = Mock(return_value={"request_id": "request"})
        reconcile = Mock(return_value={"state": "settled"})
        with patch.object(anim, "ROOT", self.root), patch("studio.paid_requests.record_quote", quote, create=True), patch("studio.paid_requests.reconcile", reconcile), contextlib.redirect_stdout(io.StringIO()):
            with patch("sys.argv", ["anim.py", "run-quote", "run", "request", "--max-cost", "1", "--evidence", "receipt"]):
                anim.main()
            with patch("sys.argv", ["anim.py", "run-reconcile", "run", "request", "--actual", "0.5", "--evidence", "receipt"]):
                anim.main()
        quote.assert_called_once_with(self.root, "run", "request", "1", "receipt", retry=False)
        reconcile.assert_called_once_with(self.root, "run", "request", "0.5", "", evidence="receipt")
