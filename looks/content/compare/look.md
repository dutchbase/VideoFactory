---
id: "compare"
axis: "content"
title: "Compare A vs B"
summary: "Puts two options side by side on the same rows, then gives a clear verdict."
aliases: ["versus", "A vs B", "head to head"]
sources: ["https://yansmedia.com/blog/explainer-video-structure", "https://adwave.com/resources/explainer-video-styles", "https://www.yumyumvideos.com/blog/short-vs-long-videos-explainer-video-length-wp/"]
best_for: ["explainer", "course", "short"]
formats: ["wide", "tall"]
pairs_with: ["swiss-modernist", "data-journalism", "minimalist-premium", "keynote-black", "flat-vector", "depth-bento", "vox-explainer", "brutalist-bold"]
preview: "native"
build: "native"
---

## Look
Puts two options side by side on the same rows, then gives a clear verdict. Two equal columns share one row grid.

## Behaviour
- Structure (percent of runtime): 1) hook and the question "A or B?" 0–8%, 2) rules: the 3–5 criteria that matter, named once 8–18%, 3) round by round, one criterion per row, A then B 18–80%, 4) verdict with one reason 80–94%, 5) "it depends" rule and call to action 94–100%.
- Layout: wide splits the frame 50/50 with a centre line at x=50%. Tall stacks A on top and B below. Each criterion is one row; labels sit in the centre column.
- Round pacing: 6–10 s per criterion. A enters on the word that names it (`P.ease.enter`, 450 ms, 24 px from its side); B enters 0.5–0.8 s later on its own word. Never show both values before the voice says them.
- Winner of a round: its card gets the accent outline (`P.spring` pop, scale 1.0 to 1.03 and back, 400 ms); the loser dims to 55% (`P.ease.exit`, 250 ms). A running score chip in the corner ticks up.
- Verdict: the other side fades to 30% (500 ms, `P.ease.move`), the winner moves to centre and scales 1.15 (`P.ease.softLand`, 700 ms). Hold the verdict 2.5 s.
- Changes per minute: 8–12. Wide length 60–150 s. Tall length 30–60 s with maximum 3 criteria. Sound: soft tick on each win, one low hit on the verdict.

## Do
- Use the same criteria in the same order for A and B.
- Keep A and B colours fixed for the whole video (A = accent, B = accent2).
- Give a verdict, even if it is "A for you if ...".

## Don't
- No more than five criteria.
- No new criterion after the verdict.
- No bias in order: swap who enters first at least once.

## Build notes
Stage 03 cues: one cue per option name, one per value, one per round winner, one for the verdict. Use a shared row grid so A and B align. Tall format: put the centre line horizontal.
