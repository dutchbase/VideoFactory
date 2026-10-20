---
name: vf-status
description: Show the progress of the videos. Use when the user says "status", "progress", "which videos do I have", "what is done", "where am I with video X".
---
# /vf-status — progress

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
Read: nothing else. Run `python anim.py status`. For one video: `python anim.py status <id>`.
Video id: `<brand>/<slug>`.

1. Run the command. Show the table.
2. Explain the table in plain words. Each row is a video. The columns are the stages: voice, words, cues, scene, render.
   A stage is done when its output file exists. A file on disk is not an approval by the user.
3. For one video, name the first stage that is not done and its command:
   - voice: `/vf-script`, then `/vf-voice`
   - words: `/vf-transcript`
   - cues: `/vf-cues`
   - scene: `/vf-scene`
   - render: `/vf-render`
4. If the user did not name a video and there are many, point at the newest one. Offer `/vf` to continue.

Gate: none.
Next: the command from step 3, or `/vf`.
