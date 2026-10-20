// Full-root accent panel as a hard transition: slides in from the right, lines snap in, leaves to the left.
(function () {
  window.Blocks = window.Blocks || {};
  window.Blocks.panel = function (H, root, o) {
    const w = root.clientWidth || 1080;
    const el = H.mk("div", "b-panel b-hide", root);
    const big = H.mk("div", "b-panel-big", el);
    const lines = o.lines.map(t => H.mk("span", "b-panel-line", big, t));
    return {
      el,
      enter(at) {
        H.tl.fromTo(el, { autoAlpha: 1, x: w }, { x: 0, duration: 0.2, ease: "power4.out", immediateRender: false }, at - 0.06);
        lines.forEach((s, i) => H.snap(s, o.wordIdx ? H.ws(o.wordIdx[i]) - H.PRE : at + 0.05 + i * 0.3, { y: 40 }, 0.14));
      },
      exit(at) { H.tl.to(el, { x: -w, duration: 0.18, ease: "power4.in" }, at - 0.2); H.hide(el, at); },
    };
  };
})();
