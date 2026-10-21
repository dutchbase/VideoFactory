# Studio review handoff

Read `_shared/permissions.md` before production in chat or Studio. Studio shows the current permission for the session and named scope. File presence and `anim.py status` show production progress. Only a human decision for the current fingerprint in `videos/<brand>/<slug>/REVIEW.md` records approval.

1. Read only the active `stages/NN_*/CONTEXT.md` and its named inputs.
2. Claim the video or a waiting Studio request before you author. Preserve work on other videos.
3. Finish the stage output and run its checks. Compute the current fingerprint with `studio.workspace.gate_fingerprint(root, slug, gate)`.
4. Run `.venv/bin/python anim.py review <slug> <gate> --ready --expected <fingerprint>`. This records readiness and prints the exact review link. It does not approve the output.
5. Open that link with an available approved browser tool and post the same link in chat. If opening is unavailable, post the link and say so. Never use `xdg-open` as a substitute.
6. Pause when the session permission requires review. Read the recorded decision and current fingerprint with `.venv/bin/python anim.py review <slug> <gate>` or on the Studio page. Permission-based stage completion is not a human decision.
7. If edits or changes were requested, process the saved files and return for review. An unsaved browser draft is never an input.
8. Continue only when every required current revision is approved. Brief agreement and transcript checks remain required for narrated videos. The silent setup fixture follows its explicit silent path.

Research may be skipped only with a reason. Voice generation is paid work and requires an explicit confirmation of the current script (`_shared/voice.md`). The test take and the complete voice have separate reviews. A successful export stays a draft until you can inspect the MP4, the phone frames in `05_render/phone/`, and an independent judge record in `05_render/frame-critic.md`. The judge record states the reviewer, the date, seven scores (hook, 360 px readability, motion, variety, composition, accuracy, sound sync) and the three worst problems, or says explicitly that there are none. Request `review-checks` agent work in Studio when that evidence is missing. Final upload and destination are manual after your approval.

Dashboard requests stay `waiting-for-agent` until a real agent claims them. You can also press **Run agent**: it claims the request and runs an unattended `claude -p`, which never approves. `anim.py review <slug> <gate>` prints the current fingerprint for `--ready --expected`. Claim with `.venv/bin/python anim.py studio-request <id> --claim <agent>` and finish with `--finish succeeded|failed|cancelled --note '...'`. Production jobs use the same validation through `.venv/bin/python anim.py studio-job <action> <slug> --options <json-file> --request-id <id>`. The options file is structured JSON, never a shell command. `.studio/` holds operational records only. Review and production facts stay in the video files.

Managed runs stop at the review stages in their active session permission. Their stage completions, automatic validations and human review decisions are separate records. The final export needs independent current review evidence. A person must approve publication.
