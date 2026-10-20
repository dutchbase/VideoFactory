// A phone frame (ink body, hard accent shadow, notch). `screen` is the box another block fills, e.g. chat "mobile".
(function () {
  window.Blocks = window.Blocks || {};
  window.Blocks.phone = function (H, root) {
    const el = H.mk("div", "b-phone", root);
    H.mk("div", "b-phone-notch", el);
    const screen = H.mk("div", "b-phone-screen", el);
    return { el, screen };
  };
})();
