// Spotlight: dims the whole element except one area (circle or rect), which can move on. Rewritten from Onda Spotlight (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  function box(e, root) {
    let x = 0, y = 0, n = e;
    while (n && n !== root) { x += n.offsetLeft; y += n.offsetTop; n = n.offsetParent; }
    return { x, y, w: e.offsetWidth, h: e.offsetHeight };
  }
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, p) => a + (b - a) * p;
  const easeIO = p => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);

  FX.spotlight = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 0.7 : o.dur;
    const dim = o.dim == null ? 0.78 : o.dim, pad = o.pad == null ? 28 : o.pad;
    if (getComputedStyle(el).position === "static") el.style.position = "relative";
    const W = el.offsetWidth || K.size(el).w, Hh = el.offsetHeight || K.size(el).h;
    // one lit area as a rounded rect {cx, cy, w, h, rr}; a circle is a rounded rect with rr = w / 2
    const geo = (s, shape) => {
      shape = s.shape || shape;
      const t = typeof s.target === "string" ? document.querySelector(s.target) : s.target;
      let cx, cy, w, h;
      if (t) {
        const b = box(t, el);
        cx = b.x + b.w / 2; cy = b.y + b.h / 2;
        if (shape === "circle") { w = h = 2 * (Math.max(b.w, b.h) / 2 + pad); } else { w = b.w + 2 * pad; h = b.h + 2 * pad; }
      } else if (shape === "circle") {
        cx = s.x == null ? W / 2 : s.x; cy = s.y == null ? Hh / 2 : s.y; w = h = 2 * (s.r == null ? 200 : s.r);
      } else {
        cx = s.x == null ? W / 2 : s.x; cy = s.y == null ? Hh / 2 : s.y; w = s.w == null ? 500 : s.w; h = s.h == null ? 300 : s.h;
      }
      return { cx, cy, w, h, rr: shape === "circle" ? w / 2 : Math.min(s.radius == null ? 28 : s.radius, w / 2, h / 2) };
    };
    const shape0 = o.shape || "circle";
    const g0 = geo(o, shape0);
    const moves = (o.moves || []).map(m => ({ at: H.at(m.at), dur: m.dur == null ? 0.7 : m.dur, g: geo(m, m.shape || shape0) }));
    // the hole starts so large that nothing is dimmed, then closes to the lit area
    const wide = g => { const r = Math.hypot(Math.max(g.cx, W - g.cx), Math.max(g.cy, Hh - g.cy)) * 2.1; return { cx: g.cx, cy: g.cy, w: r, h: r, rr: g.rr >= Math.min(g.w, g.h) / 2 - 1e-6 ? r / 2 : g.rr }; };
    const mix = (a, b, p) => ({ cx: lerp(a.cx, b.cx, p), cy: lerp(a.cy, b.cy, p), w: lerp(a.w, b.w, p), h: lerp(a.h, b.h, p), rr: lerp(a.rr, b.rr, p) });
    const sp = K.spring({ dur, bounce: 0 });
    const exitAt = o.exitAt == null ? null : H.at(o.exitAt), exitDur = o.exitDur == null ? 0.5 : o.exitDur;
    let end = at + dur;
    moves.forEach(m => { end = Math.max(end, m.at + m.dur); });
    if (exitAt != null) end = Math.max(end, exitAt + exitDur);

    const veil = document.createElement("div");
    veil.className = "fx-spotlight";
    veil.style.background = K.color(o.color || "cream");
    el.appendChild(veil);
    const ring = o.ring === false ? null : document.createElement("div");
    if (ring) { ring.className = "fx-spotlight-ring"; ring.style.borderColor = K.color(o.ringColor || "accent"); el.appendChild(ring); }

    function draw(p, t) {
      const e = t - at >= dur ? 1 : sp(Math.max(0, t - at));
      let g = mix(wide(g0), g0, e);
      let prev = g0;
      for (const m of moves) { const q = easeIO(clamp((t - m.at) / m.dur)); if (q > 0) g = mix(prev, m.g, q); prev = m.g; }
      let vis = clamp(e * 1.4);
      if (exitAt != null) {
        const x = easeIO(clamp((t - exitAt) / exitDur));
        g = mix(g, wide(g), x); vis *= 1 - x;
      }
      const x0 = g.cx - g.w / 2, y0 = g.cy - g.h / 2, r = Math.max(0, Math.min(g.rr, g.w / 2, g.h / 2));
      const hole = `M ${x0 + r} ${y0} H ${x0 + g.w - r} A ${r} ${r} 0 0 1 ${x0 + g.w} ${y0 + r} V ${y0 + g.h - r} A ${r} ${r} 0 0 1 ${x0 + g.w - r} ${y0 + g.h} ` +
        `H ${x0 + r} A ${r} ${r} 0 0 1 ${x0} ${y0 + g.h - r} V ${y0 + r} A ${r} ${r} 0 0 1 ${x0 + r} ${y0} Z`;
      veil.style.clipPath = `path(evenodd, 'M 0 0 H ${W} V ${Hh} H 0 Z ${hole}')`;
      veil.style.opacity = String(dim * vis);
      if (ring) {
        const rs = ring.style;
        rs.left = x0 + "px"; rs.top = y0 + "px"; rs.width = g.w + "px"; rs.height = g.h + "px"; rs.borderRadius = r + "px";
        rs.opacity = String(clamp((vis - 0.7) / 0.3) * (o.ringOpacity == null ? 1 : o.ringOpacity));  // the ring shows once the hole has closed in
      }
    }
    draw(0, at);
    H.drive(draw, at, end);
    return { veil, ring };
  };
})();
