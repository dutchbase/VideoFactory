import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from studio import agent_runs
from studio.jobs import create_request
from studio.workspace import WorkspaceError


def _alive(pid):
    try: os.kill(pid, 0)
    except ProcessLookupError: return False
    stat = Path(f"/proc/{pid}/stat")
    return stat.exists() and stat.read_text().rsplit(") ", 1)[1].split()[0] != "Z"


class AgentRunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "videos/demo").mkdir(parents=True)
        (self.root / "videos/demo/project.json").write_text(json.dumps({"brand": "videofactory"}))
        create_request(self.root, "demo", "script", "Write the script.", "", "req-one")

    def tearDown(self):
        self.temp.cleanup()

    def record(self, ident="req-one"):
        return json.loads((self.root / f".studio/requests/{ident}.json").read_text())

    def run_with(self, code, mode="auto", ident="req-one"):
        with patch.object(agent_runs, "agent_argv", return_value=[sys.executable, "-c", code]):
            return agent_runs.start_run(self.root, ident, mode)

    def wait_done(self, ident="req-one"):
        for _ in range(500):
            record = self.record(ident)
            if record["state"] != "running": return record
            time.sleep(.02)
        self.fail("agent run did not finish")

    def test_auto_run_zero_exit_without_ready_output_fails(self):
        started = self.run_with("print('wrote script')")
        self.assertEqual(started["state"], "running")
        done = self.wait_done()
        self.assertEqual(done["state"], "failed")
        self.assertIn("inputs changed", done["note"])
        self.assertEqual(done["run"]["mode"], "auto")

    def test_auto_run_nonzero_exit_fails(self):
        self.run_with("import sys; sys.exit(3)")
        self.assertEqual(self.wait_done()["state"], "failed")

    def test_agent_env_is_guarded(self):
        self.run_with("import os; print(os.environ['WAYLAND_DISPLAY'], os.environ['HYPRLAND_INSTANCE_SIGNATURE'], repr(os.environ['DISPLAY']))")
        self.wait_done()
        self.assertIn("omabox-guard omabox-guard ''", agent_runs.log_tail(self.root, "req-one"))

    def test_run_is_idempotent(self):
        with patch.object(agent_runs, "agent_argv", return_value=[sys.executable, "-c", "import time; time.sleep(1)"]) as argv:
            first = agent_runs.start_run(self.root, "req-one", "auto")
            second = agent_runs.start_run(self.root, "req-one", "auto")
        self.assertEqual(argv.call_count, 1)
        self.assertEqual(first["run"]["pid"], second["run"]["pid"])
        self.wait_done()

    def test_run_refuses_while_job_active(self):
        (self.root / ".studio/jobs").mkdir(parents=True)
        (self.root / ".studio/jobs/busy.json").write_text(json.dumps({"id": "busy", "slug": "other", "state": "running"}))
        with self.assertRaises(WorkspaceError) as error:
            self.run_with("pass")
        self.assertEqual(error.exception.code, "busy")
        self.assertEqual(self.record()["state"], "waiting-for-agent")

    def test_cancel_kills_process_group(self):
        code = ("import subprocess, sys, time; "
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
                "print('child', child.pid, flush=True); time.sleep(60)")
        started = self.run_with(code)
        for _ in range(200):
            if "child" in agent_runs.log_tail(self.root, "req-one"): break
            time.sleep(.02)
        child = int(agent_runs.log_tail(self.root, "req-one").split("child", 1)[1].split()[0])
        done = agent_runs.cancel_run(self.root, "req-one")
        self.assertEqual(done["state"], "cancelled")
        self.assertIn("partial files may remain", done["note"])
        deadline = time.monotonic() + 12
        while (_alive(started["run"]["pid"]) or _alive(child)) and time.monotonic() < deadline:
            time.sleep(.05)
        self.assertFalse(_alive(started["run"]["pid"]))
        self.assertFalse(_alive(child))

    def test_recover_marks_dead_run_failed(self):
        path = self.root / ".studio/requests/req-one.json"
        record = self.record()
        record.update(state="running", agent="claude (studio)", run={"mode": "auto", "pid": 2 ** 22 + 7, "process_start": "1", "started_at": "x"})
        path.write_text(json.dumps(record))
        agent_runs.recover(self.root)
        recovered = self.record()
        self.assertEqual(recovered["state"], "failed")
        self.assertEqual(recovered["note"], "Interrupted when the studio restarted.")

    def test_recover_spares_run_owned_by_live_server(self):
        import subprocess
        agent = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
        server = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            record = self.record()
            record.update(state="running", agent="claude (studio)", run={
                "mode": "auto", "pid": agent.pid, "process_start": agent_runs._process_start(agent.pid), "started_at": "x",
                "server": {"pid": server.pid, "start": agent_runs._process_start(server.pid)}})
            (self.root / ".studio/requests/req-one.json").write_text(json.dumps(record))
            agent_runs.recover(self.root)
            self.assertEqual(self.record()["state"], "running")
            self.assertIsNone(agent.poll())
        finally:
            agent.kill(); server.kill(); agent.wait(); server.wait()

    def test_auto_run_records_its_server(self):
        started = self.run_with("pass")
        self.assertEqual(started["run"]["server"]["pid"], os.getpid())
        self.wait_done()

    def test_auto_agent_cannot_run_paid_or_server_commands(self):
        argv = agent_runs.agent_argv(self.root, self.record(), "auto")
        denied = argv[argv.index("--disallowedTools") + 1:]
        for command in ("speak", "studio", "studio-job"):
            self.assertIn(f"Bash(.venv/bin/python anim.py {command}:*)", denied)

    def test_invalid_utf8_output_still_finishes(self):
        self.run_with("import sys; sys.stdout.buffer.write(b'bad \\xff byte\\n')")
        self.assertEqual(self.wait_done()["state"], "failed")

    def test_run_finishes_when_grandchild_holds_stdout(self):
        code = ("import subprocess, sys; "
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); print('child', child.pid, flush=True)")
        self.run_with(code)
        done = self.wait_done()
        self.assertEqual(done["state"], "failed")
        child = int(agent_runs.log_tail(self.root, "req-one").split("child", 1)[1].split()[0])
        deadline = time.monotonic() + 12
        while _alive(child) and time.monotonic() < deadline: time.sleep(.05)
        self.assertFalse(_alive(child))

    def test_guided_run_is_blocked(self):
        with self.assertRaisesRegex(WorkspaceError, "copy the handoff"):
            self.run_with("pass", mode="guided")
