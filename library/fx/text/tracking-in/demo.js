// Demo for library/fx/_demo/{modern,hf}.html?fx=text/tracking-in.
window.FX_DEMO = function (H, stage) {
  const mk = (text, top, size) => {
    const el = document.createElement("div");
    el.textContent = text;
    el.style.cssText = `position:absolute;left:0;top:${top}%;width:100%;text-align:center;font:800 ${size}px/1.1 var(--head);color:var(--ink)`;
    stage.appendChild(el);
    return el;
  };
  FX.trackingIn(H, mk("Every part moves", 30, 112), { at: H.at("intro+0.3"), dur: 0.9 });
  FX.trackingIn(H, mk("on the voice.", 52, 88), { at: H.at("@here"), from: 0.4, dur: 0.9 });
};
