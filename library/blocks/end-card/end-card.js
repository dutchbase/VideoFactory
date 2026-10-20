// End card: crosshair mark plus wordmark, snapping in from the left. Hold it to the end of the video.
(function () {
  window.Blocks = window.Blocks || {};
  window.Blocks.endCard = function (H, root, o) {
    o = o || {};
    const el = H.mk("div", "b-mark b-hide", root);
    if (o.x != null) el.style.left = o.x + "px";
    if (o.y != null) el.style.top = o.y + "px";
    H.mk("span", "b-mark-cross", el);
    H.mk("span", "b-mark-word", el, o.wordmark || "");
    return { el, show(at) { H.snap(el, at, { x: -60 }, 0.16); } };
  };
})();
