# library/audio: sound effects and music
A large local library of effects and background music for every video. The audio stays on this computer: it is
never committed (the Sonniss and Mixkit licences forbid sharing the files). Only this file and `sources.json` are in git.

**Reads:** `sources.json` (every source: method, URL, licence, author, page, default category).
**Does:** `python anim.py audio ...` downloads, sorts and indexes. `python anim.py use <slug> audio:<id>` copies one sound into a video.
**Writes:** `sfx/`, `music/`, `INDEX.md`, `index/*.tsv`, `_state/`, all git-ignored. `INDEX.md` and `index/` are generated: never edit them by hand.
**Human check:** listen before you use a sound. Read the licence line that `use` writes in `04_scene/assets/sound.md`.

## Find a sound (agents start here)
1. Read `INDEX.md`: counts and examples per category, and the sources.
2. Search: `anim.py audio find "<words>" [--kind sfx|music] [--cat <category>] [--local] [--max-s 3]`,
   or `rg -i <word> library/audio/index/sfx-<category>.tsv`. Every word must match. Files on disk come first.
3. Use: `anim.py use <slug> audio:<id> --as <name> [--start s --end s]`. A remote file downloads first.
   It writes `04_scene/assets/sfx/<name>.<ext>` (effect) or `04_scene/assets/music-<name>.<ext>` (music),
   adds the licence line to `04_scene/assets/sound.md` and prints the `[sfx: file:...]` or `music: file:...` line for `cues.md`.
4. Optional: rank candidates by ear with earshot (`_shared/sound.md`, Listen).

Sonniss and SSE files often hold several takes in one file (10 whooshes, 5 hits). Find the take, then cut it with
`--start/--end`. The cut gets a 5 ms fade-in and a 10 ms fade-out, so it does not click.

## Shelves
- `sfx/<category>/<source>/[<pack>/]<file>` and `music/<category>/<source>/<file>`. File names are lowercase `a-z 0-9 . _ -`.
- Effect categories: whoosh, transition, impact, ui, tech, designed, ambience, nature, foley, mechanical, vehicle,
  weapon, creature, human, music-element, other. Music: corporate-upbeat, inspirational, cinematic, electronic,
  ambient-calm, lofi-chill, piano-classical, playful-game, dark-tension, rock-pop, jingles-stingers, other.
- Effects are sorted by the UCS code in the file name (`WHSHAir_...`), then by the pack's category, then by words in the name.
- Columns of `index/sfx-*.tsv`: id, where (local or remote), category, dur_s, size_kb, format, name, pack, source, licence, path.
  `index/music-*.tsv`: id, where, category, dur_s, loop, title, author, pack, source, licence, path.

## Fill and update
| Need | Do |
|---|---|
| Download the small packs (Kenney, OpenGameArt, GitHub music, about 3 GB) | `anim.py audio fetch` (again with `--force <id>` to refresh one) |
| List Sonniss (215 GB) and SSE (11 GB) without downloading them | `anim.py audio catalog` |
| Download remote files now | `anim.py audio get <id>...` or `--pack <source>/<pack>` |
| Add a hand download | Put the ZIP or files in `inbox/<source-id>/`, then `anim.py audio fetch`. The inbox is emptied after the sort |
| Rebuild the index | `anim.py audio index` (fetch, catalog and get do it too) |
| Add a source | Add it to `sources.json`. Its licence must be in `licences` and in `libcore.ALLOWED` |

Hand downloads (the site forbids scripts, or robots.txt blocks them): Keynata, Hellper, Ondrosik, Not Jam (itch.io: click
Download, then "No thanks, just take me to the downloads"), Mixkit (one file at a time), Freesound (only sounds marked
Creative Commons 0; keep the original file name `<id>__<user>__<name>` so the page URL is kept). Never script Mixkit,
Freesound or itch.io downloads.

## Licences
Every source is free for commercial videos without credit. A source with any other licence does not go in.
- **CC0-1.0**: public domain. Use it anywhere.
- **Sonniss-GDC** (`sonniss-*`): royalty-free in your productions. Never share the files themselves (git, a pack, a download link). No AI training.
- **Mixkit-Free** (`mixkit-*`): free in videos. Never share the files themselves. Never register them in Content ID.
Keynata and DURU music is made by software or AI; its source says CC0.
