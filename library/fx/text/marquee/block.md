---
id: "marquee"
title: "Marquee"
description: "A seamless band of words that scrolls sideways at a steady speed, with an accent dot between words; use it for a ticker row or a list of topics behind the voice."
tags: ["marquee", "ticker", "scroll", "band", "loop", "words", "text", "atmospheric", "list"]
kind: "fx"
engine: "both"
status: "approved"
files: ["marquee.js", "marquee.css"]
depends: ["core"]
api: ["FX.marquee(H, el, {at, to, items = words of el, speed = 120, direction: 'left'|'right' = 'left', gap = 96, size = 96, dots = true, color: 'ink', dur = 0.5}): fills el with a clipped, scrolling band; speed in px per second", "returns {el, track}"]
preview_at: 1.5
twins: ["remotionui/infinite-marquee"]
source: {"site": "onda", "name": "marquee", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/marquee/Marquee.tsx", "license": "MIT"}
---

# marquee

A row of words that scrolls at a steady speed (linear on purpose: a spring would look broken). The words repeat without a seam: the part measures one set and adds copies until the frame is covered. `items` is a list of strings; without it the words of `el` are used. `at` fades the band in and starts the scroll; `to` ends it (default: the end of the video). The row needs a width (for example `left:0; width:1920px`). `color` is a brand colour role for the words; the dots are always `accent`.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.marquee(H, document.querySelector('#band'), { at: H.at('hook+0.2'), items: ['Script', 'Voice', 'Scene'] });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.marquee(H, document.querySelector('#band'), { at: cue('hook') + 0.2, direction: 'right', speed: 90 });
```

Rewritten for VideoFactory from Onda `Marquee` (MIT). No upstream code is copied.
