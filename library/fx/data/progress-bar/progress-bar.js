// Progress bar: a pill bar fills to a value while the number beside it counts. Rewritten from Onda ProgressBar (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const out = x => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 4);   // one calm ease family: quart out
  const fmt = (n, d) => { const [i, f] = n.toFixed(d).split("."); return i.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (f ? "." + f : ""); };
  FX.progressBar = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 1.2 : o.dur;
    const max = o.max == null ? 100 : o.max, value = K.clamp(o.value == null ? 72 : o.value, 0, max);
    const dec = o.decimals || 0, suffix = o.suffix == null ? "%" : o.suffix;
    const root = H.mk("div", "fx-progress-bar", el);
    root.style.width = (o.width || 1200) + "px";
    const head = H.mk("div", "fx-progress-bar-head", root);
    const label = H.mk("span", "fx-progress-bar-label", head, o.label == null ? "" : o.label);
    const num = o.showValue === false ? null : H.mk("span", "fx-progress-bar-value", head);
    const track = H.mk("div", "fx-progress-bar-track", root);
    track.style.height = (o.height || 40) + "px";
    track.style.background = K.color(o.trackColor, "line");
    const fill = H.mk("div", "fx-progress-bar-fill", track);
    fill.style.background = K.color(o.color, "accent");
    function draw(p) {
      const e = out(p);
      fill.style.width = (e * value / max * 100).toFixed(3) + "%";
      if (num) num.textContent = fmt(e * value, dec) + suffix;
    }
    draw(0);
    H.tl.fromTo(root, { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.35, ease: "power3.out", immediateRender: true }, at);
    H.drive(draw, at, at + dur);
    return { el, root, label, value: num, track, fill };
  };
})();
