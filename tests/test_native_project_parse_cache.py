import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from studio import native_character as native


class NativeProjectParseCacheTest(unittest.TestCase):
    def setUp(self):
        with native._PROJECT_IMPORT_CACHE_LOCK:
            native._PROJECT_IMPORT_CACHE.clear()

    def test_exact_bytes_cached_but_source_assets_and_confinement_stay_fresh(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            project = folder / "rig.sif"
            art = folder / "art.png"
            art.write_bytes(b"first")
            project.write_text('<canvas fps="24"><layer type="import"><param name="filename">'
                               '<string>art.png</string></param></layer></canvas>')
            with patch.object(native.ET, "fromstring", wraps=native.ET.fromstring) as parse:
                first = native.project_dependencies(project)
                self.assertEqual(first, native.project_dependencies(project))
                self.assertEqual(parse.call_count, 1)
                art.write_bytes(b"second")
                self.assertNotEqual(first, native.project_dependencies(project))
                self.assertEqual(parse.call_count, 1)
                project.write_text(project.read_text().replace('fps="24"', 'fps="0"'))
                with self.assertRaisesRegex(native.NativeCharacterError, "fps must be positive"):
                    native.project_dependencies(project)
                self.assertEqual(parse.call_count, 2)
                project.write_text(project.read_text().replace('fps="0"', 'fps="24"'))
                art.unlink()
                outside = folder.parent / (folder.name + "-outside.png")
                try:
                    outside.write_bytes(b"outside")
                    art.symlink_to(outside)
                    with self.assertRaisesRegex(native.NativeCharacterError, "escapes"):
                        native.project_dependencies(project)
                finally:
                    outside.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
