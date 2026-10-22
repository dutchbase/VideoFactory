---
id: "high-end-social"
axis: "visual"
title: "High-end social"
summary: "Premium vertical video: huge captions, a flipping light and dark field, one accent and punchy whip cuts."
aliases: ["kinetic rhythm", "signal", "premium short", "reels style"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["hook-one-idea", "listicle", "short", "ad", "launch-announcement"]
formats: ["tall", "wide"]
pairs_with: {"editing": "word-stagger", "content": "hook-one-idea"}
preview: "native"
build: "native"
palette_roles: {"dark": "bg", "light": "ink", "accent": "accent", "dim": "dim", "rule": "line"}
---

## Look
- Format: tall first (9:16). Keep key content inside the safe zone: 120 px from the top, 260 px from the bottom, 60 px at the sides.
- Field: flips each shot between `bg` (dark) and `ink` (light). One accent colour (`accent`) per shot, used on one word or one shape.
- Type: `head` in its heaviest weight, 120-200 px tall, 2-4 words per line, tight leading (0.92). Key money or number words get an `accent` highlight bar.
- Support: a thin `line` rule, a small `mono` tag (16-20 px) and one flat shape. No clutter.
- Photos, if any, in a duotone of `bg` and `accent`.

## Behaviour
- Text: words appear in a fast 4-frame stagger (about 133 ms at 30 fps), `P.ease.whip`, each word 230 ms.
- Entrances: shapes and numbers punch in with `P.ease.crashIn` (330 ms) from 120% scale to 100%.
- Transition: whip cut between shots. The old shot slides out 200 ms with `P.ease.accelExit` while the field flips light to dark.
- Highlight: the accent bar wipes under the key word in 250 ms, `P.ease.whip`.
- Camera: locked, with a 3% push-in over each hold using `P.ease.linear`.
- Pacing: a hook in the first 1 s. Shot length 1.2-2.5 s, 30-40 changes per minute. Always a visible change every 2 s.
- Ambient: none. Sound: bass hit on each cut, tick on each word, short riser before the payoff.

## Do
- Put one big sentence in each shot.
- Cut on the beat of the voice and the music.
- Keep the last shot as a clear call to action with the accent.

## Don't
- No small text under 48 px for captions.
- No long holds over 3 s.
- No gradients, glow or glass.
- No more than one accent per shot.

## Build notes
Modern kit text blocks with per-word spans and `P.prog` stagger. Flip the field with swapped CSS variables per shot. Respect the platform safe zone from `_shared/image-sizes.json`. Wide format: same shot rules on a 16:9 canvas with left-aligned text.
