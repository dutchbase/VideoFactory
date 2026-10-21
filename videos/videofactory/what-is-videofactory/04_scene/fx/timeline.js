// Timeline: a thin line strokes itself on, dots land at each anchor as it passes, labels settle beneath; the last dot takes the accent.
// Rewritten from Onda Timeline (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const NS = "http://www.w3.org/2000/svg";
  const out = x => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 3);
  FX.timeline = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 2.0 : o.dur;
    const pts = o.points || [{ label: "Plan", sub: "Week 1" }, { label: "Build", sub: "Week 2" }, { label: "Test", sub: "Week 3" }, { label: "Launch", sub: "Week 4" }, { label: "Grow", sub: "Week 5" }];
    const n = pts.length, W = o.width || 1600, lw = o.labelWidth || 300, dot = o.dotSize || 44, lineH = o.lineHeight || 6;
    const padX = lw / 2, innerW = W - 2 * padX, mid = Math.ceil(dot * 0.7) + 4, ly = mid + Math.ceil(dot / 2) + 28;
    const root = H.mk("div", "fx-timeline", el);
    root.style.width = W + "px"; root.style.height = (ly + 40 + 44 + 10 + 38) + "px";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${W} ${mid * 2}`); svg.setAttribute("width", W); svg.setAttribute("height", mid * 2);
    root.appendChild(svg);
    const mk = (tag, attrs) => {
      const e = document.createElementNS(NS, tag);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      svg.appendChild(e);
      return e;
    };
    mk("rect", { x: padX, y: mid - lineH / 2, width: innerW, height: lineH, fill: K.color(o.lineColor || "line") });
    const fill = mk("rect", { x: padX, y: mid - lineH / 2, width: 0, height: lineH, fill: K.color(o.color || "dim") });
    const items = pts.map((p, i) => {
      const f = n > 1 ? i / (n - 1) : 0.5, x = padX + f * innerW, lastDot = i === n - 1;
      const d = mk("circle", { cx: x, cy: mid, r: 0, fill: K.color(lastDot ? (o.accentColor || "accent") : "ink") });
      const lab = H.mk("div", "fx-timeline-label", root);
      lab.style.left = (x - lw / 2) + "px"; lab.style.width = lw + "px";
      H.mk("span", "fx-timeline-name", lab, p.label);
      if (p.sub) H.mk("span", "fx-timeline-sub", lab, p.sub);
      return { f: n > 1 ? f : 0, d, lab, rad: (lastDot ? dot * 1.4 : dot) / 2 };
    });
    function draw(p) {
      const e = out(p);
      fill.setAttribute("width", (e * innerW).toFixed(2));
      items.forEach(it => {
        const a = K.clamp((e - it.f * 0.9) / 0.08), b = K.clamp((e - it.f * 0.9 - 0.04) / 0.1);
        it.d.setAttribute("r", (it.rad * (0.4 + 0.6 * a) * (a > 0 ? 1 : 0)).toFixed(2));
        it.d.setAttribute("fill-opacity", a.toFixed(3));
        it.lab.style.opacity = b.toFixed(3);
        it.lab.style.top = Math.round(ly + (1 - b) * 14) + "px";
      });
    }
    draw(0);
    H.tl.fromTo(root, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.2, ease: "power3.out", immediateRender: true }, at);
    H.drive(draw, at, at + dur);
    return { el, root, items };
  };
})();
