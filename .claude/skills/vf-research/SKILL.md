---
name: vf-research
description: Research a topic from public web pages for a video (stage 00). Use when the user says "research", "find facts", "sources", "check the facts", "stage 0".
---
# /vf-research — facts with sources

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
Before production, follow `_shared/permissions.md`. Pause for review only when the active permission requires it. Ask separately before each paid request.
Read: `stages/00_research/CONTEXT.md`, `_shared/research.md`, `videos/<id>/01_voice/brief.md`.
Video id: `<brand>/<slug>`. If the user gave none, run `python anim.py status` and ask which video.

1. Ask in one batch (suggest an answer for each):
   - The question the research must answer. Suggest the topic and goal from the brief.
   - Pages the user wants used, if any. Suggest "none".
   - Maximum pages. Suggest 10.
2. Run `python anim.py research <id>`. It creates `videos/<id>/00_research/`.
   If the folder exists, say so and continue in it.
3. Follow `stages/00_research/CONTEXT.md` and `_shared/research.md`: search, read the pages, save notes.
   Write `videos/<id>/00_research/research.md` and `videos/<id>/00_research/sources.md`.
   Each fact ends with a source number. Write only what a source says.
4. Show the findings, the conflicts and the open points in plain words. Name the weakest source.

Gate: pause for human review only when this session permission requires it. Stop if facts or evidence are missing.
Next: `/vf-script`.
