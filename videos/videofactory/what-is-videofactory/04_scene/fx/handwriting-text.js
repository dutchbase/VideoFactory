// Handwriting text: a line is written letter by letter, with a pen dot on the wet edge. Rewritten from RemotionUI HandwritingText (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.handwritingText = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at);
    const per = o.perChar == null ? 0.07 : o.perChar;
    const wobble = o.wobble == null ? 1.4 : o.wobble, pen = o.pen == null ? 0.1 : o.pen;
    const rand = K.rand(o.seed == null ? 1 : o.seed);
    el.classList.add("fx-hand");
    if (getComputedStyle(el).position === "static") el.style.position = "relative";
    const parts = K.split(el, "chars", "fx-hand-char");
    const n = parts.length, total = o.dur == null ? n * per : o.dur, step = total / Math.max(1, n);
    parts.forEach((part, i) => {
      const glyph = part.textContent;
      part.textContent = "";
      const ink = H.mk("span", "fx-hand-ink", part, glyph);
      const nib = H.mk("span", "fx-hand-pen", part);
      nib.style.background = K.color(o.penColor, "accent");
      nib.style.width = nib.style.height = pen + "em";
      nib.style.marginLeft = (-pen / 2) + "em";
      part.style.rotate = ((rand() * 2 - 1) * wobble).toFixed(3) + "deg";
      part.style.translate = "0 " + ((rand() * 2 - 1) * wobble * 0.012).toFixed(4) + "em";
      const s = at + i * step;
      H.tl.fromTo(ink, { clipPath: "inset(-20% 100% -20% -20%)" }, { clipPath: "inset(-20% -20% -20% -20%)", duration: step, ease: "none", immediateRender: true }, s);
      if (pen > 0) {
        H.tl.set(nib, { autoAlpha: 0 }, 0);
        H.tl.fromTo(nib, { left: "0%" }, { left: "100%", duration: step, ease: "none", immediateRender: true }, s);
        H.tl.set(nib, { autoAlpha: 1 }, s);
        H.tl.set(nib, { autoAlpha: 0 }, s + step);
      }
    });
    let end = at + total;
    if (o.underline) {
      const ns = "http://www.w3.org/2000/svg";
      const svg = document.createElementNS(ns, "svg");
      svg.setAttribute("class", "fx-hand-line");
      svg.setAttribute("viewBox", "0 0 1000 40");
      svg.setAttribute("preserveAspectRatio", "none");
      const path = document.createElementNS(ns, "path");
      path.setAttribute("d", "M 8 24 C 160 10, 330 34, 500 20 S 840 12, 992 22");
      path.setAttribute("pathLength", "1");
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", K.color(o.lineColor, "accent"));
      path.setAttribute("stroke-width", "7");
      path.setAttribute("stroke-dasharray", "1");
      svg.appendChild(path);
      el.appendChild(svg);
      const ld = o.lineDur == null ? 0.5 : o.lineDur;
      H.tl.fromTo(path, { strokeDashoffset: 1, autoAlpha: 0 }, { strokeDashoffset: 0, autoAlpha: 1, duration: ld, ease: "power2.out", immediateRender: true }, end + 0.08);
      end += 0.08 + ld;
    }
    return { el, parts, end };
  };
})();
