// Demo for library/fx/_demo/{modern,hf}.html?fx=shapes/arrow-annotate. Builds its own markup on the stage.
window.FX_DEMO = function (H, stage) {
  const mk = (css, text) => {
    const e = document.createElement("div");
    e.textContent = text;
    e.style.cssText = "position:absolute;" + css;
    stage.appendChild(e);
    return e;
  };
  mk("left:120px;top:140px;width:900px;font:800 100px/1.08 var(--head);color:var(--ink)", "Point at what matters.");
  const card = "width:600px;height:220px;display:flex;align-items:center;justify-content:center;border-radius:28px;" +
    "border:3px solid var(--line);background:color-mix(in srgb, var(--ink) 8%, var(--cream));font:700 64px/1 var(--head);color:var(--ink)";
  const a = mk("left:1180px;top:140px;" + card, "Input");
  const b = mk("left:1180px;top:700px;" + card, "Result");
  FX.arrowAnnotate(H, stage, { at: H.at("intro+0.3"), from: { x: 620, y: 560 }, target: a, label: "Start", bow: -0.22 });
  FX.arrowAnnotate(H, stage, { at: H.at("point+0.2"), from: { x: 620, y: 700 }, target: b, label: "End", bow: 0.22, seed: 7 });
};
