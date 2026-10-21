---
id: "dynamic-grid"
title: "Dynamic grid"
description: "A technical grid of lines or dots drifts diagonally and loops by one cell; a calm full-frame backdrop for data, dev and dashboard scenes."
tags: ["background", "grid", "lines", "dots", "technical", "dashboard", "drift", "atmosphere", "data"]
kind: "fx"
engine: "both"
status: "approved"
files: ["dynamic-grid.js", "dynamic-grid.css"]
depends: ["core"]
api: ["FX.dynamicGrid(H, root, {from = 0, to, cell = 96, speed = 36, angle = 45, variant = 'lines'|'dots', color = 'dim', opacity = 0.5, fade = true, glow = 0}): a grid as the first child of root, drawn from `from` to `to` (default: the end of the video)", "cell is the size of one cell in stage px; speed is the drift in px per second; angle is the drift direction in degrees (0 = right, 90 = down); color is a brand colour role; fade softens the edges of the frame; glow (0-1) adds an accent light in the middle", "returns {el}"]
preview_at: 2.0
twins: ["remotionui/dynamic-grid"]
source: {"site": "onda", "name": "dynamic-grid", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/dynamic-grid/DynamicGrid.tsx", "license": "MIT"}
---

# dynamic-grid

A grid plane one cell larger than the frame on each side, moved by `speed` px per second along `angle` and wrapped by one cell, so the loop has no seam and the picture depends only on the time. `variant: 'dots'` draws a dot in each cell instead of lines. With `fade` the grid dissolves toward the edges of the frame.

Use it for data and dev scenes. Keep `opacity` low so text stays legible; the drift is the only motion of the layer. `glow` is off by default: do not put a glow under a centred title (`_shared/motion.md`, Banned defaults).

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.dynamicGrid(H, document.getElementById('stage'), { variant: 'dots', cell: 80 });
// HyperFrames
const H = Blocks.core(tl);
FX.dynamicGrid(H, document.querySelector('[data-composition-id="main"]'), { to: window.ANIM.meta.duration, speed: 50, angle: 30 });
```

Rewritten for VideoFactory from Onda `DynamicGrid` (MIT). No upstream code is copied.
