---
id: "newsdesk"
axis: "visual"
title: "Newsdesk"
summary: "Broadcast news look: bold straps, lower thirds, a LIVE tag and a scrolling ticker over a dark studio field."
aliases: ["news broadcast", "breaking news", "lower thirds"]
sources: ["https://ideatomotion.com/looks", "https://explain.film/explainer-video-styles", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["data-story", "launch-announcement", "listicle", "ad", "short", "explainer"]
formats: ["wide", "tall"]
pairs_with: {"editing": "whip-pan", "content": "launch-announcement"}
preview: "native"
build: "native"
palette_roles: {"field": "bg", "strap": "accent", "strap-text": "bg", "panel": "surface", "ticker": "raised", "text": "ink", "alert": "danger", "rule": "line"}
---

## Look
- Field: dark `bg` studio backdrop with a faint `surface` grid or soft vignette. One large area stays free for the "story" (chart, image or big number).
- Straps: a solid `accent` bar with `bg` text in heavy caps for the headline, and a `raised` sub-bar under it for the detail line. Square or 4 px corners. A small `danger` tag with "LIVE" or "BREAKING".
- Lower third: name or topic strap at the bottom left, 56–72 px tall, with a short `accent2` tab at its left edge.
- Ticker: a 44–52 px bar along the bottom edge with `mono` caps text in `ink` and a `accent` label box ("NEWS") at its left.
- Type: brand `head` in heavy caps, 56–96 px for the main strap; `mono` 18–22 px caps for ticker and time stamps.

## Behaviour
- Entrances: the headline strap wipes in from the left edge with `P.ease.whip` (260 ms), and its text reveals through a rectangular mask 80 ms later. The sub-bar follows 120 ms after, sliding from the same edge with `P.ease.softLand` (400 ms).
- Lower third: the accent tab grows first (160 ms `P.ease.move`), then the strap extends to full width (360 ms `P.ease.softLand`).
- Exits: straps retract to the left with `P.ease.accelExit` (300 ms), reverse order of entry.
- Ticker: text scrolls right to left at a constant 90–120 px/s with `P.ease.linear`, looping. The ticker is the only ambient motion.
- LIVE tag: the dot pulses between 100% and 40% opacity once per 1.2 s.
- Transitions: a full-frame accent bar sweeps across in 300 ms (`P.ease.whip`) and wipes the next scene in behind it.
- Camera: locked. A 2% push-in on the story area over a 5 s hold is allowed.
- Pacing: 3–5 s holds, about 14–18 changes per minute. A new strap or number every 4 s.
- Sound: short broadcast whooshes, soft stings on each new strap, a low news bed.

## Do
- Keep each strap to one line of 3–6 words.
- Put one hard number or fact in the story area per scene.
- Time the strap to land on the key word of the voice.
- Keep straps inside a 5% safe margin.

## Don't
- No bounce or springy pops.
- No more than two straps on screen at once, plus the ticker.
- No fake real network logos or real channel names.
- No long sentences in the ticker.

## Build notes
Native CSS: absolute bars, `clip-path: inset()` for strap wipes, a duplicated `mono` text row translated with `P.ease.linear` for the ticker. Use `P.prog` for each strap. In tall format, move the lower third up to 18% from the bottom, and keep the ticker at the very bottom. Works in both formats.
