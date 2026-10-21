// Connector lines: edges that draw between anchored elements. Rewritten from RemotionUI connector-lines (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const NS = "http://www.w3.org/2000/svg";
  function box(e, root) {
    let x = 0, y = 0, n = e;
    while (n && n !== root) { x += n.offsetLeft; y += n.offsetTop; n = n.offsetParent; }
    return { x, y, w: e.offsetWidth, h: e.offsetHeight };
  }
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
  const easeIO = p => (p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2);
  const DASH = 0.02;  // dash and gap length, as a fraction of the edge

  FX.connectorLines = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 0.7 : o.dur, stagger = o.stagger == null ? 0.25 : o.stagger;
    const sw = o.strokeWidth == null ? 4 : o.strokeWidth, gap = o.gap == null ? 14 : o.gap, dashed = !!o.dashed;
    if (getComputedStyle(el).position === "static") el.style.position = "relative";
    const W = el.offsetWidth || K.size(el).w, Hh = el.offsetHeight || K.size(el).h;
    // anchors: {id, x, y} in stage px, or {id, el} for an element (its centre; lines stop at its edge)
    const A = {};
    (o.anchors || []).forEach(a => {
      const t = typeof a.el === "string" ? document.querySelector(a.el) : a.el;
      const b = t ? box(t, el) : null;
      A[a.id] = { x: b ? b.x + b.w / 2 : a.x, y: b ? b.y + b.h / 2 : a.y, b: b && { x: b.x - gap, y: b.y - gap, w: b.w + 2 * gap, h: b.h + 2 * gap } };
    });
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("class", "fx-connector-lines");
    svg.setAttribute("viewBox", `0 0 ${W} ${Hh}`);
    el.appendChild(svg);
    const g = document.createElementNS(NS, "g");
    svg.appendChild(g);
    const trim = (a, tx, ty) => (a.b ? enter(tx, ty, a.x, a.y, a.b) : { x: a.x, y: a.y });
    const edges = [];
    (o.edges || []).forEach(e => {
      const a = A[e.from], z = A[e.to];
      if (!a || !z) return;  // an edge that names an unknown anchor is dropped
      const shape = e.shape || o.shape || "curve", bow = e.bow == null ? (o.bow == null ? 0.16 : o.bow) : e.bow;
      const col = K.color(e.color || o.color || "accent");
      let d, end;
      if (shape === "elbow") {
        const mx = (a.x + z.x) / 2, s = trim(a, mx, a.y), t = trim(z, mx, z.y);
        d = `M ${s.x} ${s.y} L ${mx} ${s.y} L ${mx} ${t.y} L ${t.x} ${t.y}`; end = t;
      } else if (shape === "straight") {
        const s = trim(a, z.x, z.y), t = trim(z, a.x, a.y);
        d = `M ${s.x} ${s.y} L ${t.x} ${t.y}`; end = t;
      } else {
        const dx = z.x - a.x, dy = z.y - a.y, cx = (a.x + z.x) / 2 - dy * bow, cy = (a.y + z.y) / 2 + dx * bow;
        const s = trim(a, cx, cy), t = trim(z, cx, cy);
        d = `M ${s.x} ${s.y} Q ${cx} ${cy}, ${t.x} ${t.y}`; end = t;
      }
      const path = document.createElementNS(NS, "path");
      path.setAttribute("class", "fx-connector-path");
      path.setAttribute("d", d); path.setAttribute("pathLength", "1");
      path.style.cssText = `stroke:${col};stroke-width:${sw}px;stroke-dasharray:${dashed ? "0 9" : "1 2"}`;
      g.appendChild(path);
      let dot = null;
      if (e.dot !== false && o.dot !== false) {
        dot = document.createElementNS(NS, "circle");
        dot.setAttribute("class", "fx-connector-dot");
        dot.setAttribute("cx", end.x); dot.setAttribute("cy", end.y); dot.setAttribute("r", sw * 1.9);
        dot.style.cssText = `fill:${col};opacity:0`;
        g.appendChild(dot);
      }
      edges.push({ path, dot });
    });
    const total = dur + stagger * Math.max(0, edges.length - 1);
    // one drive redraws every edge from t alone: solid edges move a dash offset, dashed edges grow a dash list
    function draw(p, t) {
      edges.forEach((e, i) => {
        const q = easeIO(Math.min(1, Math.max(0, (t - at - i * stagger) / dur)));
        e.path.style.visibility = q > 0 ? "visible" : "hidden";  // a round cap would draw a dot for an empty dash
        if (dashed) {
          let s = "";
          for (let k = 0; k * 2 * DASH < q; k++) s += `${Math.min(DASH, q - k * 2 * DASH).toFixed(4)} ${DASH} `;
          e.path.style.strokeDasharray = (s || "0 ") + "9";
        } else e.path.style.strokeDashoffset = String(1 - q);
        if (e.dot) e.dot.style.opacity = String(Math.min(1, Math.max(0, (q - 0.85) / 0.15)));
      });
    }
    draw(0, at);
    H.drive(draw, at, at + total);
    if (o.exitAt != null) H.tl.to(g, { autoAlpha: 0, duration: o.exitDur == null ? 0.3 : o.exitDur, ease: "power2.in", immediateRender: false }, H.at(o.exitAt));
    return { svg, edges: edges.map(e => e.path) };
  };
})();
