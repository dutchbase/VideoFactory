---
id: "ken-burns"
title: "Ken burns"
description: "A slow, steady zoom and pan over any element, usually a picture; the documentary move for a still image."
tags: ["ken burns", "zoom", "pan", "drift", "photo", "still", "documentary", "camera", "slow", "cinematic"]
kind: "fx"
engine: "both"
status: "draft"
files: ["ken-burns.js", "ken-burns.css"]
depends: ["core"]
api: ["FX.kenBurns(H, el, {at, dur = 5, fromScale = 1, toScale = 1.1, from: {x: 0.5, y: 0.5}, to: {x: 0.5, y: 0.5}, clip = true}): el zooms from `at` for `dur` seconds and then holds", "returns {el, wrap}"]
preview_at: 1.5
source: {"site": "onda", "name": "ken-burns", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/ken-burns/KenBurns.tsx", "license": "MIT"}
---

# ken-burns

The element scales from `fromScale` to `toScale` in a straight line, with no ease, so the drift is constant. The scale origin moves from `from` to `to` (fractions of the element), and that makes the pan. The element is wrapped in a frame of the same size and place that clips it (`clip: false` skips the frame when you clip it yourself). The part never loads media: pass a block with a layout box: an `img`, a `video` or a `div` (put an inline SVG in a `div`).

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.kenBurns(H, document.querySelector('.photo'), { at: H.at('hook'), dur: 5, toScale: 1.15, to: { x: 0.7, y: 0.4 } });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.kenBurns(H, document.querySelector('.photo'), { at: cue('hook'), dur: 5, toScale: 1.15 });
```

Rewritten for VideoFactory from Onda `KenBurns` (MIT). No upstream code is copied.
