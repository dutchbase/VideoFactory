// modern.js - the Modern kit: brand tokens -> CSS variables, icons, captions, and entrance helpers on GSAP.
// Load after brand/tokens.js, gsap.min.js, cues/cues.js, player.js and icons.js; before scene.js.
// Guide with examples: _shared/modern.md.
//
//   <section class="vf-shot" data-cue="hook">                 shown while cue "hook" is live
//     <h1 class="vf-title" data-in="words">Make <em>videos</em></h1>   words rise in at the cue start
//     <p class="vf-sub" data-in="rise" data-delay="0.4">…</p>          0.4 s later
//   </section>
//
//   const tl = P.timeline();                                  // or use the helpers below in scene.js
//   Modern.in(tl, '#card', 'problem+0.2', 'pop');
//   Modern.count('#stat', 'money', 87, { suffix: '%' });
(() => {
  if (!window.P) throw new Error('modern.js: load runtime/player.js first.');
  const stage = document.getElementById('stage');
  const $ = (x, root = document) => typeof x === 'string' ? [...root.querySelectorAll(x)] : x instanceof Element ? [x] : [...x];

  // ---- brand: tokens.js -> CSS variables on :root ----
  const T = window.BrandTokens || {};
  const vars = { bg: T.bg, surface: T.surface, raised: T.raised, ink: T.ink, dim: T.dim, faint: T.faint, line: T.line,
    accent: T.accent || (T.ramp && T.ramp[3]), accent2: T.accent2, green: T.green, danger: T.danger,
    font: T.font, head: T.head, mono: T.mono, hand: T.hand, cream: T.bg,   // cream: the HyperFrames name of the page background
    'grad-a': T.grads && T.grads[0] && T.grads[0][0], 'grad-b': T.grads && T.grads[0] && T.grads[0][1] };
  for (const [k, v] of Object.entries(vars)) if (v) document.documentElement.style.setProperty('--' + k, v);
  if (stage) stage.dataset.format = (+stage.dataset.width || 1920) >= (+stage.dataset.height || 1080) ? 'wide' : 'tall';

  // ---- time: a cue id, "id+0.3", "id-0.2", "@word", "@word>id", or seconds ----
  function at(x) {
    if (typeof x === 'number') return x;
    const m = /^(.*?)([+-]\d*\.?\d+)?$/.exec(String(x).trim());
    const base = m[1], off = m[2] ? parseFloat(m[2]) : 0;
    if (base.startsWith('@')) {
      const [word, after] = base.slice(1).split('>');
      return P.at(word, after || 0) + off;
    }
    return P.cue(base).start + off;
  }

  // ---- icons: <i data-icon="rocket"></i> -> inline SVG that takes the text colour ----
  // <i data-icon="lucide-animated/bell" data-play="@bell" data-loop="1"> is an animated icon (runtime/animicon.js): it
  // plays at data-play (any time form; empty = the shot start). Optional: data-loop (1 = repeat, N = N runs), data-gap, data-speed.
  function icons(root = document) {
    const set = window.VF_ICONS || {}, moving = window.VF_ANIM_ICONS || {};
    for (const el of root.querySelectorAll('[data-icon]')) {
      const name = el.dataset.icon;
      if (moving[name]) {
        if (!window.AnimIcon) { console.warn('[anim] animated icon needs runtime/animicon.js before runtime/modern.js'); continue; }
        el.classList.add('vf-icon'); window.AnimIcon.mount(el, name);
        if (el.dataset.play != null) {
          const lp = el.dataset.loop, o = {};
          if (lp != null && lp !== 'false' && lp !== '0') o.loop = lp === '' || lp === 'true' || lp === '1' ? true : +lp;
          if (el.dataset.gap != null) o.gap = +el.dataset.gap;
          if (el.dataset.speed != null) o.speed = +el.dataset.speed;
          auto = auto || P.timeline();
          window.AnimIcon.play(auto, el, name, el.dataset.play ? at(el.dataset.play) + (+el.dataset.delay || 0) : whenOf(el), o);
        }
        el.removeAttribute('data-icon'); continue;
      }
      const svg = set[name];
      if (!svg) { console.warn(`[anim] no icon "${name}". Run: python anim.py lib find ${name}`); continue; }
      el.classList.add('vf-icon'); el.innerHTML = svg; el.removeAttribute('data-icon');
    }
  }

  // ---- split text into word or letter spans, keeping inline tags such as <em> ----
  function split(target, by = 'words') {
    const out = [];
    for (const el of $(target)) {
      if (el.dataset.split) { out.push(...el.querySelectorAll('.vf-split-w, .vf-split-c')); continue; }
      el.dataset.split = by;
      const walk = (node) => {
        for (const child of [...node.childNodes]) {
          if (child.nodeType === 1) { walk(child); continue; }
          if (child.nodeType !== 3 || !child.data.trim()) continue;
          const frag = document.createDocumentFragment();
          for (const part of child.data.split(/(\s+)/)) {
            if (!part) continue;
            if (/^\s+$/.test(part)) { frag.append(' '); continue; }
            const w = document.createElement('span'); w.className = 'vf-split-w';
            if (by === 'chars') for (const ch of part) { const c = document.createElement('span'); c.className = 'vf-split-c'; c.textContent = ch; w.append(c); out.push(c); }
            else { w.textContent = part; out.push(w); }
            frag.append(w);
          }
          child.replaceWith(frag);
        }
      };
      walk(el);
    }
    return out;
  }

  // ---- entrances and exits on a GSAP timeline (time = at(x)) ----
  const E = P.ease;
  const IN = {
    rise: { from: { y: 48, opacity: 0 }, dur: 0.8, ease: E.enter },
    fade: { from: { opacity: 0 }, dur: 0.6, ease: E.out },
    pop: { from: { scale: 0.72, opacity: 0 }, dur: 0.6, ease: E.pop },
    left: { from: { x: -90, opacity: 0 }, dur: 0.8, ease: E.enter },
    right: { from: { x: 90, opacity: 0 }, dur: 0.8, ease: E.enter },
    drop: { from: { y: -60, opacity: 0 }, dur: 0.7, ease: E.enter },
    zoom: { from: { scale: 1.18, opacity: 0 }, dur: 0.9, ease: E.enter },
    blur: { from: { filter: 'blur(18px)', opacity: 0 }, dur: 0.8, ease: E.out },
    wipe: { from: { clipPath: 'inset(0% 100% 0% 0%)' }, to: { clipPath: 'inset(0% 0% 0% 0%)' }, dur: 0.9, ease: E.move },
    words: { from: { y: '0.45em', opacity: 0 }, dur: 0.7, ease: E.enter, split: 'words', stagger: 0.05 },
    chars: { from: { y: '0.5em', opacity: 0 }, dur: 0.5, ease: E.enter, split: 'chars', stagger: 0.022 },
  };
  const OUT = {
    fade: { to: { opacity: 0 }, dur: 0.35, ease: E.in },
    sink: { to: { y: 40, opacity: 0 }, dur: 0.4, ease: E.exit },
    shrink: { to: { scale: 0.9, opacity: 0 }, dur: 0.4, ease: E.exit },
    blur: { to: { filter: 'blur(14px)', opacity: 0 }, dur: 0.4, ease: E.in },
  };

  function enter(tl, target, when, kind = 'rise', o = {}) {
    const p = IN[kind];
    if (!p) throw new Error(`modern.js: no entrance "${kind}". Use one of: ${Object.keys(IN).join(', ')}`);
    let els = $(target);
    if (p.split) els = split(els, p.split);
    else if (o.children) els = els.flatMap((e) => [...e.children]);
    if (!els.length) return tl;
    const vars = { duration: o.dur ?? p.dur, ease: o.ease ?? p.ease, stagger: o.stagger ?? p.stagger ?? (o.children ? 0.12 : 0) };
    const t0 = at(when) + (o.delay || 0);
    if (p.to) tl.fromTo(els, { ...p.from }, { ...p.to, ...vars }, t0);
    else tl.from(els, { ...p.from, ...vars }, t0);
    return tl;
  }

  function exit(tl, target, when, kind = 'fade', o = {}) {
    const p = OUT[kind];
    if (!p) throw new Error(`modern.js: no exit "${kind}". Use one of: ${Object.keys(OUT).join(', ')}`);
    tl.to($(target), { ...p.to, duration: o.dur ?? p.dur, ease: o.ease ?? p.ease, stagger: o.stagger || 0 }, at(when) + (o.delay || 0));
    return tl;
  }

  // ---- frame-driven helpers (no timeline needed) ----
  function count(target, when, to, o = {}) {
    const from = o.from ?? 0, dur = o.dur ?? 1.4, ease = o.ease || E.outExpo, dec = o.decimals ?? 0;
    const fmt = (v) => (o.prefix || '') + v.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }) + (o.suffix || '');
    for (const el of $(target)) P.onFrame((t) => { el.textContent = fmt(from + (to - from) * ease(P.clamp((t - at(when)) / dur))); });
  }

  function type(target, when, o = {}) {
    const cps = o.cps ?? 32;
    for (const el of $(target)) {
      const full = el.textContent, text = document.createTextNode(''), caret = document.createElement('span');
      caret.className = 'vf-caret'; el.replaceChildren(text, caret);
      P.onFrame((t) => {
        const n = Math.max(0, Math.min(full.length, Math.floor((t - at(when)) * cps)));
        if (text.data.length !== n) text.data = full.slice(0, n);
        caret.style.opacity = (n > 0 && n < full.length) || Math.floor(t * 2) % 2 === 0 ? 1 : 0;
        if (o.caret === false && n === full.length) caret.style.opacity = 0;
      });
    }
  }

  function draw(target, when, o = {}) {
    const dur = o.dur ?? 1.2, ease = o.ease || E.inOut;
    for (const el of $(target)) {
      const parts = el instanceof SVGGeometryElement ? [el] : [...el.querySelectorAll('path, line, polyline, polygon, circle, rect, ellipse')];
      for (const s of parts) {
        const len = s.getTotalLength();
        s.style.strokeDasharray = `${len} ${len}`;
        P.onFrame((t) => { s.style.strokeDashoffset = len * (1 - ease(P.clamp((t - at(when)) / dur))); });
      }
    }
  }

  // Slow camera push on a wrapper: scale from..to between two times (the shot keeps moving while you talk).
  function push(target, from, until, o = {}) {
    const s0 = o.from ?? 1, s1 = o.to ?? 1.06;
    for (const el of $(target)) P.onFrame((t) => {
      const a = at(from), b = until == null ? P.cue(from).end : at(until);
      el.style.transform = `scale(${P.lerp(s0, s1, E.sine(P.clamp((t - a) / Math.max(0.01, b - a))))})`;
    });
  }

  // A recorded browser clip (`anim.py record`): frames assets/<name>/f001.jpg … played on the clock.
  // The frames are preloaded and drawn on a canvas, so every rendered frame shows the right picture.
  // o.speed plays faster or slower; o.from starts that many seconds into the clip (skip an empty intro).
  function clip(target, name, when, o = {}) {
    const meta = window.REAL && window.REAL.clips && window.REAL.clips[name];
    if (!meta) throw new Error(`modern.js: no clip "${name}" in assets/real.js. Run: python anim.py record <slug> ${name} <steps-file>`);
    const frames = Array.from({ length: meta.n }, (_, i) => {
      const im = new Image();
      P.wait(P.loaded(im, `assets/${name}/f${String(i + 1).padStart(3, '0')}.jpg`));
      return im;
    });
    for (const el of $(target)) {
      const c = el.tagName === 'CANVAS' ? el : el.appendChild(document.createElement('canvas'));
      c.style.display = 'block'; c.style.width = '100%';
      const ctx = c.getContext('2d');
      P.onFrame((t) => {
        const im = frames[Math.max(0, Math.min(meta.n - 1, Math.floor(((t - at(when)) * (o.speed ?? 1) + (o.from ?? 0)) * meta.fps)))];
        if (!im.naturalWidth) return;
        if (c.width !== im.naturalWidth) { c.width = im.naturalWidth; c.height = im.naturalHeight; }
        ctx.drawImage(im, 0, 0);
      });
    }
  }

  // Bars in a .vf-bars chart grow from 0 to their --v value.
  function bars(target, when, o = {}) {
    const dur = o.dur ?? 1, gap = o.stagger ?? 0.12;
    for (const el of $(target)) [...el.querySelectorAll('.vf-bar')].forEach((bar, i) => {
      const v = parseFloat(bar.style.getPropertyValue('--v') || getComputedStyle(bar).getPropertyValue('--v')) || 0;
      P.onFrame((t) => bar.style.setProperty('--v', v * E.enter(P.clamp((t - at(when) - i * gap) / dur))));
    });
  }

  // ---- declarative: data-in / data-out / data-count / data-type / data-draw on any element ----
  // Time: data-at (cue id, "id+0.3", "@word", seconds); default = the start of the nearest [data-cue] parent.
  // data-delay adds seconds. data-stagger on a parent animates its children one by one.
  function whenOf(el) {
    if (el.dataset.at) return at(el.dataset.at) + (+el.dataset.delay || 0);
    const host = el.closest('[data-cue]');
    return (host ? at(host.dataset.cue) + (+host.dataset.cueOffset || 0) : 0) + (+el.dataset.delay || 0);
  }
  let auto = null;
  function scan(root = document) {
    icons(root);
    for (const el of root.querySelectorAll('[data-brand]')) { el.textContent = T[el.dataset.brand] ?? ''; el.removeAttribute('data-brand'); }
    for (const el of root.querySelectorAll('[data-in]')) {
      auto = auto || P.timeline();
      const stagger = el.dataset.stagger != null ? +el.dataset.stagger || 0.12 : undefined;
      enter(auto, el, whenOf(el), el.dataset.in, { children: stagger != null && !IN[el.dataset.in]?.split, stagger, dur: el.dataset.dur ? +el.dataset.dur : undefined });
      el.removeAttribute('data-in');
    }
    for (const el of root.querySelectorAll('[data-out]')) {
      // Default: finish exactly when the shot ends (its cue end, or the start of its data-until cue).
      const host = el.closest('[data-cue]'), kind = el.dataset.out;
      const end = host ? (host.dataset.until ? at(host.dataset.until) : P.cue(host.dataset.cue).end) : P.duration;
      auto = auto || P.timeline();
      exit(auto, el, el.dataset.outAt ? at(el.dataset.outAt) : end - (OUT[kind]?.dur ?? 0.35), kind);
      el.removeAttribute('data-out');
    }
    for (const el of root.querySelectorAll('[data-count]')) {
      const m = /^([^\d-]*)(-?[\d.,]+)(.*)$/.exec(el.dataset.count.trim());
      if (m) count(el, whenOf(el), parseFloat(m[2].replace(/,/g, '')), { prefix: m[1], suffix: m[3], decimals: (m[2].split('.')[1] || '').length });
      el.removeAttribute('data-count');
    }
    for (const el of root.querySelectorAll('[data-type]')) { type(el, whenOf(el)); el.removeAttribute('data-type'); }
    for (const el of root.querySelectorAll('[data-draw]')) { draw(el, whenOf(el)); el.removeAttribute('data-draw'); }
    for (const el of root.querySelectorAll('.vf-bars[data-grow]')) { bars(el, whenOf(el)); el.removeAttribute('data-grow'); }
  }

  // ---- chrome: captions and the progress line ----
  for (const p of document.querySelectorAll('.vf-captions p')) P.captions(p);
  for (const bar of document.querySelectorAll('.vf-progress')) P.onFrame((t) => bar.style.setProperty('--p', P.clamp(t / P.duration)));

  window.Modern = { at, icons, split, in: enter, out: exit, count, type, draw, push, clip, bars, scan, IN, OUT };
  scan();  // scripts sit at the end of <body>, so the scene markup exists now
})();
