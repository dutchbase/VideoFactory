---
id: "shimmer-sweep"
title: "Shimmer sweep"
description: "A single band of accent colour sweeps once (or a few times) across the text without moving the layout; a restrained emphasis for a key phrase."
tags: ["shimmer", "sweep", "shine", "highlight", "emphasis", "text", "light", "band", "gradient"]
kind: "fx"
engine: "both"
status: "approved"
files: ["shimmer-sweep.js", "shimmer-sweep.css"]
depends: ["core"]
api: ["FX.shimmerSweep(H, el, {at, dur = 0.9, repeat = 1, interval = 1.6, color = 'ink', shimmerColor = 'accent', angle = 100, text = el.textContent}): the first sweep runs from `at` to `at + dur`", "returns {el, text, end}"]
preview_at: 0.8
twins: ["remotionui/light-sweep-text"]
source: {"site": "onda", "name": "shimmer-sweep", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/shimmer-sweep/ShimmerSweep.tsx", "license": "MIT"}
---

# shimmer-sweep

The text is painted by a gradient: base colour with one band of `shimmerColor`. Only the gradient position moves, so the layout stays still. After the sweep the text is plain again. `repeat` runs the sweep more than once, `interval` seconds apart. The band moves from left to right with a power2 in-out ease.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.shimmerSweep(H, document.querySelector('#title'), { at: H.at('point') });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.shimmerSweep(H, document.querySelector('#title'), { at: cue('point'), repeat: 2, interval: 1.4 });
```

Rewritten for VideoFactory from Onda `ShimmerSweep` (MIT). No upstream code is copied.
