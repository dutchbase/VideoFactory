// Oversized mouse cursor with a click ring. Positions are px in the root; the cursor tip is the point.
(function () {
  window.Blocks = window.Blocks || {};
  const ARROW = '<svg viewBox="0 0 60 90"><path d="M3 3 L3 72 L20 56 L32 84 L44 79 L32 52 L55 52 Z"/></svg>';
  window.Blocks.cursor = function (H, root) {
    const tl = H.tl, w = root.clientWidth || 1080, h = root.clientHeight || 1920;
    const el = H.mk("div", "b-cursor b-hide", root);
    el.innerHTML = ARROW;
    const ring = H.mk("div", "b-cursor-ring b-hide", root);
    let last = { x: w + 60, y: h * 0.8 };  // enters from the lower right
    return {
      el, ring,
      move(x, y, at, dur = 0.7) {
        tl.fromTo(el, { autoAlpha: 1, x: last.x, y: last.y }, { x, y, duration: dur, ease: "power3.out", immediateRender: false }, at);
        last = { x, y };
      },
      click(x, y, at) {  // squash on the press, ring on the release; put the cause (send, next scene) on `at`
        tl.to(el, { scale: 0.86, duration: 0.06, ease: "power2.in", transformOrigin: "0 0" }, at - 0.06);
        tl.to(el, { scale: 1, duration: 0.14, ease: "power3.out" }, at);
        tl.fromTo(ring, { autoAlpha: 1, x, y, scale: 0.3 }, { scale: 1.5, duration: 0.24, ease: "power2.out", immediateRender: false }, at);
        H.hide(ring, at + 0.24);
      },
      leave(at, dur = 0.3) {
        const to = { x: w + 80, y: last.y + 200 };
        tl.fromTo(el, { x: last.x, y: last.y }, { ...to, duration: dur, ease: "power4.in", immediateRender: false }, at);
        H.hide(el, at + dur);
        last = to;
      },
    };
  };
})();
