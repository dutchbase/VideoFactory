---
id: "callout"
title: "Callout"
description: "A label box lands next to one spot, then a line draws from the box to that spot; use it to name a part of the picture."
tags: ["callout", "label", "annotation", "pointer", "line", "tutorial", "name the part", "tooltip", "arrow"]
kind: "fx"
engine: "both"
status: "approved"
files: ["callout.js", "callout.css"]
depends: ["core"]
api: ["FX.callout(H, root, {at, label = 'Look here', target: el|selector, x, y, position = 'top-right'|'top-left'|'bottom-right'|'bottom-left', offset = 170, size = 52, color: 'accent', lineWidth = 5, dur = 0.5, lineDelay = 0.3, lineDur = 0.5, margin = 60, gap = 20, exitAt, exitDur = 0.25}): box and line are added to root; x, y and the target are stage px inside root", "returns {el: box, svg, anchor}"]
preview_at: 1.5
twins: ["onda/bounding-box"]
source: {"site": "onda", "name": "callout", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/callout/Callout.tsx", "license": "MIT"}
---

# callout

The box scales in on a calm spring. After `lineDelay` seconds the line draws from the box edge to the anchor and ends in a dot. The anchor is the centre of `target` (the line stops `gap` px before its edge) or the point `x`, `y`. `position` sets which side the box takes (`offset` px beyond the target's corner); the box stays inside `margin` px of the frame. The target position is read from its layout when you call the part. `exitAt` fades everything out.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.callout(H, document.getElementById('stage'), { at: H.at('hook+0.2'), target: document.querySelector('.card'), label: 'Start here' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.callout(H, document.querySelector('[data-composition-id="main"]'), { at: cue('hook') + 0.2, x: 900, y: 500, label: 'Look here', position: 'bottom-left' });
```

Rewritten for VideoFactory from Onda `Callout` (MIT). No upstream code is copied.
