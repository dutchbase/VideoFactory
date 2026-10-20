import json, os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import libcore as L
import library as LIBR


class Core(unittest.TestCase):
    def test_safe_name_rejects_escape(self):
        for bad in ("../x", "a/b", "", ".."):
            with self.assertRaises(ValueError):
                L.safe_name(bad)
        self.assertEqual(L.safe_name("Rocket_1"), "rocket_1")

    def test_parse_ref(self):
        self.assertEqual(L.parse_ref("icon:lucide/rocket"), ("icon", "lucide/rocket"))
        with self.assertRaises(ValueError):
            L.parse_ref("nocolon")

    def test_license_allowlist(self):
        L.check_license("MIT")
        L.check_license("CC0-1.0")
        with self.assertRaises(L.LicenseError):
            L.check_license("CC-BY-4.0")

    def test_env_key_missing_names_var(self):
        os.environ.pop("PEXELS_API_KEY", None)
        with self.assertRaises(L.KeyMissing) as c:
            L.env_key("PEXELS_API_KEY", env_file=Path("/nonexistent"))
        self.assertIn("PEXELS_API_KEY", str(c.exception))

    def test_env_key_from_file(self):
        os.environ.pop("PEXELS_API_KEY", None)
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / ".env"
            f.write_text('PEXELS_API_KEY="abc123"\n')
            self.assertEqual(L.env_key("PEXELS_API_KEY", env_file=f), "abc123")

    def test_offline(self):
        os.environ["ANIM_OFFLINE"] = "1"
        try:
            with self.assertRaises(L.NetError):
                L.http_get("https://x.test")
        finally:
            del os.environ["ANIM_OFFLINE"]

    def test_http_get_uses_fetch(self):
        self.assertEqual(L.http_get("https://x.test", fetch=lambda url, headers: b"ok"), b"ok")

    def test_record_use_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            v = Path(d)
            for _ in range(2):
                L.record_use(v, "icon:lucide/rocket", "ISC", "u", "assets/rocket.svg")
            lines = (v / "04_scene/assets/library.md").read_text().splitlines()
            self.assertEqual(sum("icon:lucide/rocket" in l for l in lines), 1)


SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path stroke="currentColor" d="M1 1"/></svg>'


def fake_iconify(spdx="ISC"):
    calls = []
    def fetch(url, headers):
        calls.append(url)
        if "/collections" in url:
            return json.dumps({"lucide": {"license": {"spdx": spdx}}}).encode()
        if url.endswith(".svg"):
            return SVG
        return json.dumps({"icons": ["lucide:rocket"]}).encode()
    return fetch, calls


class Icons(unittest.TestCase):
    def test_add_writes_file_and_is_idempotent(self):
        fetch, calls = fake_iconify()
        with tempfile.TemporaryDirectory() as d:
            p = LIBR.icon_add("lucide/rocket", fetch=fetch, root=Path(d))
            self.assertEqual(p, Path(d) / "icons/lucide/rocket.svg")
            self.assertTrue(p.read_bytes().startswith(b"<svg"))
            n = len(calls)
            LIBR.icon_add("lucide:rocket", fetch=fetch, root=Path(d))
            self.assertEqual(len(calls), n)

    def test_unlisted_set_refused(self):
        fetch, _ = fake_iconify()
        with self.assertRaises(L.LicenseError):
            LIBR.icon_add("fa-solid/rocket", fetch=fetch, root=Path("/nonexistent"))

    def test_bad_license_from_iconify_refused(self):
        fetch, _ = fake_iconify(spdx="CC-BY-4.0")
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(L.LicenseError):
                LIBR.icon_add("lucide/rocket", fetch=fetch, root=Path(d))
            self.assertFalse((Path(d) / "icons").exists())

    def test_path_escape_rejected(self):
        fetch, _ = fake_iconify()
        with self.assertRaises(ValueError):
            LIBR.icon_add("lucide/../../x", fetch=fetch, root=Path("/nonexistent"))

    def test_search(self):
        fetch, _ = fake_iconify()
        self.assertEqual(LIBR.icon_search("rocket", set="lucide", fetch=fetch), ["lucide:rocket"])


class Use(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.v = Path(self.tmp.name) / "videos" / "demo"
        (self.v / "04_scene").mkdir(parents=True)
        self.root = Path(self.tmp.name) / "library"

    def tearDown(self):
        self.tmp.cleanup()

    def test_icon_copied_and_logged_once(self):
        fetch, _ = fake_iconify()
        for _ in range(2):
            out = LIBR.use(self.v, "icon:lucide/rocket", fetch=fetch, root=self.root)
        self.assertTrue((self.v / "04_scene/assets/icons/lucide/rocket.svg").exists())
        log = (self.v / "04_scene/assets/library.md").read_text()
        self.assertEqual(log.count("icon:lucide/rocket"), 1)
        self.assertIn("ISC", out[0])

    def test_unknown_kind(self):
        with self.assertRaises(ValueError):
            LIBR.use(self.v, "sound:x/y", root=self.root)

    def test_name_escape_rejected(self):
        with self.assertRaises(ValueError):
            LIBR.use(self.v, "icon:lucide/rocket", name="../x", root=self.root)

    def test_orientation_from_format(self):
        self.assertEqual(LIBR.video_orientation(self.v), "landscape")
        (self.v / "04_scene/index.html").write_text('<div id="stage" data-width="1080" data-height="1920">')
        self.assertEqual(LIBR.video_orientation(self.v), "portrait")

    def test_stock_video_needs_range_and_calls_clip(self):
        import stock
        stock.CACHE = Path(self.tmp.name) / "cache"
        item = {"ref": "stock:pexels/video/11", "provider": "pexels", "kind": "video", "id": "11", "license": "Pexels",
                "page_url": "https://p/11", "author": "Ann", "download_url": "https://v/hd.mp4"}
        found = stock.CACHE / "found"
        found.mkdir(parents=True)
        (found / "pexels-video-11.json").write_text(json.dumps(item))
        fetch = lambda url, headers: b"VIDEO"
        with self.assertRaises(ValueError):
            LIBR.use(self.v, "stock:pexels/video/11", fetch=fetch, root=self.root)
        seen = []
        out = LIBR.use(self.v, "stock:pexels/video/11", name="bg", start="0", end="5", fetch=fetch, root=self.root,
                       clip=lambda src, n, s, e: seen.append((src.name, n, s, e)))
        self.assertEqual(seen, [("11.mp4", "bg", "0", "5")])
        self.assertIn(LIBR.ENDORSE, out)
        self.assertIn("Ann", (self.v / "04_scene/assets/library.md").read_text())


LOTTIE = {"v": "5.7.0", "fr": 30, "ip": 0, "op": 60, "w": 200, "h": 200, "layers": []}


class Lottie(unittest.TestCase):
    def add(self, data, **kw):
        body = data if isinstance(data, bytes) else json.dumps(data).encode()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        kw.setdefault("license", "CC0-1.0")
        return LIBR.lottie_add("https://assets.lottiefiles.com/x/confetti.json", fetch=lambda u, h: body, root=Path(self.tmp.name), **kw)

    def test_valid_saved_with_meta(self):
        p = self.add(LOTTIE, license_ok=True)
        self.assertEqual(p.name, "confetti.json")
        meta = json.loads(p.with_suffix(".meta.json").read_text())
        self.assertEqual(meta["license"], "CC0-1.0")
        self.assertIn("lottiefiles.com", meta["source"])
        js = p.with_suffix(".js").read_text()
        self.assertIn('LOTTIE_DATA', js)
        self.assertIn('["confetti"]', js)

    def test_license_flag_required(self):
        with self.assertRaises(L.LicenseError):
            self.add(LOTTIE, license_ok=False)

    def test_explicit_allowlisted_license_required(self):
        with self.assertRaises(L.LicenseError):
            self.add(LOTTIE, license_ok=True, license=None)
        with self.assertRaises(L.LicenseError):
            self.add(LOTTIE, license_ok=True, license="CC-BY-4.0")

    def test_missing_layers_rejected(self):
        bad = {k: v for k, v in LOTTIE.items() if k != "layers"}
        with self.assertRaises(ValueError):
            self.add(bad, license_ok=True)

    def test_bad_dimensions_and_timing_rejected(self):
        for values in ({'fr': 0}, {'fr': float('inf')}, {'fr': '30'}, {'w': 0}, {'h': -1},
                       {'ip': 60}, {'op': float('nan')}, {'layers': {}}, {'assets': {}}):
            with self.subTest(values=values), self.assertRaisesRegex(ValueError, 'invalid Lottie'):
                self.add(dict(LOTTIE, **values), license_ok=True)

    def test_external_image_rejected(self):
        bad = dict(LOTTIE, assets=[{"id": "i", "w": 10, "h": 10, "u": "images/", "p": "a.png", "e": 0}])
        with self.assertRaises(ValueError):
            self.add(bad, license_ok=True)

    def test_embedded_image_ok(self):
        ok = dict(LOTTIE, assets=[{"id": "i", "w": 10, "h": 10, "u": "", "p": "data:image/png;base64,AAAA", "e": 1}])
        self.add(ok, license_ok=True)

    def test_use_copies_js_wrapper(self):
        p = self.add(LOTTIE, license_ok=True)
        v = Path(self.tmp.name) / "videos" / "demo"
        (v / "04_scene").mkdir(parents=True)
        out = LIBR.use(v, "lottie:confetti", root=Path(self.tmp.name))
        self.assertTrue((v / "04_scene/assets/lottie/confetti.js").exists())
        self.assertIn("CC0-1.0", out[0])

    def test_dotlottie_zip_rejected(self):
        with self.assertRaises(ValueError):
            self.add(b"PK\x03\x04zip", license_ok=True)

    def test_existing_import_keeps_recorded_rights(self):
        p = self.add(LOTTIE, license_ok=True)
        before = p.with_suffix('.meta.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'already exists'):
            LIBR.lottie_add('https://assets.lottiefiles.com/x/confetti.json', license_ok=True, license='MIT',
                            fetch=lambda u, h: json.dumps(LOTTIE).encode(), root=Path(self.tmp.name))
        self.assertEqual(before, p.with_suffix('.meta.json').read_bytes())


DIRTY = (b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 10 10" onload="x()">'
         b'<script>alert(1)</script><foreignObject><div>x</div></foreignObject>'
         b'<a xlink:href="javascript:alert(1)"><rect width="5" height="5" onclick="y()"/></a>'
         b'<image href="https://evil.test/a.png"/><use href="#ok"/><image href="data:image/png;base64,AAAA"/></svg>')


class Graphics(unittest.TestCase):
    def add(self, body, license="CC0-1.0", url="https://x/a.svg"):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        return LIBR.graphic_add(url, "peeps", "Sitting", license, fetch=lambda u, h: body, root=Path(self.tmp.name))

    def test_sanitized(self):
        out = self.add(DIRTY).read_text().lower()
        for bad in ("<script", "foreignobject", "onload", "onclick", "javascript:", "evil.test"):
            self.assertNotIn(bad, out)
        self.assertIn('href="#ok"', out)
        self.assertIn("data:image/png", out)
        self.assertIn("<rect", out)

    def test_path_and_meta(self):
        p = self.add(DIRTY)
        self.assertEqual(p.relative_to(self.tmp.name).as_posix(), "graphics/peeps/sitting.svg")
        self.assertEqual(json.loads(p.with_suffix(".meta.json").read_text()), {"license": "CC0-1.0", "source": "https://x/a.svg"})

    def test_bad_license_refused(self):
        with self.assertRaises(L.LicenseError):
            self.add(DIRTY, license="CC-BY-4.0")

    def test_non_svg_refused(self):
        with self.assertRaises(ValueError):
            self.add(b"\x89PNG\r\n")


class Index(unittest.TestCase):
    def test_index_lists_all_kinds_and_is_stable(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            fetch, _ = fake_iconify()
            LIBR.icon_add("lucide/rocket", fetch=fetch, root=r)
            LIBR.graphic_add("https://x/a.svg", "peeps", "sit", "CC0-1.0", fetch=lambda u, h: DIRTY, root=r)
            LIBR.lottie_add("https://x/pulse.json", license_ok=True, license="CC0-1.0", fetch=lambda u, h: json.dumps(LOTTIE).encode(), root=r)
            first = LIBR.index(r)
            text1 = (r / "INDEX.json").read_text()
            LIBR.index(r)
            self.assertEqual(text1, (r / "INDEX.json").read_text())
            self.assertEqual([e["ref"] for e in first], ["graphic:peeps/sit", "icon:lucide/rocket", "lottie:pulse"])
            self.assertEqual({e["ref"]: e["license"] for e in first}["icon:lucide/rocket"], "ISC")
            self.assertEqual([e["ref"] for e in LIBR.find("rocket", r)], ["icon:lucide/rocket"])
            self.assertEqual(LIBR.find("zzz", r), [])


try:
    import playwright.sync_api  # noqa: F401
    HAVE_PW = True
except ImportError:
    HAVE_PW = False


@unittest.skipUnless(HAVE_PW, "playwright not installed (use .venv)")
class LottieBrowser(unittest.TestCase):
    def test_frame_is_a_pure_function_of_time(self):
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = (Path(__file__).parent / "fixtures" / "pulse.json").read_bytes()
            LIBR.lottie_add("https://x/pulse.json", license_ok=True, license="CC0-1.0", fetch=lambda u, h: data, root=root)
            page = root / "t.html"
            page.write_text(f"""<!doctype html><meta charset=utf-8><canvas id=c width=200 height=200></canvas>
<script src="{(L.ROOT / '_runtime' / 'lib.js').as_uri()}"></script><script>
Lib.bases.lottie=[{json.dumps((root / 'lottie').as_uri() + '/')}];
const clip=Lib.lottie('pulse'), ctx=document.getElementById('c').getContext('2d');
window.shot=(t)=>{{ctx.clearRect(0,0,200,200);clip.at(ctx,t,100,100,200,200);return document.getElementById('c').toDataURL();}};
clip.whenReady.then(()=>window.__ready=true);
</script>""")
            with sync_playwright() as p:
                b = p.chromium.launch()
                pg = b.new_page()
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(page.as_uri())
                pg.wait_for_function("window.__ready===true", timeout=15000)
                a, z, e, a2 = (pg.evaluate(f"shot({t})") for t in (0.5, 0, 1.9, 0.5))
                b.close()
            self.assertEqual(errs, [])
            self.assertEqual(a, a2)
            self.assertNotEqual(a, z)
            self.assertNotEqual(a, e)

    def test_missing_lottie_rejects_asset_wait(self):
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as d:
            page = Path(d) / "t.html"
            page.write_text(f"""<script src="{(L.ROOT / '_runtime' / 'lib.js').as_uri()}"></script><script>
Lib.bases.lottie=[{json.dumps(Path(d).as_uri() + '/')}];
Lib.lottie('missing').whenReady.catch(e => window.assetError = e.message);
</script>""")
            with sync_playwright() as p:
                b = p.chromium.launch()
                pg = b.new_page()
                pg.goto(page.as_uri())
                pg.wait_for_function("window.assetError")
                self.assertIn('missing', pg.evaluate('window.assetError'))
                b.close()

    def test_stalled_renderer_script_times_out(self):
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as d:
            page = Path(d) / 't.html'
            page.write_text(f"""<script src="{(L.ROOT / '_runtime' / 'lib.js').as_uri()}"></script><script>
window.setTimeout=(fn,ms)=>{{if(ms===30000)window.timeoutAsset=fn;return 0;}};
document.head.appendChild=(el)=>el;
Lib.lottie('stalled').whenReady.catch(e=>window.assetError=e.message);
</script>""")
            with sync_playwright() as p:
                b = p.chromium.launch()
                pg = b.new_page()
                pg.goto(page.as_uri())
                pg.evaluate('window.timeoutAsset()')
                pg.wait_for_function('window.assetError')
                self.assertIn('30 seconds', pg.evaluate('window.assetError'))
                b.close()

    def test_timeout_and_renderer_errors_stay_failed_after_late_loaded_event(self):
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            LIBR.lottie_add('https://x/pulse.json', license_ok=True, license='CC0-1.0',
                            fetch=lambda u, h: json.dumps(LOTTIE).encode(), root=root)
            page = root / 't.html'
            page.write_text(f"""<script src="{(L.ROOT / '_runtime' / 'lib.js').as_uri()}"></script><script>
Lib.bases.lottie=[{json.dumps((root / 'lottie').as_uri() + '/')}];
const append=document.head.appendChild.bind(document.head), timeout=window.setTimeout.bind(window);
window.setTimeout=(fn,ms)=>{{if(ms===30000){{window.timeoutAsset=fn;return 0;}}return timeout(fn,ms);}};
document.head.appendChild=(el)=>{{
  if(el.src?.endsWith('/lottie_canvas.min.js')) {{
    window.lottie={{loadAnimation(){{
      const listeners={{}};
      window.fake={{listeners, destroy(){{window.destroyed=true;}}}};
      return {{addEventListener(k,f){{listeners[k]=f;}},removeEventListener(k){{delete listeners[k];}},destroy:window.fake.destroy}};
    }}}};
    queueMicrotask(()=>el.onload()); return el;
  }}
  return append(el);
}};
const clip=Lib.lottie('pulse'); window.clip=clip;
clip.whenReady.catch(e=>window.assetError=e.message);
</script>""")
            with sync_playwright() as p:
                b = p.chromium.launch()
                for event in ('timeout', 'data_failed', 'error'):
                    with self.subTest(event=event):
                        pg = b.new_page()
                        errors = []
                        pg.on('pageerror', lambda e: errors.append(str(e)))
                        pg.goto(page.as_uri())
                        pg.wait_for_function('window.fake || window.assetError', timeout=5000)
                        self.assertIn('DOMLoaded', pg.evaluate('Object.keys(window.fake.listeners)'),
                                      (pg.evaluate('window.assetError'), errors))
                        pg.evaluate('() => { window.lateLoaded=window.fake.listeners.DOMLoaded; }')
                        if event == 'timeout':
                            pg.evaluate('window.timeoutAsset()')
                        else:
                            pg.evaluate(f"window.fake.listeners[{json.dumps(event)}]({{message:'broken'}})")
                        pg.wait_for_function('window.assetError')
                        self.assertIn('30 seconds' if event == 'timeout' else 'broken', pg.evaluate('window.assetError'))
                        self.assertTrue(pg.evaluate('window.destroyed'))
                        pg.evaluate('window.lateLoaded()')
                        self.assertFalse(pg.evaluate('window.clip.ready'))
                        pg.close()
                b.close()


@unittest.skipUnless(HAVE_PW, "playwright not installed (use .venv)")
class SVGMorphBrowser(unittest.TestCase):
    def test_paths_seek_deterministically_with_hole_and_exact_endpoints(self):
        from playwright.sync_api import sync_playwright
        start = 'M10 10 H90 V90 H10 Z M30 30 H70 V70 H30 Z'
        end = 'M50 0 L100 50 L50 100 L0 50 Z M50 20 L80 50 L50 80 L20 50 Z'
        with tempfile.TemporaryDirectory() as d:
            page = Path(d) / 't.html'
            page.write_text(f"""<canvas id=c width=100 height=100></canvas>
<script src="{(L.ROOT / '_runtime' / 'lib.js').as_uri()}"></script><script>
const a={json.dumps(start)}, b={json.dumps(end)}, m=Lib.svgMorph(a,b);
const c=document.getElementById('c'), ctx=c.getContext('2d');
window.shot=(p)=>{{ctx.clearRect(0,0,100,100);ctx.fill(m.path(p),'evenodd');return c.toDataURL();}};
window.direct=(d)=>{{ctx.clearRect(0,0,100,100);ctx.fill(new Path2D(d),'evenodd');return c.toDataURL();}};
window.pixel=(x,y)=>[...ctx.getImageData(x,y,1,1).data];
m.ready.then(()=>window.__ready=true).catch(e=>window.__error=e.message);
</script>""")
            with sync_playwright() as p:
                b = p.chromium.launch()
                pg = b.new_page()
                pg.goto(page.as_uri())
                pg.wait_for_function('window.__ready || window.__error')
                self.assertIsNone(pg.evaluate('window.__error'))
                self.assertEqual(pg.evaluate('shot(0)'), pg.evaluate('direct(a)'))
                self.assertEqual(pg.evaluate('shot(1)'), pg.evaluate('direct(b)'))
                first = pg.evaluate('shot(.37)')
                pg.evaluate('shot(.91)')
                pg.evaluate('shot(.1)')
                self.assertEqual(first, pg.evaluate('shot(.37)'))
                pg.evaluate('shot(.5)')
                self.assertEqual(pg.evaluate('pixel(50,50)[3]'), 0)
                b.close()

    def test_invalid_geometry_rejects(self):
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as d:
            page = Path(d) / 't.html'
            page.write_text(f"""<script src="{(L.ROOT / '_runtime' / 'lib.js').as_uri()}"></script><script>
Lib.svgMorph('not a path','M0 0 L10 0 L0 10 Z').ready.catch(e => window.assetError=e.message);
</script>""")
            with sync_playwright() as p:
                b = p.chromium.launch()
                pg = b.new_page()
                pg.goto(page.as_uri())
                pg.wait_for_function('window.assetError')
                self.assertIn('must be SVG path data', pg.evaluate('window.assetError'))
                pg.evaluate("Lib.svgMorph('M0 0 L10 0 rubbish','M0 0 L10 0').ready.catch(e => window.tailError=e.message)")
                pg.wait_for_function('window.tailError')
                self.assertIn('invalid path syntax', pg.evaluate('window.tailError'))
                pg.evaluate("Lib.svgMorph('M0 0 A5 5 0 2 1 10 10','M0 0 L10 0').ready.catch(e => window.arcError=e.message)")
                pg.wait_for_function('window.arcError')
                self.assertIn('invalid path syntax', pg.evaluate('window.arcError'))
                b.close()


if __name__ == "__main__":
    unittest.main()


class MotionIndex(unittest.TestCase):
    def test_manifest_assets_are_findable(self):
        with tempfile.TemporaryDirectory() as d:
            m = Path(d) / "motion" / "demo"
            m.mkdir(parents=True)
            (m / "manifest.json").write_text(json.dumps({"assets": [
                {"id": "CAP-01", "name": "Karaoke-blok", "section": "08 Voice-over captions", "type": "overlay", "file": "CAP-01.dc.html"}]}))
            hit = LIBR.find("karaoke overlay", root=Path(d))
            self.assertEqual([e["ref"] for e in hit], ["motion:demo/CAP-01"])
            self.assertEqual(hit[0]["path"], "motion/demo/CAP-01.dc.html")

    def test_motion_brands_have_distinct_refs_and_search(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for brand in ["demo", "videofactory"]:
                pack = root / "motion" / brand
                pack.mkdir(parents=True)
                (pack / "manifest.json").write_text(json.dumps({"assets": [
                    {"id": "CAP-01", "name": "Karaoke", "section": "08 Captions", "type": "overlay", "file": "CAP-01.dc.html"}]}))
            entries = LIBR.index(root)
            self.assertEqual({e["ref"] for e in entries}, {"motion:demo/CAP-01", "motion:videofactory/CAP-01"})
            hit = LIBR.find("demo karaoke", root)
            self.assertEqual([e["ref"] for e in hit], ["motion:demo/CAP-01"])
            self.assertIn("--brand demo", hit[0]["description"])
