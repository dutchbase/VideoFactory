---
id: "tutorial"
axis: "content"
title: "Tutorial: step by step"
summary: "Teaches one task as numbered steps, with the screen or the hands always in view."
aliases: ["how to", "walkthrough", "step by step", "screencast"]
sources: ["https://www.techsmith.com/blog/explainer-video/", "https://yansmedia.com/blog/explainer-video-structure", "https://fliki.ai/features/saas-explainer-video-maker"]
best_for: ["course", "onboarding", "explainer"]
formats: ["wide"]
pairs_with: ["saas-product-demo", "swiss-modernist", "blueprint", "terminal", "keynote-black", "graphpaper", "flat-vector", "depth-bento"]
preview: "native"
build: "native"
---

## Look
Teaches one task as numbered steps, with the screen or the hands always in view. The screen or hands fill the frame; a step chip and progress bar guide.

## Behaviour
- Structure (percent of runtime): 1) result first: show the finished outcome 0–8%, 2) what you need (tools, files) 8–14%, 3) steps 1..N, 14–86%, 4) check: how to know it worked 86–93%, 5) common mistake and next step 93–100%.
- Each step: step chip "Step 2 of 5" enters (`P.ease.enter`, 350 ms); the screen or hands show the action; a highlight ring or cursor moves to the target (`P.ease.move`, 400 ms) and clicks (scale 0.92 and back, 150 ms) on the verb word.
- Step length: 8–20 s. Rest 1 s between steps. Zoom into the target area by 1.4x (`P.ease.move`, 700 ms) when the action is small, and zoom out when the step ends.
- A progress bar (`P.ease.linear`) fills with the steps. Finished steps stay in a side list, ticked.
- Show only the part of the screen that matters; blur or dim the rest to 40%.
- Changes per minute: 6–10. Length: wide 2–8 min for a course lesson, 30 s–2 min for onboarding. Tall is not advised. Sound: soft click on each action, a tick on each finished step.

## Do
- Say the action first, then do it.
- Show the result before step 1.
- Name the exact button or key as on screen.

## Don't
- No step with two actions.
- No skipped step, even a small one.
- No fast cursor: move at 400 ms minimum.

## Build notes
Stage 03 cues: step chip, cursor move, click, result per step. Capture the screen with `_shared/capture.md`. The highlight ring is a CSS outline with `color-mix` accent.
