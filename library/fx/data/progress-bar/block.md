---
id: "progress-bar"
title: "Progress bar"
description: "A pill-shaped bar fills from 0 to a value while the number above it counts up in step; use it for one percentage or score that the voice names."
tags: ["bar", "progress", "percent", "data", "chart", "fill", "counter", "score"]
kind: "fx"
engine: "both"
status: "approved"
files: ["progress-bar.js", "progress-bar.css"]
depends: ["core"]
api: ["FX.progressBar(H, el, {at, dur = 1.2, value = 72, max = 100, label = '', suffix = '%', decimals = 0, showValue = true, width = 1200, height = 40, color: 'accent', trackColor: 'line'}): builds the bar inside el; the bar fills over `dur` seconds from `at`", "returns {el, root, label, value, track, fill}"]
preview_at: 1.5
twins: ["remotionui/progress-bar"]
source: {"site": "onda", "name": "progress-bar", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/progress-bar/ProgressBar.tsx", "license": "MIT"}
---

# progress-bar

A label on the left and the number on the right sit on the ground above the track, so they stay readable while the bar grows. The fill and the number follow one calm ease with no overshoot. The number is set from the time, rounded to `decimals`, so a seek always shows the same picture. `color` and `trackColor` take a brand role name. Place `el` with CSS; the part sets only its own width.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.progressBar(H, document.querySelector('#bar'), { at: H.at('proof+0.2'), value: 72, label: 'Videos rendered' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.progressBar(H, document.querySelector('#bar'), { at: cue('proof') + 0.2, value: 72, label: 'Videos rendered' });
```

Rewritten for VideoFactory from Onda `ProgressBar` (MIT). No upstream code is copied.
