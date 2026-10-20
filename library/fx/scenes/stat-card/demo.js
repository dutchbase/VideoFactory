// Demo for library/fx/_demo/{modern,hf}.html?fx=scenes/stat-card. One card, then a second one at the point cue.
window.FX_DEMO = function (H, stage) {
  const card = () => {
    const el = document.createElement("div");
    el.style.cssText = "position:absolute;left:60px;top:60px;width:1800px;height:960px";
    stage.appendChild(el);
    return el;
  };
  const a = card(), b = card();
  FX.statCard(H, a, { at: H.at("intro+0.3"), value: 12480, label: "words placed on cue" });
  H.tl.fromTo(a, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.01, immediateRender: false }, H.at("point"));
  FX.statCard(H, b, { at: H.at("point+0.1"), value: 98, suffix: "%", label: "of cues land on the word" });
};
