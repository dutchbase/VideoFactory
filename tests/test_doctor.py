import collections
import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import doctor  # noqa: E402

GOOD = doctor.row("fake", True, "fine", "")


def run_main(**fakes) -> tuple[int, str]:
    """Run doctor.main() with every check replaced by a fake that passes, except the ones given."""
    names = ("python_version", "chromium", "fonts", "brand", "whisper", "hyperframes", "earshot", "tesseract")
    patches = [mock.patch.object(doctor, n, return_value=fakes.get(n, GOOD)) for n in names]
    patches += [mock.patch.object(doctor, "package", return_value=GOOD), mock.patch.object(doctor, "program", return_value=GOOD),
                mock.patch.object(doctor, "key", return_value=GOOD)]
    out = io.StringIO()
    with contextlib.ExitStack() as stack, contextlib.redirect_stdout(out):
        for p in patches:
            stack.enter_context(p)
        code = doctor.main()
    return code, out.getvalue()


class Doctor(unittest.TestCase):
    def test_all_good_exits_zero(self):
        code, text = run_main()
        self.assertEqual(code, 0)
        self.assertIn("All required parts are OK", text)

    def test_missing_required_part_exits_one_with_a_fix(self):
        code, text = run_main(chromium=doctor.row("Chromium for Playwright", False, "no browser", "run the install"))
        self.assertEqual(code, 1)
        self.assertIn("MISSING", text)
        self.assertIn("fix: run the install", text)

    def test_missing_optional_part_still_exits_zero(self):
        code, text = run_main(whisper=doctor.row("Whisper", False, "not installed", "pip install it", required=False))
        self.assertEqual(code, 0)
        self.assertIn("optional", text)
        self.assertIn("fix: pip install it", text)

    def test_old_python_is_missing(self):
        with mock.patch.object(doctor.sys, "version_info", collections.namedtuple("V", "major minor micro")(3, 11, 0)):
            self.assertEqual(doctor.python_version()["status"], doctor.MISSING)

    def test_row_status(self):
        self.assertEqual(doctor.row("a", True, "", "", True)["status"], doctor.OK)
        self.assertEqual(doctor.row("a", False, "", "fix", True)["status"], doctor.MISSING)
        self.assertEqual(doctor.row("a", False, "", "fix", False)["status"], doctor.OPTIONAL)

    def test_key_is_found_in_env_file_and_never_printed(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / ".env").write_text('ELEVEN_API_KEY="sk_secretvalue"\n')
            with mock.patch.object(doctor, "ROOT", Path(folder)), mock.patch.dict(os.environ, {}, clear=True):
                found = doctor.key("ElevenLabs", ("ELEVENLABS_API_KEY", "ELEVEN_API_KEY"))
                missing = doctor.key("Pexels", ("PEXELS_API_KEY",))
        self.assertEqual((found["status"], found["detail"]), (doctor.OK, "found"))
        self.assertEqual(missing["status"], doctor.OPTIONAL)
        self.assertNotIn("sk_secretvalue", str(found))

    def test_missing_program_is_reported(self):
        with mock.patch.object(doctor.shutil, "which", return_value=None):
            r = doctor.program("ffmpeg", "install it")
        self.assertEqual((r["status"], r["fix"]), (doctor.MISSING, "install it"))


if __name__ == "__main__":
    unittest.main()
