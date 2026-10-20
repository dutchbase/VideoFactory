# Native character pilot status

Updated 2026-10-10. The measurements use the synthetic `switch-gesture.sif` fixture. They show tool behaviour only. A synthetic fixture never approves a character, a rig or an action.

| Check | Result |
|---|---|
| Synfig version | Official Synfig Studio CLI 1.4.5 AppImage, extracted into a local tools folder to avoid FUSE. AppImage SHA-256: `2f2f073a171a9a7eec1f89e70ad3ac2ff96f10ea9dc561cb1a1855c194801715`. |
| Local tool capabilities | Synfig 1.4.5 PNG target, Rhubarb 1.14.0 and FFmpeg 9.0.1 are discovered and version-checked by the adapter. |
| Editable controls | Passed on CLI single-frame renders at 0f, 96f and 120f. The switch changes open eyes to closed eyes at 96f. The separate arm gesture moves at 120f. Imports are relative PNGs. |
| 1280 × 720, 240 frames at 24 fps | One full render completed in 137.678 s: 240 frames, 4 Synfig queue workers (5 process threads including main), peak RSS 111,915,008 bytes, sampled process VmSwap 0. Decoded alpha was nonopaque at frames 0, 120 and 239. |
| 60-second adoption target | Waived. A 137.678 s local 720p, 240-frame render is acceptable. The 4 GiB, no-swap, 30-second and 900-frame safety limits remain. |
| Clean serial repeat | Stopped by the adapter after Synfig reported 8,192 bytes of process VmSwap. It had written 151 of 240 frames. File mtimes show 140.659 s between frame 0 and frame 150. The host already had 22 GiB of system swap in use, with 7.5 GiB of RAM available. The adapter measures the child process, not host-wide swap. This run is a no-swap failure. |
| Synthetic 256 × 256 determinism | Passed. Two independent 240-frame, 24-fps Synfig renders produced matching PNG digests at all 240 positions. Frames 0, 96, 120 and 239 rendered alone matched the same frames of the sequence and had transparent alpha. The runs took 3.541 s and 3.862 s, peaked at 39.8 MB and 40.8 MB RSS, with process swap 0. This checks the synthetic switch and gesture mechanism only. |
| Blender 5.2.2 LTS fallback controls | The official portable archive SHA-256 `84098912789dc450e95697c4184fb8a90acbe5111c2ba4aede3fecb57806a168` matched Blender's published checksum. The editable, packed synthetic flat-plane fixture rendered four 256 × 256 control frames in 11.83 s. Frame 96 shows closed eyes, frame 120 moves the arm, frames 0 and 239 match pixel for pixel, and all are decoded RGBA with transparent pixels. |
| Blender 1280 × 720, 240-frame target | Failed. Cycles CPU with one sample and four renderer threads completed 2 of 240 frames in 60.13 s. The guarded adapter stopped at the 60 s target. Peak process RSS was 1,188,765,696 bytes and process VmSwap was 0. |
| 1920 × 1080 and a real 240-frame character render | Not run. The 720p synthetic render and the 256p determinism proof do not establish full-resolution performance or visual correctness for a real character. |
| Rhubarb 1.14.0 cue pilot | Passed technical validation on a 10 s English test clip (mono 22.05 kHz WAV) with PocketSphinx, `--dialogFile` and one worker. Rhubarb returned 61 ordered, nonoverlapping intervals that cover all of A–H and X. No new voice was generated. |
| Studio native action route | Implemented behind a current approved rig gate. Candidate registration, rig review, activation, native jobs, the source-aware cache, atomic output promotion and dashboard playback are wired. They wait for complete reviewed source. |

Rhubarb's `phonetic` recognizer is available for languages without a PocketSphinx model. Other languages than English were not tested.

Rhubarb's A–H cues cannot yet be claimed as working mouth animation. No native rig and no reviewed A–H/X head artwork is registered.

The adapter test suite passes 13 tests. They cover cue and correction intervals, exact half-open sampling, nonfinite times, relative project and input dependency hashes and confinement, blocking on a missing viseme, render caps, fresh-output preservation, worker limits, tool capability flags, and cancellation and timeout with partial logs. These checks establish adapter behaviour. They do not establish performance or creative readiness for a real character.

## Technical decision

Synfig 1.4.5 is the selected native renderer after the 60-second target was waived. The successful synthetic 720p, 240-frame pass took 137.678 s. A second pass stopped on process swap, so the no-swap guard stays essential. Blender is kept only as a technical fallback fixture. Tool performance never grants creative approval.

## Reproduction references

- Set `SYNFIG_BIN` (the extracted AppImage's `usr/bin/synfig`), `RHUBARB_BIN` and `BLENDER_BIN` to the pinned tools. The adapter reads them.
- `studio.native_character` detects the extracted Synfig AppImage tree and supplies its bundled library and module paths.
- Keep the official Blender archive and its `.sha256` file next to the tool, so you can verify it again. The synthetic `.blend` and its builder are in `studio/blender_pilot/`.
- [Synfig Studio 1.4.5 release](https://github.com/synfig/synfig/releases/tag/v1.4.5) and [official CLI syntax](https://wiki.synfig.org/Doc:Synfig_CLI_Syntax).
- [Rhubarb Lip Sync 1.14.0 release](https://github.com/DanielSWolf/rhubarb-lip-sync/releases/tag/v1.14.0). The English 10-second cue pilot used `--recognizer pocketSphinx --threads 1 --dialogFile <dialog.txt> --exportFormat json`.
- [Blender 5.2 LTS release](https://www.blender.org/releases/5-2/) and the [official command-line render manual](https://docs.blender.org/manual/en/5.2/advanced/command_line/render.html).

For a real character, complete `calibration/native/manifest.json` with hashed projects, linked art, audio, raw cues, corrections, dialog, settings and verified action and expression project bindings. Attach `rig-review.json` with both views, six distinct hashed review images per view (neutral, blink, mouth contact sheet, head movement, bent elbows, hands crossing the torso) and A–H/X mouth state metadata. Register the complete source as `native-candidate` with the exact source and variant hashes, then request your `rig:<variant>` decision. An approved candidate can be activated without discarding a previous validated clip. Render only its verified bindings through the native Studio job. You still review each action separately. A draft atlas, an agent report or a synthetic fixture cannot supply those decisions.
