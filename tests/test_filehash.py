import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from studio import filehash
from studio.filehash import file_sha256


class FileHashTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / "data.bin"
        self.path.write_bytes(b"abc")

    def tearDown(self):
        self.folder.cleanup()

    def test_matches_hashlib(self):
        self.assertEqual(file_sha256(self.path), hashlib.sha256(b"abc").hexdigest())

    def test_second_call_does_not_reread(self):
        real_open, opens = Path.open, []

        def counting_open(path, *args, **kwargs):
            if path == self.path:
                opens.append(path)
            return real_open(path, *args, **kwargs)

        with patch.object(Path, "open", counting_open):
            first, second = file_sha256(self.path), file_sha256(str(self.path))
        self.assertEqual(first, second)
        self.assertEqual(len(opens), 1)

    def test_content_change_with_same_size_rehashes(self):
        before = file_sha256(self.path)
        stat = self.path.stat()
        self.path.write_bytes(b"bbb")
        os.utime(self.path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 10**9))
        self.assertNotEqual(file_sha256(self.path), before)
        self.assertEqual(file_sha256(self.path), hashlib.sha256(b"bbb").hexdigest())


    def test_eviction_keeps_recent_entries(self):
        others = [Path(self.folder.name) / f"f{i}.bin" for i in range(3)]
        for index, path in enumerate(others):
            path.write_bytes(bytes([index]))
        with patch.object(filehash, "_LIMIT", 2), patch.dict(filehash._CACHE, clear=True):
            for path in others:
                file_sha256(path)
            self.assertLessEqual(len(filehash._CACHE), 2)
            self.assertIn(str(others[-1]), {key[0] for key in filehash._CACHE})

    def test_returns_hash_even_when_entry_is_evicted_at_once(self):
        with patch.object(filehash, "_LIMIT", 0), patch.dict(filehash._CACHE, clear=True):
            self.assertEqual(file_sha256(self.path), hashlib.sha256(b"abc").hexdigest())


if __name__ == "__main__":
    unittest.main()
