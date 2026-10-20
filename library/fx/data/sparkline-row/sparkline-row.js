// Sparkline row: a stack of rows, each with a label, a small trend line that draws on, a counting headline value and a change. Rewritten from RemotionUI SparklineRow (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const NS = "http://www.w3.org/2000/svg";
  const out = x => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 3);
  const fmt = (n, d) => { const [i, f] = n.toFixed(d).split("."); return i.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (f ? "." + f : ""); };
  FX.sparklineRow = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 1.2 : o.dur, stagger = o.stagger == null ? 0.35 : o.stagger;
    const rows = o.rows || [
      { label: "Visits", values: [12, 14, 13, 18, 22, 21, 27], delta: "+18%" },
      { label: "Signups", values: [8, 9, 12, 10, 14, 13, 16], delta: "+12%" },
      { label: "Refunds", values: [9, 8, 9, 7, 6, 7, 5], delta: "-9%" }];
    const W = o.width || 1600, rh = o.rowHeight || 150, sw = o.sparkWidth || 560, sh = 100, dec = o.decimals || 0, unit = o.unit || "";
    const root = H.mk("div", "fx-sparkline-row", el);
    root.style.width = W + "px";
    const items = rows.map((r, i) => {
      const row = H.mk("div", "fx-sparkline-row-item", root);
      row.style.height = rh + "px"; row.style.gridTemplateColumns = `${o.labelWidth || 340}px ${sw}px 1fr ${o.deltaWidth || 200}px`;
      H.mk("div", "fx-sparkline-row-label", row, r.label);
      const svg = document.createElementNS(NS, "svg");
      svg.setAttribute("viewBox", `0 0 ${sw} ${sh}`); svg.setAttribute("width", sw); svg.setAttribute("height", sh);
      row.appendChild(svg);
      const mk = (tag, attrs) => {
        const e = document.createElementNS(NS, tag);
        for (const k in attrs) e.setAttribute(k, attrs[k]);
        svg.appendChild(e);
        return e;
      };
      const vals = r.values.map(Number), n = vals.length, lo = Math.min(...vals), hi = Math.max(...vals), span = hi - lo || 1;
      const pad = 14, pts = vals.map((v, k) => [pad + (n <= 1 ? 0 : k / (n - 1)) * (sw - 2 * pad), pad + (1 - (v - lo) / span) * (sh - 2 * pad)]);
      const cum = [0];
      for (let k = 1; k < n; k++) cum.push(cum[k - 1] + Math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]));
      const role = r.color || o.color || "accent";
      const area = o.showArea === false ? null : mk("polygon", { fill: K.color(role), "fill-opacity": 0.16 });
      const line = mk("polyline", { fill: "none", stroke: K.color(role), "stroke-width": 6, "stroke-linecap": "round", "stroke-linejoin": "round" });
      const tip = mk("circle", { r: 0, fill: K.color("ink") });
      const val = H.mk("div", "fx-sparkline-row-value", row);
      const target = r.value != null ? +r.value : vals[n - 1];
      const txt = r.delta == null ? "" : String(r.delta);
      const down = /^[-−]/.test(txt);
      const dl = H.mk("div", "fx-sparkline-row-delta", row, txt);
      dl.style.color = K.color(down ? (o.downColor || "accent") : (o.upColor || "green"));
      return { r, line, area, tip, val, dl, pts, cum, n, target, unit: r.unit != null ? r.unit : unit, t0: i * stagger, base: sh - pad / 2 };
    });
    const total = dur + (rows.length - 1) * stagger + 0.3;
    function draw(p) {
      const s = p * total;
      items.forEach(it => {
        const q = out((s - it.t0) / dur), L = q * (it.cum[it.n - 1] || 1), run = [];
        let k = 0;
        while (k < it.n - 1 && it.cum[k + 1] <= L) { run.push(it.pts[k]); k++; }
        run.push(it.pts[k]);
        if (k < it.n - 1 && L > it.cum[k]) {
          const f = (L - it.cum[k]) / (it.cum[k + 1] - it.cum[k] || 1);
          run.push([it.pts[k][0] + (it.pts[k + 1][0] - it.pts[k][0]) * f, it.pts[k][1] + (it.pts[k + 1][1] - it.pts[k][1]) * f]);
        }
        const sp = run.map(c => c[0].toFixed(2) + "," + c[1].toFixed(2)).join(" "), h = run[run.length - 1];
        it.line.setAttribute("points", q <= 0 ? "" : sp);
        if (it.area) it.area.setAttribute("points", q <= 0 ? "" : `${sp} ${h[0].toFixed(2)},${it.base} ${it.pts[0][0]},${it.base}`);
        it.tip.setAttribute("cx", h[0].toFixed(2)); it.tip.setAttribute("cy", h[1].toFixed(2));
        it.tip.setAttribute("r", q > 0 ? 9 : 0);
        it.val.textContent = q > 0 ? fmt(it.target * q, dec) + it.unit : "";
        it.dl.style.opacity = K.clamp((s - it.t0 - dur * 0.7) / 0.3).toFixed(3);
      });
    }
    draw(0);
    H.tl.fromTo(root, { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.35, ease: "power3.out", immediateRender: true }, at);
    H.drive(draw, at, at + total);
    return { el, root, rows: items };
  };
})();
