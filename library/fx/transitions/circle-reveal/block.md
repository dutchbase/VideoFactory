---
id: "circle-reveal"
title: "Circle reveal"
description: "A round hole opens from any point of the frame and shows the next full-frame shot, led by a strip of its ground colour; use it for a clean, deliberate scene change (cut K5)."
tags: ["transition", "circle", "iris", "reveal", "cut", "scene", "mask", "radial", "wipe"]
kind: "fx"
engine: "both"
status: "draft"
files: ["circle-reveal.js", "circle-reveal.css"]
depends: ["core"]
api: ["FX.circleReveal(H, from, to, {at, dur = 0.58, x = 0.5, y = 0.5, soft = 0.12, lag = 0.2, push = 1.04, ground = null|role|false}): from is shot A, to is shot B, both full-frame on one stage; the circle opens from `at` to `at + dur`", "x and y are the centre of the circle as a share of the frame; soft is the soft edge as a share of the radius; lag is how far B trails the strip (share of dur); push is the scale A leans to under the hole (1 = still); ground is a colour role for the strip (default: the background B already has, false = no strip)", "returns {panel, end}: the strip element and the end time"]
preview_at: 1.5
twins: ["onda/iris"]
source: {"site": "remotionui", "name": "transition-circle-reveal", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/transition-circle-reveal.tsx", "license": "MIT"}
---

# circle-reveal

A K5 cut (`_shared/transitions.md`) with a round edge. The circle grows from (`x`, `y`) until it covers the far corner, so no wedge stays shut. A disc in B's ground colour leads; B follows inside it. A pushes in a little (4 %) under the hole. Length 0.58 s; start it 0.1-0.2 s before the voice phrase ends.

The part sets the visibility of both shots: B is hidden before `at`, A is hidden after `at + dur`. Give the shots no `data-cue`. Both shots must be full-frame, positioned elements in the same parent, A first. The part sets inline `z-index` 1, 2 and 3 on A, the disc and B. Open the circle from the thing the viewer looks at, not from the middle by default.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.circleReveal(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: H.at('point-0.2'), x: 0.8, y: 0.3 });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.circleReveal(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: cue('point') - 0.2 });
```

Rewritten for VideoFactory from RemotionUI `TransitionCircleReveal` (MIT). No upstream code is copied.
