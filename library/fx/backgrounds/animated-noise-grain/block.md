---
id: "animated-noise-grain"
title: "Animated noise grain"
description: "Film grain laid over the whole frame on a canvas; the pattern changes every second frame and is the same on every seek. Use it to take the clean digital look off a scene."
tags: ["grain", "noise", "film", "texture", "overlay", "vignette", "analog", "canvas", "background"]
kind: "fx"
engine: "both"
status: "draft"
files: ["animated-noise-grain.js", "animated-noise-grain.css"]
depends: ["core"]
api: ["FX.animatedNoiseGrain(H, root, {from = 0, to, opacity = 0.14, size = 2, hold = 2, fps = 30, vignette = 0.6, seed = 1}): canvas over the content of root, drawn from `from` to `to` (default: the end of the video)", "returns {canvas}"]
preview_at: 1.5
twins: ["onda/grain-overlay"]
source: {"site": "remotionui", "name": "animated-noise-grain", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/animated-noise-grain.tsx", "license": "MIT"}
---

# animated-noise-grain

Light and dark specks over the frame, one pattern per `hold` frames (2 gives the 15 fps chatter of real film at 30 fps). The pattern comes from `FX.kit.rand` seeded by the frame index, so the same frame always gives the same grain, also when you seek backwards. `opacity` is the strength (film sits at 0.12 to 0.25; above 0.4 it reads as damage), `size` is the grain size in stage pixels, `vignette` adds grain toward the corners. Call it last, after the content, so it sits on top. Use one grain layer per scene, kept low: it must not hide text.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.animatedNoiseGrain(H, document.getElementById('stage'), { opacity: 0.16 });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.animatedNoiseGrain(H, document.querySelector('[data-composition-id="main"]'), { to: window.ANIM.meta.duration, hold: 2 });
```

Rewritten for VideoFactory from RemotionUI `AnimatedNoiseGrain` (MIT). No upstream code is copied.
