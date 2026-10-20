# VideoFactory: start here

VideoFactory makes explainer videos from a script and a voice. An AI agent (Claude Code or Codex) runs the commands. You give the topic, check each stage and approve it.
This file is the one home for setup. The agent command `/vf-setup` follows it.

## What you need

- Linux. This is the tested system.
- Python 3.12 or 3.13. Use 3.12. The pinned numpy has no wheel for 3.14.
- FFmpeg, with `ffprobe`.
- Chromium. Playwright installs it in the setup below.
- Claude Code or Codex, started in this folder.

## Setup

```
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python doctor.py
```

With `uv`: `uv venv -p 3.12 .venv`, then `uv pip install -p .venv/bin/python -r requirements.txt`.

## Test the setup

```
.venv/bin/python anim.py status
.venv/bin/python anim.py stills silent-first-scene
.venv/bin/python anim.py render silent-first-scene --workers 1
```

The result is an eight-second silent MP4 in `tests/fixtures/silent-first-scene/05_render/`. If it plays, the setup works.

## Optional parts

| Part | You need it for | How |
|---|---|---|
| Whisper | `transcribe`: the time of every word | `.venv/bin/pip install -r requirements-transcription.txt`. The first run downloads model weights. A CPU works but is slow. |
| ElevenLabs | `speak`: a paid AI voice. You can record your own voice for free. | A key in `.env` |
| Stock keys | `stock`: stock photos and video | Keys in `.env` |
| Earshot | `listen`: the agent hears effects, music and renders | `bash tools/setup_earshot.sh` (about 1.4 GB of models) |
| HyperFrames | The advanced engine (`_shared/hyperframes.md`) | Node.js, then `cd tools/hyperframes && npm ci --ignore-scripts` |
| Tesseract | The privacy scan of captures (`_shared/capture.md`) | Install the `tesseract` package of your system |

### Keys

Copy the example file, then add the keys you want. `.env` is not committed to git.

```
cp .env.example .env
```

| Name in `.env` | Used for | Where to get it |
|---|---|---|
| `ELEVENLABS_API_KEY` | `speak` (a key starts with `sk_`) | elevenlabs.io, Developers, API Keys |
| `PEXELS_API_KEY` | stock photos and video | pexels.com/api |
| `PIXABAY_API_KEY` | stock photos and video | pixabay.com/api/docs |
| `UNSPLASH_ACCESS_KEY` | stock photos | unsplash.com/developers |

`speak` also reads `ELEVEN_API_KEY`. Paid AI images use `OPENAI_API_KEY` only on the explicit API route (`_shared/image-generation.md`).
Paste keys into `.env` yourself. Never put a key in chat.

## Make your first video

1. Choose a brand. `brands/videofactory/` is the house brand. For your own brand run `/vf-new-brand` (steps: `brands/CONTEXT.md`).
2. Start the video: `.venv/bin/python anim.py new <slug> --brand videofactory`. Add `--format tall` for 9:16. Add `recording.wav` to use your own voice.
3. Fill `videos/<brand>/<slug>/01_voice/brief.md` (`_shared/audience.md`).
4. Work through the stages. The files appear in `videos/<brand>/<slug>/`:

| Stage | Folder | Result |
|---|---|---|
| 00 Research (optional) | `00_research` | Facts with sources (`.venv/bin/python anim.py research <slug>`) |
| 01 Voice | `01_voice` | Brief, script, voice file (`_shared/voice.md`) |
| 02 Transcript | `02_transcript` | The time of every word |
| 03 Cues | `03_cues` | The moments when things appear |
| 04 Scene | `04_scene` | The pictures (`_shared/modern.md`) |
| 05 Render | `05_render` | The MP4 |

The workflow is in `CONTEXT.md`. Progress: `.venv/bin/python anim.py status`.

## Agent commands

Start with `/vf`. It finds the next step. Others: `/vf-setup`, `/vf-new-brand`, `/vf-new-style`, `/vf-new-character`, `/vf-new-video`, `/vf-research`, `/vf-script`, `/vf-voice`, `/vf-transcript`, `/vf-cues`, `/vf-scene`, `/vf-render`, `/vf-status`, `/vf-help`.

## Studio

`.venv/bin/python anim.py studio` starts the local page at http://127.0.0.1:8765. Stop it with Ctrl+C. It shows reviews, videos, the material library, styles and characters.

When the agent finishes a stage, it marks it ready and prints a review link, for example `http://127.0.0.1:8765/videos/videofactory/my-video/review/scene`. Open the link and decide. A saved file and a ready state are not approval (`_shared/dashboard-review.md`).

Styles and characters start as guided workshops in Studio (`styles/CONTEXT.md`, `characters/CONTEXT.md`). Paid AI image batches need their own approval first.

## Saved runs

`.venv/bin/python anim.py run <brand>/<slug>` runs a video with saved settings. Resume with `--resume <run-id>`. Review modes, cost limits and recovery: `_shared/autonomous-runs.md`. A video export is not a publication approval.
