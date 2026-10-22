---
id: "myth-vs-fact"
axis: "content"
title: "Myth vs fact"
summary: "States a common claim, shows why it fails, and gives the proof and the true version."
aliases: ["debunk", "myth buster", "fact check"]
sources: ["https://yansmedia.com/blog/explainer-video-structure", "https://fliki.ai/blog/explainer-video-script-template", "https://pexo.ai/blog/types-of-explainer-videos-0995"]
best_for: ["short", "explainer", "course"]
formats: ["wide", "tall"]
pairs_with: ["data-journalism", "newsdesk", "broadsheet", "brutalist-bold", "swiss-modernist", "vox-explainer", "high-end-social", "editorial-collage"]
preview: "native"
build: "native"
---

## Look
States a common claim, shows why it fails, and gives the proof and the true version. A plain claim card turns into a proven fact card.

## Behaviour
- Structure (percent of runtime): 1) the myth stated as people say it, in quote marks 0–12%, 2) the stamp: "Myth" 12–16%, 3) evidence: one or two proofs with source 16–70%, 4) the fact, stated short 70–85%, 5) what to do instead 85–100%. Repeat as rounds for 3 myths.
- Myth card enters plain (`P.ease.enter`, 450 ms). On the voice word "but" or "actually", a stamp or strike line draws across it (`P.ease.whip`, 230 ms) and the card drops to 40% opacity.
- Evidence enters 0.6 s later: a number, chart or source name (`P.ease.softLand`, 400 ms). Show the source label in small mono text.
- The fact card replaces the myth in the same position (`P.ease.move`, 500 ms swap), with the accent colour. Hold the fact 2.5 s.
- Round length: 12–20 s. Changes per minute: 8–12. Wide 45–120 s, tall 20–45 s (one myth only, or max 3 rounds of 8 s).
- Sound: low thud on the stamp, clean chime on the fact.

## Do
- Quote the myth as people really say it.
- Show the evidence on screen with its source.
- Use danger colour only for the Myth stamp, green or accent for Fact.

## Don't
- No straw-man myths.
- No fact without proof.
- Do not repeat the myth more than twice.

## Build notes
Stage 03 cues: myth in, stamp, evidence, fact per round. Stamp is an SVG line or rotated box. Keep the same card position for myth and fact.
