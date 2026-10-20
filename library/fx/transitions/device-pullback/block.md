---
id: "device-pullback"
title: "Device pullback"
description: "The outgoing shot starts at about 3x, pulls back slowly, then snaps in one frame into a laptop or phone frame; use it for the beat 'this is inside the real product' (cut K6)."
tags: ["transition", "device", "mockup", "pullback", "reveal", "laptop", "phone", "cut", "scene", "product"]
kind: "fx"
engine: "both"
status: "draft"
files: ["device-pullback.js", "device-pullback.css"]
depends: ["core"]
api: ["FX.devicePullback(H, from, to, {at, dur = 1, hold = 0.6, device = 'laptop'|'phone', start = 3, ratio = 0.56, focus = [0.5, 0.5], frame = 'line', ground = 'cream'}): from is shot A (the product screen), to is shot B, both full-frame on one stage; the pull-back runs from `at` to `at + dur`, the snap is at `at + dur`, the cut to B at `at + dur + hold`", "start is the scale A starts at; ratio is the scale change of the last step (K6: about 0.56); focus is the point of A that sits in the middle at the start, as a share of the frame; frame and ground are colour roles for the device and the ground around it", "returns {wrap, snap, cut}: the device element and the two times"]
preview_at: 1.5
source: {"site": "onda", "name": "device-pullback", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/transitions/device-pullback/devicePullback.tsx", "license": "MIT"}
---

# device-pullback

Cut K6 (`_shared/transitions.md`). Shot A shows one fragment at 3x (aim it with `focus`) and pulls back at a steady rate. At `at + dur` one frame snaps it down by `ratio` (about 0.56) to the screen size, and the device frame (bezel, base or camera dot, shadow) is there around it. After `hold` seconds a hard cut shows shot B. The device frame never draws in gradually: the snap is the beat.

The laptop adds a base under the screen; the phone has a camera dot and rounder corners, and suits the tall format. The screen has the shape of the frame. The part sets the visibility of both shots. Give the shots no `data-cue`. Both shots must be full-frame, positioned elements in the same parent, A first. The part sets `scale`, `x`, `y` and `clip-path` on A with GSAP and inline `z-index` 1, 2 and 3 on the device, A and B. Let A move a little during the hold if the beat needs it; the device itself stays still.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.devicePullback(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: H.at('demo'), focus: [0.7, 0.3] });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.devicePullback(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: cue('demo'), dur: 1.2, device: 'laptop' });
```

Rewritten for VideoFactory from Onda `DevicePullback` (MIT). No upstream code is copied.
