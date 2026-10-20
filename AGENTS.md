# VideoFactory

A folder workspace that turns a voice into an explainer video: script → voice → words → cues → scene → MP4.
One video lives in `videos/<brand>/<slug>/`; its numbered folders are the stages. State is the files in them.

**Talk rule:** every chat reply follows `_shared/talk.md` (ASD-STE100, the user's language).
**Work rule:** every guided command follows `_shared/guide.md` (ask in one batch, stop at each human check).

## Guided commands
| Command | Job | Contract |
|---|---|---|
| `/vf` | Find where the user is and run the next step | `CONTEXT.md` |
| `/vf-help` | List the commands in plain words | this file |
| `/vf-setup` | Install, test render, optional keys | `START-HERE.md` |
| `/vf-new-brand` | Make a brand: colours, fonts, logo, voice, sound | `brands/CONTEXT.md` |
| `/vf-new-style` | Make a style on the Modern kit | `styles/CONTEXT.md`, `_shared/style-workshop.md` |
| `/vf-new-character` | Make a character with the character factory | `characters/CONTEXT.md`, `_shared/character-workshop.md` |
| `/vf-new-video` | Start a video: brand, format, topic | `_shared/audience.md` |
| `/vf-research` | Stage 00: facts and sources | `stages/00_research/CONTEXT.md` |
| `/vf-script` | Stage 01: brief and script | `stages/01_voice/CONTEXT.md`, `_shared/script-production.md` |
| `/vf-voice` | Stage 01: record or generate the voice | `_shared/voice.md` |
| `/vf-transcript` | Stage 02: words with times | `stages/02_transcript/CONTEXT.md` |
| `/vf-cues` | Stage 03: the moments the picture changes | `stages/03_cues/CONTEXT.md` |
| `/vf-scene` | Stage 04: the animation | `stages/04_scene/CONTEXT.md`, `_shared/modern.md` |
| `/vf-render` | Stage 05: check and render the MP4 | `stages/05_render/CONTEXT.md` |
| `/vf-status` | Progress of every video | `python anim.py status` |

## Routes
| Need | Contract |
|---|---|
| Pipeline and stages | `CONTEXT.md` |
| Rules for every run | `_shared/production-policy.md` |
| Tone, script, voice | `_shared/tone.md`, `_shared/script-production.md`, `_shared/voice.md` |
| Scene look and helpers | `_shared/modern.md`, `_shared/motion.md`, `_shared/transitions.md` |
| HTML engine (advanced) | `_shared/hyperframes.md` |
| Review and checks | `_shared/review.md`, `_shared/plan-check.md` |
| Sound and music | `_shared/sound.md`, `library/audio/CONTEXT.md` (effects and music library) |
| What the library holds (every part, by category) | `library/CATALOG.md` |
| Library, stock, AI images | `_shared/library.md`, `_shared/image-generation.md` |
| Rewrite a new component into the library | `_shared/porting.md` |
| Screenshots and recordings | `_shared/capture.md` |
| Studio (browser app) | `studio/CONTEXT.md`, `_shared/dashboard-review.md` |
| Autonomous runs | `_shared/autonomous-runs.md` |
| Limits | `LIMITATIONS.md` |

The CLI is `python anim.py <command>` (`-h` lists all). A video needs `--brand`; the house brand is `videofactory`.
Automatic checks never approve publication: a person does.
