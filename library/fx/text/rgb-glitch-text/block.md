---
id: "rgb-glitch-text"
title: "Rgb glitch text"
description: "Two colour copies ride just off the text and burst wider now and then, then the text settles clean; a short high-energy hit for a title."
tags: ["glitch", "rgb", "chromatic", "split", "text", "title", "distortion", "burst", "tech"]
kind: "fx"
engine: "both"
status: "approved"
files: ["rgb-glitch-text.js", "rgb-glitch-text.css"]
depends: ["core"]
api: ["FX.rgbGlitchText(H, el, {at, dur = 2.4, split = 0.02, intensity = 0.07, period = 0.8, burst = 0.2, rate = 12, seed = 7, color = 'ink', colorA = 'accent', colorB = 'green', text = el.textContent}): the text snaps in at `at`, the glitch ends at `at + dur`", "returns {el, end}"]
preview_at: 0.5
twins: ["remotionui/rgb-glitch-text", "remotion-bits/bit-glitch-in"]
source: {"site": "onda", "name": "rgb-glitch-text", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/rgb-glitch-text/RgbGlitchText.tsx", "license": "MIT"}
---

# rgb-glitch-text

The text snaps in at `at` with a burst, keeps a small colour split (`split` em), and shows a burst every `period` seconds that lasts `burst` seconds. The burst offsets come from a seeded generator, so the same time always gives the same picture. At `at + dur` the copies disappear and the text stays clean. `split` and `intensity` are in em.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.rgbGlitchText(H, document.querySelector('#title'), { at: H.at('hook+0.2') });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.rgbGlitchText(H, document.querySelector('#title'), { at: cue('hook') + 0.2, dur: 1.6, seed: 12 });
```

Rewritten for VideoFactory from Onda `RgbGlitchText` (MIT). No upstream code is copied.
