---
id: "spotlight"
title: "Spotlight"
description: "Dims everything in an element except one circle or rounded rectangle, with an accent ring on the edge; the light can move on and switch off."
tags: ["spotlight", "focus", "dim", "highlight", "vignette", "attention", "darken", "reveal", "look here", "light"]
kind: "fx"
engine: "both"
status: "draft"
files: ["spotlight.js", "spotlight.css"]
depends: ["core"]
api: ["FX.spotlight(H, el, {at, dur = 0.7, shape = 'circle'|'rect', target: el|selector, x, y, r = 200, w = 500, h = 300, radius = 28, pad = 28, dim = 0.78, color: 'cream', ring = true, ringColor: 'accent', moves: [{at, dur = 0.7, target|x,y,r|x,y,w,h}], exitAt, exitDur = 0.5}): a veil is added on top of el", "returns {veil, ring}"]
preview_at: 1.5
twins: ["remotionui/callout-spotlight"]
source: {"site": "onda", "name": "spotlight", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/spotlight/Spotlight.tsx", "license": "MIT"}
---

# spotlight

The lit area closes in from the whole frame while the veil darkens, on a calm spring. Name the area with a `target` element (the area is the element plus `pad` px) or with `x`, `y` (the centre) and `r` for a circle or `w`, `h` for a rectangle. `moves` slides the light to the next area, one entry per move. `exitAt` opens it up again. The veil is the `color` role (default the page ground), so the rest of the scene goes dark. The target position is read from its layout when you call the part.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.spotlight(H, document.getElementById('stage'), { at: H.at('focus'), shape: 'rect', target: document.querySelector('.card') });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.spotlight(H, document.querySelector('[data-composition-id="main"]'), { at: cue('focus'), x: 960, y: 540, r: 260, exitAt: cue('end') });
```

Rewritten for VideoFactory from Onda `Spotlight` (MIT). No upstream code is copied.
