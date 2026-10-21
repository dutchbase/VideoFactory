<div align="center">

# 🎬 VideoFactory

**Turn a voice into an explainer video. Talk to an AI agent, approve each step, get an MP4.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![Platform: Linux](https://img.shields.io/badge/platform-Linux-informational?logo=linux&logoColor=white)
![Works with Claude Code and Codex](https://img.shields.io/badge/works%20with-Claude%20Code%20%7C%20Codex-8A63D2)

`script` → `voice` → `words` → `cues` → `scene` → `MP4`

</div>


Make explainer videos by talking to an AI agent. You bring a topic and a voice. The agent writes the script with you, times every word, builds the animation and renders a finished MP4. You check and approve each step.

Everything lives in one folder on your computer. There is no timeline editor and no cloud service. VideoFactory works with [Claude Code](https://claude.com/claude-code) and [Codex](https://github.com/openai/codex).

<!-- DEMO -->

## How it works

A video moves through six stages. Each stage is a numbered folder, and each stage stops so you can read, edit and approve the result before the next one starts.

| Stage | Folder | What you get |
|---|---|---|
| 00 Research (optional) | `00_research/` | Facts from public web pages, each with its source |
| 01 Voice | `01_voice/` | A brief, the script, and the voice file (your own recording or ElevenLabs) |
| 02 Transcript | `02_transcript/` | Every spoken word with its exact time (Whisper) |
| 03 Cues | `03_cues/` | The moments where the picture changes, tied to words |
| 04 Scene | `04_scene/` | The animation: HTML, CSS and JavaScript, rendered in a headless browser |
| 05 Render | `05_render/` | The MP4, a phone copy, a thumbnail, YouTube chapters and check reports |

A video lives in `videos/<brand>/<slug>/`. The state of a video is simply which files exist, so you can open any folder and see where things stand.

Nothing is paid for or published without a clear yes from you. Paid voice generation only runs after you approve the script in the Studio.

## Requirements

- Linux (the tested system)
- Python 3.12 (3.13 also works; 3.14 does not yet)
- FFmpeg with `ffprobe`
- Chromium, installed by Playwright during setup
- Claude Code or Codex

## Quick start

```bash
git clone https://github.com/dutchbase/videofactory.git
cd videofactory
claude          # or: codex
```

Then type `/vf-setup` in the agent. It creates the Python environment, installs the packages and Chromium, runs a health check and renders a short test video. If you prefer to do it by hand, the commands are in [START-HERE.md](START-HERE.md).

When setup is done, type `/vf-new-video` and follow the questions. Not sure what to do next? Type `/vf`.

Want to see a result without any account or key? `python demo.py my-first-video` makes a free practice video with a silent voice track.

## The commands

Type these in Claude Code or Codex, inside the repo folder. Each command does one job and then stops.

| Command | What it does |
|---|---|
| `/vf` | Looks at your folders and runs the next step. Start here when in doubt. |
| `/vf-help` | Lists every command in plain words. |
| `/vf-setup` | Installs everything, checks your computer, renders a test video, and helps you add optional keys. |
| `/vf-new-brand` | Makes a brand: colours, fonts, logo, voice and sounds. |
| `/vf-new-style` | Designs a new look on top of the Modern kit. |
| `/vf-new-character` | Creates a character or mascot with the character factory. You approve each batch of AI images. |
| `/vf-new-video` | Starts a video: brand, wide (16:9) or tall (9:16), topic and a short brief. |
| `/vf-research` | Stage 00: collects facts from public web pages, with sources. |
| `/vf-script` | Stage 01: writes and revises the script with you. A tone check removes hype and filler. |
| `/vf-voice` | Stage 01: record your own voice for free, or generate it with ElevenLabs. |
| `/vf-transcript` | Stage 02: gives every word a time. |
| `/vf-cues` | Stage 03: writes the cue sheet, the moments the picture changes. |
| `/vf-scene` | Stage 04: builds the animation, takes stills at every cue and runs the checks. |
| `/vf-render` | Stage 05: mixes voice, music and effects, renders the MP4, the phone copy and the thumbnail. |
| `/vf-status` | Shows the progress of every video. |

Under the hood the commands call `python anim.py <command>`. Run `python anim.py -h` to see all of them.

## What goes into a scene

- **The Modern kit**: a clean, dark motion style with ready shot types (titles, cards, lists, stats, captions). The house brand `brands/videofactory/` shows every part of a brand in one place.
- **The library**: icons, graphics, Lottie animations and reusable blocks (`python anim.py lib find <word>`).
- **Motion components**: a pack of ready animated components in `brands/videofactory/library/motion/`.
- **Stock media**: video and photos from Pexels, Pixabay and Unsplash, and CC0 audio from Openverse (`python anim.py stock search`).
- **Captures**: screenshots and scripted browser recordings of real web pages (`grab`, `record`).
- **Sound**: CC0 effects and music in the brand folder, plus a built-in generator for effects and music beds (`python anim.py sounds`).
- **The Studio**: a local web app with a dashboard and review pages (`python anim.py studio`, then open http://127.0.0.1:8765).

Before you see a frame, the agent takes a still at every cue, and `python anim.py check` counts problems such as clipped text, overlap and missing sound. The agent fixes them until every counter reads zero.

## Optional parts

You can make a full video without any paid account: record your own voice, use the CC0 sounds or the built-in sound generator, and skip stock media.

| Part | What it unlocks | How to add it |
|---|---|---|
| Whisper | Word timing from any voice file | `.venv/bin/pip install -r requirements-transcription.txt` |
| ElevenLabs | A paid AI voice | `ELEVENLABS_API_KEY` in `.env` |
| Pexels, Pixabay, Unsplash | Stock video and photos (free keys) | `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `UNSPLASH_ACCESS_KEY` in `.env` |
| Earshot | The agent listens to effects, music and the final mix | `bash tools/setup_earshot.sh` (about 1.4 GB of models) |
| HyperFrames | An advanced HTML animation engine | Node.js, then `cd tools/hyperframes && npm ci --ignore-scripts` |
| Tesseract | A privacy scan of screenshots | Your system's `tesseract` package |
| Codex image generation | AI images for characters and styles | Codex CLI, logged in |

Copy `.env.example` to `.env` and paste your keys there. `.env` is never committed. Do not paste keys into the chat with the agent.

`python doctor.py` shows which parts are installed and how to add the missing ones.

### Tip: Brainstormform

The agent asks its questions in batches. If you install [Brainstormform](https://github.com/dutchbase/brainstormform), it shows those questions as a form in your browser, which is easier for long lists. It is optional; without it, the agent asks in the chat.

## Language

The agent talks to you in short, simple sentences (ASD-STE100 Simplified Technical English), in English or Dutch. The rule lives in [`_shared/talk.md`](_shared/talk.md). Videos can be made in English or Dutch.

## Folder map

| Folder | Holds |
|---|---|
| `AGENTS.md`, `CONTEXT.md` | The entry file for the agent and the pipeline definition |
| `_shared/` | Rules and guides used in every run (tone, voice, motion, sound, review) |
| `_runtime/` | The scene player, the Modern kit, fonts and the sound generator |
| `_templates/` | Starters that are copied for a new brand, style, character or video |
| `brands/` | Brands. `videofactory` is the house brand |
| `styles/`, `characters/`, `library/` | Looks, characters and the shared asset library |
| `stages/` | One contract per stage |
| `studio/` | The local web app |
| `videos/` | Your videos, one folder each |
| `.claude/skills/`, `.agents/skills/` | The `/vf` commands for Claude Code and Codex |

## Limits

Only Linux is tested. Paid and networked parts need your own accounts. See [LIMITATIONS.md](LIMITATIONS.md) for the full list.

## Licence

VideoFactory is released under the [MIT License](LICENSE). Fonts, icons, sounds and vendored libraries keep their own licences; see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) and `licenses/`.
