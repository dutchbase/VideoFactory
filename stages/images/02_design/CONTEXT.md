# Image 02 Design

Read `_shared/permissions.md` first. Needs a passed `brief` review.

**Inputs.** Working: `01_brief/brief.md`, `02_design/design.html`, `02_design/design.js`, `02_design/pictures/`. Reference: `brands/<brand>/tokens.js` and `brand.md`, `_runtime/image.css` (the layout classes), `_shared/modern.md` (the `vf-*` parts), `library/CATALOG.md`.

**Job.** Build one responsive design in `design.html`. It must look composed at every brief size, not stretched.

- Size everything in `var(--u)` (1/100 of the short side of the safe area). Never in px.
- Put text and the logo inside `.vf-frame`. That frame is the safe area: platform buttons, round crops and profile photos cover the rest.
- The page gets a layout class: `.is-avatar` (round crop or logo-only sizes), `.is-banner`, `.is-wide`, `.is-square`, `.is-portrait`, `.is-tall`. Hide parts per layout with `data-hide="avatar banner"`. Use `design.js` (`window.VF_IMAGE`) only for what CSS cannot do.
- Colours and fonts come only from the brand. Icons: `<i data-icon="lucide/name">`. Graphics: `library/graphics/...` through the `library` link.
- Pictures go in `02_design/pictures/`. Own file or stock photo: `python anim.py image picture <brand>/<slug> <file or stock:provider/photo/id>` (logs the source in `pictures/SOURCES.md`). A full-bleed picture sits in a `data-bleed` element behind the frame.
- AI picture: follow `_shared/image-generation.md` with purpose `image-picture`, `subject_type` `image`, `subject_id` `<brand>/<slug>` and `input_revision` = the current `brief` fingerprint. Show the batch and ask for its approval; ask separately for any cost. The file lands in `02_design/pictures/generated/<id>/`.

Preview: `python anim.py image export <brand>/<slug> --guides` writes `03_export/preview/` with the safe area drawn. Open them and fix the design until each size reads well.

**Output.** `design.html`, `design.js`, `pictures/`.

**Human check.** None of its own: the `final` review covers the design through its exported images.
