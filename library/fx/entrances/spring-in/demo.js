// Demo for library/fx/_demo/{modern,hf}.html?fx=entrances/spring-in. One tile for each preset.
window.FX_DEMO = function (H, stage) {
  const tile = (name, x) => {
    const el = document.createElement("div");
    el.className = "fx-spring-in";
    el.textContent = name;
    el.style.cssText = `position:absolute;left:${x}px;top:340px;width:520px;height:300px;display:flex;align-items:center;justify-content:center;box-sizing:border-box;border:6px solid var(--accent);border-radius:28px;font:800 88px/1 var(--head);color:var(--ink)`;
    stage.appendChild(el);
    return el;
  };
  FX.springIn(H, tile("Snappy", 100), { at: H.at("intro+0.3"), config: "snappy" });
  FX.springIn(H, tile("Smooth", 700), { at: H.at("intro+1.0"), config: "smooth" });
  FX.springIn(H, tile("Bouncy", 1300), { at: H.at("@here"), config: "bouncy", from: 0.7 });
};
