Stage contract: stages/04_scene/CONTEXT.md. Outputs appear here as you work.

Write the scene in `index.html` and `scene.js` with the Modern kit: `_shared/modern.md`.

After an approved creative snapshot is applied, run `anim.py cues <slug>` again. The ordinary scene player preloads its video-owned character engine and manifests. In `scene.js`, draw an approved character on a canvas context with `P.drawCharacter(ctx, {id: 'tutor', variant: 'ink', view: 'front', actions: {intro: 'idle', explain: 'point'}, expressions: {explain: 'happy'}, props: {show: 'book'}})`. Cue IDs choose actions and reset their local time. The narration level supplies the mouth opening unless `speechLevel` is passed explicitly. Check the returned `available` result when you author a scene. Position and scale the canvas context before you draw. The character's own canvas coordinates start at its top left.
