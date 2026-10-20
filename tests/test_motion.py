import asyncio, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

JS = """() => {
  const s0 = P.spring({dur: 0.5, bounce: 0}), s3 = P.spring({dur: 0.5, bounce: 0.3});
  let peak0 = 0, peak3 = 0;
  for (let k = 0; k <= 200; k++) { peak0 = Math.max(peak0, s0(k / 100)); peak3 = Math.max(peak3, s3(k / 100)); }
  const r1 = P.rand(7), r2 = P.rand(7);
  return {
    start: s0(0), settled: s0(0.9), peak0, peak3,
    before: P.track([[1, 0], [2, 100]], {}, 0.5), mid: P.track([[1, 0], [2, 100]], {}, 2.3), after: P.track([[1, 0], [2, 100]], {}, 9),
    retarget: P.track([[0, 0], [1, 100], [1.1, 50]], {}, 9),
    enter05: P.ease.enter(0.5), bez1: P.bezier(0.16, 1, 0.3, 1)(1), zoomMid: P.zoom(1, 4, 0.5),
    same: r1() === r2(), unit: [...Array(50)].every(() => { const v = r1(); return v >= 0 && v < 1; }), beat: P.beat(4, 120),
  };
}"""


class Motion(unittest.TestCase):
    def test_math(self):
        async def run():
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                b = await p.chromium.launch()
                pg = await b.new_page()
                await pg.set_content("<script>window.ANIM={meta:{duration:10},cueList:[],cues:{},words:[]}</script>")
                await pg.add_script_tag(path=str(ROOT / "_runtime" / "player.js"))
                r = await pg.evaluate(JS)
                await b.close()
                return r
        r = asyncio.run(run())
        self.assertEqual(r["start"], 0)
        self.assertAlmostEqual(r["settled"], 1, delta=0.01)
        self.assertLessEqual(r["peak0"], 1.0001)
        self.assertTrue(1.02 < r["peak3"] < 1.1, r["peak3"])
        self.assertEqual(r["before"], 0)
        self.assertTrue(50 < r["mid"] < 100)
        self.assertAlmostEqual(r["after"], 100, delta=0.01)
        self.assertAlmostEqual(r["retarget"], 50, delta=0.01)
        self.assertTrue(r["enter05"] > 0.8)
        self.assertEqual(r["bez1"], 1)
        self.assertAlmostEqual(r["zoomMid"], 2, delta=1e-9)
        self.assertTrue(r["same"])
        self.assertTrue(r["unit"])
        self.assertEqual(r["beat"], 2)

    def test_path_geometry(self):
        async def run():
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                b = await p.chromium.launch()
                pg = await b.new_page()
                await pg.set_content('<div id="stage"></div><script>window.ANIM={meta:{duration:10},cueList:[],cues:{},words:[]}</script>')
                await pg.add_script_tag(path=str(ROOT / '_runtime' / 'player.js'))
                result = await pg.evaluate('''() => {
                    const straight = P.path('M0 0 L10 0'), curve = P.path('M0 0 Q10 20 20 0');
                    const invalid = ['', 'garbage', 'M0 0 L10 0 X', 'M0 0 L10 0 L', 'M0 0 L0 0']
                        .every(d => { try { P.path(d); return false; } catch { return true; } });
                    return {straight:[straight(-1), straight(0.5), straight(2)],
                        curve:[curve(0), curve(0.5), curve(1)], invalid,
                        nanRejected:(()=>{try{straight(NaN);return false;}catch{return true;}})()};
                }''')
                await b.close()
                return result
        r = asyncio.run(run())
        self.assertTrue(r['invalid'])
        self.assertTrue(r['nanRejected'])
        self.assertEqual([p['x'] for p in r['straight']], [0, 5, 10])
        self.assertTrue(all(p['y'] == 0 and p['angle'] == 0 for p in r['straight']))
        self.assertAlmostEqual(r['curve'][0]['x'], 0, delta=0.01)
        self.assertAlmostEqual(r['curve'][1]['x'], 10, delta=0.1)
        self.assertAlmostEqual(r['curve'][1]['y'], 10, delta=0.1)
        self.assertAlmostEqual(r['curve'][2]['x'], 20, delta=0.01)
        self.assertGreater(r['curve'][0]['angle'], 0.5)
        self.assertLess(r['curve'][2]['angle'], -0.5)

    def test_rejected_asset_wait_stops_render_boot(self):
        async def run():
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                b = await p.chromium.launch()
                pg = await b.new_page()
                await pg.route('**/*', lambda route: route.fulfill(status=200, content_type='text/html', body='<div id="stage"></div><script>window.ANIM={meta:{duration:10},cueList:[],cues:{},words:[]}</script>'))
                await pg.goto('http://geometry.test/?render')
                await pg.add_script_tag(path=str(ROOT / '_runtime' / 'player.js'))
                await pg.evaluate("P.wait(Promise.reject(Error('bad asset'))); window.dispatchEvent(new Event('load'))")
                await pg.wait_for_function('window.__assetError !== undefined')
                result = await pg.evaluate('({error: window.__assetError, ready: window.__ready, render: P.render})')
                await b.close()
                return result
        r = asyncio.run(run())
        self.assertTrue(r['render'])
        self.assertIn('bad asset', r['error'])
        self.assertIsNone(r['ready'])

    def test_rejected_asset_wait_is_visible_in_preview(self):
        async def run():
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                b = await p.chromium.launch()
                pg = await b.new_page()
                await pg.route('**/*', lambda route: route.fulfill(status=200, content_type='text/html', body='<div id="stage"></div><script>window.ANIM={meta:{duration:10},cueList:[],cues:{},words:[]}</script>'))
                await pg.goto('http://geometry.test/')
                await pg.add_script_tag(path=str(ROOT / '_runtime' / 'player.js'))
                await pg.evaluate("P.wait(Promise.reject(Error('bad preview asset'))); window.dispatchEvent(new Event('load'))")
                await pg.wait_for_function('window.__assetError !== undefined')
                result = await pg.locator('#stage pre').inner_text()
                await b.close()
                return result
        self.assertIn('bad preview asset', asyncio.run(run()))


if __name__ == "__main__":
    unittest.main()
