// Demo for library/fx/_demo/{modern,hf}.html?fx=data/progress-bar.
window.FX_DEMO = function (H, stage) {
  const box = (top) => {
    const el = document.createElement("div");
    el.style.cssText = `position:absolute;left:160px;top:${top}px;width:1600px`;
    stage.appendChild(el);
    return el;
  };
  FX.progressBar(H, box(330), { at: H.at("intro+0.3"), value: 72, label: "Videos rendered", width: 1600, dur: 1.6 });
  FX.progressBar(H, box(600), { at: H.at("@here"), value: 48, label: "Checks passed", width: 1600, dur: 1.4, color: "green" });
};
