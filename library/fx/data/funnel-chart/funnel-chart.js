// Funnel chart: stage bands narrow toward the bottom, with the drop-off between them. Rewritten from RemotionUI FunnelChart (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const NS = "http://www.w3.org/2000/svg";
  const out = x => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 4);
  const fmt = (n, d) => { const [i, f] = n.toFixed(d).split("."); return i.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (f ? "." + f : ""); };
  FX.funnelChart = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 0.8 : o.dur, stagger = o.stagger == null ? 0.45 : o.stagger;
    const stages = o.stages || [{ label: "Visits", value: 12000 }, { label: "Signups", value: 4800 }, { label: "Trials", value: 1900 }, { label: "Customers", value: 640 }];
    const n = stages.length, W = o.width || 1600, bh = o.bandHeight || 120, gap = o.gap || 64, lw = o.labelWidth || 560;
    const unit = o.unit || "", dec = o.decimals || 0, tail = o.tailOpacity == null ? 0.45 : o.tailOpacity;
    const fw = W - lw - 40, H_ = n * bh + (n - 1) * gap, cx = fw / 2, top = stages[0].value || 1;
    const minW = fw * 0.12;
    const wOf = i => Math.max(minW, fw * stages[i].value / top);
    const root = H.mk("div", "fx-funnel-chart", el);
    root.style.width = W + "px"; root.style.height = H_ + "px";
    const gutter = H.mk("div", "fx-funnel-chart-gutter", root);
    gutter.style.width = lw + "px";
    const area = H.mk("div", "fx-funnel-chart-area", root);
    area.style.width = fw + "px"; area.style.height = H_ + "px";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${fw} ${H_}`); svg.setAttribute("width", fw); svg.setAttribute("height", H_);
    area.appendChild(svg);
    const items = stages.map((s, i) => {
      const y0 = i * (bh + gap);
      const poly = document.createElementNS(NS, "polygon");
      poly.setAttribute("fill", K.color(o.color || "accent"));
      poly.setAttribute("fill-opacity", (1 - (1 - tail) * (n > 1 ? i / (n - 1) : 0)).toFixed(3));
      svg.appendChild(poly);
      const cell = H.mk("div", "fx-funnel-chart-cell", gutter);
      cell.style.top = y0 + "px"; cell.style.height = bh + "px";
      H.mk("span", "fx-funnel-chart-name", cell, s.label);
      const val = H.mk("span", "fx-funnel-chart-val", cell);
      let drop = null;
      if (o.showDropoff !== false && i > 0) {
        const pct = stages[i - 1].value ? Math.round((1 - s.value / stages[i - 1].value) * 100) : 0;
        drop = H.mk("div", "fx-funnel-chart-drop", area, (pct > 0 ? "−" : "") + Math.abs(pct) + "%");
        drop.style.top = (y0 - gap) + "px"; drop.style.height = gap + "px"; drop.style.lineHeight = gap + "px";
        drop.style.color = K.color(o.dropColor || "accent");
      }
      return { s, y0, poly, cell, val, drop, wt: wOf(i), wb: i < n - 1 ? wOf(i + 1) : wOf(i), t0: i * stagger };
    });
    function draw(p) {
      const s = p * (dur + (n - 1) * stagger);
      items.forEach(it => {
        const q = out((s - it.t0) / dur), yq = it.y0 + q * bh, wq = it.wt + (it.wb - it.wt) * q;
        it.poly.setAttribute("points", q <= 0 ? "" :
          `${cx - it.wt / 2},${it.y0} ${cx + it.wt / 2},${it.y0} ${cx + wq / 2},${yq} ${cx - wq / 2},${yq}`);
        it.val.textContent = fmt(it.s.value * q, dec) + unit;
        const vis = K.clamp((s - it.t0) / 0.2).toFixed(3);
        it.cell.style.opacity = vis;
        if (it.drop) it.drop.style.opacity = vis;
      });
    }
    draw(0);
    H.tl.fromTo(root, { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.35, ease: "power3.out", immediateRender: true }, at);
    H.drive(draw, at, at + dur + (n - 1) * stagger);
    return { el, root, items };
  };
})();
