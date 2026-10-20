---
id: "browser"
title: "Browser window for real recordings"
description: "Browser window that shows real screen recordings or screenshots (anim.py record/grab), with only the domain in the address bar and a zoom to the important part."
tags: ["browser", "window", "recording", "screenshot", "screen recording", "capture", "website", "url", "zoom", "real"]
kind: "block"
category: "interface"
engine: "hyperframes"
files: ["browser.js", "browser.css"]
depends: ["core"]
api: ["const b = Blocks.browser(H, rootEl, {url})", "b.play(frames, fps, t0): recorded frames (assets/<name>/f001.jpg ...), the last one stays", "b.image(src, at): one screenshot", "b.zoom({x, y, w}, at[, dur])"]
preview_at: 1.0
---

# browser

Only the domain of `url` is shown. Frames come from `anim.py record` (12 fps) and are already privacy-scanned and cropped (`_shared/capture.md`).

See `demo.html` for a working example.
