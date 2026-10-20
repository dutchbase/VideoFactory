# Scope and limits

VideoFactory is an open-source (MIT) workspace for voice-first explainer videos. An AI agent (Claude Code or Codex) drives it on Linux. The offline checks cover the named synthetic exercise (`tests/fixtures/silent-first-scene/`) and the recorded test setup (`SMOKE-TEST.md`). They do not prove every OS or the creative quality of an unseen video. Only Linux is tested.

Paid or networked parts need your own accounts and are not covered by the offline checks: ElevenLabs voice, Whisper model downloads, stock providers, Codex or OpenAI image generation, and publishing. Importing your own recording needs no voice service. Nothing in this repo publishes or uploads a video.

Fonts are local, each with its licence. Python packages, FFmpeg, the browser and the optional speech model weights install separately and have their own terms. Offline use begins after they are installed. The code is MIT. Third-party parts keep their own licences (`THIRD-PARTY-NOTICES.md`, `licenses/`).

The repo ships no `.env`, no keys, no private projects, no voice samples, no browser state and no character records. You build your own brands, styles and characters.

The worked example is silent. App views you build with Modern classes are authored drawings, not proof of real app actions. Capture redaction is best-effort.

HyperFrames videos (optional engine): music and effects from `cues.md` are mixed at render, not in `anim.py preview`. A `<video>` must be a silent file in `04_scene/`. The Studio preview is static, so use `anim.py preview <slug>`. The `brand`, `runtime` and `voice` links in `04_scene/` need a checkout that supports symlinks. The tone gate reads only the body HTML text.

Research uses the agent's web tools and is not offline. Pages behind a login or paywall are not read. Page text is not archived in git (`pages/` is ignored).

The sound library (`library/audio/`) is not in the repo. `anim.py audio fetch` downloads about 3 GB of CC0 packs; Sonniss and SSE files download one at a time on first use. Four itch.io packs and Mixkit need a hand download. Sorting by file name is not perfect, and one long file often holds several takes: listen before you use a sound.

`anim.py record` plays scripted steps only: no live clicking, no sound, a red dot for the cursor, 90 seconds at most. Logged-in capture needs a session saved by `anim.py login`. Sessions expire. Masking personal data is best-effort.
