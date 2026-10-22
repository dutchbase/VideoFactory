---
name: vf-image
description: Make brand images in many sizes from one design. Use when the user asks for an image, a social post, an Instagram or LinkedIn picture, a banner, a header, a cover, a profile picture, an Open Graph image or "all sizes" in a brand's style.
---
# /vf-image — brand images in every size

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`. Map: `images/CONTEXT.md`.
Before production, follow `_shared/permissions.md` with the image scope named in `images/CONTEXT.md`. Ask separately before each paid request.
Read: `brands/CONTEXT.md`, then `brands/<brand>/brand.md` for the chosen brand.

1. Ask in one batch:
   - Brand. Suggest `videofactory`, or the only other brand.
   - Message and the exact words on the image.
   - Where it goes. Suggest sizes or sets from `python anim.py image sizes` (for example `instagram-all`, `linkedin-banner`, `profile-all`).
   - Picture: none, library graphic, stock photo, own file, or one AI picture (may cost money).
   Suggest a slug in the same message.
2. Run `python anim.py image new <slug> --brand <brand> --sizes <ids>`.
3. Fill `images/<brand>/<slug>/01_brief/brief.md` (`stages/images/01_brief/CONTEXT.md`). Show it in plain words.
   Run `python anim.py image review <brand>/<slug> brief` and record the decision.
4. Build the design (`stages/images/02_design/CONTEXT.md`). Add pictures with `python anim.py image picture`.
   For an AI picture follow `_shared/image-generation.md` (purpose `image-picture`).
5. Preview with `python anim.py image export <brand>/<slug> --guides`. Fix until every size reads well.
6. Export with `python anim.py image export <brand>/<slug>` (`stages/images/03_export/CONTEXT.md`). Fix every failure.
7. Show the PNGs in `images/<brand>/<slug>/03_export/`. Name what to check: text inside the safe area, the round crop, small sizes.

Gate: the `brief` review before design work, the `final` review after export (`python anim.py image review <brand>/<slug> final`). Only a person approves publication.
Next: `/vf-image-sizes` to see more sizes, or `/vf-new-video` for a video.
