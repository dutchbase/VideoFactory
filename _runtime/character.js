/* Controlled character drawing. All visible state comes from the caller's time and options. */
(function () {
  const REVISION = 2;
  const smooth = x => x * x * (3 - 2 * x);
  const unavailable = reason => ({ available: false, reason });
  function sample(frames, phase) {
    if (!frames) return { x: 0, y: 0, rotation: 0 };
    let a = frames[0], b = frames[frames.length - 1];
    for (let i = 1; i < frames.length; i++) if (phase <= frames[i].t) { b = frames[i]; a = frames[i - 1]; break; }
    const u = a === b ? 0 : smooth((phase - a.t) / (b.t - a.t));
    return { x: a.x + (b.x - a.x) * u, y: a.y + (b.y - a.y) * u,
      rotation: a.rotation + (b.rotation - a.rotation) * u };
  }

  async function load(manifest) {
    const source = typeof manifest === 'string' ? await (await fetch(manifest, { cache: 'no-store' })).json() : manifest;
    if (!source || source.schema !== 1 || source.renderer_revision !== REVISION || !source.canvas || !source.views || !source.actions)
      throw new Error('Invalid character manifest');
    const images = {};
    try {
      for (const parts of Object.values(source.views)) {
        for (const part of Object.values(parts.parts)) {
          const key = part.path + ':' + part.sha256;
          if (images[key]) continue;
          const response = await fetch(part.url || '/media/' + part.path, { cache: 'no-store' });
          if (!response.ok) throw new Error('Character artwork unavailable: ' + part.path);
          const bytes = await response.arrayBuffer();
          const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), b => b.toString(16).padStart(2, '0')).join('');
          if (hash !== part.sha256) throw new Error('Character artwork changed: ' + part.path);
          images[key] = await createImageBitmap(new Blob([bytes]));
        }
      }
    } catch (error) {
      for (const image of Object.values(images)) image.close();
      throw error;
    }
    return {
      manifest: source,
      dispose() { for (const image of Object.values(images)) image.close(); },
      draw(ctx, time, options = {}) {
        const { action, view, expression, speechLevel = 0, prop } = options;
        const pose = Object.hasOwn(source.actions, action) ? source.actions[action] : null;
        const perspective = Object.hasOwn(source.views, view) ? source.views[view] : null;
        if (!pose) return unavailable('action');
        if (!perspective) return unavailable('view');
        if (!Number.isFinite(time) || !Number.isFinite(speechLevel) || speechLevel < 0 || speechLevel > 1)
          return unavailable('state');
        const rig = perspective.rig;
        const duration = pose.duration;
        const phase = pose.loop ? ((time % duration) + duration) % duration : Math.max(0, Math.min(duration, time));
        let face = expression || pose.expression;
        if (!expression && Object.hasOwn(rig.expressions, 'blink') &&
            ((action === 'idle' && phase >= 3.1 && phase < 3.25) ||
            (action === 'blink' && phase >= 0.08 && phase < 0.22))) face = 'blink';
        if (!Object.hasOwn(rig.expressions, face)) return unavailable('expression');
        if (pose.requires_prop && !prop) return unavailable('prop');
        if (prop && !Object.hasOwn(rig.props, prop)) return unavailable('prop');
        const requestedMouth = speechLevel < 0.25 ? 'closed' : speechLevel < 0.65 ? 'half' : 'open';
        const mouth = Object.hasOwn(rig.mouths, requestedMouth) ? requestedMouth : 'closed';
        const expressionParts = rig.expressions[face];
        const selected = new Set(Array.isArray(expressionParts) ? expressionParts : [expressionParts]);
        selected.add(rig.mouths[mouth]);
        if (prop) selected.add(rig.props[prop]);
        const faces = new Set([...Object.values(rig.expressions).flatMap(value => Array.isArray(value) ? value : [value]),
          ...Object.values(rig.mouths)]);
        const props = new Set(Object.values(rig.props));
        const optional = new Set([...faces, ...props]);
        for (const id of rig.draw_order) {
          if (optional.has(id) && !selected.has(id)) continue;
          const part = perspective.parts[id];
          const own = sample(pose.tracks[id], phase);
          const parentId = id === 'hair' || faces.has(id) ? 'head' : props.has(id) ? 'arm-right' : null;
          ctx.save();
          if (parentId) {
            const parent = perspective.parts[parentId];
            const movement = sample(pose.tracks[parentId], phase);
            ctx.translate(parent.at[0] + movement.x, parent.at[1] + movement.y);
            ctx.rotate(movement.rotation);
            ctx.translate(part.at[0] - parent.at[0] + own.x, part.at[1] - parent.at[1] + own.y);
          } else {
            ctx.translate(part.at[0] + own.x, part.at[1] + own.y);
          }
          ctx.rotate(own.rotation);
          const [width, height] = part.size ?? part.crop.slice(2);
          if (part.clip) {
            const path = new Path2D();
            part.clip.forEach(([x, y], index) => {
              const px = x * width - part.anchor[0], py = y * height - part.anchor[1];
              if (index) path.lineTo(px, py); else path.moveTo(px, py);
            });
            path.closePath();
            ctx.clip(path);
          }
          ctx.drawImage(images[part.path + ':' + part.sha256], ...part.crop,
            -part.anchor[0], -part.anchor[1], width, height);
          ctx.restore();
        }
        return { available: true, action, view, time: phase, expression: face, mouth, prop: prop || null };
      }
    };
  }
  window.Character = { REVISION, load };
})();
