---
id: "product-tour"
axis: "content"
title: "Product tour"
summary: "Walks through the main features of an app or product, each tied to a benefit."
aliases: ["feature walkthrough", "demo", "app tour"]
sources: ["https://fliki.ai/features/saas-explainer-video-maker", "https://www.techsmith.com/blog/explainer-video/", "https://adwave.com/resources/explainer-video-styles"]
best_for: ["ad", "onboarding", "explainer"]
formats: ["wide", "tall"]
pairs_with: ["saas-product-demo", "depth-bento", "tech-glow", "keynote-black", "liquid-glass", "minimalist-premium", "swiss-modernist", "isometric-3d"]
preview: "native"
build: "native"
---

## Look
Walks through the main features of an app or product, each tied to a benefit. The real interface in a frame, with callouts for each feature.

## Behaviour
- Structure (percent of runtime): 1) problem in one line 0–10%, 2) the product in its main view 10–18%, 3) 3–4 features, each as: action, result, benefit 18–82%, 4) the whole product again, all features ticked 82–92%, 5) call to action with the way to try it 92–100%.
- Show the real interface in a device or window frame. Feature focus: the rest dims to 40% and the camera zooms to the feature by 1.5x (`P.ease.move`, 800 ms).
- Each feature: callout label enters (`P.ease.softLand`, 400 ms) on the feature name; the UI action plays; a benefit chip enters 0.6 s later in the accent colour.
- Feature length: 8–14 s. Zoom back to full view between features (600 ms). Changes per minute: 7–10.
- Wide 45–120 s. Tall 20–45 s, maximum 3 features, one hand-held-phone style crop of the UI.
- Sound: soft click on each interaction, a short rise into the call to action.

## Do
- Say the benefit, not only the feature.
- Use real or realistic UI, never empty boxes.
- End with the full view and one next step.

## Don't
- No feature list without the UI.
- No more than four features.
- No fake claims in the UI numbers.

## Build notes
Stage 03 cues: zoom in, callout, UI action, benefit, zoom out per feature. Screens from `_shared/capture.md` or rebuilt in the Modern kit.
