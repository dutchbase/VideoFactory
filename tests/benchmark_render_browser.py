"""Compare isolated browser-per-worker and shared-browser render captures.

Run inside omabox: .venv/bin/python tests/benchmark_render_browser.py
"""

import asyncio
import hashlib
import json
import statistics
import tempfile
import time
from pathlib import Path

from playwright.async_api import async_playwright


WIDTH, HEIGHT, FPS, FRAMES = 1920, 1080, 6, 60
HTML = """<!doctype html><canvas width=1920 height=1080></canvas><script>
const c = document.querySelector('canvas'), g = c.getContext('2d');
window.__seek = t => {
  g.fillStyle = '#12243b'; g.fillRect(0,0,1920,1080);
  g.fillStyle = '#ee8661'; g.fillRect(80 + Math.floor(t*37),180,480,360);
  g.fillStyle = '#ffffff'; g.font = 'bold 94px sans-serif';
  g.fillText('Render ' + t.toFixed(3),100,680);
};
window.__seek(0);
</script>"""


async def capture(p, url, workers, shared):
    started = time.perf_counter()
    browser = await p.chromium.launch() if shared else None
    version = browser.version if browser else None
    frames = [None] * FRAMES

    async def worker(k):
        nonlocal version
        b = browser if shared else await p.chromium.launch()
        version = b.version
        context = await b.new_context(viewport={"width": WIDTH, "height": HEIGHT})
        try:
            page = await context.new_page()
            await page.goto(url)
            for f in range(k * FRAMES // workers, (k + 1) * FRAMES // workers):
                await page.evaluate("t => window.__seek(t)", f / FPS)
                frames[f] = hashlib.sha256(await page.screenshot(type="jpeg", quality=92)).hexdigest()
        finally:
            await context.close()
            if not shared:
                await b.close()

    try:
        await asyncio.gather(*(worker(k) for k in range(workers)))
    finally:
        if browser:
            await browser.close()
    return {"seconds": round(time.perf_counter() - started, 3), "browser": version,
            "frames_sha256": hashlib.sha256("".join(frames).encode()).hexdigest(), "frame_hashes": frames}


async def main():
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "fixture.html"
        page.write_text(HTML)
        runs = []
        async with async_playwright() as p:
            for workers in (1, 4):
                for repeat in range(3):
                    for shared in (False, True):
                        result = await capture(p, page.as_uri(), workers, shared)
                        runs.append({"workers": workers, "repeat": repeat + 1,
                                     "architecture": "shared" if shared else "per-worker", **result})
        baseline = runs[0]["frame_hashes"]
        identical = all(run["frame_hashes"] == baseline for run in runs)
        summary = {str(workers): {arch: statistics.median(r["seconds"] for r in runs
                    if r["workers"] == workers and r["architecture"] == arch)
                    for arch in ("per-worker", "shared")} for workers in (1, 4)}
        print(json.dumps({"fixture": "authored canvas", "capture": "Playwright JPEG quality 92; no encoder",
                          "environment": "isolated omabox box-5", "width": WIDTH, "height": HEIGHT,
                          "fps": FPS, "frames": FRAMES, "all_frames_identical": identical,
                          "median_seconds": summary,
                          "runs": [{k: v for k, v in run.items() if k != "frame_hashes"} for run in runs]}, indent=2))
        if not identical:
            raise SystemExit("frame mismatch")


if __name__ == "__main__":
    asyncio.run(main())
