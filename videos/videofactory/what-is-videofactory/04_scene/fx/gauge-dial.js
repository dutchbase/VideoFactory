// Gauge dial: an arc fills and a needle sweeps to a target while the readout counts. Rewritten from RemotionUI GaugeDial (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const NS = "http://www.w3.org/2000/svg";
  const out = x => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 4);
  const fmt = (n, d) => { const [i, f] = n.toFixed(d).split("."); return i.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (f ? "." + f : ""); };
  FX.gaugeDial = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 1.6 : o.dur;
    const min = o.min == null ? 0 : o.min, max = o.max == null ? 100 : o.max;
    const value = K.clamp(o.value == null ? 72 : o.value, min, max);
    const size = o.size || 640, th = o.thickness || 44, sweep = o.sweep || 240, ticks = o.tickCount == null ? 9 : o.tickCount;
    const dec = o.decimals || 0, unit = o.unit == null ? "%" : o.unit;
    const c = size / 2, R = size / 2 - 70, a0 = -sweep / 2;
    const pt = (a, rad) => [c + rad * Math.sin(a * Math.PI / 180), c - rad * Math.cos(a * Math.PI / 180)];
    const arcPath = a1 => {
      const [x0, y0] = pt(a0, R), [x1, y1] = pt(a1, R);
      return `M ${x0.toFixed(2)} ${y0.toFixed(2)} A ${R} ${R} 0 ${a1 - a0 > 180 ? 1 : 0} 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`;
    };
    const root = H.mk("div", "fx-gauge-dial", el);
    root.style.width = root.style.height = size + "px";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`); svg.setAttribute("width", size); svg.setAttribute("height", size);
    root.appendChild(svg);
    const mk = (tag, attrs) => {
      const e = document.createElementNS(NS, tag);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      svg.appendChild(e);
      return e;
    };
    const stroke = (role, w) => ({ fill: "none", stroke: K.color(role), "stroke-width": w, "stroke-linecap": "round" });
    mk("path", { ...stroke(o.trackColor || "line", th), d: arcPath(-a0) });
    const fill = mk("path", { ...stroke(o.color || "accent", th), d: arcPath(a0 + 1) });
    for (let i = 0; i < ticks; i++) {
      const a = a0 + (ticks > 1 ? sweep * i / (ticks - 1) : sweep / 2), [x0, y0] = pt(a, R + th / 2 + 12), [x1, y1] = pt(a, R + th / 2 + 28);
      mk("line", { x1: x0.toFixed(2), y1: y0.toFixed(2), x2: x1.toFixed(2), y2: y1.toFixed(2), stroke: K.color("dim"), "stroke-width": 4, "stroke-linecap": "round" });
    }
    const needle = mk("line", { x1: c, y1: c, x2: c, y2: c - (R - th / 2 - 16), stroke: K.color("ink"), "stroke-width": 10, "stroke-linecap": "round" });
    mk("circle", { cx: c, cy: c, r: 20, fill: K.color("ink") });
    const edge = (a, txt) => {
      const [x, y] = pt(a, R);
      const e = H.mk("span", "fx-gauge-dial-end", root, txt);
      e.style.left = x + "px"; e.style.top = (y + th / 2 + 30) + "px";
    };
    if (o.showRange !== false) { edge(a0, fmt(min, dec)); edge(-a0, fmt(max, dec)); }
    const read = H.mk("div", "fx-gauge-dial-read", root);
    read.style.top = (c + R * 0.6) + "px";
    const num = H.mk("span", "fx-gauge-dial-value", read);
    if (o.label) H.mk("span", "fx-gauge-dial-label", read, o.label);
    function draw(p) {
      const e = out(p), v = min + (value - min) * e, a = a0 + sweep * (v - min) / (max - min || 1);
      needle.setAttribute("transform", `rotate(${a.toFixed(3)} ${c} ${c})`);
      fill.setAttribute("d", arcPath(Math.max(a0 + 0.01, a)));
      fill.setAttribute("stroke-opacity", a - a0 < 0.5 ? 0 : 1);
      num.textContent = fmt(v, dec) + unit;
    }
    draw(0);
    H.tl.fromTo(root, { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.35, ease: "power3.out", immediateRender: true }, at);
    H.drive(draw, at, at + dur);
    return { el, root, value: num };
  };
})();
