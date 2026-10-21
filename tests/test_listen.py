import contextlib, io, json, os, stat, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import anim

STUB = """#!/usr/bin/env bash
echo "$@" >> "$STUB_LOG"
if [ "$STUB_FAIL" = 1 ]; then echo "earshot timeline: error: no audio stream" >&2; exit 1; fi
echo "stub says $3"
"""


class Listen(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.vdir = self.root / "videos" / "videofactory" / "demo"
        (self.vdir / "03_cues").mkdir(parents=True)
        (self.vdir / "05_render").mkdir()
        (self.vdir / "project.json").write_text(json.dumps({"brand": "videofactory"}))
        (self.vdir / "03_cues" / "cues.json").write_text(json.dumps(
            {"cueList": [{"id": "a", "start": 1.0, "end": 2.5}, {"id": "b", "start": 2.5, "end": 4.0}]}))
        self.mp4 = self.vdir / "05_render" / "demo.mp4"
        self.mp4.write_bytes(b"x")
        self.py = self.root / "tools" / "earshot" / ".venv" / "bin" / "python"
        self.py.parent.mkdir(parents=True)
        self.py.write_text(STUB)
        self.py.chmod(self.py.stat().st_mode | stat.S_IXUSR)
        self.log = self.root / "stub.log"
        env = {"STUB_LOG": str(self.log), "STUB_FAIL": "0"}
        for p in [patch.object(anim, "ROOT", self.root), patch.object(anim, "VIDEOS", self.root / "videos"),
                  patch.object(anim, "EARSHOT_PY", self.py), patch.dict(os.environ, env)]:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def run_listen(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            anim.cmd_listen(type("A", (), {"slug": "videofactory/demo"}))
        return out.getvalue()

    def fails_with(self):
        """Run listen expecting die(); return what it printed to stderr."""
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit):
            self.run_listen()
        return err.getvalue()

    def test_not_installed_says_run_setup(self):
        self.py.unlink()
        self.assertIn("tools/setup_earshot.sh", self.fails_with())

    def test_missing_render_says_render_first(self):
        self.mp4.unlink()
        self.assertIn("render", self.fails_with())
        self.assertFalse(self.log.exists())

    def test_writes_listen_md_with_timeline_and_measure(self):
        self.run_listen()
        md = (self.vdir / "05_render" / "listen.md").read_text()
        self.assertIn("## Timeline", md)
        self.assertIn("## Measure", md)
        self.assertIn("stub says", md)
        calls = self.log.read_text().splitlines()
        self.assertEqual(len(calls), 2)
        self.assertIn("--fresh", calls[0])
        self.assertIn("--cues 1.0,2.5", calls[0])

    def test_passes_effect_times_when_cues_have_effects(self):
        # earshot must check that each effect lands, so it gets the effect times (cue start + @offset), not the cue starts
        (self.vdir / "03_cues" / "cues.json").write_text(json.dumps(
            {"cueList": [{"id": "a", "start": 1.0, "end": 2.5, "sfx": ["pop@0.4", "tick@0.4 0.5"]},
                         {"id": "b", "start": 2.5, "end": 4.0, "sfx": ["whoosh"]}]}))
        self.run_listen()
        self.assertIn("--cues 1.4,2.5", self.log.read_text().splitlines()[0])
        self.assertIn("Effect times passed to earshot: 1.40, 2.50", (self.vdir / "05_render" / "listen.md").read_text())

    def test_failure_shows_first_stderr_line_and_leaves_no_file(self):
        os.environ["STUB_FAIL"] = "1"
        self.assertIn("earshot timeline: error: no audio stream", self.fails_with())
        self.assertFalse((self.vdir / "05_render" / "listen.md").exists())

    def test_download_notice_printed_once(self):
        self.assertIn("1.4 GB", self.run_listen())
        (self.root / "tools" / "earshot" / ".cache" / "hf").mkdir(parents=True)
        self.assertNotIn("1.4 GB", self.run_listen())


if __name__ == "__main__":
    unittest.main()
