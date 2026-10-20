---
name: VideoFactory Studio
description: Contact-sheet studio for reviewing animation production.
colors:
  paper: '#f3f0e8'
  sheet: '#fbf9f3'
  sheet-deep: '#eae6dc'
  ink: '#202622'
  ink-soft: '#505851'
  ink-faint: '#636b64'
  rule: '#c7c4b9'
  rule-dark: '#aaa99e'
  rust: '#b84932'
  rust-dark: '#953925'
  rust-wash: '#f3dfd7'
  green: '#315d46'
  green-wash: '#e1e9df'
  amber: '#72551c'
  amber-wash: '#f1e9d5'
  red: '#8f3028'
  red-wash: '#f2dfdb'
  blue: '#375761'
  blue-wash: '#e0e9e9'
  focus: '#125b9a'
  sidebar: '#eeebe2'
  on-action: '#fffaf3'
  white: white
  dark-hover: '#303a34'
  field-hover: '#757b74'
  placeholder: '#60665f'
typography:
  display:
    fontFamily: DM Sans Studio, DM Sans, sans-serif
    fontSize: clamp(2.05rem, 4.1vw, 3.65rem)
    fontWeight: 700
    lineHeight: 1.04
    letterSpacing: -.035em
  headline:
    fontFamily: DM Sans Studio, DM Sans, sans-serif
    fontSize: clamp(1.35rem, 2vw, 1.85rem)
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: -.035em
  review-title:
    fontFamily: DM Sans Studio, DM Sans, sans-serif
    fontSize: clamp(1.9rem, 3.5vw, 3.15rem)
    fontWeight: 700
    lineHeight: 1.04
    letterSpacing: -.035em
  display-narrow:
    fontFamily: DM Sans Studio, DM Sans, sans-serif
    fontSize: clamp(2rem, 10vw, 3.2rem)
    fontWeight: 700
    lineHeight: 1.04
    letterSpacing: -.035em
  title:
    fontFamily: DM Sans Studio, DM Sans, sans-serif
    fontSize: 1.12rem
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: -.035em
  body:
    fontFamily: DM Sans Studio, DM Sans, sans-serif
    fontSize: 15px
    lineHeight: 1.5
  label:
    fontFamily: DM Sans Studio, DM Sans, sans-serif
    fontSize: 12px
    fontWeight: 700
    lineHeight: 1.5
  status:
    fontFamily: DM Sans Studio, DM Sans, sans-serif
    fontSize: 11px
    fontWeight: 700
    lineHeight: 1.2
  sequence:
    fontFamily: ui-monospace, SFMono-Regular, Menlo, monospace
    fontSize: 11px
    lineHeight: 1.5
    letterSpacing: .08em
  editor:
    fontFamily: DM Sans Studio, DM Sans, sans-serif
    fontSize: 15px
    lineHeight: 1.75
rounded:
  square: '0'
spacing:
  state-gap: 3px
  label-gap: 6px
  action-gap: 8px
  field-gap: 11px
  compact-gap: 12px
  section-gap: 18px
  panel-gap: 24px
  review-gap: 29px
  style-gap: 32px
components:
  button-secondary:
    backgroundColor: transparent
    textColor: '{colors.ink}'
    rounded: '{rounded.square}'
    padding: 9px 15px
  button-secondary-hover:
    backgroundColor: '{colors.sheet-deep}'
    textColor: '{colors.ink}'
  button-primary:
    backgroundColor: '{colors.rust}'
    textColor: '{colors.on-action}'
    rounded: '{rounded.square}'
    padding: 9px 15px
  button-primary-hover:
    backgroundColor: '{colors.rust-dark}'
    textColor: '{colors.white}'
  button-dark:
    backgroundColor: '{colors.ink}'
    textColor: '{colors.sheet}'
    rounded: '{rounded.square}'
    padding: 9px 15px
  button-dark-hover:
    backgroundColor: '{colors.dark-hover}'
    textColor: '{colors.white}'
  button-danger:
    backgroundColor: transparent
    textColor: '{colors.red}'
    rounded: '{rounded.square}'
    padding: 9px 15px
  button-danger-hover:
    backgroundColor: '{colors.red-wash}'
    textColor: '{colors.red}'
  input:
    backgroundColor: '{colors.sheet}'
    textColor: '{colors.ink}'
    rounded: '{rounded.square}'
    padding: 9px 11px
    typography: '{typography.body}'
  nav-current:
    backgroundColor: '{colors.sheet}'
    textColor: '{colors.ink}'
    padding: 0 10px
  status-approved:
    textColor: '{colors.green}'
    padding: 2px 8px
    typography: '{typography.status}'
  proof-card:
    backgroundColor: '{colors.paper}'
    padding: 14px 15px 15px
  review-rail-current:
    backgroundColor: '{colors.rust}'
    textColor: '{colors.white}'
    size: 25px
  output-editor:
    backgroundColor: '{colors.sheet}'
    textColor: '{colors.ink}'
    rounded: '{rounded.square}'
    padding: clamp(15px, 2.2vw, 26px)
    typography: '{typography.editor}'
  saved-evidence:
    backgroundColor: '{colors.sheet}'
    textColor: '{colors.ink}'
    rounded: '{rounded.square}'
    padding: 14px
  creative-stage-current:
    backgroundColor: '{colors.sheet-deep}'
    textColor: '{colors.ink}'
    rounded: '{rounded.square}'
    padding: 7px 12px
  creative-stage-lead:
    backgroundColor: '{colors.sheet-deep}'
    textColor: '{colors.ink}'
    rounded: '{rounded.square}'
    padding: 18px
---

# Design System: VideoFactory Studio

## Overview

**Creative North Star: "Contact-sheet studio"**

Contact-sheet studio borrows warm proof paper, dark ink, fine frame rules and numbered margins from film contact sheets and editorial proofing. DM Sans keeps controls and prose readable; monospaced labels identify sequence, timing and revisions.

Surfaces remain flat and tightly aligned. Real media carries the imagery, while labeled state colors and rust actions make review decisions easy to find. Dashboard identity is separate from each video’s chosen style.

**Key Characteristics:**
- Warm paper and flat ink rules.
- Square controls and genuine media frames.
- Numbered production paths with labeled states.

Source of truth: `studio/web/app.css`, with component structure and states in `studio/web/index.html` and `studio/web/app.js`. The direction is code-led: no full-fidelity image comp or catalog quality-bar image exists.

## Colors

Warm neutrals carry the workspace; rust identifies actions and sequence emphasis. Frontmatter values are normative.

### Primary
- **Rust / dark rust / rust wash:** primary buttons, selected review steps and production markers.

### Secondary
- **Green / green wash:** approved, ready and succeeded states.
- **Amber / amber wash:** waiting and queued states; the wash exists in the source palette but is not a universal badge fill.
- **Red / red wash:** stale, changes requested and failed states.
- **Blue / blue wash:** running, cancelling and draft states; labels retain their own distinctions.

### Neutral
- **Paper / sheet / deep sheet / sidebar:** workspace, editable output, media frames and navigation surfaces.
- **Ink / soft ink / faint ink:** titles, supporting copy and sequence metadata.
- **Rule / dark rule:** fine dividers and frame strokes.
- **On-action / white / dark hover:** action text and dark-button feedback.
- **Focus:** visible keyboard outlines; **field hover / placeholder:** field-specific feedback.

**The Labeled State Rule.** Always pair semantic state colors with their text labels; readiness, jobs and human approval stay distinct.

## Typography

**Display and body font:** self-hosted DM Sans Studio, then DM Sans, then sans-serif. The variable font is served from `/fonts/DM-Sans.ttf`, supports weights 100–1000, and uses `font-display: swap`.

**Sequence font:** ui-monospace, SFMono-Regular, Menlo, monospace; timing and sequence labels use tabular figures.

### Hierarchy
- **Display:** main page titles; review titles have their own smaller fluid role. Narrow main titles use the recorded display-narrow role; review-title specificity retains its separate ramp.
- **Headline:** section headings. **Title:** tertiary headings. Both retain the recorded tight heading tracking.
- **Body:** inherited interface and prose rhythm; paragraphs cap at 72ch, introductory copy at 64ch. Introductory copy uses 16px, falling to 14px below the narrow breakpoint.
- **Label / status:** field labels and state badges. Supporting UI copy commonly uses 11–13px; these are contextual roles, not a replacement body scale.
- **Editor:** authored text uses the body family with greater line spacing. Recipe source and logs use monospace.

## Layout

The fixed desktop sidebar is 244px wide, becomes 210px at 1120px, and becomes an in-flow header at 860px. Content caps at 1500px. Desktop inline padding is `clamp(22px, 4vw, 58px)`; main top padding is `clamp(28px, 4.2vw, 58px)`. The sticky route header has a 57px minimum height.

Use the observed gap tokens by context rather than imposing a new arithmetic spacing scale. Proof and library contact sheets use a one-pixel shared rule grid; video tiles use separate gutters. Video browsing is three columns, two at 1120px, and one at 660px. Proof browsing is two columns and library browsing three; both become one at 660px.

Review output and evidence use `minmax(0, 1fr) minmax(250px, 310px)` with the review gap; at 1120px the evidence track is `minmax(220px, 280px)` with a 20px gap. At 660px they stack with a 25px gap. Style recipes use `minmax(0, 1fr) minmax(280px, 380px)` and the style gap, then stack at 660px. Forms and comparison panes also become one column at 660px.

At 860px the project overview’s vertical production rail becomes a labeled stage selector. The review page’s horizontal numbered rail remains scrollable at narrow widths. At 660px main padding is `26px 16px 45px`; collection filters fill the available width and decision buttons wrap.

Creative catalog cards use a two-column shared-rule sheet, becoming one column at 660px. Playground controls use three equal columns and stack at the same breakpoint; saved review evidence stays in a single readable column.

Creative workshops use a wrapping, eight-pixel-gap stage sequence above one visible panel. At 660px its stages form two columns; below 360px they stack. The current panel begins with an 18px-padded deeper-sheet lead that keeps its instruction and the named user and agent roles within a readable 68ch measure.

## Elevation & Depth

No box shadows are used. Paper, sheet and deeper sheet tones distinguish surfaces; fine rules group evidence, controls and media. The sticky header uses the source’s translucent paper color. Structural frames belong to the contact-sheet world and are not a prohibited device.

**The Flat Proof Rule.** Use fine rules and surface tones to establish structure; this dashboard uses no box shadows.

## Shapes

Buttons, fields, editors and proof frames have square corners. One-pixel borders define their edges. Small circular marks identify successful states and live activity; circles do not become the container shape. Dashed borders are reserved for the upload target. Its drag/focus-within state uses a rust outline.

## Components

### Buttons

Firm, square actions. Standard buttons have a 42px minimum height, the recorded padding, a one-pixel border and weight 700. Primary actions use rust; dark actions use ink; secondary actions are transparent; destructive controls use a red stroke and text. Each hover variant is recorded in frontmatter. Small buttons use a 34px minimum height and `7px 10px` padding at 12px.

Background, text and border feedback transition for `.15s ease`. Keyboard focus uses a three-pixel focus-colored outline with a three-pixel offset. Disabled controls use opacity `.58` and a not-allowed cursor; no extra pressed treatment is defined in the source.

### Chips

Status badges are informational, not filters. They use a current-color border, a matching six-pixel mark, the recorded status type and padding, and a 24px minimum height. Successful states have round marks; not-applicable uses a one-pixel dash. They have no invented interactive state.

### Cards / Containers

Proof cards sit in a shared fine-rule contact sheet and use recorded proof-card padding. Their media frame is `16 / 8.8`; video tiles and material thumbnails are `16 / 9`. Frames use deeper sheet and a dark-rule border; no shadow. Video-tile images scale to `1.025` on hover over `.2s ease`, while proof images have no equivalent motion. Supporting captions sit below the frame with a 10px top gap.

### Inputs / Fields

Quiet editable sheets. Fields have a 42px minimum height, dark-rule borders and recorded input padding. Hover uses field-hover; focus uses the shared outline. Placeholders use their dedicated color. Disabled fields use the shared disabled treatment; error messages use red text at 12px without an invented error-border state. Textareas resize vertically.

Output editors use the recorded editor type and fluid padding, a minimum height of `min(60vh, 680px)`, and a sidebar-colored read-only surface. At 660px the minimum height is 52vh and text is 14px. Conflict comparisons retain the editable draft beside the current file.

### Navigation

Desktop links are at least 44px tall with soft ink and weight 600. Hover adds a fine border and translucent white surface; `aria-current="page"` selects sheet, ink and a rust margin marker. Below 860px navigation becomes a horizontal scroller with 39px-high links and the active marker below the link. The new-video link keeps an accessible label when its visible wording collapses to a plus at 660px.

### Numbered Production Rails

The project overview uses connected 29px stage numbers, state-colored strokes or washes, and links with text state labels. Its mobile counterpart is a labeled selector. The review rail uses connected 25px numbers and a rust-filled `aria-current="step"` marker; each step remains a link with visible focus. Sequence numbers are monospaced, not decorative headings.

### Creative Sources and Saved Evidence

Style families and character candidates use flat, square cards in the shared-rule sheet. Existing source frames have an explicit reference label; their natural aspect ratio is contained inside a rule-bordered frame. A missing approved sample stays a text state, not a simulated image.

Creative gate rows use a one-pixel shared-rule grid with a labeled status and supporting explanation. The same row pattern carries workshop requests, sample formats and generation batches. It wraps its contents at narrow widths.

Saved review artifacts use the recorded sheet surface and padding. Each card identifies the file and offers a secondary download link; text evidence appears inline in a bounded, scrollable deeper-sheet block (`max-height: 340px`) with preserved line breaks. Media evidence uses native players or contained images. The exact revision and state sit above the cards; decision controls stay below the evidence. An already approved revision leaves the ready action disabled and omits redundant approval.

On creative reviews, readable saved briefs and other prose appear directly in the evidence card. Raw JSON stays in a closed, labeled disclosure inside its card. In workshops, a substantive saved brief appears as readable evidence; the editable brief, full answers, form link, original prompt, request IDs and generation settings sit under labeled Advanced disclosures. Secondary family guides, imported references and procedural cast are closed library sections after the workshop entries; their previews remain genuine saved images or rendered cast, never simulated artwork.

### Guided Creative Stages

Style and character workshops use square, 42px-minimum stage buttons with a text status pill. The current button shifts to the deeper-sheet tone, dark ink border and bold label; other stages remain revisitable. Only its panel is shown. The lead combines a short instruction, named user and agent roles and, when available, the exact next action. It uses the existing sheet tones and one-pixel borders rather than a new accent color.

Motion stays functional: button feedback, a restrained tile hover and scroll behavior. Reduced-motion preferences set transition and animation duration to `.01ms`, limit animation iteration to one, and remove smooth scrolling.

## Do's and Don'ts

### Do:
- **Do** use DM Sans for interface prose and monospaced labels for sequence, timing and revisions.
- **Do** preserve visible keyboard focus and readable state labels.
- **Do** use real media or an explicit missing-output label in proof frames.
- **Do** keep native media controls and explicit save and review actions.

### Don't:
- **Don’t** add decorative page-load motion.
- **Don’t** conflate readiness, running jobs and human approval.
- **Don’t** borrow a video recipe’s visual style for the dashboard shell.

The sidecar’s generated tonal strips are preview metadata, not additional production palette tokens. This documentation pass changes no application source.
