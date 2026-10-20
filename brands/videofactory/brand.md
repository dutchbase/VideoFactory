# VideoFactory brand for animation (id: `videofactory`)

The house brand of this repo. It shows every brand part in one place, so a new brand can copy it.
Values live in `tokens.js`; this file says how to use them.

## Look
- Dark studio. Near-black field (`bg`), slightly lighter cards (`surface`), cream text (`ink`).
- One hot accent: factory orange `#FF5B2E`. Use it for the one thing the viewer must look at. Never for body text.
- One cool second voice: violet `#7C5CFF`. Use it for a contrast idea, a second series in a chart, or a tag.
- Green `#3DDC84` means done or correct. Red `#FF4D5E` means wrong or stop. Use them for nothing else.
- Soft depth: big rounded cards (28 px corners), deep soft shadows, two slow glows in the background. No hard outlines, no textures.
- Big type with tight letter spacing. Few words on screen; the voice carries the detail.

## Fonts (all SIL Open Font License, local in `_runtime/fonts/`)
- Headings: Archivo, weight 750–800.
- Body: Inter.
- Labels, numbers in code, kickers: JetBrains Mono, uppercase with wide spacing.
- Hand notes: Caveat, at most one per shot.

## Logo
- `logo/mark.svg`: the mark in brand colours. `logo/mark-mono.svg`: one colour (`currentColor`).
- The word mark is live text: `Video` in `ink` and `Factory` in `accent`, Archivo 800. Do not stretch or recolour the mark.

## Motion
- Things enter fast and land soft (`rise`, `words`, `pop` in `_shared/modern.md`). Exits are short.
- Each shot has one entrance moment on a spoken cue. Do not animate what the voice does not mention.
- The motion pack in `library/motion/` uses the same tokens.

## Sound
- Soft clicks, whooshes and pops, never chiptune. Files and their licences: `sound/SOURCES.md`.

## Cast
- None. All people in examples are invented. Never use a real customer, quote or face.

## Tone
Rules: `_shared/tone.md`. Brand notes: friendly maker, plain English, short sentences, no hype words.
Audience: people who want to make explainer videos with an AI agent and do not want to learn video software.
Call to action: "Clone the repo and run `/vf-setup`."
