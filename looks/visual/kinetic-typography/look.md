---
id: "kinetic-typography"
axis: "visual"
title: "Kinetic typography"
summary: "Words are the picture: huge type that slams, slides and scales in time with the voice on a flat colour field."
aliases: ["kinetic type", "text animation", "lyric video style"]
sources: ["https://explain.film/explainer-video-styles/kinetic-typography", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["hook-one-idea", "myth-vs-fact", "short", "ad", "launch-announcement"]
formats: ["wide", "tall"]
pairs_with: {"editing": "word-stagger", "content": "hook-one-idea"}
preview: "native"
build: "native"
palette_roles: {"field": "bg", "word": "ink", "hot": "accent", "alt": "accent2", "quiet": "faint", "rule": "line"}
---

## Look
- Field: one flat colour (`bg`, or `accent` for a punch frame). No images, no icons.
- Type: `head` in its heaviest weight, 140-320 px, tight leading (0.88), tight tracking (-3%). Key words in `accent`, a second voice in `accent2`.
- Layout: words stack, wrap or fill the frame edge to edge. Size shows importance. One word may bleed off the edge.
- Support: thin `line` rules, one small `mono` caption (16 px), plain bars under a word.

## Behaviour
- Word entrances: each word lands on its spoken beat. Slam: scale 1.15 to 1 with `P.ease.crashIn` (330 ms). Slide: 120 px in from one edge with `P.ease.whip` (230 ms). Rise: through a mask, 300 ms `P.ease.softLand`.
- Stagger: words in a line 60-120 ms apart, locked to the transcript times, not evenly spaced.
- Emphasis: the key word scales to 1.12 in 200 ms (`P.spring` snap) and swaps to `accent`.
- Exit: words wipe out upward through the mask in 220 ms (`P.ease.accelExit`) or the field flips colour on the cut.
- Transitions: hard cut on the beat, or a colour block wipe in 300 ms (`P.ease.whip`).
- Camera: locked. Optional 1.04 punch zoom on a big word for 150 ms.
- Pacing: a new word or phrase every 0.4-1.0 s, 2-3 s per phrase, about 25-40 changes per minute. Rest 1 s after a dense run.
- Ambient: none.
- Sound: tight thump or tick per slam, whoosh per slide, light beat bed.

## Do
- Cut on the meaning word (usually the verb).
- Keep at most 5 words on screen.
- Keep reading time: a phrase stays 0.3 s after the last word.

## Don't
- No decoration, no pictures, no more than two typefaces weights per frame.
- No bounce on long sentences.
- No tiny text under 80 px except the caption.
- No random motion that is not tied to a word.

## Build notes
Native: absolutely placed `span` words, `P.prog` per word, `clip-path` masks for rises. Take times from `02_transcript` words. Works in tall: break phrases to one or two words per line at 200-280 px.
