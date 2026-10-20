---
id: "gauge-dial"
title: "Gauge dial"
description: "A dial arc fills and a needle sweeps to a target while the readout counts up under it; use it for one score, rate or level against a known range."
tags: ["gauge", "dial", "needle", "meter", "score", "speedometer", "metric", "data", "level"]
kind: "fx"
engine: "both"
status: "draft"
files: ["gauge-dial.js", "gauge-dial.css"]
depends: ["core"]
api: ["FX.gaugeDial(H, el, {at, dur = 1.6, value = 72, min = 0, max = 100, label = '', unit = '%', decimals = 0, size = 640, thickness = 44, sweep = 240, tickCount = 9, showRange = true, color: 'accent', trackColor: 'line'}): builds the dial inside el; the needle sweeps over `dur` seconds from `at`", "returns {el, root, value}"]
preview_at: 1.5
source: {"site": "remotionui", "name": "gauge-dial", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/gauge-dial.tsx", "license": "MIT"}
---

# gauge-dial

An arc of `sweep` degrees centred on 12 o'clock, with tick marks outside it. The needle and the filled arc follow one calm ease with no overshoot. The readout (112 px), the label (40 px) and the min and max (32 px) sit in the open gap at the bottom and below the arc ends, on the ground: the needle never reaches them. The readout is set from the time and rounded to `decimals`. Give `el` the same width and height as `size`.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.gaugeDial(H, document.querySelector('#dial'), { at: H.at('score+0.2'), value: 72, label: 'Quality score' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.gaugeDial(H, document.querySelector('#dial'), { at: cue('score') + 0.2, value: 420, max: 500, unit: ' ms', label: 'Response time' });
```

Rewritten for VideoFactory from RemotionUI `GaugeDial` (MIT). No upstream code is copied.
