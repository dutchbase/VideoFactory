---
id: "beat-snap"
axis: "editing"
title: "Beat snap"
summary: "Hard cuts and snaps locked to the voice beat and the music pulse; every change lands on a beat."
aliases: ["beat cut", "rhythm edit", "on-beat cuts"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["listicle", "launch-announcement", "hook-one-idea", "short", "ad"]
formats: ["wide", "tall"]
pairs_with: ["tech-glow", "brutalist-bold", "kinetic-typography", "high-end-social", "synthwave"]
preview: "native"
build: "native"
---

## Look
The edit is a metronome. Nothing drifts. Each change is a one-frame hard cut or a short snap that lands exactly on a voice stress or a music beat, then the picture holds still until the next beat.

## Behaviour
- Grid: read the beat from the transcript stress words and, if music plays, from its BPM. Snap every cue to the nearest beat inside 2 frames (67 ms at 30 fps).
- Cut: a hard cut, one frame, no dissolve. Cut on A's fastest frame (K1 in `_shared/transitions.md`). B starts mid-move.
- Snap entrance: an element arrives in 160-240 ms with `P.ease.whip` and ends on the beat frame. Use `P.spring` snap (`{dur: 0.35, bounce: 0.1}`) for cards.
- Snap exit: 120-180 ms with `P.ease.accelExit`. The exit ends on the beat frame, not before.
- Accent beats: every 4th beat (the downbeat) gets a bigger change: a scene cut, a field inversion (bg to ink) or a scale cut (K8). Other beats move one element.
- Hold: the picture is still between beats. No ambient drift.
- Pacing: 0.5-1.0 s per beat. 60-110 changes per minute at 110-140 BPM. Rest for 1 s after 7 s of dense beats.
- Camera: locked. One scale punch of 1.06 in 120 ms on a downbeat is allowed.
- Sound: a tick or kick on every cut, a low hit on each downbeat. Music ducks 6 dB under the voice.

## Do
- Mark the beat grid once in the brief and cut every scene to it.
- Keep one element moving per beat.
- Vary the size of the change: small on beats, large on downbeats.

## Don't
- No cross-dissolves, no slow eases over 300 ms.
- No cut that lands between two beats.
- No bounce over 0.1 on any snap.

## Build notes
Modern kit: `P.past('beatN')` cues from the transcript; compute beat frames in `scene.js` as `round(t * 30)`. Snap tweens use `P.ease.whip` with `dur: 0.2`. See `_shared/transitions.md` K1 and K10.
