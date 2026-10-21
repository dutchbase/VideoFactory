---
name: vf-new-style
description: Make a new look (style) on the Modern kit. Use when the user says "new style", "new look", "different look", "style like this site", or wants a look that no existing style gives.
---
# /vf-new-style — make a style

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
Before production, follow `_shared/permissions.md`. Pause for review only when the active permission requires it. Ask separately before each paid request.
Read: `styles/CONTEXT.md`, `_shared/style-workshop.md`, `_shared/modern.md`, `styles/modern/` (the base style).

1. Ask in one batch. If `mcp__brainstormform__ask_questions` exists, offer one form for the batch.
   - Style name and id. Suggest the name as typed and an id in lowercase with hyphens.
   - Mood in three words. Suggest "calm, clear, warm".
   - References: URLs or image files. Suggest "none".
   - Motion feel: calm, lively or snappy. Suggest "calm".
   - Formats: `wide`, `tall` or both. Suggest "wide".
2. Copy `_templates/style/` to `styles/<style>/`. Write `styles/<style>/style.md` (mood, colours, motion rules)
   and `styles/<style>/materials.md` (each material with its source and licence). Use only free or licensed material.
3. Build one sample scene in `styles/<style>/template/`. Use the Modern classes and scene CSS from `_shared/modern.md`.
   Take colours and fonts from a brand's tokens. Do not type a colour in the scene.
4. Render the 12 second sample as `_shared/style-workshop.md` says. Show the MP4 path and a still.
5. Fix what the user names. Show the sample again.

Gate: pause for human review when this session permission requires it.
Next: `/vf-new-video`. The user picks the style there, or you run `python anim.py new <slug> --brand <brand> --style <style>`.
