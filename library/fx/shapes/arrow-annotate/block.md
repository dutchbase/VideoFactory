---
id: "arrow-annotate"
title: "Arrow annotate"
description: "A hand-drawn arrow draws itself from a point to a target element, with an optional label; use it to tell the viewer where to look."
tags: ["arrow", "annotate", "pointer", "hand-drawn", "sketch", "label", "highlight", "draw-on", "look here"]
kind: "fx"
engine: "both"
status: "approved"
files: ["arrow-annotate.js", "arrow-annotate.css"]
depends: ["core"]
api: ["FX.arrowAnnotate(H, root, {at, dur = 0.8, from: {x, y}, target: el|selector, to: {x, y}, label, labelSize = 44, color: 'accent', strokeWidth = 6, headSize = 38, bow = 0.25, gap = 24, sketch = true, seed = 3, exitAt, exitDur = 0.25}): the arrow is added to root; points are stage px inside root", "returns {svg, from, to}"]
preview_at: 1.5
source: {"site": "remotionui", "name": "arrow-annotate", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/arrow-annotate.tsx", "license": "MIT"}
---

# arrow-annotate

An arrow draws itself from `from` to a `target` element (or a plain point `to`). The shaft bows by `bow` (negative bows the other way). A second faint pass over the shaft gives the hand-drawn look; the head lands as the stroke ends. `label` sits behind the start of the shaft. The arrow stops `gap` px before the target. Place `root` (usually the stage) so it holds both the arrow and the target. The target position is read from its layout when you call the part, so CSS transforms on it are not counted. `exitAt` fades the arrow out.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.arrowAnnotate(H, document.getElementById('stage'), { at: H.at('hook+0.2'), from: { x: 600, y: 600 }, target: document.querySelector('.card'), label: 'Look here' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.arrowAnnotate(H, document.querySelector('[data-composition-id="main"]'), { at: cue('hook') + 0.2, from: { x: 600, y: 600 }, target: document.querySelector('.card') });
```

Rewritten for VideoFactory from RemotionUI `ArrowAnnotate` (MIT). No upstream code is copied.
