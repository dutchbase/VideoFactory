// animicon.js - animated icons that play on a GSAP timeline you pass in. Nothing here runs by itself.
// Animations converted from lucide-animated (MIT), drawings Lucide (ISC). Specs: library/icons-animated/ (tools/iconanim).
//
//   AnimIcon.mount(el, name)                       put the inline SVG into el; it takes the text colour
//   AnimIcon.play(tl, el, name, at, { loop, gap, speed, until })
//                                                  icon goes normal -> animate at `at` seconds, on tl only
//     loop   true (or 1): repeat until `until`; a number N >= 2: N runs in all. Default: one run, final pose is kept.
//     gap    seconds of rest between two runs (default 0.4), after the icon went back to normal
//     speed  2 = twice as fast (default 1)
//     until  last second a repeat may start (default: the film length P.duration, else 10 s after `at`)
//   AnimIcon.has(name)                             true when the icon's wrapper script is loaded
//
// Load order: gsap.min.js, animicon.js, the icon wrappers (assets/icons-animated/<set>/<name>.js), then the scene.
// Modern kit: <i data-icon="lucide-animated/bell" data-play="@bell" data-loop="1"></i> (modern.js calls this file).
// HyperFrames:  AnimIcon.mount(el, 'lucide-animated/bell'); AnimIcon.play(tl, el, 'lucide-animated/bell', cue('x'))
//
// Both engines jump the playhead with callbacks off (tl.totalTime(t, true)), also backwards. So every value comes from a
// tween that continues from the value before it, plus zero-length jumps where a keyframe starts elsewhere. No timers, no clock, no randomness.
(() => {
  if (!window.gsap) throw new Error('animicon.js: load runtime/vendor/gsap.min.js first.');
  const gsap = window.gsap;
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));

  // ---- eases, as in motion: p (0..1) -> value ----
  function bezier(x1, y1, x2, y2) {
    if (x1 === y1 && x2 === y2) return (p) => p;
    const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
    const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
    const X = (s) => ((ax * s + bx) * s + cx) * s, Y = (s) => ((ay * s + by) * s + cy) * s;
    const dX = (s) => (3 * ax * s + 2 * bx) * s + cx;
    return (p) => {
      if (p <= 0) return 0; if (p >= 1) return 1;
      let s = p;
      for (let i = 0; i < 8; i++) { const e = X(s) - p, d = dX(s); if (Math.abs(e) < 1e-6) return Y(s); if (Math.abs(d) < 1e-6) break; s -= e / d; }
      let lo = 0, hi = 1; s = p;   // Newton failed: bisection
      for (let i = 0; i < 40; i++) { const e = X(s) - p; if (Math.abs(e) < 1e-6) break; if (e > 0) hi = s; else lo = s; s = (lo + hi) / 2; }
      return Y(s);
    };
  }
  const reverse = (f) => (p) => 1 - f(1 - p);
  const mirror = (f) => (p) => (p <= 0.5 ? f(2 * p) / 2 : (2 - f(2 * (1 - p))) / 2);
  const circIn = (p) => 1 - Math.sin(Math.acos(clamp(p)));
  const backOut = bezier(0.33, 1.53, 0.69, 0.99), backIn = reverse(backOut);
  const NAMED = {
    linear: (p) => p,
    easeIn: bezier(0.42, 0, 1, 1), easeOut: bezier(0, 0, 0.58, 1), easeInOut: bezier(0.42, 0, 0.58, 1),
    circIn, circOut: reverse(circIn), circInOut: mirror(circIn),
    backIn, backOut, backInOut: mirror(backIn),
    anticipate: (p) => ((p *= 2) < 1 ? 0.5 * backIn(p) : 0.5 * (2 - Math.pow(2, -10 * (p - 1)))),
  };

  // Damped spring, closed form (same family as P.spring in player.js); s = seconds, ends at rest value 1.
  function springEase(k, c, m, dur) {
    const w0 = Math.sqrt(k / m), z = c / (2 * Math.sqrt(k * m));
    let f;
    if (z < 1) { const wd = w0 * Math.sqrt(1 - z * z); f = (s) => 1 - Math.exp(-z * w0 * s) * (Math.cos(wd * s) + (z * w0 / wd) * Math.sin(wd * s)); }
    else if (z === 1) f = (s) => 1 - Math.exp(-w0 * s) * (1 + w0 * s);
    else { const q = w0 * Math.sqrt(z * z - 1), r1 = -z * w0 + q, r2 = -z * w0 - q; f = (s) => 1 - (r2 * Math.exp(r1 * s) - r1 * Math.exp(r2 * s)) / (r2 - r1); }
    return (p) => (p <= 0 ? 0 : p >= 1 ? 1 : f(p * dur));
  }

  const easeOf = (v) => (Array.isArray(v) ? bezier(v[0], v[1], v[2], v[3]) : NAMED[v] || NAMED.easeInOut);
  function trackEase(tr, seg) {
    if (tr.spring) return springEase(tr.spring[0], tr.spring[1], tr.spring[2], tr.duration);
    const e = tr.ease;
    if (Array.isArray(e) && !e.every((x) => typeof x === 'number')) return easeOf(e[Math.min(seg, e.length - 1)]);   // one ease per segment
    return easeOf(e);
  }

  // ---- spec value -> GSAP vars ----
  const ATTR = { cx: 'cx', cy: 'cy', r: 'r', rx: 'rx', ry: 'ry', d: 'd', points: 'points', width: 'width', height: 'height', x1: 'x1', x2: 'x2', y1: 'y1', y2: 'y2', strokeWidth: 'stroke-width' };
  const ROOT_PX = 28;   // the icons were drawn for a 28 px box: root x / y are fractions of it, so they scale with the icon
  function put(out, prop, v, root) {
    if (prop === 'rotate') out.rotation = v;
    else if (prop === 'x' && root) out.xPercent = v / ROOT_PX * 100;
    else if (prop === 'y' && root) out.yPercent = v / ROOT_PX * 100;
    else if (prop === 'pathLength') out.strokeDasharray = v + ' 1';       // pathLength="1" on the element: dash = v, gap = 1
    else if (prop === 'pathOffset') out.strokeDashoffset = -v;
    else if (ATTR[prop]) (out.attr = out.attr || {})[ATTR[prop]] = v;
    else out[prop] = v;
    return out;
  }
  const varsOf = (props, root) => { const o = {}; for (const [k, v] of Object.entries(props)) put(o, k, v, root); return o; };

  // ---- mount ----
  function entry(name) {
    const e = (window.VF_ANIM_ICONS || {})[name];
    if (!e) throw new Error(`animicon.js: no animated icon "${name}". Load its wrapper script: assets/icons-animated/<set>/<name>.js`);
    return e;
  }
  function originVars(o, units) {
    if (o.box === 'view') {
      const n = (s) => { s = String(s); return s.endsWith('%') ? parseFloat(s) / 100 * units : parseFloat(s); };
      return { svgOrigin: n(o.x) + ' ' + n(o.y) };
    }
    return { transformOrigin: o.x + ' ' + o.y };
  }

  function mount(el, name) {
    const e = entry(name);
    if (el.__animIcon && el.__animIcon.name === name && el.__animIcon.svg.parentNode === el) return el.__animIcon.svg;
    el.innerHTML = e.svg;
    const svg = el.firstElementChild;
    svg.setAttribute('width', '100%'); svg.setAttribute('height', '100%'); svg.style.overflow = 'visible';
    const nodes = [svg, ...svg.querySelectorAll('*')], units = svg.viewBox.baseVal.width || 24;
    for (const s of e.spec.els) {
      const node = nodes[s.i];
      if (!node) throw new Error(`animicon.js: "${name}" element ${s.i} is missing`);
      const tracks = [...(s.start || []), ...(s.reset || [])];
      if (tracks.some((t) => 'pathLength' in t.props || 'pathOffset' in t.props)) node.setAttribute('pathLength', '1');
      const set = {};
      if (s.origin && s.i > 0) Object.assign(set, originVars(s.origin, units));
      if (s.base) Object.assign(set, varsOf(s.base, s.i === 0));
      if (Object.keys(set).length) gsap.set(node, set);
    }
    el.__animIcon = { name, svg, nodes };
    return svg;
  }

  // ---- play ----
  // GSAP keeps tweens consistent when they continue from the value the tween before left behind. So a track is: one
  // zero-length jump (only where the first keyframe is not the current value; it sits at the step start, before any delay,
  // and its "from" is what the icon showed before), then one .to() per keyframe segment, placed relative to `base` seconds.
  function addTrack(tl, node, root, tr, base, sp, cap) {
    const dur = Math.max(tr.duration / sp, 0.001), t0 = base + (tr.at + tr.delay) / sp;
    const rep = tr.repeat || 0, rdel = (tr.repeatDelay || 0) / sp;
    let cycles = rep === -1 ? Math.min(2000, Math.max(1, Math.ceil((cap - t0 + rdel) / (dur + rdel)))) : rep + 1;
    if (tr.pre) {
      const from = {}, to = {};
      for (const k of Object.keys(tr.pre)) { put(from, k, tr.pre[k], root); put(to, k, tr.props[k][0], root); }
      tl.fromTo(node, from, Object.assign(to, { duration: 0, immediateRender: false, overwrite: false, lazy: false }), base + tr.at / sp);
    }
    let host = tl, pos = t0;
    if (cycles > 1) { host = gsap.timeline({ repeat: cycles - 1, repeatDelay: rdel, yoyo: tr.repeatType === 'reverse' || tr.repeatType === 'mirror' }); tl.add(host, t0); pos = 0; }
    const groups = new Map();
    for (const [k, a] of Object.entries(tr.props)) { if (!groups.has(a.length)) groups.set(a.length, {}); groups.get(a.length)[k] = a; }
    for (const [n, props] of groups) {
      const times = tr.times && tr.times.length === n ? tr.times : Array.from({ length: n }, (_, i) => i / (n - 1));
      for (let j = 0; j < n - 1; j++) {
        const to = {};
        for (const [k, a] of Object.entries(props)) put(to, k, a[j + 1], root);
        host.to(node, Object.assign(to, {
          duration: Math.max((times[j + 1] - times[j]) * dur, 0.001), ease: trackEase(tr, j), overwrite: false, lazy: false,
        }), pos + times[j] * dur);
      }
    }
  }

  function play(tl, el, name, at = 0, o = {}) {
    if (!tl || typeof tl.fromTo !== 'function') throw new Error('animicon.js: play needs a GSAP timeline as the first argument.');
    mount(el, name);
    const { nodes } = el.__animIcon, spec = entry(name).spec;
    const sp = o.speed > 0 ? o.speed : 1, gap = o.gap == null ? 0.4 : o.gap;
    const film = window.P && Number.isFinite(window.P.duration) ? window.P.duration : at + 10;
    const cap = o.until == null ? film : o.until;
    const loop = o.loop === true || o.loop === 1 ? Infinity : o.loop >= 2 ? Math.floor(o.loop) : 1;
    const run = (key, t0) => { for (const s of spec.els) for (const tr of s[key] || []) addTrack(tl, nodes[s.i], s.i === 0, tr, t0, sp, cap); };
    let t = at;
    for (let k = 1; ; k++) {
      run('start', t);
      if (k >= loop || spec.dur == null) break;
      let next = t + spec.dur / sp;
      if (spec.rdur > 0) { run('reset', next); next += spec.rdur / sp; }
      next += gap;
      if (next >= cap) break;
      t = next;
    }
    return tl;
  }

  window.AnimIcon = { mount, play, has: (name) => !!(window.VF_ANIM_ICONS || {})[name] };
})();
