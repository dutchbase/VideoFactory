# How a guided command works

The `/vf-…` commands (`.claude/skills/` for Claude Code, `.agents/skills/` for Codex) all follow these steps.
Talk rules: `_shared/talk.md`. Command list: `AGENTS.md`.

1. **Locate.** Find the video (or brand, or style) the user means. If there is more than one, ask.
   `python anim.py status` lists every video and its stages.
2. **Read the contract.** Read only the files the command names: the stage `CONTEXT.md` and its inputs.
   Do not read the whole workspace.
3. **Ask, in one batch.** Collect what is missing in one message: 3 to 5 questions, each with a suggested answer
   the user can accept with "yes". Never ask what a file already answers.
   If the Brainstormform tools exist (`mcp__brainstormform__*`), offer a form for long interviews (brand, style,
   brief). Brainstormform is optional: <https://github.com/dutchbase/brainstormform>.
4. **Do the work.** Write the output files the contract names. Run the `anim.py` command the stage uses.
5. **Show the result.** Name each file the user must look at, and what to check in it. For pictures, run
   `python anim.py stills <slug>` and point at the contact sheet.
6. **Stop at the gate.** Every stage ends with a human check. Do not start the next stage until the user says the
   result is good. A change request means: edit, show again, ask again.
7. **Name the next step.** End with the next command, for example "Next: `/vf-cues`."

## Rules for every command
- Paid actions (ElevenLabs, AI images) cost money: say what it costs in plain words and ask before each one.
- Never put a key in a file that git tracks. Keys live in `.env` only.
- Never invent facts, people, quotes or numbers for a video. Ask, or use the research in `00_research/`.
- If a command fails, show the exact error, say what it means in one sentence, and give the fix.
