// Donut chart: segments sweep on one after another, the total counts in the hole, a legend lists the parts. Rewritten from RemotionUI DonutChart (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const NS = "http://www.w3.org/2000/svg";
  const out = x => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 4);
  const fmt = (n, d) => { const [i, f] = n.toFixed(d).split("."); return i.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (f ? "." + f : ""); };
  const ROLES = ["accent", "green", "ink", "dim"];
  FX.donutChart = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 1.8 : o.dur;
    const segs = (o.segments || [{ label: "Design", value: 40 }, { label: "Build", value: 30 }, { label: "Test", value: 20 }, { label: "Ship", value: 10 }])
      .map((s, i) => ({ label: s.label, value: Math.max(0, +s.value || 0), color: s.color || ROLES[i % ROLES.length] }));
    const total = segs.reduce((a, s) => a + s.value, 0) || 1;
    const size = o.size || 520, th = o.thickness || 64, r = (size - th) / 2, c = size / 2, circ = 2 * Math.PI * r;
    const gap = segs.length > 1 ? (o.gap == null ? 8 : o.gap) : 0;
    const dec = o.decimals || 0, unit = o.unit || "";
    const root = H.mk("div", "fx-donut-chart", el);
    root.style.width = (o.width || 1200) + "px";
    const wrap = H.mk("div", "fx-donut-chart-ring", root);
    wrap.style.width = wrap.style.height = size + "px";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`); svg.setAttribute("width", size); svg.setAttribute("height", size);
    wrap.appendChild(svg);
    const mkCircle = (role) => {
      const ci = document.createElementNS(NS, "circle");
      ci.setAttribute("cx", c); ci.setAttribute("cy", c); ci.setAttribute("r", r);
      ci.setAttribute("fill", "none"); ci.setAttribute("stroke", K.color(role)); ci.setAttribute("stroke-width", th);
      svg.appendChild(ci);
      return ci;
    };
    mkCircle(o.trackColor || "line");
    let acc = 0;
    segs.forEach(s => {
      s.f0 = acc / total; acc += s.value; s.f1 = acc / total;
      const a = s.f0 * circ + gap / 2, b = s.f1 * circ - gap / 2;
      s.a = a; s.b = Math.max(a, b);
      s.arc = mkCircle(s.color);
      s.arc.setAttribute("class", "fx-donut-chart-seg");
      s.arc.setAttribute("transform", `rotate(${(-90 + 360 * a / circ).toFixed(3)} ${c} ${c})`);
    });
    const mid = H.mk("div", "fx-donut-chart-center", wrap);
    const totalEl = H.mk("span", "fx-donut-chart-total", mid);
    if (o.totalLabel) H.mk("span", "fx-donut-chart-caption", mid, o.totalLabel);
    const legend = H.mk("div", "fx-donut-chart-legend", root);
    segs.forEach(s => {
      const row = H.mk("div", "fx-donut-chart-row", legend);
      const sw = H.mk("span", "fx-donut-chart-swatch", row);
      sw.style.background = K.color(s.color);
      H.mk("span", "fx-donut-chart-name", row, s.label);
      s.val = H.mk("span", "fx-donut-chart-val", row);
      s.row = row;
    });
    function draw(p) {
      const e = out(p), f = e;
      segs.forEach(s => {
        const len = Math.max(0, Math.min(f * circ, s.b) - s.a);
        s.arc.setAttribute("stroke-dasharray", `${len.toFixed(2)} ${circ.toFixed(2)}`);
        s.arc.setAttribute("stroke-opacity", len < 0.3 ? 0 : 1);
        const q = K.clamp((f - s.f0) / Math.max(1e-6, s.f1 - s.f0));
        s.val.textContent = fmt(s.value * q, dec) + unit;
        s.row.style.opacity = K.clamp((f - s.f0) / 0.06).toFixed(3);
      });
      totalEl.textContent = fmt(total * e, dec) + unit;
    }
    draw(0);
    H.tl.fromTo(root, { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.35, ease: "power3.out", immediateRender: true }, at);
    H.drive(draw, at, at + dur);
    return { el, root, total: totalEl, legend };
  };
})();
