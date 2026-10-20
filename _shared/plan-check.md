# Plan check and slop signs

Most weak animation comes from one root: nobody decided what this one video is for, so every choice falls back to a default. No move below is banned. Each one is fine when you chose it for a reason you can say in one sentence about this video. Part A runs on the brief, before `04_scene`. Part B runs on the stills and the render, by the judge (`.claude/agents/frame-critic.md`). Motion rules: `motion.md`. Counters: `review.md`.

## A. Plan check (on the brief)

Write the answers in the brief's "Plan check" field: one sentence for each reach you took on purpose, and the one thing the video is about.

| # | The default reach | Ask yourself |
|---|---|---|
| 1 | A page, not a picture: headline left, sub-line under it, an image on the right, the words change while the frame stays. | Would this frame work as a slide or a website hero? Then it is a page. |
| 2 | Showing everything: every point in the brief gets an equal beat. | What is the one thing? What did I leave out on purpose? |
| 3 | States, not events: things fade in and hold; the plan lists end states. | Does each scene say what happens, what moves and what it causes? |
| 4 | Premium pastiche: near-black ground, soft glow, a gold spark, one italic serif word. | Is the ground dark because the brand is dark, or because dark looks expensive? |
| 5 | Production metadata as decoration: `01 / 04`, timecodes, version stamps, HUD corners. | Does the viewer need this text? (`check`: invented labels) |
| 6 | Invented proof: unsourced numbers, grey skeleton UI, a redrawn logo, emoji as icons. | Is anything made up to look real? Did I use the captures and the library first? (judge: accuracy) |
| 7 | The first association of the name or topic: "launch" gets a rocket, "security" a shield. | What was my first idea, and did I look past it? |
| 8 | Effects instead of quality: a new technique in every scene. | Does the idea need this effect, or does it show effort? |
| 9 | A script with illustrations: one picture under each sentence, each noun drawn. | Does the picture have its own job, or does it repeat the words? |
| 10 | Sound as wallpaper: one loop at one level, or silence by default. | Where is the first big hit or silence, and which visible event is it on? (`sound.md`) |
| 11 | The ending as a web footer: logo, tagline, button and URL held as furniture. | Does the end card arrive by a cause on screen, as the last beat of the story? Its length is a brand setting. |
| 12 | Minimalism as a hiding place: a small object on an empty ground, long holds. | Is the emptiness a breath before a payoff, or an unbuilt scene? Which frame would someone screenshot? |

The overcorrection is a default too. Told "no slides, be bold", an agent reaches for a giant word cropped by the frame edge, a colour flood between every beat, a dot that becomes the logo, and motion that never stops. Use one of these only when it is the idea for this video.

Last questions:
- Cover the logo and swap the colours. Is this the video I would make for a competitor?
- Cover all text. Does every scene still show a picture?
- Which choices did I decide, and which did I reach for? (scene shape, ground, type, cuts, ending, sound)

## B. Slop signs (on the render)

Ranked: the most disliked first. The judge reports every sign it sees by id, with the sheet file and time. A brand file wins over a sign: when `brands/<id>/brand.md` asks for a style (for example corner brackets or tracked caps), it is not slop for that brand.

| Id | Sign | What a pro does instead |
|---|---|---|
| S1 | Corner chrome: small tracked caps, a name, a counter or a timecode in a corner or edge band | Nothing in the corners; the picture names itself |
| S2 | Chapter counter: `02 / 05`, `01 — THE WAIT`, `FILM 01`, a progress hairline (`check`: invented labels) | A chapter change is a change of ground or a carried object, not a number |
| S3 | Deck layout: left headline with a sub-line or a small kicker above it, media on the right | One centred line, or a phrase split across the frame |
| S4 | A flat swatch ground per scene, more than three different grounds in one video | One built world; the ground changes by act, for a reason |
| S5 | A generic UI card as proof: white rounded card, three toolbar dots, invented strings | A real capture or a faithful rebuild of the real screen |
| S6 | Feature tour: card plus caption, many times, equal beats, caption at the same place | One proof per frame; beats of unequal length |
| S7 | Stat wall: a big centred number with a small label on a flat ground | The number lands inside a physical event, with its source |
| S8 | A pinned element: the same pill or caption at the same place through three or more shots | A carrier that moves, scales or changes role each shot |
| S9 | Technique showreel: adjacent scenes share no colour, object or layout | One idea, one motif, only the effects it needs |
| S10 | Ghost decoration: giant words at 3–9 % opacity, hairline grids, grain as depth | No decoration that does no job |
| S11 | A serif-italic accent word inside a sans line | One family; size carries the emphasis |
| S12 | A tracked-caps tagline or label chip that names the scene | The picture shows it; no caption |
| S13 | A giant single word as a slide, on a flat ground, with no object | Spend scale once and give the word a surface or a cause |
| S14 | 3D tilt or orbit rings around a flat card as "depth" | A held device, a 2D camera move, or real 3D when the idea is physical |
| S15 | Invented proof: names, numbers, UI labels or quotes not in the brief or the captures | Captured copy and sourced numbers only |

Gates and counters are a floor, not a verdict: a clean `check.md` on a weak video is still a weak video.

Source: re-expressed from tejashmakwana/motionmaxxing `references/slop.md` (Apache-2.0); no text copied.
