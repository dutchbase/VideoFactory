"""Session permission boundaries for the Studio HTTP API."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from studio.server import make_server


class PermissionHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        video = self.root / "videos/demo/clip"
        (video / "01_voice").mkdir(parents=True)
        (video / "project.json").write_text('{"brand":"demo"}')
        (video / "01_voice/script.md").write_text("First")
        (self.root / "styles/plain").mkdir(parents=True)
        (self.root / "styles/plain/style.md").write_text("Style")
        self.server = make_server(self.root, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.bootstrap = self.request("/api/bootstrap")
        self.a = "a" * 32 + "." + self.bootstrap["session_nonce"]
        self.b = "b" * 32 + "." + self.bootstrap["session_nonce"]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, path, method="GET", body=None, session=None):
        headers = {"Content-Type": "application/json"}
        if session: headers["X-VF-Session-ID"] = session
        if method != "GET": headers["X-Studio-Token"] = self.bootstrap["token"] if hasattr(self, "bootstrap") else ""
        request = Request(self.base + path, data=json.dumps(body).encode() if body is not None else None,
                          headers=headers, method=method)
        with urlopen(request) as response:
            return json.load(response)

    def grant(self, session, mode="full", stages=()):
        return self.request("/api/permission", "POST", {"action": "grant", "scope": "video:demo/clip",
            "mode": mode, "selected_stages": list(stages)}, session)

    def test_fresh_session_and_revoke(self):
        path = "videos/demo/clip/01_voice/script.md"
        revision = self.request("/api/files?path=" + path)["revision"]
        write = {"path": path, "text": "Second", "expected_revision": revision}
        with self.assertRaises(HTTPError) as blocked:
            self.request("/api/files", "PUT", write, self.a)
        self.assertEqual(blocked.exception.code, 403)
        self.assertTrue(self.grant(self.a)["active"])
        self.assertFalse(self.request("/api/permission?scope=video:demo/clip", session=self.b)["active"])
        with self.assertRaises(HTTPError) as blocked:
            self.request("/api/files", "PUT", write, self.b)
        self.assertEqual(blocked.exception.code, 403)
        self.request("/api/files", "PUT", write, self.a)
        self.request("/api/permission", "POST", {"action": "revoke", "scope": "video:demo/clip"}, self.a)
        with self.assertRaises(HTTPError) as blocked:
            self.request("/api/files", "PUT", {**write, "text": "Third"}, self.a)
        self.assertEqual(blocked.exception.code, 403)

    def test_selected_stages_and_shared_scope(self):
        state = self.grant(self.a, "selected-stages", ["script", "scene"])
        self.assertEqual(state["selected_stages"], ["script", "scene"])
        with self.assertRaises(HTTPError) as blocked:
            self.request("/api/files", "PUT", {"path": "styles/plain/style.md", "text": "Changed", "expected_revision": None}, self.a)
        self.assertEqual(blocked.exception.code, 403)
        self.assertEqual((self.root / "styles/plain/style.md").read_text(), "Style")

    def test_invalid_session_cannot_grant(self):
        with self.assertRaises(HTTPError) as blocked:
            self.grant("a" * 32 + "." + "x" * 32)
        self.assertEqual(blocked.exception.code, 403)

    def test_full_permission_accepts_ready_creative_stage(self):
        self.request("/api/permission", "POST", {"action": "grant", "scope": "style:new-look", "mode": "full"}, self.a)
        detail = self.request("/api/creative", "POST", {"type": "style", "id": "new-look", "prompt": "Clear lines", "metadata": {"title": "New look"}}, self.a)
        detail = self.request("/api/creative/style/new-look/answers", "PUT", {"answers": {"look": "Clear lines"}, "brief": "Clear lines and measured motion.", "expected_revision": detail["revision"]}, self.a)
        fingerprint = detail["reviews"]["brief"]["fingerprint"]
        ready = self.request("/api/creative/style/new-look/reviews/brief/ready", "POST", {"expected_revision": fingerprint}, self.a)
        self.assertEqual(ready["state"], "accepted")

    def test_full_permission_accepts_ready_video_stage(self):
        (self.root / "videos/demo/clip/01_voice/brief.md").write_text(
            "Audience: managers\nType: course\nLanguage: en\nOne outcome: learn\n")
        self.grant(self.a)
        review = self.request("/api/videos/demo/clip/reviews/brief", session=self.a)
        self.assertTrue(review["ready"])
        ready = self.request("/api/videos/demo/clip/reviews/brief/ready", "POST",
                             {"expected_fingerprint": review["fingerprint"]}, self.a)
        self.assertEqual(ready["state"], "accepted")
        self.assertEqual(self.request("/api/videos/demo/clip/reviews/brief", session=self.b)["state"], "awaiting-review")

    def test_shared_material_needs_its_own_named_grant(self):
        self.grant(self.a)
        metadata = {"id": "shared-link", "title": "Shared link", "description": "Source for the brand",
                    "kind": "reference", "source": "https://example.org", "rights": "owned", "tags": []}
        with self.assertRaises(HTTPError) as blocked:
            self.request("/api/materials", "POST", {**metadata, "permission_scope": "video:demo/clip"}, self.a)
        self.assertEqual(blocked.exception.code, 403)
        with self.assertRaises(HTTPError) as blocked:
            self.request("/api/materials", "POST", {**metadata, "permission_scope": "brand:demo"}, self.a)
        self.assertEqual(blocked.exception.code, 403)
        self.request("/api/permission", "POST", {"action": "grant", "scope": "brand:demo", "mode": "full"}, self.a)
        saved = self.request("/api/materials", "POST", {**metadata, "permission_scope": "brand:demo"}, self.a)
        self.assertEqual(saved["id"], "shared-link")
        upload_metadata = {**metadata, "id": "shared-image", "kind": "image", "source": "upload", "permission_scope": "brand:demo"}
        upload = Request(self.base + "/api/materials/upload", data=b"image", method="POST", headers={
            "X-Studio-Token": self.bootstrap["token"], "X-VF-Session-ID": self.a,
            "X-Material-Filename": "image.png", "X-Material-Metadata": json.dumps(upload_metadata)})
        with urlopen(upload) as response:
            self.assertEqual(json.load(response)["id"], "shared-image")
        self.assertTrue((self.root / "library/materials/shared-image/image.png").is_file())

    def test_stock_download_requires_the_video_brand_grant(self):
        self.grant(self.a)
        body = {"action": "stock-get", "slug": "demo/clip", "options": {"ref": "stock:pexels/photo/1"}, "request_id": "stock-test"}
        with patch("studio.server.jobs.start_job", return_value={"job": {"id": "stock-test"}}) as start:
            with self.assertRaises(HTTPError) as blocked:
                self.request("/api/jobs", "POST", body, self.a)
            self.assertEqual(blocked.exception.code, 403)
            start.assert_not_called()
            self.request("/api/permission", "POST", {"action": "grant", "scope": "brand:demo", "mode": "full"}, self.a)
            result = self.request("/api/jobs", "POST", body, self.a)
            self.assertEqual(result["job"]["id"], "stock-test")
            start.assert_called_once()
