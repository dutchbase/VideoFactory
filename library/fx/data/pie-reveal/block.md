---
id: "pie-reveal"
title: "Pie reveal"
description: "A single ring fills clockwise from 12 o'clock to a percent while the big number in its middle counts up; use it for one share or score."
tags: ["pie", "ring", "percent", "chart", "data", "reveal", "donut", "counter", "gauge"]
kind: "fx"
engine: "both"
status: "draft"
files: ["pie-reveal.js", "pie-reveal.css"]
depends: ["core"]
api: ["FX.pieReveal(H, el, {at, dur = 1.4, value = 72, max = 100, label = '', suffix = '%', decimals = 0, size = 560, thickness = 56, color: 'accent', trackColor: 'line'}): builds the ring inside el; it fills over `dur` seconds from `at`", "returns {el, root, value, label, arc}"]
preview_at: 1.5
source: {"site": "onda", "name": "pie-reveal", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/pie-reveal/PieReveal.tsx", "license": "MIT"}
---

# pie-reveal

An SVG ring on a quiet track. The arc and the number in the middle follow one calm ease with no overshoot. The number is set from the time and rounded to `decimals`, so a seek always shows the same picture. The number is 20% of `size` (112 px at the default), the optional `label` is 36 px; both sit in the empty middle of the ring, never on the arc. `color` and `trackColor` take a brand role name. Give `el` the same width and height as `size`.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.pieReveal(H, document.querySelector('#ring'), { at: H.at('proof+0.2'), value: 72, label: 'Videos done' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.pieReveal(H, document.querySelector('#ring'), { at: cue('proof') + 0.2, value: 72, label: 'Videos done' });
```

Rewritten for VideoFactory from Onda `PieReveal` (MIT). No upstream code is copied.
