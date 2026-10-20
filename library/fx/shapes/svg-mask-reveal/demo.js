// Demo for library/fx/_demo/{modern,hf}.html?fx=shapes/svg-mask-reveal. Two full-frame panels, each opened by a shape.
window.FX_DEMO = function (H, stage) {
  const panel = (bg, fg, text, sub) => {
    const e = document.createElement("div");
    e.style.cssText = `position:absolute;inset:0;background:${bg};color:${fg};display:flex;flex-direction:column;justify-content:center;padding:0 120px;gap:24px`;
    e.innerHTML = "<div></div><div></div>";
    e.children[0].style.cssText = "font:800 140px/1.05 var(--head);max-width:1500px";
    e.children[0].textContent = text;
    e.children[1].style.cssText = "font:600 52px/1.2 var(--font);opacity:.8";
    e.children[1].textContent = sub;
    stage.appendChild(e);
    return e;
  };
  const a = panel("var(--ink)", "var(--cream)", "A shape opens the picture.", "Any outline works as the mask.");
  const b = panel("var(--accent)", "var(--cream)", "Then a new one.", "It grows from a corner.");
  FX.svgMaskReveal(H, a, { at: H.at("intro+0.2"), dur: 1.4, shape: "star", rotation: 60, origin: { x: 0.5, y: 0.5 } });
  FX.svgMaskReveal(H, b, { at: H.at("point+0.3"), dur: 1.2, shape: "circle", origin: { x: 0.08, y: 0.92 } });
};
