// Demo for library/fx/_demo/{modern,hf}.html?fx=text/strikethrough-replace.
window.FX_DEMO = function (H, stage) {
  const mk = (text, top, size) => {
    const el = document.createElement("div");
    el.textContent = text;
    el.style.cssText = `position:absolute;left:10%;top:${top}%;width:80%;text-align:center;font:800 ${size}px/1.15 var(--head);color:var(--ink)`;
    stage.appendChild(el);
    return el;
  };
  FX.strikethroughReplace(H, mk("Ready in three weeks", 26, 104), { at: H.at("intro+0.4"), to: "Ready in three days" });
  FX.strikethroughReplace(H, mk("Costs a little extra", 52, 88), { at: H.at("@here"), to: "Costs nothing extra", replaceColor: "accent" });
};
