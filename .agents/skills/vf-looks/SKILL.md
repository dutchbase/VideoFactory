---
name: vf-looks
description: Show the video looks of a brand and save the user's picks. Use when the user says "looks", "video styles", "style board", "which style", "always use X", "shortlist", "use X for courses/shorts", "default style", or after a brand or a look is added.
---
# /vf-looks — pick video looks per brand

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`. Map: `looks/CONTEXT.md`.
`list`, `check`, `pick` and `board` only read the cards. `prefs` changes the brand and needs `brand:<id>` permission (`_shared/permissions.md`).

1. Find the brand. With no board yet, or after a brand's `tokens.js` changed, run `python anim.py looks board --brand <brand>`.
   After a new look card, run `python anim.py looks board --all`.
2. Open the board for the user: `python anim.py looks open --brand <brand>` (add `--look visual-<id>` for one look).
   If no browser opens, give the printed link. Say the three groups: visual (how it looks), editing (how it moves and cuts),
   content (what the video does). A click on an image shows the look's explanation.
3. Save what the user says with `python anim.py looks prefs --brand <brand>`:
   - "always use X" → `--default visual=X` (or `editing=`, `content=`).
   - "put X on the shortlist" → `--shortlist <all ids, max 5>`. With 5 already, ask which one to drop.
   - "use X for courses" → `--rule course:visual=X`. Rule keys are video types from `_shared/audience.md` or content ids.
   - Several looks: join ids with `+`, main look first (`--rule course:visual=whiteboard+data-journalism`).
   Then run `python anim.py looks board --brand <brand>` so the board shows the badges.
4. To show what a new video gets: `python anim.py looks pick --brand <brand> --type <type>`. Say the source of each pick.
5. AI previews (cards with `preview: "ai"`) need a paid or approved image batch. Offer it; never start it without approval (`looks/CONTEXT.md`, Board).

Gate: none for reading. A change to the picks is the user's own instruction.
Next: `/vf-new-video`.
