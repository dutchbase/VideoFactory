// Comparison bars: a muted "before" bar and a coloured "after" bar per row, with a change chip. Rewritten from RemotionUI ComparisonBars (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const out = x => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 4);
  const fmt = (n, d) => { const [i, f] = n.toFixed(d).split("."); return i.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (f ? "." + f : ""); };
  FX.comparisonBars = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 1.0 : o.dur;
    const stagger = o.stagger == null ? 0.3 : o.stagger, pair = o.pairOffset == null ? 0.18 : o.pairOffset;
    const rows = o.rows || [{ label: "Speed", before: 40, after: 68 }, { label: "Quality", before: 55, after: 82 }, { label: "Cost", before: 90, after: 60 }];
    const names = o.seriesLabels || ["Before", "After"];
    const dec = o.decimals || 0, unit = o.unit || "", barH = o.barHeight || 44, W = o.width || 1600;
    const lw = o.labelWidth || 340, vw = o.valueWidth || 190, dw = o.deltaWidth || 220;
    const cB = o.beforeColor || "dim", cA = o.afterColor || "accent";
    const max = Math.max(1e-9, ...rows.map(r => Math.max(r.before, r.after)));
    const root = H.mk("div", "fx-comparison-bars", el);
    root.style.width = W + "px";
    const leg = H.mk("div", "fx-comparison-bars-legend", root);
    [[names[0], cB], [names[1], cA]].forEach(([n, role]) => {
      const it = H.mk("span", "fx-comparison-bars-key", leg);
      H.mk("i", "fx-comparison-bars-swatch", it).style.background = K.color(role);
      H.mk("span", "", it, n);
    });
    const list = H.mk("div", "fx-comparison-bars-list", root);
    list.style.rowGap = (o.rowGap || 54) + "px";
    const items = rows.map((r, i) => {
      const row = H.mk("div", "fx-comparison-bars-row", list);
      row.style.gridTemplateColumns = `${lw}px 1fr ${vw}px ${dw}px`;
      H.mk("div", "fx-comparison-bars-label", row, r.label);
      const bars = H.mk("div", "fx-comparison-bars-bars", row);
      const vals = H.mk("div", "fx-comparison-bars-vals", row);
      const mkBar = role => {
        const t = H.mk("div", "fx-comparison-bars-track", bars);
        t.style.height = barH + "px";
        const f = H.mk("div", "fx-comparison-bars-fill", t);
        f.style.background = K.color(role);
        return f;
      };
      const fb = mkBar(cB), fa = mkBar(cA);
      const vb = H.mk("div", "fx-comparison-bars-val", vals), va = H.mk("div", "fx-comparison-bars-val fx-comparison-bars-after", vals);
      vb.style.height = va.style.height = barH + "px"; vb.style.lineHeight = va.style.lineHeight = barH + "px";
      const pct = r.before ? Math.round((r.after - r.before) / r.before * 100) : 0;
      const txt = r.delta != null ? String(r.delta) : (pct > 0 ? "+" : pct < 0 ? "−" : "") + Math.abs(pct) + "%";
      const up = r.after >= r.before;
      const dl = H.mk("div", "fx-comparison-bars-delta", row, o.showDelta === false ? "" : txt);
      dl.style.color = K.color(up ? (o.upColor || "green") : (o.downColor || "accent"));
      return { r, fb, fa, vb, va, dl, s0: i * stagger };
    });
    const total = dur + (rows.length - 1) * stagger + pair + 0.3;
    function draw(p, t) {
      const s = p * total;
      items.forEach(it => {
        const qb = out((s - it.s0) / dur), qa = out((s - it.s0 - pair) / dur);
        it.fb.style.width = (qb * it.r.before / max * 100).toFixed(3) + "%";
        it.fa.style.width = (qa * it.r.after / max * 100).toFixed(3) + "%";
        it.vb.textContent = fmt(qb * it.r.before, dec) + unit;
        it.va.textContent = fmt(qa * it.r.after, dec) + unit;
        it.dl.style.opacity = K.clamp((s - it.s0 - pair - dur) / 0.3).toFixed(3);
      });
    }
    draw(0);
    H.tl.fromTo(root, { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.35, ease: "power3.out", immediateRender: true }, at);
    H.drive(draw, at, at + total);
    return { el, root, rows: items };
  };
})();
