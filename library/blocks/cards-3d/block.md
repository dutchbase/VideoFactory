---
id: "cards-3d"
title: "3D card stack"
description: "Three thick choice cards fan out and the chosen card comes forward."
tags: ["cards", "3d", "select", "fan", "choice"]
kind: "block"
category: "3d"
engine: "hyperframes"
files: ["cards-3d.js", "cards-3d.css"]
depends: ["core", "room-3d"]
api: ["const b = Blocks.cards3d(H, root, {cards: [text, ...]})", "b.cards: DOM solids", "b.spread(at)", "b.select(index, at)", "b.el, b.camera, b.shadow"]
preview_at: 6.6
---

# cards-3d

Extracted from an approved 30-second portrait showcase scene (2026-10-13).

Use a root of 1080×1920 scene units. The constructor only makes DOM; motion goes on `H.tl` and you plan it explicitly. All text styling uses brand variables, and every text goes in through `textContent`. Only local GSAP and fonts and the block's listed dependencies.

`demo.html` loads `_demo/cues.js` and the shared demo set-up `_demo/3d.js`. This fixture normalises the initial numeric GSAP transforms and shows the camera arrival of the source video; the render clock stays one paused main timeline. The caller can plan camera and shadow on `H.tl`. No new media and no volume from script.

The card layout is tuned for three choices and the prompt layout for four short layers. Check another count or long content for readability in your own scene. Invalid selection indices and non-positive or non-finite cube durations are refused at once when you call the method during scene set-up.

Render costs: see `render-costs.md` (full 30-second measurement). They are not a per-block benchmark of the original combined showcase.
