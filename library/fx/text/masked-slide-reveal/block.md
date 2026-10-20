---
id: "masked-slide-reveal"
title: "Masked slide reveal"
description: "Words or lines slide up out of a line mask one after another; use it for a headline that builds word by word."
tags: ["mask", "slide", "reveal", "text", "words", "lines", "headline", "stagger", "entrance"]
kind: "fx"
engine: "both"
status: "draft"
files: ["masked-slide-reveal.js", "masked-slide-reveal.css"]
depends: ["core"]
api: ["FX.maskedSlideReveal(H, el, {at, dur = 0.55, stagger = 0.09, lines: null|[...], by: 'words'|'lines', align = 'center', gap = 0.28, text = el.textContent}): the items slide in from `at`", "returns {el, parts, end}"]
preview_at: 1.2
source: {"site": "remotionui", "name": "masked-slide-reveal", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/masked-slide-reveal.tsx", "license": "MIT"}
---

# masked-slide-reveal

A text without a line break reveals word by word; `lines` (an array, or a text with line breaks) reveals line by line. Each item rises 135 % of its height out of a mask with power4 ease. The mask has padding below and above the line, so descenders (g, j, p, q, y) and accents are not cut. `align` sets the alignment of the words and lines inside the element.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.maskedSlideReveal(H, document.querySelector('#title'), { at: H.at('hook+0.2'), align: 'left' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.maskedSlideReveal(H, document.querySelector('#title'), { at: cue('hook') + 0.2, lines: ['First line', 'Second line'] });
```

Rewritten for VideoFactory from RemotionUI `masked-slide-reveal` (MIT). No upstream code is copied.
