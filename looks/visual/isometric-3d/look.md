---
id: "isometric-3d"
axis: "visual"
title: "Isometric 3D"
summary: "Clean isometric blocks, platforms and flows on a quiet field; every object has three flat shaded faces and the system reads at a glance."
aliases: ["isometric", "isoboard", "isometric explainer"]
sources: ["https://explain.film/explainer-video-styles/isometric", "https://ideatomotion.com/looks"]
best_for: ["explain-mechanism", "product-tour", "data-story", "explainer", "ad"]
formats: ["wide", "tall"]
pairs_with: {"editing": "canvas-pan", "content": "explain-mechanism"}
preview: "ai"
build: "ai"
palette_roles: {"bg": "bg", "top": "r5", "left": "r3", "right": "r2", "hot": "accent", "alt": "accent2", "line": "line", "ink": "ink"}
---

## Look
- View: true isometric, 30 degree axes, no perspective. All objects sit on one diamond platform or a tile grid.
- Solids: cubes, slabs, cylinders. Three flat faces: top (light ramp tone), left (mid), right (dark). No gradients inside a face.
- Accent: one object per frame in `accent`; a second voice in `accent2` for flows (arrows, paths, packets).
- Ground: soft contact shadow in `ink` at 12% opacity under each object.
- Type: `head` headline 64-88 px at the top left. Labels are small `mono` plates floating above objects.

## Behaviour
- Entrances: objects drop onto the grid from 60 px above with `P.spring` pop (`{ dur: 0.4, bounce: 0.25 }`), 60 ms stagger, shadow grows in as they land.
- Build: a stack builds up block by block, 120 ms per block, `P.ease.softLand`.
- Flow: packets travel along isometric paths at constant speed (`P.ease.linear`), 1.2-2.4 s per path, turning at 90 degree corners.
- Camera: the whole board slides 80-200 px along an iso axis over 1.6-2.4 s (`P.ease.move`), or rotates 90 degrees in 900 ms to show the next district. Zoom to a detail takes 1.6 s.
- Exit: objects sink 40 px and fade in 250 ms (`P.ease.exit`), reverse order.
- Pacing: one new object or one new flow per beat, 3-6 s holds, about 10-14 changes per minute.
- Ambient: packets loop on finished paths; a lit tile pulses `accent` at 4% every 2 s.
- Sound: soft thunk on each landing, whoosh on camera slides, light bed.

## Do
- Keep the axes exact. Align every object to the tile grid.
- Use only three tones per object plus one accent.
- Leave an empty ring of floor around the focus object.

## Don't
- No perspective, no lens blur, no gradients on faces.
- No more than 12 objects on screen.
- No bounce on the camera, only on object drops.
- No real-world textures or photos.

## Build notes
The native preview is a CSS/SVG stand-in with polygons. The final look needs AI or hand-built isometric assets (see `_shared/image-generation.md`): build them as transparent PNG parts, one per object, in brand colours, then animate the parts with `P.spring`. Simple block scenes can be built natively with SVG `polygon` and `transform`.
