---
id: "code-block"
title: "Code block"
description: "A code window with syntax colours where the code types itself character by character or appears line by line; use it to show a snippet."
tags: ["code", "syntax", "highlight", "snippet", "developer", "editor", "typing", "programming", "window", "lines"]
kind: "fx"
engine: "both"
status: "draft"
files: ["code-block.js", "code-block.css"]
depends: ["core"]
api: ["FX.codeBlock(H, root, {at, code, title, lang = 'js'|'py', by = 'chars'|'lines', lineNumbers = false, size = 40, width = 1500, chrome = true, x, y, typeDur = total characters / 45 s, lead = 0.3, stagger = 0.2}): a window centred in root (or at x, y)", "returns {el, lines, end}"]
preview_at: 1.5
twins: ["remotion-bits/code-block"]
source: {"site": "onda", "name": "code-block", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/code-block/CodeBlock.tsx", "license": "MIT"}
---

# code-block

A small built-in tokenizer colours keywords (accent), strings (green) and comments (dim); everything else is the ink colour. `lang: 'py'` makes `#` the comment mark. With `by: 'chars'` the whole text types in a straight line over `typeDur` seconds. With `by: 'lines'` one line snaps in every `stagger` seconds. The window has its full height from the start. Keep lines short: a line never wraps. No library is loaded.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.codeBlock(H, document.getElementById('stage'), { at: H.at('code'), title: 'total.js', code: 'const a = 1;\nreturn a;', by: 'lines' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.codeBlock(H, document.querySelector('[data-composition-id="main"]'), { at: cue('code'), code: 'print(1)', lang: 'py', typeDur: 1.5 });
```

Rewritten for VideoFactory from Onda `CodeBlock` (MIT). No upstream code is copied.
