// A stamp that slams onto the picture (scale 1.9 -> 1, power4.in), optionally shaking another element on impact.
(function () {
  window.Blocks = window.Blocks || {};
  window.Blocks.stamp = function (H, root, o) {
    const el = H.mk("div", "b-stamp b-hide", root, o.text);
    if (o.x != null) el.style.left = o.x + "px";
    if (o.y != null) el.style.top = o.y + "px";
    const rot = o.rotation == null ? -8 : o.rotation;
    return {
      el,
      slam(at) {  // lands on `at`, so put the stamp sound effect on the same cue
        H.tl.fromTo(el, { autoAlpha: 0, scale: 1.9, rotation: rot }, { autoAlpha: 1, scale: 1, rotation: rot, duration: 0.12, ease: "power4.in", immediateRender: false }, at - 0.08);
        if (o.shake) [-12, 9, -4, 0].forEach((x, i) => H.tl.to(o.shake, { x, duration: 0.03 }, at + 0.04 + i * 0.03));
      },
      clear(at) { H.hide(el, at); },
    };
  };
})();
