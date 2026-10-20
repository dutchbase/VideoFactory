import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import capture


class Pure(unittest.TestCase):
    def test_parse_ok(self):
        opts, steps = capture.parse_steps('url: http://x\nmask: .a, .b\n---\n# note\nclick text="Go"\ntype #q "va jobs"\nwait 1.5\nshot home\n')
        self.assertEqual(opts, {"url": "http://x", "mask": ".a, .b"})
        self.assertEqual(steps, [("click", ['text=Go'], None), ("type", ["#q", "va jobs"], None), ("wait", ["1.5"], None), ("shot", ["home"], None)])

    def test_breakpoints(self):
        self.assertEqual(capture.size("mobile"), (390, 844))
        self.assertEqual(capture.size("1000x700"), (1000, 700))
        with self.assertRaises(ValueError):
            capture.size("phablet")
        self.assertEqual(capture.breakpoints({}, None), ["laptop"])
        self.assertEqual(capture.breakpoints({"breakpoints": "mobile, desktop"}, None), ["mobile", "desktop"])
        self.assertEqual(capture.breakpoints({"breakpoints": "mobile"}, "all"), list(capture.BREAKPOINTS))
        with self.assertRaises(ValueError):
            capture.breakpoints({}, "mobile,phablet")

    def test_step_prefix_and_suffix(self):
        _, steps = capture.parse_steps("---\n@mobile,tablet click .menu\nshot a\n")
        self.assertEqual(steps[0], ("click", [".menu"], ("mobile", "tablet")))
        self.assertEqual(capture.steps_for(steps, "mobile"), [("click", [".menu"]), ("shot", ["a"])])
        self.assertEqual(capture.steps_for(steps, "desktop"), [("shot", ["a"])])
        with self.assertRaises(ValueError):
            capture.parse_steps("---\n@phablet click .x\n")
        self.assertEqual(capture.suffix("jobs", ["laptop"], "laptop"), "jobs")
        self.assertEqual(capture.suffix("jobs", ["mobile", "desktop"], "mobile"), "jobs-mobile")

    def test_parse_errors_name_the_line(self):
        with self.assertRaisesRegex(ValueError, "line 2: unknown step 'fly'"):
            capture.parse_steps("---\nfly 1\n")
        with self.assertRaisesRegex(ValueError, "line 2: 'type' takes 2"):
            capture.parse_steps("---\ntype #q\n")
        with self.assertRaisesRegex(ValueError, "line 1: expected"):
            capture.parse_steps("click x\n")

    def test_password_refused(self):  # Review Focus 4
        with self.assertRaisesRegex(ValueError, "password"):
            capture.parse_steps('---\ntype input[type=password] "hunter2"\n')

    def test_mask_script(self):
        js = capture.mask_script(".a, .b")
        self.assertIn("blur(", js)
        self.assertIn(".a, .b", js)

    def test_auth_path(self):
        self.assertEqual(capture.auth_path("example-hub").name, "example-hub.json")
        for bad in ("../x", "A b", ""):
            with self.assertRaises(ValueError):
                capture.auth_path(bad)

    def test_log_capture_replaces_same_name(self):
        with tempfile.TemporaryDirectory() as t:
            a = Path(t)
            capture.log_capture(a, "home", "screenshot", "http://x", False)
            capture.log_capture(a, "demo", "recording", "http://y", True)
            capture.log_capture(a, "home", "screenshot", "http://z", False)
            rows = (a / "captures.md").read_text().splitlines()[4:]
            self.assertEqual(len(rows), 2)
            self.assertTrue(any("http://z" in r for r in rows))
            self.assertFalse(any("http://x" in r for r in rows))


import asyncio, functools, http.server, subprocess, threading, time
FIXTURE = """<!doctype html><title>Fixture</title><body style="font:20px sans-serif">
<style>#m{display:none}@media(max-width:600px){#m{display:block}}</style><button id="m">Menu</button>
<h1>Jobs</h1><p class="email">me@example.com</p>
<input id="q"><button onclick="document.getElementById('out').textContent='clicked'">Search</button><p id="out"></p>
<div style="height:3000px"></div></body>"""


class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        (Path(cls.tmp.name) / "index.html").write_text(FIXTURE)
        (Path(cls.tmp.name) / "plain.html").write_text(FIXTURE.replace('<p class="email">me@example.com</p>', ""))  # passes the privacy scan
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=cls.tmp.name)
        h.log_message = lambda *a, **k: None
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.srv.server_address[1]}/index.html"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.tmp.cleanup()

    def go(self, header, body, record=False, bp="laptop"):
        out = Path(tempfile.mkdtemp())
        opts, steps = capture.parse_steps(f"url: {self.url}\n{header}\n---\n{body}")
        asyncio.run(capture.run(opts, capture.steps_for(steps, bp), out, out / "vid" if record else None, bp))
        return out

    def test_breakpoint_sizes_and_prefix(self):  # all breakpoints
        from PIL import Image
        for bp, (w, _h) in capture.BREAKPOINTS.items():
            out = self.go("", "shot s", bp=bp)
            self.assertEqual(Image.open(out / "s.png").size[0], w * 2, bp)  # screenshots are 2x
        # #m (a "menu" button) shows only under 600 px: an @mobile click works on mobile and is skipped on desktop
        self.go("", "@mobile click #m\nshot s", bp="mobile")
        self.go("", "@mobile click #m\nshot s", bp="desktop")

    def test_record_size_per_breakpoint(self):
        for bp in ("mobile", "desktop"):
            out = self.go("", "wait 1", record=True, bp=bp)
            webm = next((out / "vid").glob("*.webm"))
            w = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width",
                                "-of", "csv=p=0", str(webm)], capture_output=True, text=True).stdout.strip()
            self.assertEqual(int(w), capture.BREAKPOINTS[bp][0], bp)

    def test_shot_and_click(self):
        out = self.go("", "click text=Search\nshot after")
        self.assertGreater((out / "after.png").stat().st_size, 5000)

    def test_record_makes_webm(self):
        out = self.go("", "click text=Search\nwait 1\nscroll 300\nwait 1", record=True)
        webms = list((out / "vid").glob("*.webm"))
        self.assertEqual(len(webms), 1)
        self.assertGreater(webms[0].stat().st_size, 1000)

    def test_missing_selector_names_step_and_is_fast(self):  # Review Focus 2
        t = time.time()
        with self.assertRaisesRegex(RuntimeError, r"step 1 \(click #nope\)"):
            self.go("", "click #nope")
        self.assertLess(time.time() - t, 25)

    def test_expect_fails_loudly(self):  # Review Focus 1
        with self.assertRaisesRegex(RuntimeError, "session expired"):
            self.go("expect: Welcome back", "shot x")

    def test_mask_blurs(self):  # Review Focus 3
        opts, _ = capture.parse_steps(f"url: {self.url}\nmask: .email\n---\nshot x")

        async def probe():
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                b, ctx = await capture.open_context(p, opts, None)
                pg = await ctx.new_page()
                await pg.goto(self.url)
                f = await pg.eval_on_selector(".email", "e => getComputedStyle(e).filter")
                await b.close()
                return f
        self.assertIn("blur", asyncio.run(probe()))

    def new_video(self, slug):
        import anim, argparse, shutil
        vdir = anim.ROOT / "videos" / "videofactory" / slug
        shutil.rmtree(vdir, ignore_errors=True)
        anim.cmd_new(argparse.Namespace(slug=slug, voice=None, format="wide", style="modern", brand="videofactory", src=None, start=None, end=None))
        self.addCleanup(shutil.rmtree, vdir, True)
        return anim, vdir / "04_scene" / "assets"

    def test_grab_selector_and_log(self):
        import argparse
        anim, assets = self.new_video("zz-capture-test")
        anim.cmd_grab(argparse.Namespace(slug="zz-capture-test", url=self.url, name="h", find=None, above=140, height=1600,
                                         width=None, light=False, auth=None, bp="mobile,desktop", mask=".email",
                                         selector="h1", wait_for=None))
        self.assertGreater((assets / "h-mobile.png").stat().st_size, 500)
        self.assertGreater((assets / "h-desktop.png").stat().st_size, 500)
        log = (assets / "captures.md").read_text()
        self.assertIn("| h-mobile | screenshot |", log)
        self.assertIn("| h-desktop | screenshot |", log)

    def test_auth_file_ignored_by_git(self):  # Review Focus 5
        root = Path(__file__).resolve().parent.parent
        r = subprocess.run(["git", "check-ignore", "_auth/example-hub.json"], cwd=root, capture_output=True)
        self.assertEqual(r.returncode, 0)

    def test_record_command_end_to_end(self):
        import argparse
        from PIL import Image
        anim, assets = self.new_video("zz-capture-test")
        steps = Path(self.tmp.name) / "steps.txt"
        steps.write_text(f"url: {self.url.replace('index.html', 'plain.html')}\nbreakpoints: mobile, desktop\n---\n@mobile click #m\nclick text=Search\nwait 1\nshot mid\nscroll 300\nwait 1\n")
        anim.cmd_record(argparse.Namespace(slug="zz-capture-test", name="demo", steps=str(steps), fps=12, start=0.3, bp=None))
        for bp, w in (("mobile", 390), ("desktop", 1280)):  # frame width = min(viewport, 1280)
            frames = sorted((assets / f"demo-{bp}").glob("f*.jpg"))
            self.assertGreater(len(frames), 12, bp)
            with Image.open(frames[0]) as im:
                self.assertEqual(im.size[0], w, bp)
            self.assertIn(f'"demo-{bp}"', (assets / "real.js").read_text())
            self.assertTrue((assets / f"mid-{bp}.png").exists(), bp)
            self.assertIn(f"| demo-{bp} | recording |", (assets / "captures.md").read_text())


if __name__ == "__main__":
    unittest.main()


class Private(unittest.TestCase):
    """Sessions: _auth/ 0700, files 0600 from creation, never printed."""
    def test_auth_written_private(self):
        import io, os, stat
        from contextlib import redirect_stdout
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(capture, "AUTH_DIR", Path(d) / "_auth"):
                old = os.umask(0o022)
                try:
                    buf = io.StringIO()
                    with redirect_stdout(buf):
                        f = capture.save_auth("chatgpt", {"cookies": [{"name": "s", "value": "geheim123"}], "origins": []})
                finally:
                    os.umask(old)
                self.assertEqual(stat.S_IMODE((Path(d) / "_auth").stat().st_mode), 0o700)
                self.assertEqual(stat.S_IMODE(f.stat().st_mode), 0o600)
                self.assertNotIn("geheim123", buf.getvalue())
                self.assertIn("geheim123", f.read_text())

    def test_captures_log_strips_query(self):
        with tempfile.TemporaryDirectory() as d:
            capture.log_capture(Path(d), "chat", "recording", "https://chatgpt.com/c/abc?token=x#frag", True)
            text = (Path(d) / "captures.md").read_text()
            self.assertIn("https://chatgpt.com/c/abc", text)
            self.assertNotIn("token", text)
            self.assertNotIn("frag", text)

    def test_crop_step_parses(self):
        _, steps = capture.parse_steps("---\ncrop main\nshot s\n")
        self.assertEqual(steps[0], ("crop", ["main"], None))


class SecureBrowser(unittest.TestCase):
    """Login that finishes by itself, crop, and the mandatory privacy scan in record (Review Focus 1-3)."""
    setUpClass = classmethod(Browser.setUpClass.__func__)  # same fixture server, without re-running Browser's tests
    tearDownClass = classmethod(Browser.tearDownClass.__func__)

    def test_login_expect_timeout(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(capture, "AUTH_DIR", Path(d) / "_auth"):
                with self.assertRaisesRegex(RuntimeError, "not logged in, or a check page; nothing saved"):
                    asyncio.run(capture.login_session("fixture", self.url, "Welcome back", 2, headless=True))
                self.assertFalse((Path(d) / "_auth" / "fixture.json").exists())

    def test_login_expect_saves(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(capture, "AUTH_DIR", Path(d) / "_auth"):
                f = asyncio.run(capture.login_session("fixture", self.url, "#q", 5, headless=True))
                self.assertEqual(f, Path(d) / "_auth" / "fixture.json")
                self.assertTrue(f.exists())

    def record(self, body):
        """Runs anim.cmd_record on the fixture; returns (assets folder, stderr text, exited)."""
        import anim, io
        from contextlib import redirect_stderr
        from unittest import mock
        root = Path(tempfile.mkdtemp())
        (root / "v" / "04_scene").mkdir(parents=True)
        steps = root / "s.txt"; steps.write_text(f"url: {self.url}\n---\n{body}\n")
        a = anim.argparse.Namespace(slug="v", name="clip", steps=str(steps), bp=None, start=0.0, fps=12)
        err, exited = io.StringIO(), False
        with mock.patch.object(anim, "VIDEOS", root), mock.patch("sys.stdout"), redirect_stderr(err):
            try:
                anim.cmd_record(a)
            except SystemExit:
                exited = True
        return root / "v" / "04_scene" / "assets", err.getvalue(), exited

    def test_record_refused_and_deleted_on_hit(self):
        assets, err, exited = self.record("wait 1\nshot s")
        self.assertTrue(exited)
        self.assertIn("privacyscan: email", err)
        self.assertNotIn("me@example.com", err)
        self.assertEqual([p.name for p in assets.rglob("*") if p.suffix in (".jpg", ".png")], [])

    def grab(self, url, patch=None):
        import anim, io
        from contextlib import redirect_stderr
        from unittest import mock
        root = Path(tempfile.mkdtemp())
        (root / "v" / "04_scene").mkdir(parents=True)
        a = anim.argparse.Namespace(slug="v", url=url, name="g", bp=None, light=False, auth=None, mask=None, selector=None,
                                    wait_for=None, find=None, above=0, width=None, height=800)
        err, exited = io.StringIO(), None
        with mock.patch.object(anim, "VIDEOS", root), mock.patch("sys.stdout"), redirect_stderr(err), (patch or mock.MagicMock())():
            try:
                anim.cmd_grab(a)
            except BaseException as e:  # SystemExit from a scan hit, or the injected scan error
                exited = e
        return root / "v" / "04_scene" / "assets", exited

    def test_grab_hit_leaves_nothing(self):
        assets, exited = self.grab(self.url)
        self.assertIsInstance(exited, SystemExit)
        self.assertEqual(list(assets.glob("*.png")), [])

    def test_grab_scan_error_leaves_nothing(self):  # e.g. tesseract missing or Ctrl+C during the scan
        import anim
        from unittest import mock
        assets, exited = self.grab(self.url.replace("index.html", "plain.html"),
                                   lambda: mock.patch.object(anim, "refuse_private", side_effect=KeyboardInterrupt))
        self.assertIsInstance(exited, KeyboardInterrupt)
        self.assertEqual(list(assets.glob("*.png")), [])

    def test_record_crop_excludes_hit(self):
        assets, err, exited = self.record("crop h1\nwait 1\nshot s")
        self.assertFalse(exited, err)
        self.assertTrue(list((assets / "clip").glob("f*.jpg")))
        self.assertTrue((assets / "s.png").exists())
        from PIL import Image
        self.assertLess(Image.open(assets / "s.png").size[1], 200)  # the shot is the h1 box, not the page
