---
id: "watercolor"
axis: "visual"
title: "Watercolor"
summary: "Soft translucent colour washes with bleeding edges on paper grain, plus loose ink linework; gentle and human."
aliases: ["watercolor wash", "painted explainer", "ink and wash"]
sources: ["https://explain.film/explainer-video-styles", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["founder-story", "before-after", "hook-one-idea", "founder story", "explainer", "short"]
formats: ["wide", "tall"]
pairs_with: {"editing": "cinematic-drift", "content": "founder-story"}
preview: "native"
build: "library"
palette_roles: {"paper": "bg", "ink": "ink", "wash1": "accent", "wash2": "accent2", "wash3": "r3", "wash4": "green", "soft": "dim"}
---

## Look
- Field: warm paper (`bg`) with a faint grain (noise at 4–6% opacity). Colour sits in blobs of 30–60% opacity washes that overlap and darken where they cross.
- Shapes: irregular round blobs with a darker rim on the edge (a "bloom"). No hard geometric edges. Colours: `accent`, `accent2`, `r3`, `green`.
- Line: a loose `ink` line at 3–4 px, slightly offset from the colour, as if sketched first and painted after.
- Type: `head` in a medium weight at 80–120 px, ink colour, sentence case. A `hand` face at 28–36 px for small notes.

## Behaviour
- Entrances: a wash blooms from a point: scale 0.4 to 1 and opacity 0 to the target in 900 ms, `P.ease.softLand`, with a mask edge that grows by 6% beyond the final size and settles back. Ink lines draw in 600 ms, `P.ease.move`.
- Text: a headline fades in with a 6 px blur to sharp over 500 ms, `P.ease.enter`, word by word at 110 ms stagger.
- Transitions: a big wash floods across the frame (700 ms, `P.ease.move`) and the next scene appears as it dries back. Or a 500 ms cross dissolve.
- Camera: very slow drift, 1.0 to 1.05 over the hold, `P.ease.linear`. No shake.
- Pacing: slow. 4–7 s holds, about 8–12 changes per minute. Let washes finish drying for 0.8 s before the next change.
- Ambient: washes breathe 1.5% in scale on a 6 s loop. Paper grain stays still.
- Sound: soft brush swishes and a warm acoustic or piano bed.

## Do
- Use at most 3 wash colours in a frame.
- Leave 30–40% of the paper bare.
- Let two washes overlap so the mix colour shows.
- Keep type clean and dark for contrast.

## Don't
- No hard vector edges, no neon, no drop shadows.
- No fast cuts or whip moves.
- No full opacity fills. Everything stays translucent.
- No more than 12 words in a frame.

## Build notes
Native fallback: blurred `border-radius` blobs with `mix-blend-mode: multiply` and an SVG `feTurbulence` filter for the rough rim and grain. Library parts (brush strokes, paper texture) give the best result. Animate blobs with `P.prog` on scale and opacity.
