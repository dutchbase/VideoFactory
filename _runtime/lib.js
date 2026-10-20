// lib.js - draw items from the asset library (library/) on any canvas context. Load after player.js.
// Works on any 2d canvas context: pass the context of the scene canvas.
// Call at the top of scene.js so rendering waits for the files; draw calls are pure functions of time.
//
//   Lib.icon(g.ctx, 'lucide/rocket', 160, 90, 48, '#FF8A1C');     // centred at x, y; size in px; tinted
//   Lib.graphic(g.ctx, 'undraw/laptop', 160, 90, 300);            // centred, width 300, keeps ratio, own colours
//   const spin = Lib.lottie('confetti');                          // a Lottie file as a time-driven clip
//   spin.at(g.ctx, t, 160, 90, 200, 200);                         // t = seconds into the clip
//   Lib.lottie('confetti', { colors: 'brand' });                  // same file, recoloured with window.BrandTokens
//
// Files come from the video's assets/ first (`python anim.py use <slug> <ref>` copies them there),
// then from the shared library/ folder.
(() => {
  const ROOT = (document.currentScript && document.currentScript.src || '').replace(/[^/]*$/, '');  // the _runtime/ folder
  const shared = window.ANIM?.creative ? [] : ['../../../library/'];
  const bases = { icons: ['assets/icons/', ...shared.map(b => b + 'icons/')],
    graphics: ['assets/graphics/', ...shared.map(b => b + 'graphics/')],
    lottie: ['assets/lottie/', ...shared.map(b => b + 'lottie/')] };
  const IMG = new Map();

  // Load an image, trying each base in turn. The first one that loads wins.
  function load(kind, name, ext) {
    const key = `${kind}/${name}`;
    if (IMG.has(key)) return IMG.get(key);
    const im = new Image();
    IMG.set(key, im);
    const tries = bases[kind].map((b) => `${b}${name}.${ext}`);
    const p = new Promise((res, rej) => {
      const next = () => {
        const src = tries.shift();
        if (!src) return rej(new Error(`[lib] no ${kind} "${name}". Run: python anim.py lib find ${name.split('/').pop()}`));
        im.onload = () => res(im); im.onerror = next; im.src = src;
      };
      next();
    });
    if (window.P) P.wait(p.catch((e) => console.error(e)));
    return im;
  }

  const TINT = new Map();
  // An icon is one colour: the SVG strokes use currentColor, which an <img> renders black, so tint it.
  function tinted(name, size, color) {
    const im = load('icons', name, 'svg');
    if (!(im.complete && im.naturalWidth)) return null;
    const px = Math.ceil(size * 2), key = `${name}|${px}|${color}`;
    if (!TINT.has(key)) {
      const c = document.createElement('canvas'); c.width = c.height = px;
      const x = c.getContext('2d');
      x.drawImage(im, 0, 0, px, px);
      x.globalCompositeOperation = 'source-in'; x.fillStyle = color; x.fillRect(0, 0, px, px);
      TINT.set(key, c);
    }
    return TINT.get(key);
  }

  function icon(ctx, name, x, y, size, color = '#fff', o = {}) {
    const c = tinted(name, size, color);
    if (!c) return;
    ctx.save(); ctx.globalAlpha *= o.alpha ?? 1;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(c, x - size / 2, y - size / 2, size, size);
    ctx.restore();
  }

  function graphic(ctx, name, x, y, w, o = {}) {
    const im = load('graphics', name, 'svg');
    if (!(im.complete && im.naturalWidth)) return;
    const h = w * (im.naturalHeight / im.naturalWidth);
    ctx.save(); ctx.globalAlpha *= o.alpha ?? 1;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(im, x - w / 2, y - h / 2, w, h);
    ctx.restore();
  }

  // ── Lottie ────────────────────────────────────────────────────────────────
  // Lottie data arrives as a script (library/lottie/NAME.js, made by `anim.py lib lottie add`): a render opens scenes
  // from file://, where fetch() of JSON is blocked. lottie-web draws to an offscreen canvas; a frame is a function of t.
  const script = (srcs) => new Promise((res, rej) => {
    const next = () => {
      const src = srcs.shift();
      if (!src) return rej(new Error('script not found'));
      const el = document.createElement('script');
      el.onload = res; el.onerror = () => { el.remove(); next(); }; el.src = src; document.head.appendChild(el);
    };
    next();
  });
  // Brand recolour: every static or animated colour of a fill, stroke, gradient or solid layer becomes a brand token.
  // Greys go to ink/dim/faint/surface by lightness. Saturated colours go to the nearest brand hue (accent, accent2, green,
  // danger); very light ones become the lightest grey token and very dark ones the darkest, so the light order survives.
  const BRAND_HUES = ['accent', 'accent2', 'green', 'danger'], BRAND_GREYS = ['ink', 'dim', 'faint', 'surface'];
  const hex2rgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
  function hsl([r, g, b]) {
    const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
    let h = 0;
    if (d) h = mx === r ? ((g - b) / d + 6) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
    return { h: h * 60, c: d, l: (mx + mn) / 2 };
  }
  function brandLottie(data, tokens) {
    const need = [...BRAND_HUES, ...BRAND_GREYS];
    for (const k of need) if (!/^#[0-9a-f]{6}$/i.test(tokens?.[k] || '')) throw new Error(`BrandTokens.${k} must be a #rrggbb colour`);
    const grey = BRAND_GREYS.map((k) => hex2rgb(tokens[k])).sort((a, b) => hsl(b).l - hsl(a).l);  // lightest first
    const hue = BRAND_HUES.map((k) => ({ rgb: hex2rgb(tokens[k]), h: hsl(hex2rgb(tokens[k])).h }));
    const one = (rgb) => {
      const { h, c, l } = hsl(rgb);
      if (c < 0.1) return grey[l >= 0.75 ? 0 : l >= 0.5 ? 1 : l >= 0.25 ? 2 : 3];
      if (l >= 0.85) return grey[0];
      if (l < 0.2) return grey[3];
      const dist = (x) => Math.min(Math.abs(x - h), 360 - Math.abs(x - h));
      return hue.reduce((a, b) => (dist(b.h) < dist(a.h) ? b : a)).rgb;
    };
    // v is [r, g, b, a?] in 0..1, or in 0..255 when a channel is above 1
    const rgba = (v) => {
      if (!Array.isArray(v) || v.length < 3 || !v.slice(0, 3).every(Number.isFinite)) return v;
      const big = v[0] > 1 || v[1] > 1 || v[2] > 1, k = big ? 255 : 1;
      return [...one(v.slice(0, 3).map((x) => x / k)).map((x) => x * k), ...v.slice(3)];
    };
    // A value is static ({a:0,k:[..]}) or keyframes ({a:1,k:[{s,e}..]}); map the colour in each keyframe's start and end.
    const prop = (p, fn) => {
      if (!p || !Array.isArray(p.k)) return;
      if (p.k.length && typeof p.k[0] === 'object' && !Array.isArray(p.k[0])) {
        for (const kf of p.k) for (const f of ['s', 'e']) if (Array.isArray(kf[f])) kf[f] = fn(kf[f]);
      } else p.k = fn(p.k);
    };
    // Gradient stops: [offset, r, g, b] repeated n times, then optional [offset, alpha] pairs that stay as they are.
    const stops = (n) => (v) => {
      const out = v.slice();
      for (let i = 0; i < n && i * 4 + 3 < v.length; i++) out.splice(i * 4 + 1, 3, ...rgba(v.slice(i * 4 + 1, i * 4 + 4)));
      return out;
    };
    const hexOf = (rgb) => '#' + rgb.map((x) => Math.round(x * 255).toString(16).padStart(2, '0')).join('');
    const walk = (n) => {
      if (Array.isArray(n)) return n.forEach(walk);
      if (!n || typeof n !== 'object') return;
      if ((n.ty === 'fl' || n.ty === 'st') && n.c) prop(n.c, rgba);
      else if ((n.ty === 'gf' || n.ty === 'gs') && n.g) prop(n.g.k, stops(n.g.p | 0));
      else if (n.ty === 1 && /^#[0-9a-f]{6}$/i.test(n.sc || '')) n.sc = hexOf(one(hex2rgb(n.sc)));
      for (const k in n) if (n[k] && typeof n[k] === 'object') walk(n[k]);
    };
    const copy = JSON.parse(JSON.stringify(data));
    walk(copy);
    return copy;
  }

  let engine;
  const LOT = new Map();
  function lottie(name, opts = {}) {
    if (opts.colors != null && opts.colors !== 'brand') throw new Error(`[lib] lottie colors must be 'brand', got ${JSON.stringify(opts.colors)}`);
    const key = opts.colors ? `${name}|${opts.colors}` : name;
    if (LOT.has(key)) return LOT.get(key);
    const clip = { dur: 0, ready: false, at() {} };
    LOT.set(key, clip);
    let expired = false, abort, timer;
    engine = engine || script([`${ROOT}vendor/lottie_canvas.min.js`]);
    const loading = engine.then(() => {
      if (expired) return;
      return script(bases.lottie.map((b) => `${b}${name}.js`));
    }).then(() => new Promise((res, rej) => {
      if (expired) return res();
      let data = window.LOTTIE_DATA?.[name];
      if (!data) return rej(new Error(`no Lottie data for "${name}"`));
      if (opts.colors) {
        try { data = brandLottie(data, window.BrandTokens); } catch (e) { return rej(e); }
      }
      const frames = data.op - data.ip, fr = data.fr;
      if (!['fr', 'ip', 'op', 'w', 'h'].every((k) => typeof data[k] === 'number' && Number.isFinite(data[k])) ||
          !(frames > 0 && fr > 0 && data.w > 0 && data.h > 0) || !Array.isArray(data.layers))
        return rej(new Error(`invalid data for Lottie "${name}"`));
      const cv = document.createElement('canvas');
      cv.width = data.w * 2; cv.height = data.h * 2;
      const anim = lottie_.loadAnimation({ renderer: 'canvas', loop: false, autoplay: false, animationData: data,
        rendererSettings: { context: cv.getContext('2d'), clearCanvas: true, preserveAspectRatio: 'xMidYMid meet' } });
      clip.dur = frames / fr;
      clip.at = (ctx, t, x, y, w, h, o = {}) => {
        const f = o.loop ? ((t * fr) % frames + frames) % frames : Math.min(Math.max(t * fr, 0), frames - 1);
        anim.goToAndStop(f, true);
        ctx.save(); ctx.globalAlpha *= o.alpha ?? 1; ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(cv, x - w / 2, y - h / 2, w, h);
        ctx.restore();
      };
      let settled = false;
      const done = (error) => {
        if (settled) return;
        settled = true;
        anim.removeEventListener('DOMLoaded', loaded);
        anim.removeEventListener('data_failed', failed);
        anim.removeEventListener('error', failed);
        if (error) { anim.destroy(); rej(error); }
        else { clip.ready = true; res(); }
      };
      abort = done;
      const loaded = () => done();
      const failed = (e) => done(new Error(`Lottie "${name}" failed: ${e?.message || e || 'data failed'}`));
      anim.addEventListener('DOMLoaded', loaded);
      anim.addEventListener('data_failed', failed);
      anim.addEventListener('error', failed);
    }));
    const timeout = new Promise((_, rej) => { timer = setTimeout(() => {
      expired = true;
      const error = new Error(`Lottie "${name}" did not become ready within 30 seconds`);
      abort?.(error);
      rej(error);
    }, 30000); });
    const p = Promise.race([loading, timeout]).finally(() => clearTimeout(timer))
      .catch((e) => { throw new Error(`[lib] lottie "${name}": ${e.message}. Run: python anim.py lib find ${name}`); });
    clip.whenReady = p;
    if (window.P) P.wait(p);
    return clip;
  }
  // lottie-web names its global `lottie`; keep a handle so a scene variable of that name cannot shadow it.
  const lottie_ = new Proxy({}, { get: (_, k) => window.lottie[k] });

  // MorphSVG normalizes unlike SVG commands and point counts before we seek any frame.
  let morphEngine;
  function svgMorph(fromD, toD, options = {}) {
    let start, end;
    const shape = (d, label) => {
      if (typeof d !== 'string' || !/^\s*[Mm]/.test(d)) throw new Error(`[lib] svgMorph ${label} must be SVG path data`);
      if (!CSS.supports('offset-path', `path(${JSON.stringify(d)})`))
        throw new Error(`[lib] svgMorph ${label} has invalid path syntax`);
      const raw = MorphSVGPlugin.stringToRawPath(d);
      if (!raw.length || raw.some((segment) => segment.length < 8 || segment.some((n) => !Number.isFinite(n))))
        throw new Error(`[lib] svgMorph ${label} has invalid geometry`);
      return d;
    };
    morphEngine = morphEngine || script([`${ROOT}vendor/gsap.min.js`]).then(() =>
      script([`${ROOT}vendor/MorphSVGPlugin.min.js`])).then(() => gsap.registerPlugin(MorphSVGPlugin));
    const ready = morphEngine.then(() => {
      shape(fromD, 'fromD'); shape(toD, 'toD');
      if (options.map && !['size', 'position', 'complexity'].includes(options.map)) throw new Error('[lib] svgMorph map must be size, position or complexity');
      const normalized = MorphSVGPlugin.normalizeStrings(fromD, toD,
        { shapeIndex: options.shapeIndex ?? 'auto', map: options.map ?? 'size' });
      start = MorphSVGPlugin.stringToRawPath(normalized[0]);
      end = MorphSVGPlugin.stringToRawPath(normalized[1]);
      if (start.length !== end.length || start.some((s, i) => s.length !== end[i].length))
        throw new Error('[lib] svgMorph could not normalize the shapes');
    }).catch((e) => { throw new Error(`[lib] svgMorph: ${e.message}`); });
    if (window.P) P.wait(ready);
    return { ready, path(progress) {
      if (!start) throw new Error('[lib] svgMorph is not ready; await morph.ready');
      if (!Number.isFinite(progress)) throw new Error('[lib] svgMorph progress must be finite');
      if (progress <= 0) return new Path2D(fromD);
      if (progress >= 1) return new Path2D(toD);
      const raw = start.map((segment, i) => {
        const values = segment.map((value, j) => value + (end[i][j] - value) * progress);
        values.closed = segment.closed;
        return values;
      });
      return new Path2D(MorphSVGPlugin.rawPathToString(raw));
    } };
  }

  window.Lib = { icon, graphic, lottie, brandLottie, svgMorph, bases, load };
})();
