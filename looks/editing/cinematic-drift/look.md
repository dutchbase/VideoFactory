---
id: "cinematic-drift"
axis: "editing"
title: "Cinematic drift"
summary: "Slow parallax, gentle push-ins and dissolves through blur; calm, filmic, unhurried."
aliases: ["slow push", "parallax drift", "dream dissolve"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["founder-story", "timeline", "hook-one-idea", "explainer", "founder story"]
formats: ["wide", "tall"]
pairs_with: ["cinematic-papercut", "layered-papercut", "archival-documentary", "watercolor", "minimalist-premium"]
preview: "native"
build: "native"
---

## Look
The camera always moves, slowly, and the scene is built in layers at different depths. Scenes melt into each other through blur. Think a quiet film title sequence.

## Behaviour
- Camera: a constant push-in of 4-8% scale over the scene length, `P.ease.linear` or `P.ease.move`, 4-8 s. Direction alternates between scenes (push in, then slow pull out).
- Parallax: 3 depth layers. Back moves 0.3x, middle 1x, front 1.8x the camera shift. Maximum shift 40 px per second on the middle layer.
- Entrance: elements fade up 0.0 to 1.0 and rise 16 px with `P.ease.enter` over 700-900 ms, 150 ms apart.
- Exit: fade and 6 px blur over 500 ms with `P.ease.exit`.
- Scene change: a dissolve through blur, 800-1200 ms. A ends by blurring 0 to 14 px while it fades; B starts at 14 px blur and sharpens to 0 with `P.ease.softLand`. The overlap is 40%.
- Rhythm: one change per 3-6 s. The voice is slow; leave 0.5 s of air after each phrase.
- Pacing: 10-18 changes per minute. Hold each key frame at least 2.5 s.
- Ambient: dust or light particles drift at 6 px per second, at most 5% opacity.
- Sound: a soft pad, a low riser under each dissolve, no clicks.

## Do
- Keep all motion on one slow axis per scene.
- Use depth blur on the back layer (3-6 px).
- End on a held frame, not a fade to black.

## Don't
- No hard cuts, no fast moves.
- No bounce or overshoot.
- No more than 8% scale change per scene.

## Build notes
Modern kit: wrap layers in groups and set `transform` from `P.prog` with `P.ease.linear`. Blur with `filter: blur()` driven by the same progress. For the dissolve the one allowed cross-fade in this look, overlap A and B for 0.4 s of the 1.0 s.
