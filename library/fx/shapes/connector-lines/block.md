---
id: "connector-lines"
title: "Connector lines"
description: "Lines draw between named anchors or boxes, one after the other, with a dot where each one lands; use it for flows, diagrams and relations."
tags: ["connector", "lines", "diagram", "flow", "edges", "graph", "network", "dashed", "relationship"]
kind: "fx"
engine: "both"
status: "approved"
files: ["connector-lines.js", "connector-lines.css"]
depends: ["core"]
api: ["FX.connectorLines(H, root, {at, anchors: [{id, x, y} | {id, el}], edges: [{from, to, shape, bow, color, dot}], shape = 'curve'|'elbow'|'straight', bow = 0.16, color: 'accent', strokeWidth = 4, dashed = false, dot = true, dur = 0.7, stagger = 0.25, gap = 14, exitAt, exitDur = 0.3}): the SVG is added to root, under the boxes", "returns {svg, edges}"]
preview_at: 1.5
twins: ["onda/node-graph"]
source: {"site": "remotionui", "name": "connector-lines", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/connector-lines.tsx", "license": "MIT"}
---

# connector-lines

An anchor is a point (`x`, `y` in stage px inside root) or an element (`el`: its centre; lines stop `gap` px before its edge). Each edge draws in order, `stagger` seconds apart, and takes `dur` seconds. `bow` bends a curve (negative bends it the other way). `dashed` draws marching dashes instead of a solid line. An edge that names an unknown anchor is dropped. The lines sit under the boxes (z-index 1); give the boxes `z-index: 2`.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.connectorLines(H, document.getElementById('stage'), { at: H.at('flow'), anchors: [{ id: 'a', el: boxA }, { id: 'b', el: boxB }], edges: [{ from: 'a', to: 'b' }] });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.connectorLines(H, document.querySelector('[data-composition-id="main"]'), { at: cue('flow'), anchors: [{ id: 'a', x: 300, y: 500 }, { id: 'b', x: 1500, y: 500 }], edges: [{ from: 'a', to: 'b', shape: 'elbow' }], dashed: true });
```

Rewritten for VideoFactory from RemotionUI `ConnectorLines` (MIT). No upstream code is copied.
