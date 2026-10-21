---
id: "marker-highlight"
title: "Marker highlight"
description: "A highlighter stroke sweeps word by word across a phrase, as marker, knockout, underline or box; use it to stress the key words of a line."
tags: ["highlight", "marker", "highlighter", "emphasis", "text", "underline", "box", "knockout", "phrase"]
kind: "fx"
engine: "both"
status: "approved"
files: ["marker-highlight.js", "marker-highlight.css"]
depends: ["core"]
api: ["FX.markerHighlight(H, el, {at, phrase = null (all words), variant = 'marker'|'knockout'|'underline'|'box', dur = 0.45, stagger = 0.16, softness = 12, markerColor = 'accent' ('ink' for knockout), flipColor = 'cream', text = el.textContent}): the first word is marked from `at`", "returns {el, words, end}"]
preview_at: 1.5
twins: ["onda/highlight"]
source: {"site": "remotionui", "name": "marker-highlight", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/marker-highlight.tsx", "license": "MIT"}
---

# marker-highlight

`phrase` picks the words to mark (others stay plain); without it all words are marked. Each marked word gets a stroke that sweeps left to right, `stagger` seconds after the one before. Variants: `marker` (a band behind the word), `knockout` (a dark band and the word flips to `flipColor`), `underline` (a thin band under the word), `box` (an outline). Use `knockout` for the strongest stress.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.markerHighlight(H, document.querySelector('#line'), { at: H.at('point'), phrase: 'the point' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.markerHighlight(H, document.querySelector('#line'), { at: cue('point'), phrase: 'the point', variant: 'knockout' });
```

Rewritten for VideoFactory from RemotionUI `MarkerHighlight` (MIT). No upstream code is copied.
