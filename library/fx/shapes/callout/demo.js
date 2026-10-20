// Demo for library/fx/_demo/{modern,hf}.html?fx=shapes/callout. Builds its own markup on the stage.
window.FX_DEMO = function (H, stage) {
  const mk = (css, text) => {
    const e = document.createElement("div");
    e.textContent = text;
    e.style.cssText = "position:absolute;" + css;
    stage.appendChild(e);
    return e;
  };
  mk("left:120px;top:120px;width:1100px;font:800 96px/1.08 var(--head);color:var(--ink)", "Name the part you mean.");
  const card = "display:flex;align-items:center;justify-content:center;border-radius:28px;border:3px solid var(--line);" +
    "background:color-mix(in srgb, var(--ink) 8%, var(--cream));font:700 56px/1 var(--head);color:var(--ink)";
  const a = mk("left:160px;top:500px;width:520px;height:260px;" + card, "Panel one");
  const b = mk("left:1240px;top:500px;width:520px;height:260px;" + card, "Panel two");
  FX.callout(H, stage, { at: H.at("intro+0.3"), target: a, label: "Start here", position: "top-right", offset: 120 });
  FX.callout(H, stage, { at: H.at("point+0.2"), target: b, label: "Then this", position: "bottom-left", offset: 120 });
};
