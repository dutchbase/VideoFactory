---
id: "faq"
axis: "content"
title: "FAQ"
summary: "Answers a set of real questions one by one, each with a short direct answer."
aliases: ["Q&A", "questions answered", "common questions"]
sources: ["https://yansmedia.com/blog/explainer-video-structure", "https://fliki.ai/blog/explainer-video-script-template", "https://adwave.com/resources/explainer-video-styles"]
best_for: ["onboarding", "course", "explainer"]
formats: ["wide", "tall"]
pairs_with: ["swiss-modernist", "sticky-note-wall", "flat-vector", "minimalist-premium", "napkin-sketch", "depth-bento", "brutalist-bold", "newsdesk"]
preview: "native"
build: "native"
---

## Look
Answers a set of real questions one by one, each with a short direct answer. One question card, one answer card, a row of dots for progress.

## Behaviour
- Structure (percent of runtime): 1) hook: "3 questions we get every day" 0–8%, 2) question 1..N, each: question, direct answer first, then one detail, 8–90%, 3) a pointer for more questions and the call to action 90–100%. Order: most asked first, or the biggest doubt first.
- Each question: it enters as a large text card (`P.ease.softLand`, 400 ms) with the number; the answer line enters 0.5 s after the voice finishes the question (`P.ease.enter`, 450 ms) as a bold first sentence; a small visual supports it.
- Between questions: the old card exits left (`P.ease.exit`, 250 ms) and a progress row of N dots moves one step.
- Question length: 8–20 s; keep each under 20 s wide and 10 s tall. Changes per minute: 6–10.
- Wide 1–5 min, tall 30–60 s with maximum 3 questions. Sound: soft pop on the question card, a tick on the answer.

## Do
- Answer in the first sentence.
- Use the real wording of customers.
- Keep each answer to one idea.

## Don't
- No answer that starts with the history.
- No more than seven questions.
- Do not hide the hard question.

## Build notes
Stage 03 cues: question in, answer in, support visual, exit per item. Use one reusable Q/A component fed by data. Questions come from support mail or research (`stages/00_research`).
