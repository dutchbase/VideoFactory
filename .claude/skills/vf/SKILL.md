---
name: vf
description: Start here. Use when the user types /vf, or says "start", "where am I", "what next", "continue my video", or does not know which command to run.
---
# /vf — find the next step

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
Before production, follow `_shared/permissions.md`. Pause for review only when the active permission requires it. Ask separately before each paid request.
Read: `AGENTS.md`, `CONTEXT.md`. Run `python anim.py status`.
If the system `python` lacks the packages, use `.venv/bin/python` wherever a skill says `python`.

1. If the folder `.venv` does not exist, offer `/vf-setup` and stop.
2. If `status` lists no video, offer `/vf-new-video`. If the user has no brand of their own, mention `/vf-new-brand`.
3. If `status` lists many videos, ask which one. Suggest the newest.
4. For the chosen video, find the first stage that is not done:
   - Brief empty: `/vf-new-video` (it fills the brief).
   - `videos/<id>/01_voice/script.md` still contains `Replace this with the script`: `/vf-script`.
   - No voice file in `videos/<id>/01_voice/`: `/vf-voice`.
   - No words in `videos/<id>/02_transcript/`: `/vf-transcript`.
   - No cues in `videos/<id>/03_cues/`: `/vf-cues`.
   - `videos/<id>/04_scene/scene.js` still has the `TEMPLATE` marker: `/vf-scene`.
   - No MP4 in `videos/<id>/05_render/`: `/vf-render`.
   - All done: tell the user the video is ready to watch. The user decides to publish.
5. `/vf-research` is optional, before `/vf-script`. Offer it when the video needs facts from the web.
   If the user asks for an image, a post, a banner or a profile picture, run `python anim.py image status` and use `/vf-image`.
6. Say in two sentences where the video stands and which command is next. If the user asked to continue, open the matching skill in `.agents/skills/` or `.claude/skills/` and follow it. If the user only asked for status, offer the command and wait for their instruction.

A file on disk is not an approval. Check `_shared/permissions.md` to see whether the last stage needs human review.
Gate: session permission controls stage reviews. Do not ask for another start confirmation when the user already asked to continue.
Next: the skill from step 4.
