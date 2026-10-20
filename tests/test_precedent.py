"""Vendored precedent library (tools/precedent/README.md): the CLI finds its own library and answers queries."""
import subprocess, sys, unittest
from pathlib import Path

CLI = Path(__file__).resolve().parent.parent / "tools" / "precedent" / "precedent.py"


def run(*args):
    return subprocess.run([sys.executable, "-I", str(CLI), *args], capture_output=True, text=True, cwd="/")


class Precedent(unittest.TestCase):
    def test_stats_counts_every_row(self):  # run from / : the default library path must not depend on the working dir
        r = run("stats")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("716 rows", r.stdout)

    def test_query_returns_k_rows(self):
        r = run("query", "--beat", "hook", "--content", "ui", "--k", "3")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("top 3 of 716 rows", r.stdout)

    def test_bad_beat_is_usage_error(self):
        self.assertEqual(run("query", "--beat", "middle").returncode, 2)


if __name__ == "__main__":
    unittest.main()
