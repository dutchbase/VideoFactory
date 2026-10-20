// Demo for library/fx/_demo/{modern,hf}.html?fx=backgrounds/particle-field.
window.FX_DEMO = function (H, stage) {
  FX.particleField(H, stage, { count: 90, color: "accent" });
  const el = document.createElement("div");
  el.textContent = "Calm depth behind your words.";
  el.style.cssText = "position:absolute;left:10%;top:42%;width:80%;font:800 88px/1.1 var(--head);color:var(--ink);z-index:1";
  stage.appendChild(el);
};
