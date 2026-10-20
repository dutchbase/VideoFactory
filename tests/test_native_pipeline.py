import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from studio import native_pipeline as pipeline
from studio import characters
from studio.creative import creative_fingerprint
from studio.native_character import NativeCharacterError
from studio.workspace import WorkspaceError


class NativePipelineTests(unittest.TestCase):
    def _count_validations(self, actions, cached):
        calls = []

        def fake_validate(path):
            calls.append(path)
            return {"projects": {}, "controls": {}}

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "characters/tutor/03_animation/original-look/native").mkdir(parents=True)
            with patch.object(pipeline, "validate_native_registration", fake_validate):
                if cached:
                    with pipeline.request_cache():
                        statuses = [pipeline.render_status(root, "tutor", "original-look", "front", a, "neutral") for a in actions]
                else:
                    statuses = [pipeline.render_status(root, "tutor", "original-look", "front", a, "neutral") for a in actions]
        self.assertTrue(all(s["error"] == "native view is not registered" for s in statuses))
        return len(calls)

    def test_request_cache_validates_each_manifest_once(self):
        self.assertEqual(self._count_validations(["idle", "wave", "point"], cached=True), 1)

    def test_without_request_cache_each_status_revalidates(self):
        self.assertEqual(self._count_validations(["idle", "wave"], cached=False), 2)

    def test_encoder_and_compositor_changes_invalidate_cache_key(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            native = root / "characters/tutor/03_animation/original-look/native"
            native.mkdir(parents=True)
            (native / "manifest.json").write_text("{}")
            (native / "front.sif").write_text("<canvas/>")
            synfig, ffmpeg = root / "synfig", root / "ffmpeg"
            synfig.write_bytes(b"synfig-1.4.5")
            ffmpeg.write_bytes(b"encoder-one")
            manifest = {"projects": {"front": {"path": "front.sif"}},
                        "controls": {"bindings": {"front": {"idle": {"neutral": {"project": "front.sif"}}}}},
                        "settings": {"width": 32, "height": 32, "fps": 24, "frame_count": 2}}
            resolve = lambda _explicit, _env, executable: str(synfig if executable == "synfig" else ffmpeg)
            original_hash = pipeline._hash
            code_revision = ["code-one"]
            def hashed(path):
                return code_revision[0] if Path(path) == Path(pipeline.__file__) else original_hash(path)
            with patch.object(pipeline, "validate_native_registration", return_value=manifest), \
                 patch.object(pipeline, "_resolve_tool", side_effect=resolve), \
                 patch.object(pipeline, "_version", return_value="synfig 1.4.5"), \
                 patch.object(pipeline, "_hash", side_effect=hashed):
                first = pipeline._selection(root, "tutor", "original-look", "front", "idle", "neutral")[-1]
                ffmpeg.write_bytes(b"encoder-two")
                second = pipeline._selection(root, "tutor", "original-look", "front", "idle", "neutral")[-1]
                code_revision[0] = "code-two"
                third = pipeline._selection(root, "tutor", "original-look", "front", "idle", "neutral")[-1]
                (native / "front-talk.sif").write_text("<canvas/>")
                manifest["projects"]["front-talk"] = {"path": "front-talk.sif"}
                manifest["controls"]["bindings"]["front"]["talk"] = {"neutral": {"project": "front-talk.sif"}}
                with self.assertRaisesRegex(NativeCharacterError, "talk needs registered approved audio"):
                    pipeline._selection(root, "tutor", "original-look", "front", "talk", "neutral")
            self.assertEqual(len({first, second, third}), 3)

    def test_candidate_registration_requires_exact_hashes_and_activation_requires_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pack = root / "characters/tutor/03_animation/original-look"
            candidate = pack / "calibration/native"
            candidate.mkdir(parents=True)
            (pack / "variant.json").write_text("{}")
            (candidate / "manifest.json").write_text('{"schema":1}')
            (candidate / "front.sif").write_text("<canvas/>")
            revision = pipeline._hash(pack / "variant.json")
            source = pipeline._hash(candidate / "manifest.json")
            with patch("studio.native_character.validate_native_registration", return_value={}), \
                 patch("studio.creative._validate_rig_evidence"), \
                 patch.object(characters, "_registered_variant", return_value={}):
                with self.assertRaises(WorkspaceError):
                    characters.register_native_candidate(root, "tutor", "original-look", revision, "0" * 64)
                result = characters.register_native_candidate(root, "tutor", "original-look", revision, source)
                self.assertEqual(result["state"], "draft")
                self.assertFalse((pack / "native").exists())
                self.assertTrue((pack / "native-candidate/manifest.json").is_file())
                with patch.object(characters, "creative_review_state", return_value={"state": "awaiting-review", "fingerprint": "revision"}):
                    with self.assertRaises(WorkspaceError):
                        characters.activate_native_candidate(root, "tutor", "original-look", "revision")
                with patch.object(characters, "creative_review_state", return_value={"state": "approved", "fingerprint": "revision"}):
                    activated = characters.activate_native_candidate(root, "tutor", "original-look", "revision")
                self.assertEqual(activated["state"], "active")
                self.assertEqual((pack / "native/manifest.json").read_bytes(), (pack / "native-candidate/manifest.json").read_bytes())
                prior = pack / "native/renders/front/idle/neutral"
                prior.mkdir(parents=True)
                (prior / "previous.mp4").write_bytes(b"previous clip")
                before = creative_fingerprint(root, "character", "tutor", "rig:original-look")
                (candidate / "manifest.json").write_text('{"schema":1,"revision":2}')
                with self.assertRaises(WorkspaceError):
                    characters.register_native_candidate(root, "tutor", "original-look", revision,
                        pipeline._hash(candidate / "manifest.json"), replace_revision=source)
                characters.register_native_candidate(root, "tutor", "original-look", revision,
                    pipeline._hash(candidate / "manifest.json"), replace_revision=source, confirm_replace=True)
                self.assertNotEqual(before, creative_fingerprint(root, "character", "tutor", "rig:original-look"))
                self.assertEqual((pack / "native/manifest.json").read_text(), '{"schema":1}')
                self.assertEqual((prior / "previous.mp4").read_bytes(), b"previous clip")
                self.assertTrue(list((pack / "native-history").glob("*/manifest.json")))
                with patch.object(characters, "creative_review_state", return_value={"state": "approved", "fingerprint": "new-revision"}):
                    characters.activate_native_candidate(root, "tutor", "original-look", "new-revision")
                self.assertIn(b'"revision":2', (pack / "native/manifest.json").read_bytes())
                self.assertEqual((prior / "previous.mp4").read_bytes(), b"previous clip")
                (candidate / "evidence-note.txt").write_text("new reviewed evidence")
                second_source = pipeline._hash(candidate / "manifest.json")
                characters.register_native_candidate(root, "tutor", "original-look", revision, second_source,
                    replace_revision=second_source, confirm_replace=True)
                with patch.object(characters, "creative_review_state", return_value={"state": "approved", "fingerprint": "evidence-revision"}):
                    characters.activate_native_candidate(root, "tutor", "original-look", "evidence-revision")
                self.assertEqual((pack / "native/evidence-note.txt").read_text(), "new reviewed evidence")
                self.assertEqual((prior / "previous.mp4").read_bytes(), b"previous clip")

    def test_validated_cache_and_failed_replacement_preserve_previous_clip(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            native = root / "characters/tutor/03_animation/original-look/native"
            native.mkdir(parents=True)
            project = native / "front.sif"
            project.write_text("<canvas/>")
            source = ["first"]
            selection = lambda *_: (native, {}, project, (32, 32, 24, 2), source[0])
            calls = []

            def render(_project, output, **_options):
                calls.append(source[0])
                output.mkdir()
                frames = []
                for index in range(2):
                    path = output / f"frame.{index:04d}.png"
                    Image.new("RGBA", (32, 32), (255, 0, 0, 0)).save(path)
                    frames.append({"file": path.name, "sha256": pipeline._hash(path)})
                return {"frame_count": 2, "frames": frames, "output_dir": str(output)}

            def encode(command, **_options):
                Path(command[-1]).write_bytes(b"valid-encoded-preview")
                return type("Result", (), {"returncode": 0, "stderr": ""})()

            with patch.object(pipeline, "_selection", side_effect=selection), \
                 patch.object(pipeline, "render_project", side_effect=render), \
                 patch.object(pipeline.subprocess, "run", side_effect=encode), \
                 patch.object(pipeline.shutil, "which", return_value="/usr/bin/ffmpeg"):
                first = pipeline.render_native(root, "tutor", "original-look", "front", "idle", "neutral")
                self.assertEqual(calls, ["first"])
                self.assertFalse(first["cached"])
                again = pipeline.render_native(root, "tutor", "original-look", "front", "idle", "neutral")
                self.assertTrue(again["cached"])
                self.assertEqual(calls, ["first"])
                source[0] = "second"
                status = pipeline.render_status(root, "tutor", "original-look", "front", "idle", "neutral")
                self.assertFalse(status["current"])
                self.assertEqual(status["clip"]["source_fingerprint"], "first")
                with patch.object(pipeline, "render_project", side_effect=NativeCharacterError("render failed")):
                    with self.assertRaisesRegex(NativeCharacterError, "render failed"):
                        pipeline.render_native(root, "tutor", "original-look", "front", "idle", "neutral")
                cancelled = threading.Event()
                def cancel_encode(command, **_options):
                    Path(command[-1]).write_bytes(b"new-preview")
                    cancelled.set()
                    return type("Result", (), {"returncode": 0, "stderr": ""})()
                with patch.object(pipeline, "render_project", side_effect=render), \
                     patch.object(pipeline.subprocess, "run", side_effect=cancel_encode):
                    with self.assertRaisesRegex(NativeCharacterError, "cancelled"):
                        pipeline.render_native(root, "tutor", "original-look", "front", "idle", "neutral",
                                               cancel_event=cancelled)
                self.assertTrue((root / first["path"] / "preview.mp4").is_file())
                self.assertEqual(json.loads((native / "renders/front/idle/neutral/current.json").read_text())["source_fingerprint"], "first")


if __name__ == "__main__":
    unittest.main()
