---
id: "particle-field"
title: "Particle field"
description: "Glowing dots drift across the frame with depth: near dots are bigger, faster and brighter. A calm backdrop under a whole scene."
tags: ["background", "particles", "dust", "bokeh", "stars", "ambient", "depth", "glow", "drift", "canvas"]
kind: "fx"
engine: "both"
status: "approved"
files: ["particle-field.js", "particle-field.css"]
depends: ["core"]
api: ["FX.particleField(H, root, {from = 0, to, color: 'accent', count = 70, angle = 8, speed = 1, size = 14, minSize = 2, drift = 4, glow = 1.6, intensity = 1, seed = 1}): canvas behind the content of root", "returns {canvas}"]
preview_at: 2.0
source: {"site": "remotionui", "name": "particle-field", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/particle-field.tsx", "license": "MIT"}
---

# particle-field

A canvas of drifting dots. Put it first in the stage (or in a shot) so the content sits on top. It draws from `from` to `to` (default: the end of the video). `color` is a brand colour role (`accent`, `accent2`, `ink`, `green`). `angle` 0 drifts up, 90 to the right.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.particleField(H, document.getElementById('stage'), { color: 'accent2', count: 90 });
// HyperFrames
const H = Blocks.core(tl);
FX.particleField(H, document.querySelector('[data-composition-id="main"]'), { to: window.ANIM.meta.duration });
```

Rewritten for VideoFactory from RemotionUI `ParticleField` (MIT). No upstream code is copied.
