# 01 Plan and voice

Read `_shared/permissions.md` before production. Pause for a human review only at the gates required by the active session permission. Paid voice generation always needs separate approval.

Inputs: the video's `project.json` and `01_voice/brief.md`. Read `_shared/script-production.md`, the brand's `brand.md`, `_shared/tone.md` and `_shared/voice.md`. Use supplied evidence for facts.

Direction first. Write in the brief: audience, purpose, language, outcome, evidence, three really different opening angles, the story structure and why, the selected opening, beats, payoff and essential visuals. Answer part A of `_shared/plan-check.md` in the brief's "Plan check" field. Pause for brief review when the active permission requires it. Optional, for each scene: `tools/precedent/precedent.py query --beat ...` shows how human designers handled that kind of beat (`tools/precedent/README.md`).

Draft and critique. Keep the first draft in `draft-original.md`. The canonical `script.md` has only spoken narration in its first fenced block. Notes and scene cues follow outside it. Run a separate critique in `critique.md` (passage, effect, concrete improvement), with at most two revision rounds. Take unresolved points to your own review. Use the **script** gate.

Create the video with `anim.py new <slug> --brand <id>`. To import your own recording, add it: `anim.py new <slug> --brand <id> recording.wav`.

Voice. Record your own voice for free, or make one with ElevenLabs. Both paths, the review gate and the listening check: `_shared/voice.md`.
- `speak --dry-run` shows the chunks and the script fingerprint. It needs no key, no network and writes nothing.
- `speak --check` tests the key, model and voice. It generates nothing.
- Paid `speak` needs the approved script and `--confirm-script <current-script-fingerprint>`. Studio passes its own confirmation fingerprint.
- Generation costs credits.

Outputs for generated narration: `01_voice/takes/NN.mp3`, the exact text in `NN.txt`, the request without credentials in `NN.json`, and the joined `01_voice/voice.mp3`. A take is reusable only when all three files match the current request. Normal runs redo stale takes. `--chunk N` redoes only chunk N and joins the takes when every take is current. If an API call or the join fails, the previous final recording stays. An imported recording stays as `01_voice/voice.*`.

Voice check: listen to the short test take and the complete final recording. Check meaning, names, pronunciation, pace, facts and permissions. Record a human decision in `REVIEW.md` only when a person reviews the exact current take. File presence and `anim.py status` are not approval. The silent fixture has no narration.

Handoff: use `_shared/dashboard-review.md` for the separate `brief`, `script`, `voice-test` and `voice` review links when the permission requires a human review. Agree the brief before scripting when its gate requires review. Paid generation always needs exact script confirmation and separate cost approval. Then complete the voice check.

Managed runs follow their saved review stages. They record automatic validation separately, reserve paid costs before each request and stop on unknown costs or uncertain charges (`_shared/autonomous-runs.md`).

Guided commands: `/vf-script`, then `/vf-voice`. Next: `/vf-transcript`.
