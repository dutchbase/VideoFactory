// Demo for library/fx/_demo/{modern,hf}.html?fx=entrances/motion-trail. Two cards fly in with echoes.
window.FX_DEMO = function (H, stage) {
  const card = (text, top, color) => {
    const el = document.createElement("div");
    el.textContent = text;
    el.style.cssText = `position:absolute;left:400px;top:${top}px;width:1120px;height:240px;display:flex;align-items:center;justify-content:center;box-sizing:border-box;border:6px solid var(${color});border-radius:28px;font:800 120px/1 var(--head);color:var(--ink)`;
    stage.appendChild(el);
    return el;
  };
  FX.motionTrail(H, card("Fast in.", 220, "--accent"), { at: H.at("intro+0.3"), x: -900 });
  FX.motionTrail(H, card("Soft landing.", 600, "--ink"), { at: H.at("@here"), x: 900, count: 6 });
};
