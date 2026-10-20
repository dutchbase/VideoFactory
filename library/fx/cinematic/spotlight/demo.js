// Demo for library/fx/_demo/{modern,hf}.html?fx=cinematic/spotlight. Three tiles; the light picks one, then moves on to the next.
window.FX_DEMO = function (H, stage) {
  const head = document.createElement("div");
  head.textContent = "Look at one thing.";
  head.style.cssText = "position:absolute;left:120px;top:110px;width:1500px;font:800 100px/1.08 var(--head);color:var(--ink)";
  stage.appendChild(head);
  const tile = (x, text) => {
    const e = document.createElement("div");
    e.textContent = text;
    e.style.cssText = `position:absolute;left:${x}px;top:520px;width:480px;height:360px;display:flex;align-items:center;justify-content:center;` +
      "border-radius:28px;border:3px solid var(--line);background:color-mix(in srgb, var(--ink) 8%, var(--cream));font:700 64px/1 var(--head);color:var(--ink)";
    stage.appendChild(e);
    return e;
  };
  const a = tile(160, "Plan"), b = tile(720, "Build"), c = tile(1280, "Ship");
  FX.spotlight(H, stage, {
    at: H.at("intro+0.3"), shape: "rect", target: a, pad: 28,
    moves: [{ at: H.at("point+0.2"), target: b }, { at: H.at("outro"), target: c }],
    exitAt: 5.4, exitDur: 0.5,
  });
};
