---
id: "terminal"
title: "Terminal"
description: "A terminal window where a command types itself after the prompt and the output lines appear one by one; use it to show a command being run."
tags: ["terminal", "shell", "cli", "command", "typing", "console", "developer", "prompt", "output", "cursor"]
kind: "fx"
engine: "both"
status: "draft"
files: ["terminal.js", "terminal.css"]
depends: ["core"]
api: ["FX.terminal(H, root, {at, command = 'make video', output: [string | {text, tone: 'green'|'accent'|'ink'}], prompt = '$', title, chrome = true, size = 40, width = 1500, x, y, typeDur = 0.05 s per character, lead = 0.3, outputDelay = 0.5, stagger = 0.35}): a window centred in root (or at x, y)", "returns {el, typed, end}"]
preview_at: 1.5
twins: ["remotion-bits/cli-simulation", "remotionui/terminal-simulator"]
source: {"site": "onda", "name": "terminal", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/terminal/Terminal.tsx", "license": "MIT"}
---

# terminal

The window snaps in at `at`. After `lead` seconds the command types itself in a straight line over `typeDur` seconds; the cursor stays solid while it types, then blinks every 0.5 s until the first output line, then disappears. Output lines appear `stagger` seconds apart; a line is a string (dim) or `{text, tone}`. The window has a fixed height from the start, so nothing jumps. Text comes from the clock, so a seek always gives the same picture.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.terminal(H, document.getElementById('stage'), { at: H.at('run'), command: 'make video', output: ['done', { text: 'out.mp4 ready', tone: 'green' }] });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.terminal(H, document.querySelector('[data-composition-id="main"]'), { at: cue('run'), command: 'make video', output: ['done'] });
```

Rewritten for VideoFactory from Onda `Terminal` (MIT). No upstream code is copied.
