---
id: "grid-pixelate"
title: "Grid pixelate"
description: "Square cells of the next shot's ground colour fill the frame in a seeded scatter, the shots swap under them, then the cells clear; a retro, high-energy cut between two scenes (cut K5 variant)."
tags: ["transition", "grid", "pixelate", "mosaic", "cells", "cut", "scene", "scatter", "retro"]
kind: "fx"
engine: "both"
status: "approved"
files: ["grid-pixelate.js", "grid-pixelate.css"]
depends: ["core"]
api: ["FX.gridPixelate(H, from, to, {at, dur = 0.6, cols = 16, rows = cols * height / width, seed = 1, accent = 0, ground = null|role}): from is shot A, to is shot B, both full-frame on one stage; the cells run from `at` to `at + dur`, the shots swap at `at + dur / 2`", "cols and rows are 2-64; seed sets the scatter (same seed, same order); accent is the share of cells painted in the accent colour (0-1); ground is a colour role for the cells (default: the background B already has)", "returns {canvas, end}"]
preview_at: 1.5
twins: ["remotionui/grid-pixelate-wipe"]
source: {"site": "onda", "name": "grid-pixelate", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/transitions/grid-pixelate/gridPixelate.tsx", "license": "MIT"}
---

# grid-pixelate

A K5 cut (`_shared/transitions.md`) with a hard, stepped look. In the first half every cell turns on at its own seeded time, so shot A is covered. In one frame in the middle the shots swap. In the second half the cells turn off in a different scatter and shot B shows through. Cells never fade: each one is on or off. Length 0.6 s; start it 0.1-0.2 s before the voice phrase ends.

The part sets the visibility of both shots: B is hidden before the middle, A is hidden after it. Give the shots no `data-cue`. Both shots must be full-frame, positioned elements in the same parent, A first. The part adds one canvas to that parent and sets inline `z-index` 1, 2 and 3 on A, B and the canvas. Start B's hero 0.1 s before `at + dur`.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.gridPixelate(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: H.at('point-0.3'), cols: 12 });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.gridPixelate(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: cue('point') - 0.3, accent: 0.06, seed: 4 });
```

Rewritten for VideoFactory from Onda `GridPixelate` (MIT). No upstream code is copied.
