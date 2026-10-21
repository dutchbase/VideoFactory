---
id: "zoom-through"
title: "Zoom through"
description: "The old shot pushes past the lens and blurs, a hard cut lands, and the new shot settles out of the same push from blur to sharp; use it when the video already uses blur (cut K4)."
tags: ["transition", "zoom", "push", "blur", "cut", "scene", "camera", "through", "depth"]
kind: "fx"
engine: "both"
status: "approved"
files: ["zoom-through.js", "zoom-through.css"]
depends: ["core"]
api: ["FX.zoomThrough(H, from, to, {at, out = 0.2, dur = 0.5, blur = 18, outScale = 1.2, inScale = 0.75}): from is shot A, to is shot B, both full-frame on one stage; A exits from `at`, the cut is at `at + out`, B settles over `dur`", "out is the length of A's exit in s; dur is the length of B's arrival in s; blur is the blur in px at the cut (motion.md: 10 for objects, 18-20 for full-frame surfaces); outScale is A's end scale; inScale is B's start scale", "returns {cut, end}: the cut time and the time B is at rest"]
preview_at: 1.5
twins: ["onda/zoom"]
source: {"site": "remotionui", "name": "zoom-through", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/zoom-through.tsx", "license": "MIT"}
---

# zoom-through

Cut K4 (`_shared/transitions.md`, numbers in `_shared/motion.md` Cuts). A scales 1 to 1.2 and blurs 0 to 18 px over 0.2 s, speeding up into the cut. One frame later B is on screen at scale 0.75 and the same blur, and settles to scale 1 and blur 0 over 0.5 s. B starts at equal or more blur than A ended with. There is no fade: the switch is one frame. The default blur is 18 px because the shots are full-frame surfaces; use `blur: 10` when only a small object blurs.

The part sets the visibility of both shots. Give the shots no `data-cue`. Both shots must be full-frame, positioned elements in the same parent, A first. The part sets `scale` and `filter` with GSAP and inline `z-index` 1 and 2. B's own hero should start moving at the cut.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.zoomThrough(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: H.at('point-0.2') });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.zoomThrough(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: cue('point') - 0.2, blur: 10 });
```

Rewritten for VideoFactory from RemotionUI `ZoomThrough` (MIT). No upstream code is copied.
