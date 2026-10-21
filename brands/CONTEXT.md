# Brands

One folder per brand: `brands/<id>/`. The house brand is `brands/videofactory/`. It shows every part in one place, so copy it as an example. Select a brand explicitly: `anim.py new <slug> --brand <id>`. A video stores its brand in `project.json`. A missing brand is an error.

| File | Holds |
|---|---|
| `brand.md` | Look, fonts, logo, motion, sound and tone in prose |
| `tokens.js` | The values: colours, fonts, ramp, gradients. It sets `window.BrandTokens` |
| `voice.md` | Voice settings (`voice_id`, `model`, `stability`, `similarity_boost`, `format`). Guide: `_shared/voice.md`. A video freezes its selection in `settings.json` |
| `logo/` | `mark.svg` and, if you have one, `mark-mono.svg` |
| `sound/` | Optional brand sounds with their licences in `sound/SOURCES.md` |
| `library/` | Optional brand assets, such as a motion pack |

Inputs: the brand's real source (site CSS, styleguide, logo files, or a repo: local path or GitHub link, see `_shared/brand-from-repo.md`), supplied by you or invented for a new brand.

Process (guided: `/vf-new-brand`):
1. Copy `_templates/brand/` to `brands/<id>/`.
2. Fill `tokens.js` (a flat file with the same keys as `brands/videofactory/tokens.js`) and `brand.md`.
3. Add each brand font to `_runtime/fonts/`, `fonts.css` and `FONT-SOURCES.json`, with its licence file.
4. Fill `voice.md`, add the logo files, then check the brand counters (`_shared/design-lookup.md`, step 5). They must read 0.

Outputs: `brands/<id>/brand.md` and `brands/<id>/tokens.js`. From a repo also `brands/<id>/SOURCE.md`: what came from where.

Human check: compare each colour and font with the brand source. Confirm the font licences. Record your approval in the video's `REVIEW.md`.

Optional design ideas for a new brand, style or chart: `_shared/design-lookup.md`. Brand tokens still win.
