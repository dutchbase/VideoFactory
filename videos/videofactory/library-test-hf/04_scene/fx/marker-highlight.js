// Marker highlight: a highlighter stroke sweeps across chosen words one after another (marker, knockout, underline or box). Rewritten from RemotionUI marker-highlight (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const norm = w => w.toLowerCase().replace(/[^\p{L}\p{N}]/gu, "");
  FX.markerHighlight = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 0.45 : o.dur;
    const stagger = o.stagger == null ? 0.16 : o.stagger;
    const soft = o.softness == null ? 12 : o.softness;
    const variant = ["marker", "knockout", "underline", "box"].includes(o.variant) ? o.variant : "marker";
    const text = o.text != null ? o.text : el.textContent;
    const words = text.trim().split(/\s+/);
    let marked = words.map(() => !o.phrase);
    if (o.phrase) {
      const pw = o.phrase.trim().split(/\s+/).map(norm);
      for (let i = 0; i + pw.length <= words.length; i++) {
        if (pw.every((w, k) => norm(words[i + k]) === w)) { marked = words.map((_, j) => j >= i && j < i + pw.length); break; }
      }
      if (!marked.some(Boolean)) marked = words.map(() => true);
    }
    el.textContent = "";
    el.classList.add("fx-marker-highlight", "fx-marker-highlight-" + variant);
    el.style.setProperty("--fx-mh-soft", soft);
    el.style.setProperty("--fx-mh-color", FX.kit.color(o.markerColor, variant === "knockout" ? "ink" : "accent"));
    el.style.setProperty("--fx-mh-flip", FX.kit.color(o.flipColor, "cream"));
    const wraps = [];
    words.forEach((w, i) => {
      if (i) el.appendChild(document.createTextNode(" "));
      const wrap = H.mk("span", "fx-marker-highlight-word", el);
      if (marked[i]) {
        const join = marked[i + 1] ? " fx-marker-highlight-join" : "";
        H.mk("span", "fx-marker-highlight-band" + join, wrap);
        H.mk("span", "fx-marker-highlight-label", wrap, w);
        if (variant === "knockout") H.mk("span", "fx-marker-highlight-flip", wrap, w);
        wraps.push(wrap);
      } else H.mk("span", "fx-marker-highlight-label", wrap, w);
    });
    wraps.forEach((wrap, k) => H.tl.fromTo(wrap, { "--fx-mh-p": 0 },
      { "--fx-mh-p": 100 + soft, duration: dur, ease: "power3.out", immediateRender: true }, at + k * stagger));
    return { el, words: wraps, end: at + (wraps.length - 1) * stagger + dur };
  };
})();
