---
id: "schematic"
axis: "visual"
title: "Schematic"
summary: "Tiles, terminals and pills joined by wires that draw in, one node at a time, under a steady headline."
aliases: ["system diagram", "architecture explainer", "wiring diagram"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["explain-mechanism", "product-tour", "explainer", "onboarding"]
formats: ["wide", "tall"]
pairs_with: {"editing": "scroll-build", "content": "explain-mechanism"}
preview: "native"
build: "native"
palette_roles: {"field": "bg", "tile": "surface", "wire": "dim", "hot": "accent", "packet": "accent2", "text": "ink"}
---

## Look
- Field: dark `bg`. Rounded tiles in `surface` with a 1 px `line` border. Terminals are small pills in `raised`. Wires are 2 px `dim` lines with right-angle bends.
- Colour: one hot colour (`accent`) for the headline keyword, the active tile and the active wire. `accent2` only for the moving packet.
- Type: headline in the brand `head` font, 56-72 px, top-left, always on screen. Tile labels in `mono` 16-20 px. Small port dots at every wire end.
- Layout: 3-6 tiles on an implied grid. Leave a clear lane between tiles for wires.

## Behaviour
- Entrances: the headline lands first with `P.ease.softLand` (400 ms) and stays for the whole scene. Tiles then scale from 0.94 and fade in, `P.ease.enter`, 360 ms each, 160 ms apart in data-flow order.
- Wires: after both ends exist, the wire draws with `stroke-dashoffset` over 500-700 ms, `P.ease.linear`. Port dots pop in at the end with `P.spring` pop.
- Packets: a small `accent2` dot travels along a wire in 700-900 ms (`P.ease.move`) when the voice says the data moves. One packet at a time.
- Focus: the tile the voice names gets an `accent` border (200 ms) and the rest stay calm. No dimming of other tiles.
- Exits: tiles and wires fade out together in 240 ms (`P.ease.exit`) or the whole diagram pushes up 60 px while the next one builds.
- Camera: locked. Pacing: one new node or wire per spoken beat, 0.6-1.2 s apart; 5-8 s holds; about 8-12 changes per minute.
- Ambient: none. Sound: soft ticks on each node, a quiet whoosh on each wire, low synth bed.

## Do
- Build in the order data flows, left to right.
- Label every tile with one or two words.
- Keep the headline up while the diagram builds.
- Keep at most 6 tiles per frame.

## Don't
- No shadows or gradients on tiles.
- No diagonal wires; use right angles only.
- No more than one packet moving at once.
- No icons with detail inside tiles.

## Build notes
Native: absolutely positioned divs for tiles, one inline SVG for wires with `stroke-dasharray` reveals computed from `getTotalLength()`. Drive with `P.prog` per wire. Tall format: stack tiles vertically, headline on top, wires run down.
