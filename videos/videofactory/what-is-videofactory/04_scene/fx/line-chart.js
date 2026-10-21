// Line chart: the line draws on left to right, with a soft area, dots that pop as the line reaches them and the last value at the end.
// Rewritten from Onda LineChart (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const NS = "http://www.w3.org/2000/svg";
  const out = x => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 3);
  const fmt = (n, d) => { const [i, f] = n.toFixed(d).split("."); return i.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (f ? "." + f : ""); };
  FX.lineChart = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 2.0 : o.dur;
    const data = (o.values || [12, 18, 15, 24, 31, 28, 40]).map(Number), n = data.length;
    const labels = o.labels || null, W = o.width || 1500, Hc = o.height || 560, gutter = o.valueGutter == null ? 200 : o.valueGutter;
    const sw = o.strokeWidth || 8, dec = o.decimals || 0, unit = o.unit || "";
    const padL = 30, padT = 50, padB = 30, x1 = W - gutter, innerW = x1 - padL, innerH = Hc - padT - padB;
    const lo = o.zero ? Math.min(0, ...data) : Math.min(...data), hi = Math.max(...data), span = hi - lo || 1;
    const pts = data.map((v, i) => [padL + (n <= 1 ? 0 : i / (n - 1)) * innerW, padT + (1 - (v - lo) / span) * innerH]);
    const cum = [0];
    for (let i = 1; i < n; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    const len = cum[n - 1] || 1, base = padT + innerH;
    const root = H.mk("div", "fx-line-chart", el);
    root.style.width = W + "px";
    const wrap = H.mk("div", "fx-line-chart-plot", root);
    wrap.style.width = W + "px"; wrap.style.height = Hc + "px";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${W} ${Hc}`); svg.setAttribute("width", W); svg.setAttribute("height", Hc);
    wrap.appendChild(svg);
    const mk = (tag, attrs) => {
      const e = document.createElementNS(NS, tag);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      svg.appendChild(e);
      return e;
    };
    for (let g = 0; g <= 3; g++) {
      const y = padT + innerH * g / 3;
      mk("line", { x1: padL, y1: y, x2: x1, y2: y, stroke: K.color("line"), "stroke-width": 2 });
    }
    const role = o.color || "accent";
    const area = o.fill === false ? null : mk("polygon", { fill: K.color(role), "fill-opacity": 0.16 });
    const line = mk("polyline", { fill: "none", stroke: K.color(role), "stroke-width": sw, "stroke-linecap": "round", "stroke-linejoin": "round" });
    const dots = o.showDots === false ? [] : pts.map((p, i) => mk("circle", { cx: p[0], cy: p[1], r: 0, fill: K.color(i === n - 1 ? role : "ink") }));
    if (labels) labels.slice(0, n).forEach((t, i) => {
      if (o.labelEvery && i % o.labelEvery) return;
      const l = H.mk("span", "fx-line-chart-tick", wrap, t);
      l.style.left = pts[i][0] + "px"; l.style.top = (Hc + 14) + "px";
    });
    if (labels) root.style.paddingBottom = "56px";
    const last = H.mk("div", "fx-line-chart-last", wrap, fmt(data[n - 1], dec) + unit);
    last.style.left = (pts[n - 1][0] + 34) + "px"; last.style.top = pts[n - 1][1] + "px";
    function head(f) {   // the point at fraction f of the line length, and the corners passed so far
      const L = f * len, run = [];
      let i = 0;
      while (i < n - 1 && cum[i + 1] <= L) { run.push(pts[i]); i++; }
      run.push(pts[i]);
      if (i < n - 1 && L > cum[i]) {
        const q = (L - cum[i]) / (cum[i + 1] - cum[i] || 1);
        run.push([pts[i][0] + (pts[i + 1][0] - pts[i][0]) * q, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * q]);
      }
      return run;
    }
    function draw(p) {
      const e = out(p), run = head(e), s = run.map(q => q[0].toFixed(2) + "," + q[1].toFixed(2)).join(" ");
      line.setAttribute("points", e <= 0 ? "" : s);
      if (area) area.setAttribute("points", e <= 0 ? "" : `${s} ${run[run.length - 1][0].toFixed(2)},${base} ${pts[0][0]},${base}`);
      dots.forEach((d, i) => d.setAttribute("r", (K.clamp((e - 0.95 * cum[i] / len) / 0.05) * (i === n - 1 ? sw * 2 : sw * 1.3)).toFixed(2)));
      last.style.opacity = K.clamp((e - 0.9) / 0.1).toFixed(3);
    }
    draw(0);
    H.tl.fromTo(root, { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.35, ease: "power3.out", immediateRender: true }, at);
    H.drive(draw, at, at + dur);
    return { el, root, last };
  };
})();
