---
name: vf-new-video
description: Start a new video. Use when the user says "new video", "make a video", "start a video", "new project", or gives a topic for a video and no video folder exists yet.
---
# /vf-new-video — start a video

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
Before production, follow `_shared/permissions.md`. Pause for review only when the active permission requires it. Ask separately before each paid request.
Read: `_shared/audience.md`, `brands/CONTEXT.md`. List the brands: the folders in `brands/` (ignore names that start with `_`).

1. Ask in one batch. If `mcp__brainstormform__ask_questions` exists, offer one form for the batch.
   - Brand. Suggest `videofactory`, or the only other brand.
   - Topic and goal: what the viewer knows or does after the video.
   - Audience and video type. Suggest the type that fits the topic in `_shared/audience.md`.
   - Format and length: `wide` (16:9) or `tall` (9:16). Suggest the format and length of that type.
   - Language and voice: record yourself (free) or ElevenLabs (paid). Suggest the user's language and "record yourself".
   - Looks. Run `python anim.py looks pick --brand <brand> --type <type>` and suggest its result with the source.
     Offer the brand shortlist (`brands/<brand>/looks/prefs.md`) and the board `brands/<brand>/looks/board.html`.
     If the user says "always use X" or "use X for <type>", save it with `anim.py looks prefs` (`looks/CONTEXT.md`).
   Suggest a slug in the same message (lowercase letters, digits, hyphens). Use another style only if the user names one in `styles/`.
2. Run `python anim.py new <slug> --brand <brand> --format <wide|tall> --type <type>`. Add `--style <style>` if chosen,
   and `--visual/--editing/--content <ids>` for looks the user picked that differ from the suggestion.
   Several looks are fine: comma separated, main look first (`--visual swiss-modernist,data-journalism`).
   In the brief, fill the Looks line and name the look of each scene that does not use the main look.
   If the user already has a recording, add its path after the slug: `python anim.py new <slug> <recording> --brand <brand>`.
3. Fill every heading in `videos/<brand>/<slug>/01_voice/brief.md` from the answers. Never invent facts.
   Write an open question where you do not know.
4. Show the brief in plain words and ask for changes.

Gate: pause for brief review only when this session permission requires it.
Next: `/vf-research` if the video needs facts from the web. Else `/vf-script`.
