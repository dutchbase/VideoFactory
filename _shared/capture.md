# Capture: screenshots and screen recordings of web pages and apps

Show real pages and apps in a scene. Three commands make the material. All write to `videos/<brand>/<slug>/04_scene/assets/` and log every capture in `assets/captures.md` (name, URL, breakpoint, date, login). Use that log for the brief's `Captures:` line and the sources in `DESCRIPTION.md`.

| Command | Makes |
|---|---|
| `python anim.py login <site> <url> --expect "<text or selector>" [--timeout 600]` | Opens a browser window on your desktop. You log in. The session is saved as soon as the expected text or selector shows, in `_auth/<site>.json` (folder 0700, file 0600 from creation, git-ignored). If the text does not show before the timeout, the command reports that you are not logged in and saves nothing. Needed once per site, and again when the session expires. |
| `python anim.py grab <slug> <url> <name> [--bp ..] [--auth <site>] [--mask ".email, .avatar"] [--selector ..] [--wait-for ..] [--find "text"]` | A PNG at 2x: `assets/<name>.png`. Show it in a `vf-browser` frame with `<img src="assets/<name>.png">` (`_shared/modern.md`). |
| `python anim.py record <slug> <name> <steps.txt> [--bp ..]` | A scripted screen recording: `assets/<name>/f001.jpg…` at 12 fps. Play it with `Modern.clip` (`_shared/modern.md`). Shots inside the steps file become PNGs. |

## Breakpoints
| Name | Size (CSS px) | Use for |
|---|---|---|
| `mobile` | 390x844 | tall videos (shorts), "on your phone" |
| `tablet` | 768x1024 | |
| `laptop` | 1280x800 | default |
| `desktop` | 1920x1080 | wide screens |

`--bp` takes one name, a comma list (`mobile,desktop`), `all`, or `WxH` (`1000x700`). With more than one breakpoint the output is `<name>-<bp>` (`home-mobile`). A `breakpoints:` line in the steps file does the same, and `--bp` wins. Recording frames are `min(width, 1280)` wide.

Show a `mobile` capture in a `vf-phone` frame (`_shared/modern.md`).

## Steps file
One steps file runs once per breakpoint, in a fresh browser each time.

```
url: https://app.example.com/dashboard
auth: my-app                  # a saved login
breakpoints: mobile, desktop  # or all
scheme: light                 # default dark
mask: .user-email, .avatar    # blurred in every shot and recording
expect: Jobs                  # text that must show; if not, the run stops (login expired?)
---
@mobile,tablet click .menu-toggle   # an @ prefix limits a step to those breakpoints
click text="Search"
type #q "remote work"
press Enter
wait 1.5
shot dashboard-list
scroll 600
wait 2
```

Steps: `goto URL`, `click SEL`, `hover SEL`, `type SEL TEXT`, `press KEY`, `scroll PX`, `wait SECONDS`, `wait_for SEL`, `shot NAME`, `crop SEL`. `crop` keeps only that element's box, measured at that step, in the recording and in shots. Use it to keep sidebars and account menus out. Ready-made steps files for ChatGPT and Claude: `lib find recording --brand <brand>`, in `library/captures/`. `SEL` is a Playwright selector (`#id`, `.class`, `text="Search"`). A comment is a whole line that starts with `#`.

## Rules
- Never put a password in a steps file. The parser refuses it. Use `login`.
- Never commit or share `_auth/`. It holds logged-in sessions. Agents never read `_auth/*.json` and never print cookies, tokens or URL queries.
- Every `grab` and `record` runs a privacy scan (tesseract OCR, frames enlarged 2x). It looks for e-mail addresses, phone numbers, IBANs, card numbers, key-like strings and token queries. A hit deletes the capture and stops with the kind, frame and position only. There is no switch to turn it off. OCR can miss things, so always `crop` to the part the video needs.
- `mask:` blurs extra selectors. It is best-effort and no replacement for `crop`.
- A step that fails stops the run and names the step. A recording lasts at most 90 seconds.
- Recordings have no sound. The cursor is a red dot.
- Record in the brief and in `REVIEW.md` whether a screen is a real capture or authored. Never say it on screen (`_shared/tone.md`).
