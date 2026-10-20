# Sound

Effects, music bed and loudness for every video. The voice always leads. Stock music: `library.md` (Music). Timing words: `motion.md`.

## Where sounds come from
- Brand files win. A brand keeps its own sounds in `brands/<id>/sound/`: one file per effect name (`sfx/<name>.ogg`) and one per song (`music/study.ogg`, `music/tinker.ogg`). If the file exists, it plays.
- No brand file for a name: the built-in generator `_runtime/synth.py` plays. It makes soft tones, bells and filtered noise, and calm lo-fi beds. It is the free fallback, and also an option: delete or rename a brand file to hear the generated sound instead.
- Preview everything: `python anim.py sounds` writes every effect and song to `_shared/sound/`.
- The `videofactory` brand ships free CC0 sounds. Each file is listed in `brands/videofactory/sound/SOURCES.md`.
- The sound library holds thousands of effects (whooshes, risers, impacts, UI, ambience) and music tracks: read `library/audio/INDEX.md`, search with `anim.py audio find "<words>"`, bring one in with `anim.py use <slug> audio:<id> [--start s --end s]`. `use` writes the licence line in `04_scene/assets/sound.md`. Contract: `library/audio/CONTEXT.md`.
- Licence rule: a brand sound file is CC0 or your own work, nothing else. Write every file in the brand's `sound/SOURCES.md` (file, original name, pack, author, URL, licence). Start from `_templates/brand/sound/SOURCES.md`.

## Write it in cues.md
- An effect on a cue: `## intro.card "a phrase" [sfx: pop]` (several: `[sfx: pop, tick]`). It plays at the cue start. Only the heading line counts: `cues` stops on a tag in a description line.
- Gain per effect: `[sfx: pop 0.5]` (default 1, on top of the `sfx:` level below).
- A sound file as an effect: `[sfx: file:door-close.wav]`, like `music: file:`. Gain works too: `[sfx: file:door.wav 0.6, pop 0.5]`. Formats: wav, mp3, ogg, flac, m4a, aif. The file lives in `04_scene/assets/` (subfolders allowed: `file:sfx/door.wav`), or in the shared `library/sfx/` (create it when needed; the video's own `assets/` wins). The mixer decodes it to 44.1 kHz mono, peak-normalises it to 0.5 (about the level of the built-in effects), applies the `sfx:` level and then the same speech limiter, ducking and mastering as every effect. It starts on its cue.
- An unknown effect name, a malformed token or a missing file is an error: `cues` warns, `check` counts `sound effect unknown`, render stops. Nothing is skipped silently.
- Effects inside speech are pushed at least 12 dB under the voice: a tick on a spoken word is inaudible. Put small effects in pauses or leave them out.
- A music bed: one line before the first cue, `music: study 0.2` (a song: `study` is calm, for explaining, about 84 bpm; `tinker` is playful, about 116 bpm) or `music: file:<name>.mp3 0.2` (a stock track).
- Effect level for the whole video: `sfx: 0.4` before the first cue (default 0.25).
- Run `anim.py cues <slug>` after a change.

## Effects
| Name | Use it for |
|---|---|
| `pop` | a card or icon arrives |
| `tick`, `step` | small steps in a list, a cursor move |
| `click` | a button press in an app view |
| `key` | one key press while text types (one per word, not per letter) |
| `blip`, `select` | a choice is made, a tab changes |
| `whoosh` | a fast move or a scene change |
| `stamp` | something is confirmed: approved, certified |
| `chime`, `coin`, `powerup` | a win: a result, a payment, a level up |
| `error` | a mistake on screen |
| `riser` | the build before the thesis or the call to action. It ends on its cue |
| `impact` | the turn: the one moment the story changes |

## Rules
- Every video has a music bed (`music: study 0.2`, or `music: file:<name> <gain>` with stock from `library.md`). Missing music is a warning in `check` and at render; leave it out only when the user asks.
- Effects sparingly: only where they mark an action on screen (a click, a stamp, a cut). No effect is better than a decorative one.
- At most one `riser` and one `impact` in a video.
- Continuous motion stays silent. Sound marks events, not movement.
- A hit may lead its picture by 2–3 frames (about 0.1 s). Never let it trail.
- Put the payoff hit in the pause before the line that names it. Under speech the ducking swallows it.
- Leave about 0.3 s of near-silence before the biggest hit.
- Cue gain (`sfx:`, default 0.25) is only an input level; it cannot guarantee balance against a soft voice. The music bed ducks under the voice automatically.
- During speech, the sum of all effects must stay at least **12 dB below the voice for both RMS and peaks**. The mixer measures 44.1 kHz PCM in 20 ms windows, using 13 dB internally. Stereo analysis protects the quietest voice channel against the loudest effect channel without changing the voice.
- Speech uses corrected word times from `cues.json`, matching `02_transcript/words.json`, padded 50 ms before and 150 ms after each word; overlapping intervals merge. Missing or stale timings with effects stop export.
- Effects receive their cue gain first, then a continuous attenuation curve on the full timeline before fragment trimming. Silent voice inside speech mutes effects; gain returns within 250 ms after speech and never exceeds the original effect level. Music ducking and master goals stay unchanged.
- Every export writes `05_render/check-audio.md`: stems, period, minimum measured RMS/peak distance and violations. Measurement checks the written effect WAV; violations stop export before replacing the MP4. Analysis windows remain anchored to the full timeline for consistent fragment balance. Studio requires a passing report tied by hashes to the current export and sources. Without effects the report explicitly says not applicable.
- Manual mixes must use `anim.prepare_effects` with separate voice and summed effects, retain its report, and pass it to `after_render` (or `write_audio_check` after mastering). A premixed track without separate stems cannot receive a successful balance check. HyperFrames videos get the same mixer: `anim.py render` draws the frames, then mixes voice, music bed and effects (`mix_soundtrack`).
- Listen on headphones and a phone speaker for clarity, clicks and pumping. Track measurements do not capture frequency masking or perceived balance; the automatic report leaves listening approval pending.

## Sound-design pass
Required for every video, short and long. Done before the scene gate.
- Music bed under the whole video, ducked under the voice (automatic). CC0 or an allowlisted licence without attribution (`library.md`; every sound in `library/audio/` qualifies); never a track you cannot trace.
- Effects on cuts, snaps and reveals, and on the hook. The rules above still hold: one riser and one impact at most, nothing on continuous motion, 12 dB under the voice.
- `04_scene/assets/sound.md` records the plan and the rights: music (file, source URL, author, licence, gain), each effect by cue id (name, purpose), and the licence of every sound. Built-in effects (`[sfx: name]`) are synthesized by `_runtime/synth.py` in this project: licence "own, built-in". If the brand has a sound file for that name, write "brand sound, see `brands/<id>/sound/SOURCES.md`". A file effect (`[sfx: file:<name>]`) is CC0 or allowlisted (`library.md`) and needs one line in `sound.md` with the file name, its source URL and its licence, for example `- door-close.wav: https://freesound.org/s/123 (CC0 1.0), cue intro.card`. Without that line `check` counts `sound effect unlicensed`, for every brand.
- `anim.py check` counts `sound design missing` (no `music:` line, no `[sfx:]` (built-in or file), no `sound.md` or no licence in it). Only on the user's request: `"allow": ["minimal"]` in `project.json`, noted in `REVIEW.md`.

## Listen
Optional: `bash tools/setup_earshot.sh` installs earshot (CPU, about 1.4 GB of models) and `claude mcp add` registers it, so the assistant can hear. Don't claim a sound fits without a reading; quote the number ("strong match, z +3.9; -14.2 LUFS").
- Pick an effect or track: `rank "a short pop" candidates/*.wav`, `find` for a trim (reject "head cut" / "tail cut"), `describe` to confirm.
- After render: `.venv/bin/python anim.py listen <slug>` writes `05_render/listen.md` (second-by-second transcript, loudness, sync against the cues). Not a counter; it never blocks render.
- Times and levels are reliable; event labels are not (about half right when exposed, a quarter under music). It cannot judge taste, music quality, speech content or licences, and it misses soft build-ups (risers, whooshes). Treat it as evidence; the user's headphone and phone listen decides.
- Never run `earshot llm`: it uploads audio to Google.

## Loudness
- `anim.py render` masters the mix to −14 LUFS with a true peak of −1 dBTP or lower (the level YouTube and social apps play at).
- `--lufs -16` changes the target. `--no-master` skips it.
- Read the result in `05_render/check-video.md`. A video with a silent test voice is not mastered.
