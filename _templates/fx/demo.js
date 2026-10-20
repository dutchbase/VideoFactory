// Demo for library/fx/_demo/{modern,hf}.html?fx=<category>/<id>. Builds its own markup on the stage.
window.FX_DEMO = function (H, stage) {
  const el = document.createElement("div");
  el.className = "fx-<id>";
  el.textContent = "Every part moves on the voice.";
  el.style.cssText = "position:absolute;left:160px;top:420px;font-size:96px;font-weight:800";
  stage.appendChild(el);
  FX.<camelId>(H, el, { at: H.at("intro+0.3") });
};
