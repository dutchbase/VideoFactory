---
name: vf-new-brand
description: Make a new brand with colours, fonts, logo and voice. Use when the user says "new brand", "my brand", "use my website style", "add my logo", or the brand they need is missing.
---
# /vf-new-brand — make a brand

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
Read: `brands/CONTEXT.md`, `_templates/brand/`, `brands/videofactory/` (the example brand), `_shared/design-lookup.md`.

1. Ask in one batch. If `mcp__brainstormform__ask_questions` exists, offer one form for the batch.
   - Brand name and id. Suggest the name as typed and an id in lowercase with hyphens.
   - Source: website URL, logo file, or "invent". Suggest "invent".
   - Colours. Suggest reading them from the site CSS. With no site, suggest three colours from `_shared/design-lookup.md`.
   - Fonts. They must be local and licensed. Suggest one from `_runtime/fonts/`, or an OFL font from Google Fonts.
   - Tone, audience and voice. Suggest plain and friendly, and "the user records their own voice".
2. Copy `_templates/brand/` to `brands/<brand>/`. Fill `brands/<brand>/tokens.js`, `brands/<brand>/brand.md` and
   `brands/<brand>/voice.md`. Put the logo in `brands/<brand>/logo/`.
3. If you add a new font file, register it as `brands/CONTEXT.md` says.
4. Check the brand: `.venv/bin/python -c "import check,pathlib;print(check.brand_counters(pathlib.Path('.'),'<brand>'))"`.
   Every counter must read 0. Fix and run again.
5. Make a sample: `python anim.py new <brand>-sample --brand <brand>`.
   Then `python anim.py stills <brand>/<brand>-sample --at 1,4`. Show the stills.

Gate: the user approves the colours and fonts on the stills.
Next: `/vf-new-video`.
