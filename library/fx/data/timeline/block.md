---
id: "timeline"
title: "Timeline"
description: "A horizontal timeline: a thin line strokes itself on, dots land at each step as it passes and labels settle beneath, with the last dot in the accent; use it for a sequence of steps or dates."
tags: ["timeline", "steps", "milestones", "roadmap", "dots", "sequence", "history", "process", "data"]
kind: "fx"
engine: "both"
status: "draft"
files: ["timeline.js", "timeline.css"]
depends: ["core"]
api: ["FX.timeline(H, el, {at, dur = 2.0, points: [{label, sub?}] (5 sample steps), width = 1600, labelWidth = 300, dotSize = 44, lineHeight = 6, color: 'dim', lineColor: 'line', accentColor: 'accent'}): builds the timeline inside el; the line draws over `dur` seconds from `at`", "returns {el, root, items}"]
preview_at: 1.5
twins: ["remotionui/timeline-steps"]
source: {"site": "onda", "name": "timeline", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/timeline/Timeline.tsx", "license": "MIT"}
---

# timeline

Points sit evenly along the line. Each dot lands, then its label (44 px, optional `sub` line 32 px) rises 14 px under it, both timed from the line head so the order always reads left to right. The labels sit on the ground below the line and never depend on the line reaching them. The last dot is larger and uses `accentColor`: one focal point, the rest neutral. With `labelWidth` 300 and 5 points the labels have room; for more points, lower `labelWidth` or raise `width`. The part keeps `labelWidth / 2` free at both ends.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.timeline(H, document.querySelector('#steps'), { at: H.at('plan+0.2'), points: [{ label: 'Plan' }, { label: 'Build' }, { label: 'Launch' }] });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.timeline(H, document.querySelector('#steps'), { at: cue('plan') + 0.2, dur: 2.4, points: [{ label: 'Plan', sub: '2024' }, { label: 'Launch', sub: '2025' }] });
```

Rewritten for VideoFactory from Onda `Timeline` (MIT). No upstream code is copied.
