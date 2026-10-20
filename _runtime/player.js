/* player.js - the scene clock and the scene API (window.P). MIT. Plain browser JavaScript, no build step.
 *
 * One number, t (seconds), drives everything. Every visible thing is a pure function of t.
 *   render mode  (?render in the URL): Python calls window.__seek(t) once per frame.
 *   preview mode (no ?render):         a loop follows the voice <audio> (or the wall clock) and a scrub bar.
 * Load order in a scene page: cues.js (window.ANIM), brand tokens, gsap (optional), this file, kits, scene.js.
 *
 * Ideas credited: measured eases from tejashmakwana/motionmaxxing (Apache-2.0, same math as window.Eases in
 * hf-bridge.js), spring idea from motiondivision/motion (MIT), track idea from cth9191/animate (MIT).
 */
(function () {
  'use strict';

  // ---------------------------------------------------------------- input
  if (!window.ANIM) console.warn('[anim] no window.ANIM: run python anim.py cues <slug>');
  const A = window.ANIM || { meta: { duration: 10, slug: '', voice: null }, cueList: [], cues: {}, words: [] };
  const meta = A.meta || {};
  const duration = Number.isFinite(meta.duration) ? meta.duration : 10;
  const cueList = A.cueList || [];
  const cueMap = A.cues || Object.fromEntries(cueList.map((c) => [c.id, c]));
  const words = A.words || [];
  const render = new URLSearchParams(location.search).has('render');

  let t = 0;            // the clock
  let booted = false;
  const frameFns = [];  // P.onFrame callbacks
  const waits = [];     // promises boot must wait for
  const timelines = []; // GSAP timelines made by P.timeline()
  const chars = {};     // loaded workshop characters, keyed id:variant
  const missing = new Set();  // cue ids that were asked for but do not exist

  // ---------------------------------------------------------------- maths
  const clamp = (v, lo = 0, hi = 1) => (v > lo ? (v < hi ? v : hi) : lo);   // NaN becomes lo
  const lerp = (a, b, p) => a + (b - a) * p;
  const floorDur = (d) => Math.max(d, 1e-6);

  // CSS cubic-bezier(): solve x -> parameter with Newton steps, bisection as a safety net.
  function bezier(x1, y1, x2, y2) {
    const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
    const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
    const X = (s) => ((ax * s + bx) * s + cx) * s;
    const Y = (s) => ((ay * s + by) * s + cy) * s;
    const dX = (s) => (3 * ax * s + 2 * bx) * s + cx;
    return (x) => {
      if (!(x > 0)) return 0;
      if (x >= 1) return 1;
      let s = x;
      for (let i = 0; i < 8; i++) {
        const err = X(s) - x;
        if (Math.abs(err) < 1e-7) return Y(s);
        const d = dX(s);
        if (Math.abs(d) < 1e-6) break;
        s -= err / d;
      }
      let lo = 0, hi = 1;
      s = x;
      for (let i = 0; i < 48; i++) {
        const err = X(s) - x;
        if (Math.abs(err) < 1e-7) break;
        if (err > 0) hi = s; else lo = s;
        s = (lo + hi) / 2;
      }
      return Y(s);
    };
  }

  // Every ease returns 0 at x <= 0 and 1 at x >= 1.
  const guard = (f) => (x) => (!(x > 0) ? 0 : x >= 1 ? 1 : f(x));
  // Measured eases: an exponential snap with overshoot, power-out, expo-out, power-in.
  function snapOver(amp, rise, settle) {
    const raw = (x) => (1 + amp * Math.exp(-x / settle)) * (1 - Math.exp(-x / rise));
    const top = raw(1);
    return (x) => raw(x) / top;
  }
  function expoOut(k) {
    const top = 1 - Math.exp(-k);
    return (x) => (1 - Math.exp(-k * x)) / top;
  }
  const ease = {
    linear: guard((x) => x),
    in: guard((x) => x * x * x),
    out: guard((x) => 1 - Math.pow(1 - x, 3)),
    inOut: guard((x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2)),
    outQuart: guard((x) => 1 - Math.pow(1 - x, 4)),
    outExpo: guard((x) => 1 - Math.pow(2, -10 * x)),
    back: guard((x) => 1 + 2.4 * Math.pow(x - 1, 3) + 1.4 * Math.pow(x - 1, 2)),   // overshoot constant 1.4
    sine: guard((x) => -(Math.cos(Math.PI * x) - 1) / 2),
    enter: bezier(0.16, 1, 0.3, 1),
    exit: bezier(0.7, 0, 0.84, 0),
    move: bezier(0.65, 0, 0.35, 1),
    pop: bezier(0.34, 1.56, 0.64, 1),
    crashIn: guard(snapOver(2.0, 0.19, 0.218)),
    whip: guard((x) => 1 - Math.pow(1 - x, 2.52)),
    softLand: guard(expoOut(3.41)),
    accelExit: guard((x) => Math.pow(x, 2.6)),
  };

  // Damped spring, closed form. The envelope decays like exp(-6.5 s / dur), so it is settled at about dur.
  function spring({ dur = 0.5, bounce = 0 } = {}) {
    const sigma = 6.5 / floorDur(dur);
    const zeta = clamp(1 - bounce, 0.05, 1);
    if (zeta >= 1) return (s) => (s <= 0 ? 0 : 1 - (1 + sigma * s) * Math.exp(-sigma * s));
    const wd = (sigma / zeta) * Math.sqrt(1 - zeta * zeta), k = sigma / wd;
    return (s) => (s <= 0 ? 0 : 1 - Math.exp(-sigma * s) * (Math.cos(wd * s) + k * Math.sin(wd * s)));
  }

  // Value starts at keys[0][1]; each later key adds its step, sprung in at its own time.
  function track(keys, opts, time = t) {
    if (!keys || !keys.length) return 0;
    const sp = spring(opts);
    let v = keys[0][1];
    for (let i = 1; i < keys.length; i++) v += (keys[i][1] - keys[i - 1][1]) * sp(time - keys[i][0]);
    return v;
  }

  const zoom = (a, b, p) => Math.exp(lerp(Math.log(a), Math.log(b), p));
  const beat = (n, bpm) => (n * 60) / bpm;
  const step = (fps = 12, time = t) => Math.floor(time * fps + 1e-9) / fps;

  // Seeded PRNG (mulberry32): same seed, same sequence, values in [0, 1).
  function rand(seed) {
    let s = typeof seed === 'string' ? [...seed].reduce((h, ch) => Math.imul(h ^ ch.charCodeAt(0), 16777619), 2166136261) : seed;
    s >>>= 0;
    return () => {
      s = (s + 0x6d2b79f5) >>> 0;
      let x = Math.imul(s ^ (s >>> 15), s | 1);
      x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
      return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
    };
  }

  // Strict check of SVG path data (the browser would quietly accept a broken tail, we do not).
  const PATH_ARITY = { m: 2, l: 2, h: 1, v: 1, c: 6, s: 4, q: 4, t: 2, a: 7, z: 0 };
  function pathIsValid(d) {
    const NUM = /[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?/y;
    let i = 0, first = true;
    const skip = () => { while (i < d.length && /\s/.test(d[i])) i++; };
    const comma = () => { skip(); if (d[i] === ',') i++; };
    const number = (flag) => {
      skip();
      if (flag) { if (d[i] === '0' || d[i] === '1') { i++; return true; } return false; }
      NUM.lastIndex = i;
      if (!NUM.exec(d)) return false;
      i = NUM.lastIndex;
      return true;
    };
    skip();
    if (i >= d.length) return false;
    while (i < d.length) {
      const cmd = d[i].toLowerCase(), arity = PATH_ARITY[cmd];
      if (arity === undefined || (first && cmd !== 'm')) return false;
      first = false;
      i++;
      skip();
      if (arity === 0) continue;
      let groups = 0;
      for (;;) {
        skip();
        if (groups > 0 && (i >= d.length || /[A-Za-z]/.test(d[i]))) break;
        for (let a = 0; a < arity; a++) {
          if (a > 0) comma();
          if (!number(cmd === 'a' && (a === 3 || a === 4))) return false;
        }
        groups++;
        comma();
      }
    }
    return true;
  }
  function path(d) {
    if (typeof d !== 'string' || !pathIsValid(d)) throw new TypeError('P.path: invalid SVG path data');
    const el = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    el.setAttribute('d', d);
    const len = el.getTotalLength();
    if (!(len > 0)) throw new TypeError('P.path: the path has zero length');
    const eps = len / 1000;
    return (progress) => {
      if (typeof progress !== 'number' || Number.isNaN(progress)) throw new TypeError('P.path: progress must be a number');
      const s = clamp(progress) * len;
      const p = el.getPointAtLength(s);
      const a = el.getPointAtLength(Math.max(0, s - eps)), b = el.getPointAtLength(Math.min(len, s + eps));
      return { x: p.x, y: p.y, angle: Math.atan2(b.y - a.y, b.x - a.x) };
    };
  }

  // ---------------------------------------------------------------- cues
  const NO_CUE = Object.freeze({ id: '', start: Infinity, end: Infinity, phraseEnd: Infinity, text: '', note: '' });
  function cue(id) {
    if (typeof id === 'number') return { id: String(id), start: id, end: duration, phraseEnd: id, text: '', note: '' };
    if (typeof id === 'string' && Object.hasOwn(cueMap, id)) return cueMap[id];
    const key = String(id);
    if (!missing.has(key)) { missing.add(key); console.warn('[anim] no cue "' + key + '" in cues.json'); }
    return NO_CUE;
  }
  // End of a cue's window: cue end, a time in seconds, or the start of another cue.
  function endOf(c, until) {
    if (typeof until === 'number') return until;
    if (typeof until === 'string') return cue(until).start;
    return c.end;
  }
  function prog(id, { dur, delay = 0, ease: fn = ease.out } = {}) {
    const c = cue(id);
    const len = dur ?? (Number.isFinite(c.end - c.start) ? c.end - c.start : 1);
    return fn(clamp((t - c.start - delay) / floorDur(len)));
  }
  function fade(id, { in: rise = 0.4, out: fall = 0.3, until, delay = 0 } = {}) {
    const c = cue(id), start = c.start + delay, end = endOf(c, until);
    return ease.out(clamp((t - start) / floorDur(rise))) * ease.out(clamp((end - t) / floorDur(fall)));
  }
  const live = (id, until) => { const c = cue(id); return t >= c.start && t < endOf(c, until); };
  const past = (id) => t >= cue(id).start;
  function pick(map, fallback) {
    let hit;
    for (const c of cueList) if (c.start <= t && Object.hasOwn(map, c.id)) hit = c;
    return hit ? map[hit.id] : fallback;
  }
  const since = (t0, dur) => clamp((t - t0) / floorDur(dur));

  // ---------------------------------------------------------------- words, captions, voice level
  const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9$%]/g, '');
  function at(word, after = 0) {
    const from = (typeof after === 'string' ? cue(after).start : after) - 0.05;
    const want = norm(word);
    for (const w of words) if (w.start >= from && norm(w.text).startsWith(want)) return w.start;
    return Infinity;
  }
  function wordAt(time = t) {
    let lo = 0, hi = words.length - 1, found = -1;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      if (words[mid].start <= time) { found = mid; lo = mid + 1; } else hi = mid - 1;
    }
    return found;
  }
  // Caption lines are built once, on first use.
  let lines = null, lineOf = null;
  function buildLines() {
    lines = []; lineOf = [];
    let cur = [];
    words.forEach((w, i) => {
      cur.push(w);
      lineOf[i] = lines.length;
      const next = words[i + 1];
      const stop = /[.?!,]$/.test(String(w.text).trim());
      if (!next || (stop && cur.length >= 3) || next.start - w.end > 0.6 || cur.length >= 7) {
        lines.push({ words: cur, first: i - cur.length + 1 });
        cur = [];
      }
    });
  }
  function line(time = t) {
    const i = wordAt(time);
    if (i < 0) return null;
    if (!lines) buildLines();
    const ln = lines[lineOf[i]];
    if (time > ln.words[ln.words.length - 1].end + 0.5) return null;
    return { words: ln.words, active: i - ln.first };
  }
  // Returns a function that paints the caption line for a time into el. It touches the DOM only on a change.
  function captionPainter(el) {
    let shown = null, shownActive = -2;
    return (time) => {
      const ln = line(time);
      const w = ln ? ln.words : null, a = ln ? ln.active : -1;
      if (w === shown && a === shownActive) return;
      shown = w; shownActive = a;
      el.textContent = '';
      if (!ln) return;
      ln.words.forEach((word, i) => {
        if (i) el.appendChild(document.createTextNode(' '));
        const span = document.createElement('span');
        span.className = i < a ? 'said' : i === a ? 'now' : 'next';
        span.textContent = word.text;
        el.appendChild(span);
      });
    };
  }
  function level(time = t) {
    const L = A.levels;
    if (!L || !L.data || !L.data.length || !(L.rate > 0) || time < 0) return 0;
    const x = time * L.rate, n = L.data.length;
    if (x >= n - 1) return clamp(L.data[n - 1] / 100);
    const i = Math.floor(x);
    return clamp(lerp(L.data[i], L.data[i + 1], x - i) / 100);
  }

  // ---------------------------------------------------------------- the frame
  const cueEls = [];       // [data-cue] elements: { el, id, offset, until }
  const tracked = new Set(); // every Animation seen. A finished one drops out of getAnimations(); we keep it so a scrub back works.
  let gsapT = 0;            // the time GSAP was last drawn at, to tell a jump back from a step forward
  const isBarAnimation = (a) => { const el = a.effect && a.effect.target; return !!(el && el.closest && el.closest('#vf-bar')); };

  function drawFrame() {
    for (const e of cueEls) {
      const c = cue(e.id), start = c.start + e.offset, end = e.until ? cue(e.until).start : c.end;
      const state = t < start ? 'before' : t < end ? 'live' : 'after';
      if (e.el.getAttribute('data-state') !== state) e.el.setAttribute('data-state', state);
    }

    for (const a of document.getAnimations()) if (!isBarAnimation(a)) tracked.add(a);
    for (const a of tracked) {
      if (a.playState === 'idle') { tracked.delete(a); continue; }   // cancelled
      if (a.playState === 'running') a.pause();
      a.currentTime = t * 1000;
    }

    if (window.gsap) {
      // Forward: timelines in the order they were made. Backward: the reverse order, so a later timeline puts back
      // its start values first and an earlier entrance (data-in) can then hide its element again.
      const all = [...new Set([...timelines, ...Object.values(window.__timelines || {})])];
      if (t < gsapT) all.reverse();
      gsapT = t;
      for (const tl of all) {
        if (!tl || typeof tl.totalTime !== 'function') continue;
        if (typeof tl.paused === 'function' && !tl.paused()) tl.pause();
        tl.totalTime(t, true);   // true: do not fire callbacks while jumping
      }
    }

    // Frame callbacks run last, so they can read values that CSS and GSAP just set.
    for (let i = 0; i < frameFns.length; i++) frameFns[i](t);
  }

  // CSS keyframes must start paused, or a short animation can finish before the first frame is drawn.
  const hold = document.createElement('style');
  hold.textContent = '*,*::before,*::after{animation-play-state:paused !important}';
  (document.head || document.documentElement).appendChild(hold);

  // Shift animation-delay of a [data-cue] element and its own descendants by the cue start (+ offset).
  function wireCues() {
    for (const el of document.querySelectorAll('[data-cue]')) {
      const id = el.getAttribute('data-cue');
      const entry = { el, id, offset: parseFloat(el.getAttribute('data-cue-offset')) || 0, until: el.getAttribute('data-until') };
      cueEls.push(entry);
      if (!Object.hasOwn(cueMap, id)) continue;
      const shift = cueMap[id].start + entry.offset;
      for (const node of [el, ...el.querySelectorAll('*')]) {
        if (node.closest('[data-cue]') !== el) continue;
        const cs = getComputedStyle(node);
        if (cs.animationName === 'none') continue;
        node.style.animationDelay = cs.animationDelay.split(',').map((d) => {
          const v = parseFloat(d);
          return (/ms\s*$/.test(d) ? v / 1000 : v) + shift + 's';
        }).join(', ');
      }
    }
  }

  // ---------------------------------------------------------------- lifecycle API
  function onFrame(fn) {
    frameFns.push(fn);
    if (booted) fn(t);
  }
  function wait(promise) {
    Promise.resolve(promise).catch(() => {});   // boot reports the failure; this stops a stray unhandled-rejection report
    waits.push(Promise.resolve(promise));
    return promise;
  }
  // Resolves when the image has loaded. If src is given and the image has none yet, it is set (after listeners are on).
  function loaded(img, src) {
    return new Promise((resolve) => {
      const name = () => src || img.currentSrc || img.getAttribute('src') || '';
      if (src && !img.getAttribute('src')) img.src = src;   // set first: a new Image() reports complete
      const fail = () => { console.error('[anim] image failed to load: ' + name()); resolve(); };
      if (img.complete && (img.naturalWidth || !(src || img.getAttribute('src')))) return resolve();
      if (img.complete) return fail();
      img.addEventListener('load', () => resolve(), { once: true });
      img.addEventListener('error', fail, { once: true });
    });
  }
  function timeline(vars) {
    if (!window.gsap) throw new Error('P.timeline needs GSAP. Load _runtime/vendor/gsap.min.js before player.js.');
    const tl = window.gsap.timeline({ paused: true, ...vars });
    timelines.push(tl);
    return tl;
  }
  function drawCharacter(ctx, o = {}) {
    const ch = chars[o.id + ':' + o.variant];
    if (!ch) return { available: false, reason: 'character' };
    const time = o.time ?? t;
    const latest = (map) => {
      let hit = null;
      if (map) for (const c of cueList) if (c.start <= time && Object.hasOwn(map, c.id)) hit = c;
      return hit;
    };
    const a = latest(o.actions), e = latest(o.expressions), p = latest(o.props);
    return ch.draw(ctx, time - (a ? a.start : 0), {
      action: a ? o.actions[a.id] : (o.action || 'idle'),
      view: o.view || 'front',
      expression: e ? o.expressions[e.id] : o.expression,
      prop: p ? o.props[p.id] : o.prop,
      speechLevel: o.speechLevel ?? level(time),
    });
  }
  async function loadCharacters() {
    const list = A.creative && A.creative.characters;
    if (!list || !list.length) return;
    await new Promise((ok, bad) => {
      const s = document.createElement('script');
      s.src = '../creative/character.js';
      s.onload = ok;
      s.onerror = () => bad(new Error('could not load ../creative/character.js'));
      document.head.appendChild(s);
    });
    for (const c of list) {
      try { chars[c.id + ':' + c.variant] = await window.Character.load(c.manifest); }
      catch (error) { throw new Error('character ' + c.id + ':' + c.variant + ' failed: ' + (error && error.message || error)); }
    }
  }

  // ---------------------------------------------------------------- public API
  const P = window.P = {
    words, cues: cueList,
    cue, prog, fade, live, past, pick, since, at,
    clamp, lerp, bezier, ease, spring, track, zoom, rand, beat, path, step,
    wordAt, line, level,
    captions(el) { onFrame(captionPainter(el)); },
    onFrame, wait, loaded, timeline, drawCharacter,
  };
  Object.defineProperties(P, {
    t: { get: () => t, enumerable: true },
    duration: { get: () => duration, enumerable: true },
    render: { get: () => render, enumerable: true },
  });

  // ---------------------------------------------------------------- boot
  // Give the stage its frame size now, so a scene script that measures the page (fx parts, scene.js) sees the real
  // frame instead of an empty div; boot() sets it again with the preview scale.
  const early = document.getElementById('stage');
  if (early) Object.assign(early.style, { position: 'absolute', overflow: 'hidden', width: (+early.dataset.width || 1920) + 'px',
    height: (+early.dataset.height || 1080) + 'px', transformOrigin: '0 0' });
  window.addEventListener('load', boot);

  async function boot() {
    const stage = document.getElementById('stage');
    if (!stage) {
      const msg = 'index.html needs <div id="stage">';
      document.body.textContent = msg;
      document.body.style.cssText = 'margin:0;padding:24px;background:#3a0a0a;color:#ff6b6b;font:20px monospace';
      window.__assetError = msg;
      return;
    }
    for (const el of [document.documentElement, document.body]) Object.assign(el.style, { margin: '0', padding: '0', overflow: 'hidden', background: '#0f0f10' });

    const W = +stage.dataset.width || 1920, H = +stage.dataset.height || 1080;
    Object.assign(stage.style, { position: 'absolute', overflow: 'hidden', width: W + 'px', height: H + 'px', transformOrigin: '0 0' });
    let barHeight = 64;
    const fit = () => {
      if (render) { Object.assign(stage.style, { left: '0px', top: '0px', transform: 'none' }); return; }
      const aw = window.innerWidth, ah = Math.max(1, window.innerHeight - barHeight);
      const k = Math.max(0.01, Math.min(aw / W, ah / H));
      Object.assign(stage.style, { transform: 'scale(' + k + ')', left: (aw - W * k) / 2 + 'px', top: (ah - H * k) / 2 + 'px' });
    };
    fit();
    if (!render) window.addEventListener('resize', fit);

    try {
      wait(loadCharacters());
      await document.fonts.ready;
      for (const img of document.images) wait(loaded(img));
      let seen;
      do { seen = waits.length; await Promise.all(waits.slice()); } while (waits.length > seen);
      wireCues();
      if (render) {
        window.__size = { w: W, h: H };
        window.__seek = (time) => {
          if (!Number.isFinite(time)) throw new TypeError('__seek needs a finite number of seconds');
          t = time;
          drawFrame();
          return new Promise((resolve) => requestAnimationFrame(() => resolve()));
        };
        drawFrame();
        booted = true;
        window.__ready = true;
      } else {
        startPreview({ fit, setBar: (h) => { barHeight = h; fit(); } });
      }
    } catch (error) {
      window.__assetError = String(error);
      console.error(error);
      if (!render) {
        const box = document.createElement('pre');
        box.textContent = String(error && error.stack || error);
        box.style.cssText = 'position:absolute;inset:0;margin:0;padding:48px;box-sizing:border-box;overflow:auto;white-space:pre-wrap;' +
          'background:#2a0d0d;color:#ffb4b4;font:22px/1.4 monospace;z-index:99999';
        stage.appendChild(box);
      }
    }
  }

  // ---------------------------------------------------------------- preview bar
  const BAR_CSS = `
#vf-bar{position:fixed;left:0;right:0;bottom:0;height:64px;box-sizing:border-box;padding:6px 14px;background:#17171a;color:#d8d8dc;
  border-top:1px solid #2c2c32;font:13px/1.2 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;display:grid;
  grid-template-columns:auto auto 1fr auto;grid-template-rows:26px 24px;column-gap:14px;align-items:center;z-index:2147483000;user-select:none}
#vf-bar button{font:inherit;color:#fff;background:#2c2c34;border:1px solid #44444e;border-radius:4px;width:40px;height:24px;cursor:pointer;padding:0}
#vf-bar button:hover{background:#3a3a44}
#vf-bar .vf-track{position:relative;height:26px;cursor:pointer;touch-action:none}
#vf-bar .vf-rail{position:absolute;left:0;right:0;top:11px;height:4px;background:#2c2c32;border-radius:2px}
#vf-bar .vf-fill{position:absolute;left:0;top:11px;height:4px;width:0;background:#e9b44c;border-radius:2px}
#vf-bar .vf-tick{position:absolute;top:0;bottom:0;width:9px;margin-left:-4px;cursor:pointer}
#vf-bar .vf-tick::before{content:'';position:absolute;left:4px;top:5px;bottom:5px;width:1px;background:#8a8a96}
#vf-bar .vf-tick:hover::before{background:#fff;width:2px}
#vf-bar .vf-cue{max-width:36ch;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#e9b44c}
#vf-bar .vf-cap{grid-column:1 / -1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#8f8f9a}
#vf-bar .vf-cap .said,#vf-bar .vf-cap .next{color:#8f8f9a}
#vf-bar .vf-cap .now{color:#fff;font-weight:700}`;

  function startPreview({ setBar }) {
    const slug = meta.slug || location.pathname;
    const posKey = 'vf-pos:' + slug;
    let playing = false, wallBase = 0, barOn = true, lastSave = 0, lastSaved = -1, lastLabel = null;
    let audio = null, audioOK = false;

    // --- build the bar
    const css = document.createElement('style');
    css.textContent = BAR_CSS;
    document.head.appendChild(css);
    const bar = document.createElement('div');
    bar.id = 'vf-bar';
    const mk = (tag, cls, parent) => { const e = document.createElement(tag); if (cls) e.className = cls; parent.appendChild(e); return e; };
    const btn = mk('button', '', bar);
    const clock = mk('span', 'vf-time', bar);
    const track = mk('div', 'vf-track', bar);
    mk('div', 'vf-rail', track);
    const fill = mk('div', 'vf-fill', track);
    const cueLabel = mk('span', 'vf-cue', bar);
    const cap = mk('div', 'vf-cap', bar);
    for (const c of cueList) {
      if (!Number.isFinite(c.start)) continue;
      const tick = mk('i', 'vf-tick', track);
      tick.style.left = (duration > 0 ? 100 * c.start / duration : 0) + '%';
      tick.dataset.start = c.start;
      tick.title = c.id + '  ' + c.start.toFixed(2) + 's  ' + (c.text || '');
    }
    document.body.appendChild(bar);
    const paintCaption = captionPainter(cap);

    // --- voice
    if (meta.voice) {
      audio = new Audio(meta.voice);
      audio.preload = 'auto';
      audioOK = true;
      const drop = () => { audioOK = false; wallBase = performance.now() - t * 1000; };   // fall back to the wall clock
      audio.addEventListener('error', drop);
      audio.addEventListener('ended', drop);
    }

    // --- clock control
    const mmss = (s) => {
      const cs = Math.round(Math.max(0, s) * 100), sec = (cs % 6000) / 100;
      return String(Math.floor(cs / 6000)).padStart(2, '0') + ':' + (sec < 10 ? '0' : '') + sec.toFixed(2);
    };
    function savePosition(force) {
      const now = performance.now();
      if (!force && (now - lastSave < 500 || t === lastSaved)) return;
      lastSave = now; lastSaved = t;
      try { localStorage.setItem(posKey, String(t)); } catch (_) { /* storage can be blocked */ }
    }
    function refresh() {
      clock.textContent = mmss(t) + ' / ' + mmss(duration);
      fill.style.width = (duration > 0 ? 100 * t / duration : 0) + '%';
      btn.textContent = playing ? '❚❚' : '▶';
      let now = null;
      for (const c of cueList) if (c.start <= t) now = c;
      const label = (missing.size ? 'missing: ' + [...missing].join(', ') + ' | ' : '') + (now ? now.id : '-');
      if (label !== lastLabel) { lastLabel = label; cueLabel.textContent = label; }
      paintCaption(t);
      savePosition(false);
    }
    const reported = new Set();
    function redraw() {
      try { drawFrame(); } catch (error) {
        if (!reported.has(String(error))) { reported.add(String(error)); console.error(error); }
      }
      refresh();
    }
    function seekTo(time) {
      t = clamp(time, 0, duration);
      if (audio && audioOK) { try { audio.currentTime = t; } catch (_) { /* not seekable yet */ } }
      wallBase = performance.now() - t * 1000;
      redraw();
    }
    function play() {
      if (t >= duration - 0.01) seekTo(0);
      playing = true;
      wallBase = performance.now() - t * 1000;
      if (audio && audioOK) {
        audio.currentTime = t;
        audio.play().catch(() => { audioOK = false; wallBase = performance.now() - t * 1000; });
      }
      refresh();
    }
    function pause() {
      playing = false;
      if (audio) audio.pause();
      refresh();
    }
    function frame(now) {
      requestAnimationFrame(frame);
      if (!playing) return;
      t = audio && audioOK ? audio.currentTime : (now - wallBase) / 1000;
      if (t >= duration) { t = duration; pause(); }
      redraw();
    }

    // --- input
    btn.addEventListener('click', () => { (playing ? pause : play)(); btn.blur(); });
    const seekFromPointer = (e) => {
      const r = track.getBoundingClientRect();
      seekTo(duration * clamp((e.clientX - r.left) / Math.max(1, r.width)));
    };
    track.addEventListener('pointerdown', (e) => {
      if (e.target.classList.contains('vf-tick')) { seekTo(+e.target.dataset.start); return; }
      track.setPointerCapture(e.pointerId);
      seekFromPointer(e);
    });
    track.addEventListener('pointermove', (e) => { if (track.hasPointerCapture(e.pointerId)) seekFromPointer(e); });
    const starts = cueList.map((c) => c.start).filter(Number.isFinite).sort((a, b) => a - b);
    window.addEventListener('keydown', (e) => {
      const el = e.target;
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName))) return;
      const big = e.shiftKey ? 1 : 0.1;
      let handled = true;
      switch (e.key) {
        case ' ': (playing ? pause : play)(); break;
        case 'ArrowLeft': seekTo(t - big); break;
        case 'ArrowRight': seekTo(t + big); break;
        case ',': seekTo(t - 1 / 30); break;
        case '.': seekTo(t + 1 / 30); break;
        case '[': seekTo([...starts].reverse().find((s) => s < t - 0.05) ?? 0); break;
        case ']': { const next = starts.find((s) => s > t + 0.001); if (next !== undefined) seekTo(next); break; }
        case '0': case 'Home': seekTo(0); break;
        case 'h': barOn = !barOn; bar.style.display = barOn ? '' : 'none'; setBar(barOn ? 64 : 0); break;
        default: handled = false;
      }
      if (handled) e.preventDefault();
    });
    window.addEventListener('pagehide', () => savePosition(true));

    // --- live reload when a script changes on the Studio server
    if (/^https?:$/.test(location.protocol)) {
      const urls = [...document.scripts].map((s) => s.src).filter((u) => u && new URL(u).origin === location.origin);
      const stamps = new Map();
      let busy = false;
      setInterval(async () => {
        if (busy) return;
        busy = true;
        try {
          for (const u of urls) {
            const res = await fetch(u, { method: 'HEAD', cache: 'no-store' });
            const stamp = res.headers.get('Last-Modified');
            if (stamps.has(u) && stamps.get(u) !== stamp) { savePosition(true); location.reload(); return; }
            stamps.set(u, stamp);
          }
        } catch (_) { /* server busy or offline: try again next second */ } finally { busy = false; }
      }, 1000);
    }

    // --- start
    booted = true;
    let start = 0;
    try { start = parseFloat(localStorage.getItem(posKey)) || 0; } catch (_) { /* storage can be blocked */ }
    seekTo(start >= 0 && start <= duration ? start : 0);
    requestAnimationFrame(frame);
  }
})();
