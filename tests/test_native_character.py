import json
import os
import threading
import tempfile
import unittest
from pathlib import Path

from studio.native_character import (
    NativeCharacterError,
    capabilities,
    cue_at,
    project_dependencies,
    require_supported_shapes,
    render_project,
    validate_correction_intervals,
    validate_native_registration,
    validate_rhubarb_cues,
    write_render_manifest,
)


class NativeCharacterTests(unittest.TestCase):
    def test_raw_rhubarb_cues_keep_half_open_timing(self):
        raw = {
            "mouthCues": [
                {"start": 0.0, "end": 0.25, "value": "X"},
                {"start": 0.25, "end": 0.75, "value": "A"},
            ]
        }

        cues = validate_rhubarb_cues(raw, duration=0.75)

        self.assertEqual(cues, raw["mouthCues"])
        self.assertEqual(cues[0]["end"], cues[1]["start"])

    def test_rhubarb_rejects_unknown_shape_invalid_or_overlapping_intervals(self):
        raw_cues = [
            [{"start": 0.0, "end": 0.5, "value": "Z"}],
            [{"start": 0.5, "end": 0.5, "value": "A"}],
            [{"start": -0.1, "end": 0.5, "value": "X"}],
            [{"start": 0.0, "end": 1.1, "value": "X"}],
            [
                {"start": 0.0, "end": 0.6, "value": "X"},
                {"start": 0.5, "end": 0.75, "value": "A"},
            ],
        ]
        for cues in raw_cues:
            with self.subTest(cues=cues), self.assertRaises(NativeCharacterError):
                validate_rhubarb_cues({"mouthCues": cues}, duration=1.0)

    def test_cue_validators_reject_nonfinite_interval_times(self):
        for cue in (
            {"start": float("nan"), "end": 0.2, "value": "A"},
            {"start": 0.0, "end": float("nan"), "value": "A"},
        ):
            with self.subTest(cue=cue), self.assertRaisesRegex(NativeCharacterError, "finite number"):
                validate_rhubarb_cues({"mouthCues": [cue]}, duration=1.0)
        with self.assertRaisesRegex(NativeCharacterError, "finite number"):
            validate_correction_intervals(
                [{"start": 0.0, "end": float("nan"), "value": "X"}], duration=1.0
            )

    def test_corrections_are_separate_non_overlapping_half_open_intervals(self):
        corrections = [
            {"start": 0.2, "end": 0.4, "value": "B"},
            {"start": 0.4, "end": 0.6, "value": "C"},
        ]
        self.assertEqual(validate_correction_intervals(corrections, duration=1.0), corrections)
        with self.assertRaises(NativeCharacterError):
            validate_correction_intervals(
                [
                    {"start": 0.2, "end": 0.5, "value": "B"},
                    {"start": 0.4, "end": 0.6, "value": "C"},
                ],
                duration=1.0,
            )

    def test_cue_sampling_uses_half_open_boundaries_and_corrections_override(self):
        raw = {
            "mouthCues": [
                {"start": 0.0, "end": 0.25, "value": "X"},
                {"start": 0.25, "end": 0.75, "value": "A"},
                {"start": 0.8, "end": 0.9, "value": "C"},
            ]
        }
        corrections = [{"start": 0.3, "end": 0.4, "value": "B"}]

        self.assertEqual(cue_at(0.0, raw, corrections, duration=1.0), "X")
        self.assertEqual(cue_at(0.25, raw, corrections, duration=1.0), "A")
        self.assertEqual(cue_at(0.3, raw, corrections, duration=1.0), "B")
        self.assertEqual(cue_at(0.4, raw, corrections, duration=1.0), "A")
        self.assertEqual(cue_at(0.75, raw, corrections, duration=1.0), "X")
        self.assertEqual(cue_at(0.8, raw, corrections, duration=1.0), "C")
        self.assertEqual(cue_at(1.0, raw, corrections, duration=1.0), "X")
        self.assertEqual(raw["mouthCues"][1]["value"], "A")
        self.assertEqual(corrections[0]["value"], "B")
        for invalid_time in (float("nan"), -0.01, 1.01):
            with self.subTest(time=invalid_time), self.assertRaises(NativeCharacterError):
                cue_at(invalid_time, raw, corrections, duration=1.0)

    def test_missing_authored_visemes_block_rig_render(self):
        with self.assertRaisesRegex(NativeCharacterError, "missing authored mouth states: A"):
            require_supported_shapes([{"start": 0.0, "end": 0.2, "value": "A"}], {"closed"})
        require_supported_shapes([{"start": 0.0, "end": 0.2, "value": "X"}], {"closed"})

    def test_manifest_hashes_relative_imports_and_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            native = root / "native"
            native.mkdir()
            (native / "art.png").write_bytes(b"bitmap")
            (native / "cues.raw.json").write_text('{"mouthCues":[]}', encoding="utf-8")
            (native / "reference.wav").write_bytes(b"wav")
            (native / "source.mp3").write_bytes(b"source mp3")
            (native / "dialog.txt").write_text("approved transcript", encoding="utf-8")
            (native / "corrections.json").write_text("[]", encoding="utf-8")
            project = native / "scene.sif"
            project.write_text(
                '<canvas fps="24"><layer type="import"><param name="filename"><string>art.png</string></param></layer></canvas>',
                encoding="utf-8",
            )
            project_right = native / "scene-right.sif"
            project_right.write_text(project.read_text(encoding="utf-8"), encoding="utf-8")
            manifest = write_render_manifest(
                {"front": project, "three-quarter-right": project_right},
                native / "manifest.json",
                settings={"width": 1280, "height": 720, "fps": 24},
                capabilities_result={"renderer": {"version": "Synfig 1.4.5", "path": "/tmp/synfig"}},
                controls={"switch": ["open", "closed"]},
                cues_path=native / "cues.raw.json",
                audio_path=native / "reference.wav",
                source_audio_path=native / "source.mp3",
                dialog_path=native / "dialog.txt",
                corrections_path=native / "corrections.json",
                recognition={"tool": "Rhubarb Lip Sync", "version": "1.14.0", "recognizer": "pocketSphinx", "threads": 1},
            )
            self.assertEqual(
                manifest["projects"]["front"]["linked_assets"],
                {"art.png": {"sha256": __import__("hashlib").sha256(b"bitmap").hexdigest()}},
            )
            self.assertEqual(project_dependencies(project), [{"path": "art.png", "sha256": manifest["projects"]["front"]["linked_assets"]["art.png"]["sha256"]}])
            verified = validate_native_registration(native / "manifest.json")
            self.assertEqual(verified["schema"], 1)
            self.assertEqual(set(verified["projects"]), {"front", "three-quarter-right"})
            self.assertEqual(verified["audio"]["path"], "reference.wav")
            self.assertEqual(verified["source_audio"]["path"], "source.mp3")
            self.assertEqual(verified["dialog"]["path"], "dialog.txt")
            self.assertEqual(verified["corrections"]["path"], "corrections.json")
            self.assertEqual(verified["recognition"]["threads"], 1)
            self.assertNotIn("path", verified["capabilities"]["renderer"])

            (native / "dialog.txt").write_text("changed transcript", encoding="utf-8")
            with self.assertRaisesRegex(NativeCharacterError, "dialog hash is stale"):
                validate_native_registration(native / "manifest.json")

            project.write_text(
                '<canvas fps="24"><layer type="import"><param name="filename"><string>../elsewhere.png</string></param></layer></canvas>',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(NativeCharacterError, "must stay inside"):
                write_render_manifest(
                    project,
                    native / "manifest.json",
                    settings={},
                    capabilities_result={},
                )

    def test_native_render_limits_duration_before_tool_lookup(self):
        with tempfile.TemporaryDirectory() as folder:
            project = Path(folder) / "scene.sif"
            project.write_text('<canvas fps="24"/>', encoding="utf-8")
            with self.assertRaisesRegex(NativeCharacterError, "900 frames and 30 seconds"):
                render_project(project, Path(folder) / "out", width=1280, height=720, frame_count=901)

    def test_begin_frame_validation_preserves_shot_duration_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            project = Path(folder) / "scene.sif"
            project.write_text('<canvas fps="24"/>')
            for start in (-1, 1.5, True):
                with self.assertRaisesRegex(NativeCharacterError, "begin_frame"):
                    render_project(project, Path(folder) / "out", width=32, height=32,
                                   frame_count=1, begin_frame=start)
            with self.assertRaisesRegex(NativeCharacterError, "900 frames and 30 seconds"):
                render_project(project, Path(folder) / "out", width=32, height=32,
                               frame_count=1, begin_frame=720)

    def test_begin_and_end_frames_are_passed_to_renderer(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            binary = root / "synfig-test"
            binary.write_text(
                "#!/usr/bin/env python3\n"
                "import sys, json\n"
                "from pathlib import Path\n"
                "if '--version' in sys.argv: print('Synfig 1.4.5'); raise SystemExit(0)\n"
                "Path('arguments.json').write_text(json.dumps(sys.argv))\n"
                "print('intentional stop'); raise SystemExit(1)\n")
            binary.chmod(0o755)
            project = root / "scene.sif"
            project.write_text('<canvas fps="24"/>')
            with self.assertRaisesRegex(NativeCharacterError, "Synfig failed"):
                render_project(project, root / "out", width=32, height=32, frame_count=2,
                               begin_frame=120, synfig_bin=binary)
            arguments = json.loads((root / "arguments.json").read_text())
            self.assertEqual(arguments[arguments.index('--begin-time') + 1], '120f')
            self.assertEqual(arguments[arguments.index('--end-time') + 1], '121f')

    def test_synfig_worker_pool_minimum_is_enforced_before_tool_lookup(self):
        with tempfile.TemporaryDirectory() as folder:
            project = Path(folder) / "scene.sif"
            project.write_text('<canvas fps="24"/>', encoding="utf-8")
            with self.assertRaisesRegex(NativeCharacterError, "threads must be between 2 and 4"):
                render_project(project, Path(folder) / "out", width=1280, height=720, frame_count=1, threads=1)

    def test_existing_render_output_is_preserved_and_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = root / "scene.sif"
            project.write_text('<canvas fps="24"/>', encoding="utf-8")
            output = root / "out"
            output.mkdir()
            previous = output / "frame.0000.png"
            previous.write_bytes(b"previous valid render")

            with self.assertRaisesRegex(NativeCharacterError, "must be empty"):
                render_project(project, output, width=32, height=32, frame_count=1)

            self.assertEqual(previous.read_bytes(), b"previous valid render")

    def test_ffmpeg_capability_uses_its_single_dash_version_flag(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = Path(folder) / "ffmpeg"
            binary.write_text(
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "if sys.argv[1:] == ['-version']:\n print('ffmpeg version test-build'); raise SystemExit(0)\n"
                "print('Unrecognized option --version', file=sys.stderr); raise SystemExit(1)\n",
                encoding="utf-8",
            )
            binary.chmod(0o755)

            result = capabilities(ffmpeg_bin=binary)

            self.assertEqual(result["audio_converter"]["version"], "ffmpeg version test-build")

    def _sleeping_renderer(self, folder):
        binary = Path(folder) / "synfig-sleeper"
        binary.write_text(
            "#!/usr/bin/env python3\n"
            "import sys, time\n"
            "if '--version' in sys.argv:\n print('Synfig 1.4.5'); raise SystemExit(0)\n"
            "sys.stdout.write('partial progress without newline'); sys.stdout.flush()\n"
            "time.sleep(5)\n",
            encoding="utf-8",
        )
        binary.chmod(0o755)
        project = Path(folder) / "scene.sif"
        project.write_text('<canvas fps="24"/>', encoding="utf-8")
        return binary, project

    def test_partial_renderer_output_does_not_block_timeout_or_cleanup(self):
        with tempfile.TemporaryDirectory() as folder:
            binary, project = self._sleeping_renderer(folder)
            with self.assertRaisesRegex(NativeCharacterError, "timed out"):
                render_project(
                    project,
                    Path(folder) / "out",
                    width=32,
                    height=32,
                    frame_count=1,
                    synfig_bin=binary,
                    timeout_seconds=0.1,
                )

    def test_partial_renderer_output_does_not_block_cancellation(self):
        with tempfile.TemporaryDirectory() as folder:
            binary, project = self._sleeping_renderer(folder)
            cancel = threading.Event()
            timer = threading.Timer(0.1, cancel.set)
            timer.start()
            try:
                with self.assertRaisesRegex(NativeCharacterError, "cancelled"):
                    render_project(
                        project,
                        Path(folder) / "out",
                        width=32,
                        height=32,
                        frame_count=1,
                        synfig_bin=binary,
                        timeout_seconds=10,
                        cancel_event=cancel,
                    )
            finally:
                timer.cancel()


if __name__ == "__main__":
    unittest.main()
