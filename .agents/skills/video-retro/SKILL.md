---
name: video-retro
description: Retro after making a video in VideoFactory. Reads the whole session transcript (including the parts lost to context compaction), pulls out every piece of feedback the user gave plus the process friction, tool errors, repeats from earlier videos and reusable assets, and turns them into a numbered plan of workspace changes (brand preferences, stage rules, check.py counters, shared guides, templates, memory, tooling fixes). The user picks items, then the skill applies them. Use whenever the user says /video-retro, "retro", "wrap up this video", "what did we learn", "store my feedback so I don't have to repeat it", "update the workspace from this session", "lessons learned", or a video has just been approved or rendered and the session is winding down, even if they don't say "retro".
---

# Video retro

The point of a retro: the user should never have to give the same feedback twice, and the next video should hit fewer snags than this one. You do that by finding each correction and each snag in the session, deciding whether it will come back, and giving it a permanent home in the workspace. A real check is better than a rule, and a rule is better than a memory.

The output is a plan **in chat** (no plan file). The user picks items, then you apply only those.

## 1. Find the session(s)

Arguments are optional: a video slug, a session id, or nothing.

```bash
python3 .claude/skills/video-retro/scripts/session_digest.py --list
```

This lists recent sessions of this project with their titles, message counts and the videos they touched. The newest one is normally the session you are running in.

- **No argument:** use `current`, unless it touched no video (for example the user opened a fresh session to run the retro). In that case take the newest session that touched a video and say which one you picked.
- **Slug given:** take every listed session that touched that slug. Videos often span several sessions, and a single session often covers two videos (an English original plus a translated version, for example). Retro all the videos in scope, grouped per video.
- **Unclear:** ask in one line, offering the top candidates.

Then write a digest for each session into your scratchpad and read it in full:

```bash
python3 .claude/skills/video-retro/scripts/session_digest.py <id|current> --out <scratchpad>/digest-<id8>.md
```

Read the digest even if you remember the session. Long sessions get compacted, and the summary drops exactly the small corrections a retro is for. The digest contains:

- every message the user typed, with the tail of the agent text just before it (so "approved" or "no, not like that" has context);
- judge and subagent hand-backs;
- tool errors;
- commands repeated three or more times;
- `anim.py` usage per subcommand;
- edited files.

If one user message needs more context than the digest gives, grep the `.jsonl` around its timestamp. Don't read the raw transcript start to finish: it runs to tens of MB.

## 2. Read where things stand now

The session may already have stored some of its lessons (the user often says "remember this" mid-session). Before you propose anything, look at:

- the video's `REVIEW.md` (prose above `## Studio review events`), `01_voice/critique.md`, `05_render/frame-critic.md`, and `04_scene/README.md` if present;
- `brands/<id>/brand.md`: the brand is the `"brand"` field in `videos/<brand>/<slug>/project.json`. Read its "Preferences" section, if it has one;
- the memory index `MEMORY.md` in the project's Claude memory folder;
- `git status --short` and `git log --since=<session start> --oneline`. Many edits in this workspace go through shell scripts rather than the Edit tool, so git, not the digest, is the record of what changed.

Read a target file only when a candidate lesson points to it. The routing table in `references/routing.md` says which file owns which kind of lesson.

## 3. Extract candidate lessons

Go through the digest in order and note each candidate. Only some of them become plan items.

**User feedback.** Every correction, complaint, preference, question and moment of confusion. For each one, ask: *if nothing changes in the workspace, will the user have to say this again on a future video?*

- Yes: it's a standing lesson. Generalize it to the rule underneath. "Change '10 hours a week' to something else" really means "no invented numbers, not even hypothetical ones". "The logo disappears on the black background" means "the logo only goes on light backgrounds", and maybe a contrast check.
- No: it's one-off content for this video (a word swap in this script, a timing nudge). Leave it out, but list it under "Left out" so the user can see you considered it.
- Keep the user's own words as evidence. Don't inflate their tone or put words in their mouth.

**Process friction.** Look for what cost time or confused the user:

- gates that went stale, approvals given in chat that didn't register in Studio;
- renders or transcriptions run more than once;
- steps done in an order that forced redo work;
- the user asking "which one do I pick?";
- the user reporting broken output ("the video shows nothing").

The fix is usually a clearer stage contract, a tooling change, or a memory about how to work with the user.

**Tool bugs and errors.** Use the digest's error list. Ignore harmless ones: `grep` exiting 1 on no match, a command the agent fixed on its next try because of a typo. Keep errors that point at the workspace: an `anim.py` or Studio error, a missing dependency, a workaround the agent had to invent, the same error showing up twice. Each one becomes a fix, a check, or a `LIMITATIONS.md` line.

**Repeats.** For each candidate, search the earlier record for the same problem: grep other videos' `REVIEW.md` (including earlier `## Retro` sections), `critique.md`, `frame-critic.md`, the brand's preferences, "Banned defaults" in `_shared/motion.md`, and memory. A second occurrence triggers the workspace's steering rule (`_shared/review.md` §6): don't stop at a note, add a `check.py` counter or a "Banned defaults" line. Name the earlier video as evidence.

**Reusable assets.** Look for motion pieces, blocks, sound settings or capture scripts this video created that the next video could reuse. Propose them in the video's `REVIEW.md`. They only move into `library/blocks/` once the user has approved the video (check `anim.py review <id> render`).

**What went well.** If an approach clearly worked and the user liked it, it's worth keeping too. Write it down as the default, so a later session doesn't drift away from it.

## 4. Route and size each lesson

For each standing lesson, pick its home with `references/routing.md`, and pick the lightest kind of fix that will actually stop it happening again:

1. **Check** (`check.py` counter, a `tone.py` rule, a test). Use this when a machine can detect the problem and it recurred or was costly. It works even when nobody remembers the rule.
2. **Rule in a contract or guide** (`stages/NN_*/CONTEXT.md`, `_shared/*.md`, "Banned defaults"). Use this for how the work is done, across brands.
3. **Brand preference** (`brands/<id>/brand.md`, a "Preferences" section; add it if missing). Use this for taste, claims and wording that belong to one brand. Other brands don't inherit them.
4. **Template** (`_templates/video/`). Use this when every new video should start differently.
5. **Memory** (Claude memory). Use this for how to work with the user, or quirks of the environment that the repo can't hold. Not for anything a repo file can record.
6. **Tooling fix or follow-up.** Make a small fix to `anim.py` or Studio in the retro, with a test. Larger work becomes a follow-up item with a one-line scope. Don't build features inside a retro.

Record script lessons in the video's `01_voice/learning.md`. Shared script guidance (`_shared/script-production.md`) only changes once three independent videos show the same thing. Until then, say "1 of 3" and propose only the record.

Flag side effects up front. Editing `anim.py`, `_runtime/`, `library/` assets used by scenes, or a video's stage files can make approved gates go stale on videos that are in progress or approved. Mark those items ⚠ and name the videos you expect to be affected.

## 5. Present the plan in chat

Write in plain, short sentences. The user reads this in a terminal and does not read code. Use this shape:

```
## Retro: <slug(s)> (<session title>, <date range>)
<2–3 lines: how the video went, what went well, what cost the most time.>

### Proposed changes
1. **<the lesson, one line>** · <check | rule | brand pref | template | memory | tooling | library | script learning>
   Why: "<user quote>" (<time>) · <other evidence: error, repeat in <video>, judge note>
   Change: `<file>`: <the exact line to add, or what the check/fix does>
   <⚠ side effect, if any>
2. …

### Already in place (no action)
- <lesson> → already in `<file>` (added this session / earlier)

### Left out
- <one-off item> — only for this video
- <follow-up too big for a retro> — <one-line scope> (say if you want it as a separate task)

Reply `all`, numbers (`1 3 5`), `all but 4`, or adjust ("2: make it apply to all brands").
```

Order the items by impact: what the user would otherwise have to repeat comes first, then what cost the most time. If you found nothing new, say so plainly. A short retro is a good result, not a failure.

Then stop and wait. Don't edit anything before the user answers.

## 6. Apply the chosen items

- Match the target file's style: its language (answer in the language the file already uses), how terse it is, and its attribution habit, if it has one, e.g. `(user, 2026-10-19)`. Add to an existing section rather than starting a new one. Keep each rule to a line or two, and include the reason when it isn't obvious.
- For a new check, add it to `check.py`, add a case in `tests/test_check_rules.py`, and run `.venv/bin/python -m unittest tests.test_check_rules`. Then run `anim.py check <slug>` on the session's video to see the new counter. If the counter fires on an already-approved video, report that. Don't "fix" an approved video without asking.
- Memories go in the memory folder, one fact per file, with frontmatter, plus a line in `MEMORY.md`. Update an existing memory rather than adding a near-duplicate.
- Record the retro in each video's `REVIEW.md` as a `## Retro <date>` section **above** `## Studio review events`. Studio parses exactly one JSON block under that heading, so never touch it. List each applied change as `rule added: … (<file>)` (the steering rule's wording), plus any reusable assets you proposed.
- Never approve a gate, never run paid voice, and never start a render as part of a retro. Don't commit unless the user asks.
- Afterwards, if any item was marked ⚠, run `anim.py review <slug> <gate>` for the affected videos and report what went stale.

Finish with a short report:

- what changed, per file;
- test results, with the output if anything failed;
- what you skipped and why;
- follow-ups the user may want to start.
