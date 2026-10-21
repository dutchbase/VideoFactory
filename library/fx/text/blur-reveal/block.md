---
id: "blur-reveal"
title: "Blur reveal"
description: "Text rises 16 px out of a soft blur and fades in on a calm spring with no overshoot; the default reveal for a title or a line."
tags: ["text", "reveal", "entrance", "blur", "spring", "title", "fade", "soft", "calm"]
kind: "fx"
engine: "both"
status: "approved"
files: ["blur-reveal.js"]
depends: ["core"]
api: ["FX.blurReveal(H, el, {at, dur = 0.7, by: null|'words'|'chars', stagger = 0.06, blur = 10, rise = 16}): el appears at `at`", "returns {el, parts}"]
preview_at: 1.0
twins: ["remotionui/blur-focus-in"]
source: {"site": "onda", "name": "blur-reveal", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/blur-reveal/BlurReveal.tsx", "license": "MIT"}
---

# blur-reveal

Opacity, blur and a small rise settle together on one spring. Use it for any text reveal when the script asks for nothing special. `by: 'words'` reveals word by word with `stagger` seconds between words.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.blurReveal(H, document.querySelector('#title'), { at: H.at('hook+0.2') });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.blurReveal(H, document.querySelector('#title'), { at: cue('hook') + 0.2, by: 'words' });
```

Rewritten for VideoFactory from Onda `BlurReveal` (MIT). No upstream code is copied.
