---
name: vf-render
description: Check and render the final MP4 (stage 05). Use when the user says "render", "export", "make the MP4", "thumbnail", "final video", "stage 5".
---
# /vf-render — check and render

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
Read: `stages/05_render/CONTEXT.md`, `_shared/review.md`.
Video id: `<brand>/<slug>`. If the user gave none, run `python anim.py status` and ask which video.

1. Check that the user approved the scene. If not, go to `/vf-scene`.
2. Run `python anim.py check <id>`. It must be clean. If not, fix it with the steps of `/vf-scene`.
3. For a long video, test the first five seconds: `python anim.py render <id> --start 0 --end 5 --workers 1`.
4. Run `python anim.py render <id>`. Say that it takes minutes. Add `--phone` if the user wants a copy under 30 MB.
5. Run `python anim.py thumbnail <id>`. Follow the thumbnail rule in `stages/05_render/CONTEXT.md`.
   Run `python anim.py chapters <id>` if the video is long enough for chapters.
6. If earshot is installed, run `python anim.py listen <id>`. It is evidence only, not approval.
7. Run the `frame-critic` judge on the render (`_shared/review.md`, the judge section). Fix what it names.
8. Show the MP4 path, the length and the loudness line (from the render output, or `videos/<id>/05_render/check-video.md`).
9. Fill `videos/<id>/05_render/DESCRIPTION.md`: title, description, chapters, sources, credits for music and effects.
   Write only true statements. Add any disclosure the contract names.

Gate: the user watches the MP4 with sound and approves it. A passing check never approves it.
Next: none. You never upload or publish. The user does that.
