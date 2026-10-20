import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".claude/skills/ui-ux-pro-max/scripts/search.py"


def run(*args):
    # -I would drop the script folder from sys.path, and search.py imports its siblings.
    # -E -s -B ignore env vars and user site-packages and write no .pyc files.
    return subprocess.run([sys.executable, "-E", "-s", "-B", str(SCRIPT), *args],
                          capture_output=True, text=True, timeout=60, cwd=ROOT)


class DesignLookupTest(unittest.TestCase):
    def test_typography_json(self):
        r = run("friendly modern sans", "--domain", "typography", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(json.loads(r.stdout)["results"])

    def test_design_system(self):
        r = run("environmental consultancy permits", "--design-system")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("olor", r.stdout)

    def test_no_match_ok(self):
        self.assertEqual(run("zzqxv", "--domain", "style").returncode, 0)


if __name__ == "__main__":
    unittest.main()
