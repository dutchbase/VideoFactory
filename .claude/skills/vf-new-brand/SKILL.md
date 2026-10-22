---
name: vf-new-brand
description: Make a new brand with colours, fonts, logo and voice. Use when the user says "new brand", "my brand", "use my website style", "add my logo", or the brand they need is missing.
---
# /vf-new-brand — make a brand

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
Before production, follow `_shared/permissions.md`. Pause for review only when the active permission requires it. Ask separately before each paid request.
Read: `brands/CONTEXT.md`, `_templates/brand/`, `brands/videofactory/` (the example brand), `_shared/design-lookup.md`.

1. Ask in one batch. If `mcp__brainstormform__ask_questions` exists, offer one form for the batch.
   - Brand name and id. Suggest the name as typed and an id in lowercase with hyphens.
   - Source: website URL, local repo path, GitHub link, logo file, or "invent". Suggest "invent".
     For a repo or GitHub link, follow `_shared/brand-from-repo.md`. Show the found values first, then ask only about gaps.
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
6. Make the style board and open it for the user: `python anim.py looks open --brand <brand> --rebuild`.
   If no browser opens, give the printed link. Ask for a default look and a shortlist of up to 5 (`looks/CONTEXT.md`).
   Save the answer with `python anim.py looks prefs --brand <brand> --default visual=<id> --shortlist <ids>`.

Gate: pause for human review when this session permission requires it.
Next: `/vf-new-video`.
