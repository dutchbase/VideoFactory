---
id: "core"
title: "Core helpers (timing, typing, streaming)"
description: "Timing on the voice, show and hide, snap-ins, typing letter by letter, streaming words in and showing spoken words one by one; every other block uses this."
tags: ["core", "helpers", "basics", "timing", "typing", "stream", "words", "snap", "captions", "subtitles"]
kind: "block"
category: "helpers"
engine: "hyperframes"
files: ["core.js", "core.css"]
depends: []
api: ["const H = Blocks.core(tl[, words])", "H.ws(i), H.we(i): start/end of spoken word i", "H.show/hide(el, at), H.disp(el, display, at), H.snap(el, at[, from, dur])", "H.chars(parent, text[, 'b-hot']) -> spans; H.type(spans, t0, t1); H.untype(spans, t0, t1); H.wipe(spans, at)", "H.words(parent, text) -> spans; H.stream(spans, t0, t1)", "H.say(parent, a, b[, allHot]) -> spans: spoken words a..b-1 snap in, the current one in accent"]
preview_at: 3.2
---

# core

Load it first: `<link rel="stylesheet" href="blocks/core.css">`, then `<script src="blocks/core.js"></script>` after `runtime/hf-bridge.js`.

```js
const tl = gsap.timeline({ paused: true });
const H = Blocks.core(tl);                        // words default to window.ANIM.words
H.type(H.chars(el, "Write an email."), H.ws(3), H.we(5));
H.stream(H.words(answerEl, "Hi Sam, ..."), 4.0, 5.2);
H.say(railEl, 0, 3);                              // the first three spoken words, one by one
```
