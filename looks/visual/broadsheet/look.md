---
id: "broadsheet"
axis: "visual"
title: "Broadsheet"
summary: "A newspaper page in motion: masthead, hairline rules, serif headline, columns and a pull quote."
aliases: ["newspaper", "paper editorial", "vintage newsprint", "front page"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["timeline", "founder-story", "data-story", "explainer", "founder story"]
formats: ["wide", "tall"]
pairs_with: {"editing": "scroll-build", "content": "timeline"}
preview: "native"
build: "native"
palette_roles: {"paper": "bg", "ink": "ink", "rule": "line", "mute": "dim", "stamp": "danger", "column": "faint"}
---

## Look
- Field: paper in `bg` with a soft fibre grain at 6%. Hairline double rules in `ink` or `line` between sections.
- Masthead: top band with the brand name in the `head` font, 48-64 px, a date line and an edition line in `mono` 14 px between two rules.
- Headline: heavy `head` font (with generic `serif` after it), 72-110 px, tight leading, sentence-case. Body in 2-3 columns, 18-22 px, text greeked into grey bars when no copy is needed.
- Extras: a halftone image box, a pull quote with large quote marks, and one `danger` ring or stamp for emphasis.

## Behaviour
- Entrances: the masthead rules draw outward from the centre in 400 ms (`P.ease.softLand`). The headline sets line by line, 100 ms stagger, with a 12 px rise.
- Columns: text bars fill top to bottom, 40 ms per line, in 600-800 ms total. The photo box reveals with a wipe in 500 ms (`P.ease.enter`).
- Emphasis: the pull quote scales from 0.96 and fades in 360 ms. A red ring draws around one word in 350 ms, `P.ease.linear`.
- Transitions: the page turns up (vertical push of 100% in 800 ms, `P.ease.move`) and the next front page sits below. For a timeline, the date line changes with a tick.
- Camera: locked, or a slow 6% push over the full hold.
- Pacing: 5-8 s holds, about 6-10 changes per minute. Sound: paper rustle, press thump on each headline, soft typewriter ticks.

## Do
- Write the headline as a clear news statement.
- Keep columns tidy and aligned to a grid.
- Use one red mark per page at most.

## Don't
- No bounce or pop.
- No glow, glass or gradients.
- No more than two type families.
- No full colour; stay with paper, ink and one red.

## Build notes
Native: CSS columns for text, grey bars for greeked lines, `repeating-linear-gradient` for rules, SVG `feTurbulence` for grain. Halftone photo is a dot pattern clipped to a box. Tall format: one column and a headline on top.
