# Spoken and on-screen language

Read the selected `brands/<id>/brand.md` from `project.json`, including any voice guidance it references. A brand is required. Writing for the voice, step by step: `voice.md`.

Use active, concrete language for this audience and purpose. Vary sentence length and rhythm. Read narration aloud and split where meaning or breath requires it. Twenty words is a listening prompt, not a hard limit for narration. Keep honest uncertainty, source attribution and the brand's requirements. Never invent facts, results, experiences or testimonials.

Instead of "Unlock your productivity", say "Move the invoice into this folder, then check its label." These are authored examples, not product claims. The full self-contained guidance is in `script-production.md`.

On-screen text stays short and has one idea at a time. The visual readability checks still apply. No em dashes. Never put a provenance label on screen (such as "illustrative" or "stock footage"). Record where a screen came from in the project records instead.

`tone.py` checks em dashes, on-screen strings over 20 words and provenance labels. Narration may use longer natural sentences. `anim.py speak`, `stills` and `render` run their checks. `--skip-tone` is the explicit override. A person checks naturalness, uncertainty, brand fit and factual support at the script gate.
