// Demo for library/fx/_demo/{modern,hf}.html?fx=text/marker-highlight.
window.FX_DEMO = function (H, stage) {
  const mk = (text, top, size) => {
    const el = document.createElement("div");
    el.textContent = text;
    el.style.cssText = `position:absolute;left:10%;top:${top}%;width:80%;font:800 ${size}px/1.3 var(--head);color:var(--ink)`;
    stage.appendChild(el);
    return el;
  };
  FX.markerHighlight(H, mk("Every part moves on the voice.", 22, 92), { at: H.at("intro+0.3"), phrase: "moves on the voice" });
  FX.markerHighlight(H, mk("Here is the point.", 50, 92), { at: H.at("@here"), phrase: "the point", variant: "knockout" });
  FX.markerHighlight(H, mk("And done.", 70, 92), { at: H.at("outro+0.2"), phrase: "done", variant: "underline" });
};
