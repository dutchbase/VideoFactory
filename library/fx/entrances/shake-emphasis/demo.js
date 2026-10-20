// Demo for library/fx/_demo/{modern,hf}.html?fx=entrances/shake-emphasis. The headline lands, then shakes twice on the voice.
window.FX_DEMO = function (H, stage) {
  const mk = (text, top, size, color) => {
    const el = document.createElement("div");
    el.className = "fx-shake";
    el.textContent = text;
    el.style.cssText = `position:absolute;left:160px;top:${top}px;width:1600px;font:800 ${size}px/1.1 var(--head);color:var(${color})`;
    stage.appendChild(el);
    return el;
  };
  const head = mk("This one lands hard.", 300, 150, "--ink");
  const sub = mk("Then it settles.", 560, 96, "--accent");
  H.tl.fromTo(head, { autoAlpha: 0, y: 40 }, { autoAlpha: 1, y: 0, duration: 0.3, ease: "power3.out", immediateRender: true }, H.at("intro+0.3"));
  H.tl.fromTo(sub, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.3, ease: "power3.out", immediateRender: true }, H.at("point+0.1"));
  FX.shakeEmphasis(H, head, { at: H.at("@here"), repeat: 2, every: 1.6, dur: 0.8 });
};
