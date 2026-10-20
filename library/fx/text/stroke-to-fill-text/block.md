---
id: "stroke-to-fill-text"
title: "Stroke to fill text"
description: "Letters appear as an outline and then a solid fill floods each letter from the bottom up; use it for a bold title with a build-up."
tags: ["stroke", "outline", "fill", "text", "title", "reveal", "letters", "wipe", "entrance"]
kind: "fx"
engine: "both"
status: "draft"
files: ["stroke-to-fill-text.js", "stroke-to-fill-text.css"]
depends: ["core"]
api: ["FX.strokeToFillText(H, el, {at, by = 'chars'|'words'|'whole', stagger = 0.04, outlineDur = 0.35, fillDelay = 0.4, fillDur = 0.6, direction = 'up'|'down'|'left'|'right', strokeWidth = 3, retain = 0.35, softness = 14, strokeColor = 'ink', fillColor = 'ink', text = el.textContent}): outline at `at`, fill after `fillDelay`", "returns {el, parts, end}"]
preview_at: 2.0
source: {"site": "remotionui", "name": "stroke-to-fill-text", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/stroke-to-fill-text.tsx", "license": "MIT"}
---

# stroke-to-fill-text

Each letter shows an outline first (`strokeWidth` px). The fill follows through a soft gradient mask in `direction`; the outline thins to `retain` times its width while it fills. `by: 'whole'` fills all letters at the same time. Use a heavy font size of 72 px or more so the outline reads.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.strokeToFillText(H, document.querySelector('#title'), { at: H.at('hook+0.2'), fillColor: 'accent' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.strokeToFillText(H, document.querySelector('#title'), { at: cue('hook') + 0.2, direction: 'right' });
```

Rewritten for VideoFactory from RemotionUI `stroke-to-fill-text` (MIT). No upstream code is copied.
