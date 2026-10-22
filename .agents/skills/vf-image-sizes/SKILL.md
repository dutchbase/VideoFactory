---
name: vf-image-sizes
description: List the image sizes and ratios the workspace knows. Use when the user asks "which sizes", "what size is an Instagram post", "LinkedIn banner size", "profile picture size", "thumbnail size", "aspect ratio", or which sizes a platform needs.
---
# /vf-image-sizes — every known image size

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`. Map: `images/CONTEXT.md`.
This command only reads. It needs no permission.

1. Run `python anim.py image sizes`. Add `--platform LinkedIn` or `--set profile-all` when the user names one.
2. Answer with the size in pixels, the ratio, and the crop: "round crop" means the platform shows a circle.
   Name the safe area when a platform covers part of the image (stories, banners, profile photos).
3. The one home for the sizes is `_shared/image-sizes.json`. Each row has its source page and the date it was checked.
   If a row is more than a year old, or the user says a platform changed, check the platform's own help page.
   Ask before you change a row; record the new source and date.

Gate: none. A change to `_shared/image-sizes.json` needs the user's approval first.
Next: `/vf-image` to make images in these sizes.
