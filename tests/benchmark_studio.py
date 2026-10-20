"""Read-only Studio timings. Run in omabox; JSON goes to stdout."""
import argparse
import asyncio
import json
import math
from time import perf_counter
from playwright.async_api import async_playwright

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rounds', type=int, default=20)
    parser.add_argument('--base', default='http://127.0.0.1:8799')
    args = parser.parse_args()
    if args.rounds < 1:
        parser.error('--rounds must be positive')
    base = args.base.rstrip('/')
    targets = [('settings', '/settings', '#main h1'), ('script', '/videos/videofactory/review/script', 'textarea.output-editor'), ('library', '/library', '.material-tile')]
    output = {'widths': {}}
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        output['browser'] = browser.version
        for width in (1440, 390):
            page = await browser.new_page(viewport={'width': width, 'height': 1000})
            page.set_default_timeout(90000)
            readings = {}
            for name, path, selector in targets:
                cold = []
                for _ in range(args.rounds):
                    started = perf_counter()
                    await page.goto(base + path, wait_until='domcontentloaded')
                    await page.locator(selector).first.wait_for(state='visible')
                    if name == 'script':
                        assert await page.locator(selector).first.input_value()
                    if name == 'library':
                        assert await page.locator('.material-tile').count() >= 48
                    cold.append(round((perf_counter() - started) * 1000, 1))
                warm = []
                for _ in range(args.rounds):
                    # Route links share the normal in-page navigation handler.
                    await page.evaluate("""path => { const a=document.createElement('a');a.href=path;a.textContent='benchmark';document.body.append(a);a.click();a.remove(); }""", '/videos' if name == 'settings' else '/settings')
                    await page.locator('.video-tile' if name == 'settings' else '#main h1').first.wait_for()
                    started = perf_counter()
                    await page.evaluate("""path => { const a=document.createElement('a');a.href=path;a.textContent='benchmark';document.body.append(a);a.click();a.remove(); }""", path)
                    await page.locator(selector).first.wait_for(state='visible')
                    warm.append(round((perf_counter() - started) * 1000, 1))
                readings[name] = {'first_useful_ms': cold, 'navigation_ms': warm, 'navigation_p95_ms': sorted(warm)[math.ceil(.95*len(warm))-1]}
            output['widths'][width] = readings
            await page.close()
        await browser.close()
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
