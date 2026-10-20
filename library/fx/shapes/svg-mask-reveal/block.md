---
id: "svg-mask-reveal"
title: "Svg mask reveal"
description: "An SVG shape (circle, star, heart, your own path) grows from a point and uncovers an element; use it for a shape-led reveal of a scene or a picture."
tags: ["mask", "reveal", "svg", "shape", "clip", "wipe", "star", "circle", "transition", "uncover"]
kind: "fx"
engine: "both"
status: "draft"
files: ["svg-mask-reveal.js", "svg-mask-reveal.css"]
depends: ["core"]
api: ["FX.svgMaskReveal(H, el, {at, dur = 1, shape = 'circle'|'diamond'|'square'|'hexagon'|'star'|'plus'|'heart'|'M ... Z' (path on a 0-100 box, absolute M L H V C Q Z), origin: {x: 0.5, y: 0.5}, rotation = 0, bouncy = false, invert = false}): el is clipped by the shape from `at`", "returns {el}"]
preview_at: 1.5
source: {"site": "remotionui", "name": "svg-mask-reveal", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/svg-mask-reveal.tsx", "license": "MIT"}
---

# svg-mask-reveal

The shape grows from `origin` (fractions of the element) until it covers the whole element; then the clip is removed. `rotation` turns it by that many degrees on the way. `bouncy` uses a spring with a little overshoot. `invert` runs it the other way: the shape shrinks and hides the element. A custom shape is a path on a 0-100 box with absolute commands only.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.svgMaskReveal(H, document.querySelector('.shot'), { at: H.at('hook'), shape: 'star', rotation: 60 });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.svgMaskReveal(H, document.querySelector('.shot'), { at: cue('hook'), shape: 'circle', origin: { x: 0.1, y: 0.9 } });
```

Rewritten for VideoFactory from RemotionUI `SvgMaskReveal` (MIT). No upstream code is copied.
