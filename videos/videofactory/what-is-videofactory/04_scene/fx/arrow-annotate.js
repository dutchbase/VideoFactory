// Arrow annotate: a hand-drawn arrow that draws itself from a point to a target. Rewritten from RemotionUI arrow-annotate (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const NS = "http://www.w3.org/2000/svg";
  // Layout box of `e` inside `root` in stage px (offset chain, so tweens on the target never move the arrow).
  function box(e, root) {
    let x = 0, y = 0, n = e;
    while (n && n !== root) { x += n.offsetLeft; y += n.offsetTop; n = n.offsetParent; }
    return { x, y, w: e.offsetWidth, h: e.offsetHeight };
  }
  // First point where the segment P -> C enters rect r (C when P is already inside).
  function enter(px, py, cx, cy, r) {
    let t0 = 0, t1 = 1;
    const dx = cx - px, dy = cy - py;
    for (const [p, d, lo, hi] of [[px, dx, r.x, r.x + r.w], [py, dy, r.y, r.y + r.h]]) {
      if (Math.abs(d) < 1e-9) { if (p < lo || p > hi) return { x: cx, y: cy }; continue; }
      let a = (lo - p) / d, b = (hi - p) / d;
      if (a > b) [a, b] = [b, a];
      t0 = Math.max(t0, a); t1 = Math.min(t1, b);
    }
    return t0 > t1 ? { x: cx, y: cy } : { x: px + dx * t0, y: py + dy * t0 };
  }
  const mk = (tag, cls, parent) => { const e = document.createElementNS(NS, tag); if (cls) e.setAttribute("class", cls); parent.appendChild(e); return e; };

  FX.arrowAnnotate = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 0.8 : o.dur;
    const sw = o.strokeWidth == null ? 6 : o.strokeWidth, head = o.headSize == null ? 38 : o.headSize;
    const bow = o.bow == null ? 0.25 : o.bow, gap = o.gap == null ? 24 : o.gap, labelSize = o.labelSize == null ? 44 : o.labelSize;
    const col = K.color(o.color || "accent");
    if (getComputedStyle(el).position === "static") el.style.position = "relative";
    const tgt = typeof o.target === "string" ? document.querySelector(o.target) : o.target;
    const svg = mk("svg", "fx-arrow-annotate", el);
    const g = mk("g", "fx-arrow-annotate-g", svg);
    const line = (w, op) => {
      const p = mk("path", "fx-arrow-annotate-path", g);
      p.setAttribute("pathLength", "1");
      p.style.cssText = `stroke:${col};stroke-width:${w}px;opacity:${op};stroke-dasharray:1 2`;
      return p;
    };
    const paths = [line(sw, 0.95)];
    if (o.sketch !== false) paths.push(line(sw * 0.6, 0.45));
    const tip = line(sw, 1);
    let text = null;
    if (o.label) {
      text = mk("text", "fx-arrow-annotate-label", g);
      text.textContent = o.label;
    }
    const from = { x: 0, y: 0 }, to = { x: 0, y: 0 };

    // Every size comes from the page: measured again once the fonts have loaded (the same seed gives the same strokes).
    K.layout(() => {
      const W = el.offsetWidth || K.size(el).w, Hh = el.offsetHeight || K.size(el).h;
      Object.assign(from, o.from || { x: W * 0.15, y: Hh * 0.25 });
      Object.assign(to, o.to || { x: W / 2, y: Hh / 2 });
      if (tgt) {
        const b = box(tgt, el);
        Object.assign(to, enter(from.x, from.y, b.x + b.w / 2, b.y + b.h / 2, { x: b.x - gap, y: b.y - gap, w: b.w + 2 * gap, h: b.h + 2 * gap }));
      }
      // the shaft bows along its own normal, so the bend scales with the length
      const dx = to.x - from.x, dy = to.y - from.y;
      const cx = (from.x + to.x) / 2 - dy * bow, cy = (from.y + to.y) / 2 + dx * bow;
      const r = K.rand(o.seed == null ? 3 : o.seed), jit = () => r() * 2 - 1;
      const shaft = pass => {
        const k = pass ? 1.4 : 0;
        return `M ${from.x + jit() * k} ${from.y + jit() * k} Q ${cx + jit() * k * 2} ${cy + jit() * k * 2}, ${to.x} ${to.y}`;
      };
      const ang = Math.atan2(to.y - cy, to.x - cx);
      const barb = a => `${to.x - Math.cos(ang - a) * head} ${to.y - Math.sin(ang - a) * head}`;
      svg.setAttribute("viewBox", `0 0 ${W} ${Hh}`);
      paths.forEach((p, i) => p.setAttribute("d", shaft(i)));
      tip.setAttribute("d", `M ${barb(0.42)} L ${to.x} ${to.y} L ${barb(-0.42)}`);
      if (text) {
        // the label sits behind the start of the shaft, on the side the arrow leaves from
        const left = dx >= 0;
        text.setAttribute("x", from.x + (left ? -1 : 1) * 24);
        text.setAttribute("y", from.y + labelSize * 0.35);
        text.style.cssText = `fill:${col};font-size:${labelSize}px;text-anchor:${left ? "end" : "start"}`;
      }
    });

    H.tl.fromTo(g, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.01, immediateRender: true }, at);
    paths.forEach((p, i) => H.tl.fromTo(p, { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: dur, ease: "power1.inOut", immediateRender: true }, at + i * 0.05));
    // the head lands in the last quarter of the stroke
    H.tl.fromTo(tip, { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: dur * 0.24, ease: "none", immediateRender: true }, at + dur * 0.76);
    if (text) H.tl.fromTo(text, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.3, ease: "power2.out", immediateRender: true }, at + dur * 0.1);
    if (o.exitAt != null) H.tl.to(g, { autoAlpha: 0, duration: o.exitDur == null ? 0.25 : o.exitDur, ease: "power2.in", immediateRender: false }, H.at(o.exitAt));
    return { svg, from, to };
  };
})();
