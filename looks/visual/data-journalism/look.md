---
id: "data-journalism"
axis: "visual"
title: "Data journalism"
summary: "Thin-line editorial charts on a dark field with one highlighted series and leader-line annotations; serious, sourced and readable."
aliases: ["data noir", "ledger", "editorial chart", "ft style", "the economist style"]
sources: ["https://explain.film/explainer-video-styles/data-journalism", "https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["data-story", "compare", "timeline", "explainer", "course"]
formats: ["wide", "tall"]
pairs_with: {"editing": "scroll-build", "content": "data-story"}
preview: "native"
build: "native"
palette_roles: {"field": "bg", "grid": "line", "context": "faint", "hero": "accent", "second": "accent2", "text": "ink"}
---

## Look
- Field: deep `bg` (or `surface` for a light brand) with a faint baseline grid in `line`.
- Data: 2 px lines and flat bars. Every series is `faint` grey except the one the voice talks about, which is `accent`; a second highlight may use `accent2`. No 3D, no gradients, no pies with more than three slices.
- Type: headline in the brand `head` font, 44–64 px, written as a finding ("Prices doubled in five years"). Axis labels, units and sources in `mono` 14–16 px. Annotations sit at the end of a thin leader line.
- Every chart shows a source line bottom-left: "Source: …".

## Behaviour
- Camera: locked. The film moves down the story like a scroll; nothing slides while text is being read.
- Build order for each chart: axes and grid fade in (240 ms), then the data draws along its path (line: `P.ease.linear` stroke-dashoffset over 1.2–2.0 s; bars: grow from the baseline with `P.ease.softLand`, 40–60 ms stagger), then the annotation and its leader line draw (320 ms).
- Focus: when the voice names a point, that point brightens and grows 1.2× while everything else dims to 40%. Numbers count up over 600–1200 ms.
- Transitions: a clean vertical push to the next chart (800 ms `P.ease.move`), or the current chart morphs into the next (bars become dots on a map).
- Pacing: one chart per idea, 5–9 s holds so the viewer can read, about 6–10 changes per minute.
- Ambient: none, or a single blinking cursor tick on the latest value.
- Sound: low pulse bed; soft ticks on each data reveal.

## Do
- Write the takeaway as the headline; the chart proves it.
- Label lines directly instead of a legend.
- Start bar axes at zero; show the unit and the time span.
- Keep the source on screen as long as the chart.

## Don't
- No decorative icons or stock photos inside charts.
- No more than one accent series at a time.
- No chart moves while its annotation is on screen.
- Never invent or round numbers beyond the source.

## Build notes
Native: inline SVG paths with `stroke-dasharray` reveals, CSS bars, `P.prog` count-ups. The `library/` chart blocks may be used if present (`library/CATALOG.md`). Tall format: one chart per screen, headline on top, legend-free.
