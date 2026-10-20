# Workflow

A video moves through five stages, with an optional research stage first. Each stage has a contract in `stages/NN_*/CONTEXT.md`. Setup and commands: `START-HERE.md`.

0. Research (optional, `stages/00_research`): `anim.py research <slug>`. Notes from public pages in `research.md` and `sources.md`. Check each claim against its source. Skip it when you supply all facts.
1. Voice (`stages/01_voice`): brief, angles and outline, then a script and a separate critique (at most two revisions). Approve the script, then record your own voice or make one with ElevenLabs (`_shared/voice.md`). Listen to the complete take.
2. Transcript (`stages/02_transcript`): `words.json` and `transcript.md`. Check them against the audio.
3. Cues (`stages/03_cues`): you write `cues.md`. It compiles to `cues.json` and `cues.js`. Read the storyboard.
4. Scene (`stages/04_scene`): `index.html` and `scene.js` in the Modern kit (`_shared/modern.md`). Check the stills and watch the preview.
5. Render (`stages/05_render`): MP4, thumbnail and `DESCRIPTION.md`. Watch the exported file. A render starts at once when you run it.

Status is which files exist in each `videos/<brand>/<slug>/NN_*` folder (`anim.py status`). It is not approval. Approval lives in each video's `REVIEW.md`.

Studio review uses exact saved fingerprints and a separate ready step. Follow `_shared/dashboard-review.md`. `anim.py review <slug> <gate>` shows the current state and the review link. Start the local page with `anim.py studio` (`studio/CONTEXT.md`). Reusable looks live under `styles/`. Described source records live under `library/materials/`. `.studio/` stores jobs and requests, not production facts.

Tall (9:16) fits socials and ads. Wide (16:9) fits courses, explainers and onboarding (`_shared/audience.md`).

Managed runs use a saved review mode and the current output as evidence (`_shared/autonomous-runs.md`). Automatic validation is never your approval.
