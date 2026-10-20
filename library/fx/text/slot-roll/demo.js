// Demo for library/fx/_demo/{modern,hf}.html?fx=text/slot-roll.
window.FX_DEMO = function (H, stage) {
  const mk = (top, size) => {
    const el = document.createElement("div");
    el.style.cssText = `position:absolute;left:10%;top:${top}%;width:80%;text-align:center;font:800 ${size}px/1.1 var(--head);color:var(--ink)`;
    stage.appendChild(el);
    return el;
  };
  FX.slotRoll(H, mk(22, 200), { at: H.at("intro+0.3"), from: "0420", to: "9187", dur: 1.2 });
  FX.slotRoll(H, mk(55, 160), { at: H.at("@here"), from: "A1B2", to: "Z9Y8", dur: 1.2, color: "accent" });
};
