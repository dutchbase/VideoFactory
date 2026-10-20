# Render costs: cards-3d

2026-10-13; Intel Core i5-8250U CPU @ 1.60 GHz, Intel UHD Graphics 620 (ANGLE-Mesa hardware GPU), Chromium 139.0.7258.5, HyperFrames 0.8.86, local assets and fonts. No new dependencies.

Full 30-second render: 1080×1920, 30 fps, 900 frames, high quality, three render workers, music through the existing mixer and the loudness master. The demo action was repeated three times with camera arrivals. No other renders or tests ran during this measurement.

- Total command time including check, render, mix, master and video check: 51.026 s.
- Seconds per video second: 1.701.
- Image and mix time before the master, from the render JSON: 42.795 s.

The measurements ran one after the other in the same showcase project. Raw measurement, audio and video reports stayed with that project and are not part of this repository. They are historical benchmark reports, not a check of a later showcase version. Hardware and load can change the times. Only one brand was measured here.
