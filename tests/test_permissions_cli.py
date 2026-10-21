import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import anim
from studio.permissions import grant, revoke
from studio.workspace import (WorkspaceError, accept_under_permission, decide_review,
                              gate_fingerprint, mark_ready, review_state)


class PermissionCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "videos/house/demo"
        stage = self.project / "01_voice"
        stage.mkdir(parents=True)
        (self.project / "project.json").write_text(json.dumps({"brand": "house"}))
        (stage / "brief.md").write_text("Audience: managers\nType: course\nLanguage: en\nOne outcome: learn\n")
        self.root_patch = patch.object(anim, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.env_patch = patch.dict("os.environ", {"VF_SESSION_ID": "chat-one"})
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def command(self, *args):
        parsed = anim.build_parser().parse_args(args)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            anim._dispatch(parsed)
        return output.getvalue()

    def test_permission_command_and_direct_write_guard(self):
        output = self.command("permission", "--scope", "video:house/demo")
        self.assertIn("Do I have full permission for this session?", output)
        self.assertIn('"active": false', output)
        with self.assertRaises(ValueError):
            self.command("research", "house/demo")
        output = self.command("permission", "--scope", "video:house/demo", "--grant", "full")
        self.assertIn('"active": true', output)
        self.assertEqual(json.loads((self.root / "videos/house/.permissions/demo.json").read_text())["events"][0]["session_id"], "chat-one")

    def test_acceptance_is_bound_to_session_and_human_can_approve(self):
        grant(self.root, "video:house/demo", "full")
        fingerprint = gate_fingerprint(self.root, "house/demo", "brief")
        mark_ready(self.root, "house/demo", "brief", fingerprint)
        output = self.command("review", "house/demo", "--accept", "--expected", fingerprint)
        self.assertIn("brief: accepted", output)
        state = review_state(self.root, "house/demo", "brief")
        self.assertEqual(state["history"][-1]["kind"], "acceptance")
        with patch.dict("os.environ", {"VF_SESSION_ID": "chat-two"}):
            self.assertEqual(review_state(self.root, "house/demo", "brief")["state"], "awaiting-review")
            with self.assertRaises(ValueError):
                accept_under_permission(self.root, "house/demo", "brief", fingerprint)
        output = self.command("review", "house/demo", "brief", "--approve", "--expected", fingerprint,
                              "--reviewer", "Ada")
        self.assertIn("brief: approved", output)
        self.assertEqual(review_state(self.root, "house/demo", "brief")["state"], "approved")

    def test_revoked_acceptance_no_longer_unlocks_stage(self):
        grant(self.root, "video:house/demo", "full")
        fingerprint = gate_fingerprint(self.root, "house/demo", "brief")
        mark_ready(self.root, "house/demo", "brief", fingerprint)
        accept_under_permission(self.root, "house/demo", "brief", fingerprint)
        self.assertEqual(review_state(self.root, "house/demo", "brief")["state"], "accepted")
        revoke(self.root, "video:house/demo")
        self.assertEqual(review_state(self.root, "house/demo", "brief")["state"], "awaiting-review")
        grant(self.root, "video:house/demo", "full")
        self.assertEqual(review_state(self.root, "house/demo", "brief")["state"], "awaiting-review")

    def test_selected_stage_and_requested_changes_block_acceptance(self):
        grant(self.root, "video:house/demo", "selected-stages", ["brief"])
        fingerprint = gate_fingerprint(self.root, "house/demo", "brief")
        mark_ready(self.root, "house/demo", "brief", fingerprint)
        with self.assertRaises(WorkspaceError):
            accept_under_permission(self.root, "house/demo", "brief", fingerprint)
        grant(self.root, "video:house/demo", "full")
        decide_review(self.root, "house/demo", "brief", "changes-requested", "Ada", "Fix it", fingerprint)
        with self.assertRaises(WorkspaceError):
            accept_under_permission(self.root, "house/demo", "brief", fingerprint)

    def test_worker_cannot_make_human_decision(self):
        fingerprint = gate_fingerprint(self.root, "house/demo", "brief")
        mark_ready(self.root, "house/demo", "brief", fingerprint)
        with patch.dict("os.environ", {"VF_PERMISSION_WORKER": "1"}):
            with self.assertRaises(WorkspaceError):
                self.command("review", "house/demo", "brief", "--approve", "--expected", fingerprint,
                             "--reviewer", "Ada")
            with self.assertRaises(WorkspaceError):
                decide_review(self.root, "house/demo", "brief", "approved", "Ada", "", fingerprint)
            from studio.creative import decide_creative
            with self.assertRaises(WorkspaceError):
                decide_creative(self.root, "style", "missing", "brief", "approved", "Ada", "", "x")
            from studio.generation import approve_generation
            with self.assertRaises(WorkspaceError):
                approve_generation(self.root, "missing", "Ada")

    def test_direct_next_stage_needs_current_upstream_review(self):
        grant(self.root, "video:house/demo", "full")
        parsed = anim.build_parser().parse_args(["transcribe", "house/demo"])
        with patch.object(parsed, "fn") as run:
            with self.assertRaisesRegex(ValueError, "voice review"):
                anim._dispatch(parsed)
            run.assert_not_called()
        parsed = anim.build_parser().parse_args(["stills", "house/demo"])
        with patch("studio.workspace.review_state", return_value={"state": "accepted"}), patch.object(parsed, "fn") as run:
            anim._dispatch(parsed)
            run.assert_called_once()

    def test_uncached_stock_use_needs_brand_grant(self):
        grant(self.root, "video:house/demo", "full")
        parsed = anim.build_parser().parse_args(["use", "house/demo", "stock:pexels/photo/123"])
        item = {"provider": "pexels", "kind": "photo", "id": "123"}
        with patch("stock.load_item", return_value=item), \
             patch("stock._paths", return_value=(self.root / "missing.jpg", self.root / "missing.json")), \
             patch.object(parsed, "fn") as run:
            with self.assertRaises(ValueError):
                anim._dispatch(parsed)
            run.assert_not_called()
            grant(self.root, "brand:house", "full")
            anim._dispatch(parsed)
            run.assert_called_once()
            with patch.dict("os.environ", {"VF_PERMISSION_WORKER": "1", "VF_PERMISSION_SCOPE": "video:house/demo"}):
                with self.assertRaises(ValueError):
                    anim._dispatch(parsed)

    def test_paid_voice_post_requires_managed_exact_quote(self):
        from studio.paid_requests import BudgetError
        with patch("urllib.request.urlopen") as provider:
            with self.assertRaises(BudgetError):
                anim.eleven("/text-to-speech/voice", "sk_test", {"text": "Hello"})
            provider.assert_not_called()

    def test_pending_voice_quote_shows_exact_nonsecret_request(self):
        from studio.paid_requests import BudgetError
        grant(self.root, "video:house/demo", "full")
        run_id = "a" * 32
        run_dir = self.root / ".studio/runs"
        run_dir.mkdir(parents=True)
        (run_dir / (run_id + ".json")).write_text(json.dumps({"id": run_id, "video_id": "house/demo",
                                                             "settings": {"max_paid_spend": "1"}}))
        body = {"text": "The full spoken sentence.", "model_id": "voice-model",
                "voice_settings": {"stability": 0.5}}
        with patch.dict("os.environ", {"VF_PAID_GUARD": "1", "VF_RUN_ROOT": str(self.root),
                                       "VF_RUN_ID": run_id}), patch("urllib.request.urlopen") as provider:
            with self.assertRaises(BudgetError):
                anim.eleven("/text-to-speech/voice-id", "sk_test", body)
            provider.assert_not_called()
        pending = list((self.root / ".studio/paid").glob("*.pending.json"))
        self.assertEqual(len(pending), 1)
        metadata = json.loads(pending[0].read_text())["metadata"]
        self.assertEqual(metadata, {"path": "/text-to-speech/voice-id", "body": body})
        self.assertNotIn("sk_test", json.dumps(metadata))

    def test_video_grant_cannot_change_shared_library_even_with_slug(self):
        grant(self.root, "video:house/demo", "full")
        with patch("library.run") as library_run:
            with self.assertRaisesRegex(ValueError, "permission-scope"):
                self.command("lib", "port", "upstream:motion/example", "--slug", "house/demo")
            with self.assertRaisesRegex(ValueError, "permission-scope"):
                self.command("lib", "port", "upstream:motion/example", "--slug", "house/demo",
                             "--permission-scope", "video:house/demo")
            library_run.assert_not_called()

    def test_named_shared_scope_allows_shared_commands(self):
        grant(self.root, "style:modern", "full")
        grant(self.root, "video:house/demo", "full")
        with patch("library.run") as library_run, patch("audio.run") as audio_run:
            self.command("lib", "port", "upstream:motion/example", "--slug", "house/demo",
                         "--permission-scope", "style:modern")
            self.command("audio", "index", "--permission-scope", "style:modern")
            library_run.assert_called_once()
            audio_run.assert_called_once()
            with patch.dict("os.environ", {"VF_PERMISSION_WORKER": "1",
                                           "VF_PERMISSION_SCOPE": "video:house/demo"}):
                with self.assertRaises(ValueError):
                    self.command("audio", "index", "--permission-scope", "style:modern")

    def test_catalog_import_requires_all_named_style_grants_before_writing(self):
        families = [{"default_variant": "alpha"}, {"default_variant": "beta"}]
        with patch("studio.workspace.list_style_families", return_value=families), \
             patch("studio.workspace.import_existing_styles", return_value=[]) as importer:
            grant(self.root, "style:alpha", "full")
            with self.assertRaises(ValueError):
                self.command("catalog", "import")
            importer.assert_not_called()
            grant(self.root, "style:beta", "full")
            self.command("catalog", "import")
            importer.assert_called_once_with(self.root)

    def test_brand_grant_allows_named_brand_adaptation(self):
        args = ("lib", "adapt", "icon:sample", "--source-brand", "source", "--brand", "house",
                "--rights", "owned", "--changes", "colours")
        with patch("studio.asset_adaptation.adapt_asset", return_value={"id": "draft"}) as adapt:
            with self.assertRaises(ValueError):
                self.command(*args)
            adapt.assert_not_called()
            grant(self.root, "brand:house", "full")
            self.command(*args)
            adapt.assert_called_once()


if __name__ == "__main__":
    unittest.main()
