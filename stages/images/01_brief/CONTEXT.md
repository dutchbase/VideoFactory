# Image 01 Brief

Read `_shared/permissions.md` first. Scope: `image:<brand>/<slug>`.

**Inputs.** The user's request. Reference: `brands/<brand>/brand.md` (tone and look), `_shared/image-sizes.json` (through `python anim.py image sizes`).

**Job.** `python anim.py image new <slug> --brand <brand> --sizes <ids or sets>` copies `_templates/image/`. Fill every section of `01_brief/brief.md`:

- **Message**: one sentence; who sees it and where.
- **Text**: the exact words on the image. A headline of about 8 words or fewer, an optional kicker and one line. One version for all sizes: small sizes hide parts, they do not get other words.
- **Sizes**: size ids or set names, one per line. Each must exist in `_shared/image-sizes.json`.
- **Picture plan**: a line `kind: none|library|stock|own|ai`, then the details. `ai` needs the prompt and the reference material IDs (`library/materials/`); it costs money on the paid route, so name the route.

Never invent facts, numbers or quotes.

**Output.** `01_brief/brief.md`.

**Human check.** `python anim.py image review <brand>/<slug> brief` shows the state and what is missing. Mark it ready with `--ready --expected <fingerprint>`. A person approves with `--approve --reviewer NAME --expected <fingerprint>`, or the session permission accepts it with `--accept` when no review is required.
