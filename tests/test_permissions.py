import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from studio.permissions import (child_environment, current_session, grant, needs_review,
                                require_permission, revoke, session_state)


class PermissionsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.project = self.root / "videos" / "house" / "demo"
        self.project.mkdir(parents=True)
        (self.project / "project.json").write_text(json.dumps({"brand": "house"}))
        self.scope = "video:house/demo"
        self.record = self.root / "videos/house/.permissions/demo.json"
        self.environment = patch.dict("os.environ", {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_absent_permission_denies_work(self):
        state = session_state(self.root, self.scope)
        self.assertFalse(state["active"])
        self.assertIsNone(state["mode"])
        with self.assertRaises(ValueError):
            require_permission(self.root, self.scope, "script")
        self.assertFalse(self.record.exists())

    def test_modes_and_review_rules(self):
        full = grant(self.root, self.scope, "full")
        self.assertTrue(full["active"])
        self.assertFalse(needs_review(full, "script"))
        each = grant(self.root, self.scope, "each-stage")
        self.assertTrue(needs_review(each, "script"))
        selected = grant(self.root, self.scope, "selected-stages", ["script", "scene"])
        self.assertTrue(needs_review(selected, "script"))
        self.assertFalse(needs_review(selected, "voice"))
        self.assertEqual(require_permission(self.root, self.scope, "scene"), selected)
        events = json.loads(self.record.read_text())["events"]
        self.assertEqual([event["mode"] for event in events], ["full", "each-stage", "selected-stages"])

    def test_new_session_and_revoke(self):
        grant(self.root, self.scope, "full", session_id="first")
        self.assertTrue(session_state(self.root, self.scope, "first")["active"])
        self.assertFalse(session_state(self.root, self.scope, "second")["active"])
        revoked = revoke(self.root, self.scope, session_id="first")
        self.assertFalse(revoked["active"])
        with self.assertRaises(ValueError):
            require_permission(self.root, self.scope, session_id="first")
        events = json.loads(self.record.read_text())["events"]
        self.assertEqual(events[-1]["action"], "revoke")
        self.assertEqual(events[-1]["session_id"], "first")

    def test_scopes_are_isolated_and_canonical(self):
        grant(self.root, self.scope, "full")
        self.assertFalse(session_state(self.root, "brand:house")["active"])
        self.assertFalse(session_state(self.root, "style:modern")["active"])
        self.assertFalse(session_state(self.root, "character:alex")["active"])
        with self.assertRaises(ValueError):
            session_state(self.root, "video:demo")
        with self.assertRaises(ValueError):
            grant(self.root, "brand:../other", "full")
        brand = grant(self.root, "brand:new-brand", "full")
        self.assertTrue(brand["active"])
        self.assertTrue((self.root / "brands/.permissions/new-brand.json").is_file())
        self.assertFalse((self.root / "brands/new-brand").exists())

    def test_permission_can_precede_video_creation(self):
        scope = "video:house/future"
        state = grant(self.root, scope, "full")
        self.assertTrue(state["active"])
        self.assertFalse((self.root / "videos/house/future").exists())
        self.assertTrue((self.root / "videos/house/.permissions/future.json").is_file())
        future = self.root / "videos/house/future"
        future.mkdir()
        (future / "project.json").write_text(json.dumps({"brand": "house"}))
        self.assertTrue(require_permission(self.root, scope)["active"])

    def test_worker_inherits_only_bound_session_and_scope(self):
        grant(self.root, self.scope, "full")
        inherited = child_environment(self.root, self.scope)
        self.assertEqual(inherited["VF_SESSION_ID"], current_session(self.root))
        with patch.dict("os.environ", inherited):
            self.assertTrue(require_permission(self.root, self.scope)["active"])
            with self.assertRaises(ValueError):
                session_state(self.root, "brand:house")
            with self.assertRaises(ValueError):
                session_state(self.root, self.scope, session_id="other")
            with self.assertRaises(ValueError):
                grant(self.root, self.scope, "each-stage")
            with self.assertRaises(ValueError):
                revoke(self.root, self.scope)
            with self.assertRaises(ValueError):
                child_environment(self.root, "brand:house")

    def test_invalid_modes_and_selected_stages(self):
        for mode, stages in (("all", ()), ("selected-stages", ()),
                             ("full", ("script",)), ("selected-stages", ("bad",))):
            with self.subTest(mode=mode, stages=stages), self.assertRaises(ValueError):
                grant(self.root, self.scope, mode, stages)

    def test_record_symlink_and_invalid_record_are_rejected(self):
        record_dir = self.record.parent
        record_dir.mkdir()
        with tempfile.TemporaryDirectory() as outside:
            self.record.symlink_to(Path(outside) / "record.json")
            with self.assertRaises(ValueError):
                grant(self.root, self.scope, "full")
        self.record.unlink()
        self.record.write_text('{"events":[{"action":"grant","session_id":"bad","scope":"video:house/demo","mode":"unknown","selected_stages":[]}]}')
        with self.assertRaises(ValueError):
            session_state(self.root, self.scope)


if __name__ == "__main__":
    unittest.main()
