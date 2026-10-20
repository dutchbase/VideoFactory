# HyperFrames toolchain (optional)

HyperFrames turns HTML + GSAP into MP4 with headless Chrome and ffmpeg. It is an optional second render engine. The default engine stays `canvas`.

- Version is pinned exactly in `package.json` (`0.8.86`) and `package-lock.json`.
- Install: `cd tools/hyperframes && npm ci --ignore-scripts`. The package has no postinstall script.
- Browser: `hyperframes doctor` finds a Chrome in `~/.cache/puppeteer`. If none exists, run `HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1 node_modules/.bin/hyperframes browser ensure`.
- Always run it with `HYPERFRAMES_NO_TELEMETRY=1` and `DO_NOT_TRACK=1`. The `hf()` helper in `anim.py` sets both.
- No Lambda, no cloud render.
- Upgrade: pick a version at least 14 days old, change `package.json`, run `npm install --ignore-scripts`, commit both files, update `THIRD-PARTY-NOTICES.md`.
- `hyperframes doctor` exits 0 even when optional parts (whisper, TTS, music) are missing. Only Chrome and ffmpeg matter here.
