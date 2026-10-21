# How a guided command works

The `/vf-…` commands (`.claude/skills/` for Claude Code, `.agents/skills/` for Codex) all follow these steps.
Talk rules: `_shared/talk.md`. Command list: `AGENTS.md`.

Before production in any interface, read `_shared/permissions.md`. Identify the video, brand, style or character scope, ask exactly “Do I have full permission for this session?”, offer the three choices there, and wait for the answer. A session grant is never inferred from silence or an earlier session.

1. **Locate.** Find the video (or brand, or style) the user means. If there is more than one, ask.
   `python anim.py status` lists every video and its stages.
2. **Read the contract.** Read only the files the command names: the stage `CONTEXT.md` and its inputs.
   Do not read the whole workspace.
3. **Ask, in one batch.** After session permission is clear, collect what is missing in one message: 3 to 5 questions, each with a suggested answer
   the user can accept with "yes". Never ask what a file already answers.
   If the Brainstormform tools exist (`mcp__brainstormform__*`), offer a form for long interviews (brand, style,
   brief). Brainstormform is optional: <https://github.com/dutchbase/brainstormform>.
4. **Do the work.** Write the output files the contract names. Run the `anim.py` command the stage uses.
5. **Show the result.** Name each file the user must look at, and what to check in it. For pictures, run
   `python anim.py stills <slug>` and point at the contact sheet.
6. **Stop at the gate.** Pause at the stages required by the saved session permission. If the user reviews a stage, record the decision against its exact current fingerprint. Permission-based stage completion is not a human review decision. A change request means: edit, show again, ask again. Never publish without a person's approval.
7. **Name the next step.** End with the next command, for example "Next: `/vf-cues`."

## Rules for every command
- Permission does not cover paid actions. Before each paid request, show its exact request and known cost and ask for approval. A retry needs fresh approval. Stop if the price is unknown.
- Paid actions (ElevenLabs, AI images) cost money: say what it costs in plain words and ask before each one.
- Never put a key in a file that git tracks. Keys live in `.env` only.
- Never invent facts, people, quotes or numbers for a video. Ask, or use the research in `00_research/`.
- If a command fails, show the exact error, say what it means in one sentence, and give the fix.
