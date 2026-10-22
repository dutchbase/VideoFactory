---
id: "word-stagger"
axis: "editing"
title: "Word stagger"
summary: "Kinetic text: words appear one by one in sync with speech, with scale and weight emphasis."
aliases: ["kinetic text", "word by word", "lyric video text"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["hook-one-idea", "myth-vs-fact", "listicle", "short", "launch-announcement"]
formats: ["wide", "tall"]
pairs_with: ["kinetic-typography", "brutalist-bold", "swiss-modernist", "high-end-social", "keynote-black"]
preview: "native"
build: "native"
---

## Look
The text is the picture. Each word shows at the moment it is spoken. The key word gets bigger, heavier or in the accent colour, and the others step back.

## Behaviour
- Reveal: each word enters 0.02-0.06 s before its spoken start. Rise 18 px, scale 0.92 to 1.0, `P.ease.enter`, 280-360 ms.
- Stagger: words follow the voice, not a fixed offset. Normal speech gives 0.25-0.4 s per word. Max 4-6 words on screen.
- Emphasis: the key word is 1.4-2x larger, weight 800-900 and `accent`. Use `P.spring` pop (`{dur: 0.4, bounce: 0.25}`) for it. Other words stay `ink` at weight 500-600.
- Previous words: dim to 40% opacity over 200 ms when a new word arrives.
- Clear: when the phrase ends, all words leave together with `P.ease.accelExit`, 240 ms, or the line scrolls up one row.
- Layout: left-aligned at the same x; the baseline does not move. Line breaks follow phrase breaks.
- Cut: swap one phrase for the next with K10 (a hard word replacement). No fade.
- Pacing: 2-4 s per phrase, 15-25 phrase changes per minute. Keep a hold of 0.3 s after the last word.
- Camera: locked. A 4% push over the phrase is allowed.
- Sound: a tick on each word, a heavier hit on the key word.

## Do
- Cue words from transcript word times.
- Use at most one emphasis per phrase.
- Keep word spacing and baseline fixed.

## Don't
- No typewriter letter-by-letter.
- No more than 6 words visible.
- No rotation or random positions.

## Build notes
Modern kit: map each word to a `data-cue` from the transcript (`stages/03_cues`). Set size and weight classes per word; show with `P.prog`. See `_shared/motion.md` Stagger.
