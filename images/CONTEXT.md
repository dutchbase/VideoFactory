# Brand images

The second pipeline of this workspace, next to videos. One job makes one design and exports it to every size the brief names: social posts, stories, banners, profile pictures, thumbnails, link previews. The look comes from the brand (`brands/<brand>/tokens.js`, `logo/`, fonts) and the shared library. Video thumbnails stay in the video pipeline (`stages/05_render/CONTEXT.md`).

One job lives in `images/<brand>/<slug>/`. State is the files in it:

| Folder | Holds | Contract |
|---|---|---|
| `01_brief/brief.md` | message, exact text, sizes, picture plan | `stages/images/01_brief/CONTEXT.md` |
| `02_design/` | `design.html`, `design.js`, `pictures/`; links `brand`, `runtime`, `library` | `stages/images/02_design/CONTEXT.md` |
| `03_export/` | one `<size-id>.png` per size, `report.json` (the checks), `preview/` (with safe-area lines) | `stages/images/03_export/CONTEXT.md` |
| `REVIEW.md` | review events for the `brief` and `final` gates | `_shared/permissions.md` |

Sizes: `_shared/image-sizes.json` is the one home for every platform size (pixels, round crop, safe area, source page, date checked) and the named sets (`instagram-all`, `profile-all`, `banner-all`, …). `python anim.py image sizes` lists them. Check a size against the platform's own help page when the `checked` date is more than a year old, and update the row.

Commands: `python anim.py image new|sizes|export|status|review|picture` (`-h` on each).

Permission: scope `image:<brand>/<slug>` (`_shared/permissions.md`). `image new`, `picture` and `export` need it; `picture` and `export` also need a passed `brief` review. Two review gates: `brief` before design work, `final` after export. An edit to the brief or the design after a decision makes that decision stale. Automatic checks never approve publication: a person does.

Guided commands: `/vf-image`, `/vf-image-sizes`.
