import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from studio.blender_character import (
    BlenderCharacterError,
    _validate_frames,
    _trusted_project_hash,
    render_project,
)


class BlenderCharacterTests(unittest.TestCase):
    def _fixture(self, root):
        project = root / "fixture.blend"
        project.write_bytes(b"pilot")
        binary = root / "blender-sleeper"
        binary.write_text(
            "#!/usr/bin/env python3\n"
            "import sys, time\n"
            "if '--version' in sys.argv:\n"
            " print('Blender 5.2.2 LTS'); raise SystemExit(0)\n"
            "sys.stdout.write('partial frame progress'); sys.stdout.flush()\n"
            "time.sleep(5)\n",
            encoding="utf-8",
        )
        binary.chmod(0o755)
        return project, binary

    def test_limits_fail_before_starting_renderer(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project, binary = self._fixture(root)
            for kwargs, message in (
                ({"frame_count": 901}, "900 frames"),
                ({"frame_count": 721}, "30 seconds"),
                ({"threads": 5}, "four renderer threads"),
                ({"max_memory_bytes": 4 * 1024**3 + 1}, "4 GiB"),
            ):
                with self.subTest(kwargs=kwargs), self.assertRaisesRegex(BlenderCharacterError, message):
                    render_project(project, root / "frames", width=1280, height=720,
                                   blender_bin=binary, **kwargs)

    def test_only_pinned_packed_fixture_is_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            project, binary = self._fixture(Path(folder))
            with self.assertRaisesRegex(BlenderCharacterError, "pinned packed synthetic fixture"):
                _trusted_project_hash(project)
            with self.assertRaisesRegex(BlenderCharacterError, "pinned packed synthetic fixture"):
                render_project(project, Path(folder) / "frames", width=32, height=32,
                               frame_count=1, blender_bin=binary)

    def test_partial_output_cannot_block_timeout_or_cancellation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project, binary = self._fixture(root)
            with patch('studio.blender_character._trusted_project_hash', return_value='test'):
                with self.assertRaisesRegex(BlenderCharacterError, "timed out"):
                    render_project(project, root / "timeout", width=32, height=32,
                                   frame_count=1, blender_bin=binary, timeout_seconds=0.1)
                cancel = threading.Event()
                timer = threading.Timer(0.1, cancel.set)
                timer.start()
                try:
                    with self.assertRaisesRegex(BlenderCharacterError, "cancelled"):
                        render_project(project, root / "cancelled", width=32, height=32,
                                       frame_count=1, blender_bin=binary, cancel_event=cancel)
                finally:
                    timer.cancel()

    def test_rgba_frame_validation_rejects_gaps_and_opaque_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            Image.new("RGBA", (8, 8), (255, 0, 0, 0)).save(root / "frame_0000.png")
            with self.assertRaisesRegex(BlenderCharacterError, "contiguous"):
                _validate_frames(root, 8, 8, 2)
            Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(root / "frame_0001.png")
            with self.assertRaisesRegex(BlenderCharacterError, "lost transparency"):
                _validate_frames(root, 8, 8, 2)

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project, binary = self._fixture(root)
            out = root / "frames"
            out.mkdir()
            (out / "current.png").write_bytes(b"valid existing production")
            with patch('studio.blender_character._trusted_project_hash', return_value='test'):
                with self.assertRaisesRegex(BlenderCharacterError, "must be empty"):
                    render_project(project, out, width=32, height=32,
                                   frame_count=1, blender_bin=binary)
            self.assertEqual((out / "current.png").read_bytes(), b"valid existing production")


if __name__ == "__main__":
    unittest.main()
