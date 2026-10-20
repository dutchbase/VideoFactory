// Demo for library/fx/_demo/{modern,hf}.html?fx=text/shimmer-sweep.
window.FX_DEMO = function (H, stage) {
  const mk = (text, top, size) => {
    const el = document.createElement("div");
    el.textContent = text;
    el.style.cssText = `position:absolute;left:10%;top:${top}%;width:80%;font:800 ${size}px/1.1 var(--head);color:var(--ink)`;
    stage.appendChild(el);
    return el;
  };
  FX.shimmerSweep(H, mk("Every part moves", 26, 120), { at: H.at("intro+0.3"), dur: 1.0 });
  FX.shimmerSweep(H, mk("on the voice.", 52, 96), { at: H.at("@here"), dur: 1.0, repeat: 3, interval: 1.4 });
};
