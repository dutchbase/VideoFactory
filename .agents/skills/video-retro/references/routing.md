# Where a lesson lives

Read the target file before proposing a change to it. The rule may already be there, or the file may have a section where the new line belongs.

| Lesson is about | Home | Notes |
|---|---|---|
| Claims, wording, voice choice, logo use, stock use, look for **one brand** | `brands/<id>/brand.md` → "Preferences" (add the section if it is missing) | Brand-only. Other brands don't inherit it. |
| Spoken wording, pronunciation, banned words (all brands) | `_shared/tone.md`; machine-checkable ones also in `tone.py` (run by `anim.py speak`) | Pronunciation fixes, e.g. abbreviations TTS misreads |
| Voice provider, voice/model choice, takes, listening | `_shared/voice.md` | |
| Brief or script process, gate order before drafting | `stages/01_voice/CONTEXT.md`, `_templates/video/01_voice/brief.md` / `script.md` | Template changes affect every new video |
| Script craft (hooks, framing, edits and their reasons) | the video's `01_voice/learning.md`; shared guidance in `_shared/script-production.md` only after 3 independent videos | |
| Transcript or word timing | `stages/02_transcript/CONTEXT.md` | |
| Cues, storyboard, scene timing | `stages/03_cues/CONTEXT.md` | |
| Scene build, look checks, stills | `stages/04_scene/CONTEXT.md`, `_shared/modern.md` | |
| Eases, timing, camera, type sizes, cuts, "never do X" in motion | `_shared/motion.md` (a second occurrence goes into "Banned defaults") | |
| Music, sfx, levels, ducking, loudness, `anim.py listen` | `_shared/sound.md` | Numbers only from measurements |
| Screen captures, logins, privacy | `_shared/capture.md` | Never touch `_auth/` |
| Render, thumbnail, description, phone copy | `stages/05_render/CONTEXT.md` | |
| Review loop, judge agent, check counters | `_shared/review.md`; judge instructions in `.claude/agents/frame-critic.md` | |
| Machine-detectable defect that recurred or was costly | `check.py` + `tests/test_check_rules.py` | Counter must read 0 before shipping |
| Library use (icons, graphics, motion clips, stock) | `_shared/library.md`, `library/CONTEXT.md` | |
| Reusable scene block | propose in the video's `REVIEW.md`; `library/blocks/` only after the user approves the video | |
| Studio behaviour, review pages, approvals, agent requests | `studio/` code (bug), `studio/CONTEXT.md` or `_shared/dashboard-review.md` (how to use it) | Large UI work becomes a follow-up |
| `anim.py` bug, missing dependency, bad error message | `anim.py` / `tools/` with a test, or `LIMITATIONS.md` when it can't be fixed now | ⚠ `anim.py` edits can make the audio check stale (`stages/05_render/CONTEXT.md`) |
| Workspace-wide rule that applies to every video | `AGENTS.md` | Use sparingly. It's the entry file for every assistant. |
| How to work with this user; environment quirks the repo can't hold | Claude memory (one file per fact, plus `MEMORY.md` line) | Not for anything a repo file can record |

## Side effects to flag (⚠)

- `anim.py` edits can make scene and audio checks stale for videos in progress.
- `_runtime/`, `_shared/` JS/CSS and `library/` assets that a scene references are part of that scene's fingerprint. Changing them stales approved scene gates.
- Any file under a video's stage folders (`01_voice/` … `05_render/stills/`) is a gate input for that video.
- `REVIEW.md` prose above `## Studio review events` is free. The JSON block under that heading belongs to Studio.
