---
id: "mesh-gradient"
title: "Mesh gradient"
description: "Soft blobs of brand colour drift slowly behind a scene; a quiet atmosphere layer for a full-frame backdrop, never the subject."
tags: ["background", "gradient", "mesh", "blobs", "ambient", "atmosphere", "soft", "drift", "colour"]
kind: "fx"
engine: "both"
status: "draft"
files: ["mesh-gradient.js", "mesh-gradient.css"]
depends: ["core"]
api: ["FX.meshGradient(H, root, {from = 0, to, colors = ['accent', 'line', 'dim'], speed = 1, size = 0.45, opacity = 0.5, background = null, seed = 1}): a backdrop as the first child of root, drawn from `from` to `to` (default: the end of the video)", "colors is a list of brand colour roles, one blob each; size is the blob radius as a share of the stage width; speed 1 is one slow lap in about 16 s; opacity is the strength of the blobs (keep it low); background is an optional colour role painted under the blobs; seed sets the places and phases", "returns {el}"]
preview_at: 2.0
twins: ["remotionui/mesh-gradient-bg"]
source: {"site": "onda", "name": "mesh-gradient", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/mesh-gradient/MeshGradient.tsx", "license": "MIT"}
---

# mesh-gradient

One radial-gradient blob per colour role. Each blob drifts on a slow sine path from its own seeded phase, so the picture is a pure function of the time. The blobs sit under the content of `root` (put the call first), softly blurred.

Do not put it under a centred title: "a centred title on a gradient" is a banned default (`_shared/motion.md`, Banned defaults). Keep the text on one side, or use the gradient behind a scene that has other visual layers. Keep `opacity` low: this is atmosphere, not subject. In a dark brand `line` and `dim` give a calm haze and `accent` gives the one warm spot.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.meshGradient(H, document.getElementById('stage'), { colors: ['accent', 'line'], opacity: 0.5 });
// HyperFrames
const H = Blocks.core(tl);
FX.meshGradient(H, document.querySelector('[data-composition-id="main"]'), { to: window.ANIM.meta.duration, speed: 0.7 });
```

Rewritten for VideoFactory from Onda `MeshGradient` (MIT). No upstream code is copied.
