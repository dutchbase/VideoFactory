// Demo for library/fx/_demo/{modern,hf}.html?fx=data/pie-reveal.
window.FX_DEMO = function (H, stage) {
  const box = (left) => {
    const el = document.createElement("div");
    el.style.cssText = `position:absolute;left:${left}px;top:260px;width:560px;height:560px`;
    stage.appendChild(el);
    return el;
  };
  FX.pieReveal(H, box(260), { at: H.at("intro+0.3"), value: 72, label: "Videos done", dur: 1.6 });
  FX.pieReveal(H, box(1100), { at: H.at("@here"), value: 38, label: "On budget", color: "green", dur: 1.4 });
};
