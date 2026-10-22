---
id: "listicle"
axis: "content"
title: "Listicle: top N"
summary: "A countdown or ranked list: each item gets one number, one name, one reason."
aliases: ["top 5", "top 10", "countdown", "N things"]
sources: ["https://yansmedia.com/blog/explainer-video-structure", "https://fliki.ai/blog/explainer-video-script-template", "https://adwave.com/resources/explainer-video-styles"]
best_for: ["short", "explainer", "course"]
formats: ["wide", "tall"]
pairs_with: ["brutalist-bold", "halftone-pop", "kinetic-typography", "high-end-social", "sticky-note-wall", "editorial-collage", "swiss-modernist", "risograph"]
preview: "native"
build: "native"
---

## Look
A countdown or ranked list: each item gets one number, one name, one reason. One big number and one name fill each beat.

## Behaviour
- Structure (percent of runtime): 1) hook with the promise "5 ways to ..." 0–8%, 2) items from lowest to best, each the same shape 8–88%, 3) the best item gets 1.5x time 70–88%, 4) one-line recap of all N 88–96%, 5) call to action 96–100%.
- Each item: number slams in (`P.ease.crashIn`, 330 ms) on the word "number" or the first word of the item; name types in below (`P.ease.softLand`, 400 ms); one visual proof enters 0.6 s later (`P.ease.enter`, 450 ms); the voice gives one reason.
- Item length: 6–10 s wide, 4–6 s tall. Out: previous item exits left (`P.ease.accelExit`, 430 ms) as the next number arrives, so the list moves one way.
- A rail with N dots stays on screen; the active dot fills with the accent (`P.spring` snap). Counting down means the number gets smaller. Counting up needs a clear "best" at the end.
- Item 1 (or the last revealed): hold 1.5 s longer, add a pop on the number (`P.spring` pop).
- Changes per minute: 10–15. Length: wide 60–180 s for N = 5–10; tall 20–60 s for N = 3–5. Sound: short riser before each number, one hit on the number.

## Do
- Use the same layout for every item.
- Say the number out loud.
- Keep N at 3, 5 or 7 for tall; 10 for wide at most.

## Don't
- No item longer than 12 s.
- No item without a reason or proof.
- Do not reveal the best item first.

## Build notes
Stage 03 cues: number, name, proof, exit per item. Build one item component and repeat it with data. Rail dots are plain divs toggled by cue.
