# Voice

How to write a script for the ear, get a voice, and check it.
Stage contract: `stages/01_voice/CONTEXT.md`. Wording rules: `tone.md`. Brief and script process: `script-production.md`.

## Write for the ear

A listener hears the script once and cannot go back. Write what you can say in one breath.

- Short sentences. One idea in each sentence. Keep most under 20 words.
- Plain spoken words. Read every line aloud. If you run out of breath, split the sentence.
- Write numbers as words, the way you say them: "three hundred dollars", "twenty percent", "two thousand and twenty-six". Digits and symbols make the voice guess.
- Spell out abbreviations the voice may get wrong. If a name sounds wrong, write it the way it sounds in the script, not in the picture text.
- A pause is a new paragraph. One paragraph is one beat, and later one cue (stage 03).
- Start with the hook. End with the one thing the viewer should do.
- Only spoken words go in the script block. No stage directions inside it.

`01_voice/script.md` holds the narration in its **first fenced block**. Everything outside that block (notes, scene cues) is not spoken. With no fenced block, the whole file is used and lines that start with `#` are dropped.

The model `eleven_v4` also reads audio tags in square brackets, such as `[whispers]`. Use them rarely. Other models read the brackets as text, so do not use tags there.

### Pace

Aim for 165 to 205 words per minute. `transcribe` prints the pace of each take. Below 165 it says the take is slow: rewrite it as talk, then redo it with `speak --chunk N`. Above 205 it says the take is fast: give it a landing beat, then redo it.

## Two ways to get a voice

Both ways give the same kind of video.

1. **Free: record it yourself.** Read `script.md` aloud in a quiet room. Save the file as `01_voice/voice.wav` (`.mp3`, `.m4a`, `.flac` and `.ogg` also work). Or pass it when you start: `anim.py new <slug> --brand <id> recording.wav`. Go on with `transcribe`.
2. **Paid: ElevenLabs.** `python anim.py speak <slug>` makes the voice from the script. It costs ElevenLabs credits for each character.

Keep one voice file in `01_voice/`. `speak` stops if a `voice.*` file that is not `.mp3` is already there.

### ElevenLabs settings

Settings sit in the frontmatter of `brands/<id>/voice.md`. Each video copies them when it is created, so a later change affects only new videos.

| Key | Meaning |
|---|---|
| `voice_id` | A voice from your ElevenLabs voice library |
| `model` | A text-to-speech model your plan has, such as `eleven_v4` |
| `stability` | `creative` (most expressive), `natural` (default) or `robust` (most steady) |
| `similarity_boost` | A number from 0 to 1, default 0.75. Only `eleven_v4` uses it |
| `format` | `mp3_<sample rate>_<bitrate>`, default `mp3_44100_128` |

Put your key in `.env` as `ELEVENLABS_API_KEY` (see `START-HERE.md`). A key starts with `sk_`. Never put it in a file you commit or in chat.

## The review gate

A paid voice needs a script you confirmed. Any edit to the script, and to the brief, changes its fingerprint (a short code for the exact text) and voids the confirmation.

1. `python anim.py speak <slug> --check`. Free. It tests the key, the model and the voice, and shows the characters left.
2. `python anim.py speak <slug> --dry-run`. Free. It runs the tone check, then lists every chunk (its length and first words), the model, the voice and the script fingerprint. It contacts nothing and writes nothing. Chunks under 250 characters may come out uneven: merge short paragraphs.
3. Read the chunks. The brief must be approved first. Then mark the script ready and approve it: `python anim.py review <slug> script --ready --expected <fingerprint>` prints the review link. Open it in Studio and press Approve (`dashboard-review.md`).
4. `python anim.py speak <slug> --confirm-script <fingerprint>`. This is the paid call. It stops if the fingerprint is not the approved one.

Use `--skip-tone` only when you accept a tone finding on purpose. A saved autonomous run uses its own review mode (`autonomous-runs.md`).

## Takes

`speak` cuts the script into chunks at paragraph breaks (about 250 to 700 characters each) and makes one take for each chunk. Short requests give better results.

- Files: `01_voice/takes/NN.mp3`, the exact text in `NN.txt`, and the request without the key in `NN.json`.
- A take is fresh only when all three files match the current request. A new model, voice, setting or text makes the take stale.
- A normal run makes only the stale or missing takes. A run with nothing stale makes no call and costs nothing.
- `--chunk N` makes chunk N again, even when it is fresh. Use it to redo one bad chunk. `--stability creative|natural|robust` changes the preset for that run.
- When every take is fresh, `speak` joins them into `01_voice/voice.mp3` with 0.3 seconds of silence after each take. If a take is stale or a call fails, the old `voice.mp3` stays unchanged.

## Listening check

Listen to the whole file with the script in your hand. Check:

- every word is right, with names and numbers;
- the pace fits the content;
- the tone is right, and no breath or glitch is cut off.

Redo a bad chunk with `speak --chunk N`. Then record your decision in Studio (the `voice` review) before you go on.

After a render, `python anim.py listen <slug>` lets the agent hear the finished video and writes `05_render/listen.md`. It is optional evidence, not approval (`sound.md`, Listen).

## Next: transcribe

`python anim.py transcribe <slug>` finds the time of every word (`stages/02_transcript/CONTEXT.md`). Whisper spells names better when they are in `_shared/vocab.txt`: add one word or name per line. Guided command: `/vf-transcript`.
