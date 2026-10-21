# Production policy

Read this policy before production work. Stage details live in the stage contracts.

Before every production session in chat, Studio or a saved run, ask the exact question and offer the choices in `_shared/permissions.md`. Wait for a clear answer. Save its session ID and named scope. Never carry permission forward from an earlier session. Apply the same scope to workers.

- Work on one `videos/<brand>/<slug>/` at a time. Read only the current stage contract and its inputs.
- Agree audience, purpose, language, outcome, evidence, three opening angles, the selected framework and opening, beats, payoff and essential visuals in `01_voice/brief.md` at the brief gate before you draft. Use `_shared/script-production.md`. Keep the canonical script in this video's `01_voice/script.md`.
- The session permission selects whether work pauses after each stage or at selected stages. Full permission lets work continue to `ready-for-final-review` after required checks and evidence pass; it does not force a render-gate review. A stage completed under permission is recorded as agent completion, not as a human review. Human decisions stay separate, tied to the exact current fingerprint and reviewer in `REVIEW.md`. Chat and Studio use the same review action. Automatic validation is separate. `anim.py status` shows files, not approval. See `_shared/permissions.md`.
- All motion is a function of time. Record whether a screen is a real capture or authored in `04_scene/assets/captures.md` and `REVIEW.md`. Never put provenance labels on screen, such as "illustrative", "illustrated", "real capture" or "stock footage" (`tone.py` refuses them). Put disclosures your platform needs, such as a note about an AI voice, in the description.
- A render starts when you run it. There is no queue and no time window. A managed run may render when its saved settings and current checks permit it.
- Nothing ships until `anim.py check <slug>` reads 0 on every counter (render runs it). Capture the first clear failure as a lesson. Add a regression check when software can detect the failure (`_shared/review.md`).
- Every video moves and has pictures and music: never a text-only video, never a still stretch over 3 s (`_shared/motion.md`), always a music bed (`_shared/sound.md`). Make an exception only when you ask for it.
- A video may use shared assets within its video scope. Editing a shared asset needs permission for that named brand, style or character. After each video, propose reusable parts as new blocks in the video's `REVIEW.md`; add them to `library/blocks/` only with the matching permission.
- Capture web pages and apps with `anim.py grab`, `record` and `login` at mobile, tablet, laptop or desktop size. Guide: `_shared/capture.md`. Never share `_auth/`.
- Never invent prices, course content, testimonials, numbers or quotes. Use the selected brand's verified sources and the evidence you supply.
- Facts from the web need a source number in `research.md`. Never state third-party claims as the brand's own facts.
- Characters are invented. Never present them as real customers.
- Paid actions always need separate approval for the exact request and known cost. A retry needs fresh approval. Keep keys in `.env` (git-ignored). There is no publishing automation: upload only after a person approves the final video and the destination.
- `tests/fixtures/silent-first-scene/` is the setup test only.
