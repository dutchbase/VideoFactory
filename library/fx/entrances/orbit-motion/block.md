---
id: "orbit-motion"
title: "Ormotion"
description: "The children of an element travel round a tilted ellipse with depth (bigger and brighter in front); use it for a set of items around a central idea."
tags: ["orbit", "circle", "ellipse", "rotate", "carousel", "satellites", "items", "depth", "ring"]
kind: "fx"
engine: "both"
status: "draft"
files: ["orbit-motion.js", "orbit-motion.css"]
depends: ["core"]
api: ["FX.orbitMotion(H, el, {at, to, radiusX = 520, radiusY = 190, period = 8, phase = 0, tilt = -12, direction: 'cw'|'ccw' = 'cw', centerX = 50, centerY = 50, depth = 0.28, depthFade = 0.4, upright = true, showPath = false, enter = 0.7, stagger = 0.1}): children of el orbit from `at` to `to`", "returns {el, items}"]
preview_at: 1.5
source: {"site": "remotionui", "name": "orbit-motion", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/orbit-motion.tsx", "license": "MIT"}
---

# orbit-motion

Every child of `el` becomes an orbiting item, spaced evenly on the ellipse. `period` is the time of one turn in seconds. Items in front are bigger and brighter (`depth`, `depthFade`) and sit above items behind. From `at` the items fan out from the centre and fade in, `stagger` seconds apart. `el` needs a size; put a title in the middle as a separate element. `showPath` draws the ellipse in `--line`. `upright` keeps the items level. The orbit is the content, not an idle wobble: use it while the voice talks about the whole set.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.orbitMotion(H, document.querySelector('#ring'), { at: H.at('hook+0.2'), period: 6 });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.orbitMotion(H, document.querySelector('#ring'), { at: cue('hook') + 0.2, direction: 'ccw', showPath: true });
```

Rewritten for VideoFactory from RemotionUI `OrbitMotion` (MIT). No upstream code is copied.
