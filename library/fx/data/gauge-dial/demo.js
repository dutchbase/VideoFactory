// Demo for library/fx/_demo/{modern,hf}.html?fx=data/gauge-dial.
window.FX_DEMO = function (H, stage) {
  const box = (left) => {
    const el = document.createElement("div");
    el.style.cssText = `position:absolute;left:${left}px;top:220px;width:640px;height:640px`;
    stage.appendChild(el);
    return el;
  };
  FX.gaugeDial(H, box(240), { at: H.at("intro+0.3"), value: 72, label: "Quality score", dur: 1.6 });
  FX.gaugeDial(H, box(1040), { at: H.at("@here"), value: 35, label: "Error rate", color: "green", dur: 1.4 });
};
