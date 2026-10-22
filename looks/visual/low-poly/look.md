---
id: "low-poly"
axis: "visual"
title: "Low-poly"
summary: "Scenes built from flat triangular facets in brand tints, lit like cut crystal and shown in clean isometric or front views."
aliases: ["low poly", "faceted", "polygonal", "isometric low-poly"]
sources: ["https://explain.film/explainer-video-styles", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["explain-mechanism", "product-tour", "timeline", "explainer", "ad"]
formats: ["wide", "tall"]
pairs_with: {"editing": "canvas-pan", "content": "explain-mechanism"}
preview: "native"
build: "native"
palette_roles: {"field": "bg", "facet-light": "r4", "facet-mid": "accent", "facet-dark": "accent2", "facet-deep": "r1", "rim": "ink", "text": "ink"}
---

## Look
- Field: a flat `bg`, or a very soft two-tone gradient. No texture.
- Facets: every object is a set of flat triangles or quads. Each facet is one solid tone. Neighbouring facets differ by 6–14% lightness, so the form reads as lit from the top left.
- Palette: 4–6 tones from the brand ramp (`accent`, `accent2` and `r*`). Light facets face the key light, dark facets face away.
- Shapes: mountains, gems, terrain slabs, trees as cones, devices as chunky prisms. No curves; spheres become icospheres with 20–80 faces.
- Type: brand `head` in heavy weight, 56–90 px, `ink`, on the flat field away from the facets.

## Behaviour
- Entrances: objects assemble from facets. Facets fly in from 40–80 px away, rotating 20–40°, and snap into place with `P.ease.softLand` (400 ms). Stagger 20–30 ms per facet, total at most 800 ms.
- Alternative: an object rises from the ground with `P.ease.enter` (500 ms) while the lit facets brighten.
- Exits: facets scatter outward and fade over 300 ms with `P.ease.exit`, or the whole object sinks below the ground plane.
- Ambient: slow rotation of 6–10° per second for hero objects (`P.ease.linear`). Light facets shimmer between two adjacent tones once every 3 s on a crystal.
- Transitions: a ring of facets sweeps across the frame in 600 ms, or the camera flies through a prism into the next scene.
- Camera: a slow isometric orbit of 10–20° over 5 s with `P.ease.move`, or a fixed isometric view at 30°.
- Pacing: 3–5 s holds, about 12–16 changes per minute.
- Sound: crisp glassy clicks on facet snaps, a light synth pulse.

## Do
- Use one hero object per shot, built from 20–120 facets.
- Keep the light direction the same in every shot.
- Use flat fills only; the shading comes from the tone steps.
- Let negative space frame the hero.

## Don't
- No gradients or smooth shading inside a facet.
- No outlines or strokes around facets.
- No rounded, inflated shapes (that is `soft-3d-clay`).
- No more than six tones in one shot.

## Build notes
Native CSS and SVG: draw facets as SVG `<polygon>` or `clip-path: polygon()` divs with `fill="var(--...)"` or `color-mix()` tones. Animate each facet transform with `P.prog` and a small stagger. Group facets so a shot stays under 150 polygons. Works in both formats; in tall, scale the hero up and stack the headline above it.
