# Frame critic: what-is-videofactory

Round-4 scores (replaced): hook 8, readability 8, motion 8, variety 8, composition 7, accuracy 8, sound sync 7, showcase 8 (needs-attention).

- Reviewer: frame-critic agent (not the builder)
- Date: 2026-10-21
- Round: 5 (final; fixes for the round-4 problems, rendered again)
- Brand: videofactory (frozen `settings.json` sources: `brand.md`, `tokens.js`, `voice.md`; no hook limit, no stricter variety limit)
- Media judged: `05_render/what-is-videofactory.mp4` (215.36 s). Export sha256 as written in `check-audio.md`: 0fd2fd25ebbba2b54041d5cbc3ba9350f1ad7414c00ab7434150266922eec4a9 (not recomputed: this agent has no shell; it differs from round 4, so the render is new). Stills `sheets/sheet_00..06.png`; phone frames `phone/sheet_01..09.png` and single frames `phone/054, 076, 077, 078, 147, 149, 151, 153, 170, 205, 207, 208`.
- Counters: `check.md` all 0 (1293 frames); `check-video.md` 0 flashes, 0 flat frames, 0 dead stretches, -14.5 LUFS, -1.2 dBTP; `check-audio.md` passed (0 violations, smallest gap 4.0 dB).
- Listening: NOT done. This agent cannot play audio. Sound sync is judged from `listen.md` (Earshot), `check-audio.md`, `cues.md`, `words.json`, `scene.js` and `_shared/sound.md` only. A person must still listen (see Verdict).
- Phone frame note: `fps=1` frames can come from up to about 0.5 s after their label.

## The five round-4 fixes

| # | Fix | Result | Evidence |
|---|---|---|---|
| 1 | `reveal`: riser and impact at `@2.95` (206.77 s) | Confirmed on paper and by the Earshot cut row. Not heard. | `scene.js` line 340: `circleReveal` at `cta-0.45` = 206.77, dur 0.36. Voice pause is 206.48-207.22 (`words.json`: "commands." ends 206.48, "VideoFactory" starts 207.22). Earshot 3:27.00 CUT: "level peak -10 ms, rising 9 dB" (the slow-attack peak sits on the cut). The Earshot CUE row at 3:26.77 still says NO HIT (no onset in 250 ms): a detector limit for a slow attack (`sound.md`: it misses soft build-ups), so it needs a human ear. |
| 2 | `brand.new` handwriting smaller (50 px) and inside the edge | Confirmed. | `phone/077.png`: "your colours, your look" ends at x 325 of 360 (about 187 px from the edge at 1920); the swatch row ends at x 346 (about 75 px). Both above the 60 px rule. Still readable at 360 px. |
| 3 | Pops moved off word starts onto visible events | Mostly confirmed. One not fixed. | Earshot hits: `setup.doctor` ticks 30.87 / 31.29 / 31.71 at -11 / +4 / +2 ms; `voice.approve` whoosh 121.29 (+43 ms); `render.extras` 177.55 (-38 ms); `render.earshot` 181.84 (+46 ms); `brand.approve` 2 stamps 85.96 / 86.62 both register. `cta.clone` 210.37 shows only an onset 90 ms early ("near"). NOT fixed: `brand` `pop@0.9` (70.22) is 0.04 s after "starts" (70.18): Earshot 1:10.22 NO HIT (strong sound at +152 ms, the voice). |
| 4 | Whooshes earlier | `hook.weekend`: confirmed. `video.brief` (research cut): plausible, not proven. | Earshot 0:05.42 WHOOSH "cut -13 ms OK" (was +157 ms late). Research cut 98.80: whoosh starts 98.58, Earshot sees its onset 190 ms before the cut and no new onset at the cut (the peak is a soft swell, so it cannot be measured). It no longer trails. Needs a listen. |
| 5 | Larger parts | Two confirmed, one partial, one not. | Cube on `optional.node`: about 110 x 75 px at 360 px, "MODERN KIT" and "HYPERFRAMES" read (`phone/054.png`): confirmed. Recording on `scene.capture`: search box, "Advanced search" and the result list read at 360 px (`phone/147.png`, `149.png`, `sheets/sheet_04` 2:27): confirmed, the page is still mostly white. AGENT FLOW clip: now shows three boxes (`phone/153.png`) but is still small and dim at 360 px (`phone/151.png`): partial. Success Lottie on `check.done`: the box is 230 px (`index.html` line 111) but the visible green circle is still about 72 px at 1920, 14 px at 360 px (`phone/170.png`, `sheets/sheet_05` 2:49.9), the same as round 4: not fixed. |

## Scores

| Score | Value | One line of evidence |
|---|---|---|
| hook | 8 | 0:00 big line "An explainer video usually means" with the Editor chip already rising (phone/001), three chips with colour pictograms at 0:02, struck through with "a lost weekend" in orange at 0:05 (sheets/sheet_00 hook, hook.tools, hook.weekend). Pain lands in 5 s. |
| readability at 360 px | 8 | Every message line reads, including the smaller handwriting (phone/077), the cube labels (phone/054) and the Wikipedia recording (phone/147). Not readable and not needed: AGENT FLOW clip text (phone/153), Studio screenshot text (3:05-3:12), the 14 px success dot (phone/170). |
| motion | 8 | Chips lift then strike 0:03-0:05, cards light on the spoken word 0:38-0:58, terminals type, stamps land 1:25-1:27 (now with 2 hits for 4 stamps), words light up 2:06-2:09, wall builds 2:19-2:22, seven different transitions, no particle bursts, no drift. Flaw: the reveal decode (3:24, phone/205) is still scrambled for about 1 s while the voice says "This video was made with"; it reads from 3:25 (phone/206). |
| variety | 8 | New object every 2-4 s: grid 0:36, command list 1:06, swatches 1:12, Wikipedia grab 1:39, Studio grabs 2:01, wall 2:19, stock 2:24, recording 2:27, clips 2:31, waves 2:33, counters 2:45, gauge 2:54, donut 3:24, end card 3:27. The 1:17-2:04 stretch still repeats one template (orange command plus one card). |
| composition | 8 | Handwriting and swatches are now inside the safe margin (phone/077; sheets/sheet_02 brand.fonts 1:16). One focus per frame, captions at about 91 % of height. Remaining mild flaw: the zoomed Studio start frame 3:05-3:07 has the caption pill on the dropdown and a cropped sidebar "ory / udio" (sheets/sheet_05 studio). |
| accuracy | 8 | Donut 37 / 22 / 18 / 8 / 8 = 93 (phone/207, phone/sheet_09) equals `library.md` and `TALLY` in `scene.js`; the gauge says 3 dB, as `check-audio.md` (required 3 dB, smallest 4.0 dB); "5 stages done" and chapter times match the cues; the recording and Studio shots are real. Mild, unchanged: "Installing the rest 13-100 %", counters 5 / 6 / 1 with "-100%", an unlabelled "54" at 3:02 (phone/sheet_08). No provenance label is required. |
| sound sync | 8 | Files and Earshot only, not heard. Earshot (`listen.md`): of 128 cues, 96 % have an onset within 100 ms (was 91 %), 74 % within 40 ms (was 71 %), median 20 ms; no-hit effect times fell from 9 to 3 (70.22, 75.26, 206.77); `hook.weekend` whoosh lands on the cut (-13 ms); `check-audio.md` passed. Open: `brand` pop 70.22 and `brand.fonts` pop 75.26 sit on word starts and are inaudible; the impact is a slow swell that only the cut row supports; 129 effects far exceeds "effects sparingly" (`sound.md`) and nobody has heard if it is too much. |
| SHOWCASE | 8 | Breadth is visible and each part sits on its line: 7 transitions (expand-morph 0:06, whip-pan 0:28, zoom-through 0:35 / 1:00 / 2:24, blinds 1:08, grid-pixelate 2:39, device-pullback 3:05, circle-reveal 3:27), pictograms, Lottie chat, check mark, clock, confetti, stock video and photos, real Wikipedia grab and recording (now readable), motion-pack clips, the 3D cube (now readable), and the donut tally that closes the claim. The voice names each part as it appears, so it is not a parts dump. Weak parts left: the success Lottie (14 px at 360 px) and the dim AGENT FLOW clip. |

All eight scores are 8 or more on the evidence available. The open item is a human listen.

## Slop signs seen (plan-check part B)

- S6 / S8 / S3 (mild, brief-mandated grid): 0:36-0:59, `sheets/sheet_01.png` optional.whisper to optional.browser. The 8-card grid stays pinned left for 8 shots with a headline block on the right; only the right column changes.
- S6 (mild): 1:10-2:04, `sheets/sheet_02.png` and `sheet_03.png` (brand.style to voice.stamp). Same top headline plus one card, equal beats.
- S15 (mild): "Installing the rest 13-100 %" at 0:31-0:34 (`sheets/sheet_01.png` setup.doctor); "Reading brands ... ok" at 1:03 (`sheets/sheet_02.png` vf.reads); counters 5 / 6 / 1 and "-100%" at 2:48 (`sheets/sheet_05.png` check.zero); unlabelled "54" at 3:02 (phone/sheet_08).
- Not slop here (brand wins or real): mono uppercase chips and labels (FREE, PAID, MIT, AGENT FLOW, CARD STACK, TICKER) follow `brand.md`. The 3D cube (0:53) is real 3D from HyperFrames with a reason (the engine), not S14. The end card (3:27) arrives by the circle reveal out of the tally and keeps moving (typing, URL, confetti), so it is not S11.
- S1, S2, S4, S5, S7, S9, S10, S11, S12, S13, S14: none. No new sign came from the five fixes.

## Three worst problems now

1. Success Lottie is still a dot (SHOWCASE, readability). File `04_scene/index.html` line 111 (`#lot-ok`), cue `check.done` (169.24-170.40). The 230 px box did not enlarge the artwork: the visible circle is about 72 px at 1920 and 14 px at 360 px (phone/170.png). Fix: scale the artwork inside the box (for example `#lot-ok svg { transform: scale(2.8) }`, or a 420 px box with matching negative margins) so the check reads at about 200 px beside "zero", and keep 60 px from the right edge. Rules: `plan-check.md` A9 (each part needs its own job), `review.md` section 3 (phone test).
2. Two pops are inaudible (sound sync). File `03_cues/cues.md`, cues `brand` (`pop@0.9 0.8`, 70.22, "starts" begins 70.18) and `brand.fonts` (`pop@0.04 0.7`, 75.26, "fonts," begins 75.22). Earshot: NO HIT on both. Fix: delete both pops (the logo and the font card already have the voice and the motion); or, if you keep one, put it in the 0.26 s gap 74.96-75.22 by hand and check with `anim.py listen`. Also re-check `cta.clone` `pop@0.45` (210.37, on "the" at 210.40; Earshot only "near"). Rules: `sound.md` ("Effects sparingly", "Under speech the ducking swallows it").
3. The payoff line is scrambled while it is spoken (motion). File `04_scene/scene.js` lines 330-331, cue `reveal` (203.82). `FX.matrixDecode` on `#rl1` takes 1.0 s and on `#rl2` starts at +0.5 s for 1.0 s, so "This video was made with" is unreadable until about 204.8 s and "those same commands." until about 205.3 s, while the voice says them (phone/205.png). Fix: use `dur: 0.5` for `#rl1` and start `#rl2` at `reveal+0.3` with `dur: 0.5`, so both lines read when voiced. Rules: `motion.md` (doctrine: "Text that must be read starts 0.02-0.06 s before its word"; "Do not ask the viewer to read text that moves fast").

Also noted, no score effect: (a) a person must listen to 98.4-99.0 s (research whoosh) and 203-208 s (riser, impact, end card), and to the whole video on a phone speaker. (b) The riser ends exactly where the impact starts, so there is no 0.3 s of near-silence before the biggest hit (`sound.md`); the voice gap before it is only about 0.14 s after padding. Judge it by ear. (c) The Studio start frame (3:05-3:07) puts the caption pill on a dropdown; lift the pill or start the pull-back less zoomed. (d) Earshot reads -11.5 LUFS for the file that ffmpeg reads as -14.5 LUFS in `check-video.md` (mono counted as stereo, as in round 4); -14.5 is the master result.

## Message from the frames alone

With one chat with an AI agent (Claude Code or Codex) and a short list of /vf commands, one step each and nothing paid or published without your clear yes, VideoFactory turns a brief into a finished, branded MP4 on Linux with Python and FFmpeg. Its library of effects, transitions, icons, Lottie, stock, captures, motion-pack clips and sound is shown on the way, and this video was made with 93 of those parts and those same commands. It is free and open source (MIT): clone the repo and run /vf-setup. This matches the brief's outcome.

## Verdict

Pass on scores: all eight are 8 or more (hook 8, readability 8, motion 8, variety 8, composition 8, accuracy 8, sound sync 8, showcase 8), judged from files and Earshot. Not approved for publication: nobody has listened (this agent cannot play audio), so the sound sync score is measured evidence, not an ear check. Before approval a person listens to 203-208 s, to the research cut at 98.4-99.0 s, and to a phone speaker pass. Problems 1 to 3 are polish and do not block.

## Round 6 (confirmation: clip frames stored differently in git, scene unchanged)

- Reviewer: frame-critic agent (not the builder). Date: 2026-10-21. No shell and no audio playback: nothing recomputed, nothing heard.
- Media: `05_render/what-is-videofactory.mp4`. Export sha256 as written in `check-audio.md`: e3bd9dc1f880ad24d309d7105688fc8d18313b161947dbcb13fb87da0dd626d2 (not recomputed). It differs from round 5 (0fd2fd25...), so this is a new render, as the builder says.
- Counters read: `check-video.md` 0 flashes, 0 flat frames, 0 dead stretches, h264 / aac ok, -14.5 LUFS, -1.2 dBTP. `check-audio.md` passed, 0 violations, smallest gap 4.0 dB, 980 windows, same effect list as round 5 (riser and impact 206.77; pops 70.22, 75.26, 210.37 still there). Its "Listening review" line still says pending.
- Looked at: `phone/sheet_01..09.png` (215 frames, 1 per second). Spot-check only.
- Matches round 5: hook 0:00-0:05 chips struck for "a lost weekend" (sheet_01); handwriting inside the margin at 1:15-1:16 (sheet_04); cube "MODERN KIT / HYPERFRAMES" at 0:52-0:53 (sheet_03); Wikipedia recording readable at 2:26-2:29 (sheet_07); AGENT FLOW clip still small and dim at 2:31 (sheet_07); success dot still tiny at 2:49 (sheet_08); donut 92 then 93, with 37 / 22 / 18 / 8 / 8, at 3:25-3:26 (sheet_09); end card with typing, URL and confetti from 3:27 (sheet_09).
- Round-5 flaws still visible, none new: payoff line scrambled at 3:24 (sheet_09, "madDw4M / th+CV3L"); unlabelled "54" at about 3:03 (sheet_08); Studio start frame with caption on the dropdown at 3:05 (sheet_08).
- Builder claims (SSIM lowest frame 0.99897; audio -130.1 dB difference, largest sample 6e-05, same sample count): not checked by me. They agree with what I see: no frame differs from round 5 on the sheets, and the effect list in `check-audio.md` is unchanged. I did not view the round-5 MP4 again, only its written description.
- Scores of round 5 hold: hook 8, readability 8, motion 8, variety 8, composition 8, accuracy 8, sound sync 8, showcase 8. Sound sync still rests on round-5 Earshot evidence (`listen.md` not re-read, Earshot not re-run) plus the claimed near-zero audio difference.
- Slop signs, three worst problems and the message: unchanged from round 5. The message still matches the brief's outcome.
- Verdict: pass on scores, no change from round 5. Not approved for publication: a person must still listen (203-208 s, 98.4-99.0 s, phone speaker).
