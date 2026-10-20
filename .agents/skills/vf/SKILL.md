---
name: vf
description: Start here. Use when the user types /vf, or says "start", "where am I", "what next", "continue my video", or does not know which command to run.
---
# /vf — find the next step

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
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
6. Say in two sentences where the video stands and which command is next. Ask "Start it now?".
   On yes, open `.claude/skills/<name>/SKILL.md` for that command and follow its steps.

A file on disk is not an approval. If you are not sure the user approved the last stage, ask.
Gate: the user says yes to the proposed step.
Next: the skill from step 4.
