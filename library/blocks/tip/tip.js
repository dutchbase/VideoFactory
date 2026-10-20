// Numbered tip block (accent, ink border, hard shadow). Title words come in with the voice (H.say).
(function () {
  window.Blocks = window.Blocks || {};
  window.Blocks.tip = function (H, root, o) {
    const el = H.mk("div", "b-tip b-hide", root);
    H.mk("div", "b-tip-nr", el, String(o.nr));
    const col = H.mk("div", "b-tip-col", el);
    const title = H.mk("div", "b-tip-title", col, o.words ? null : o.title);
    if (o.words) H.say(title, o.words[0], o.words[1]);
    if (o.sub) H.say(H.mk("div", "b-tip-sub", col), o.sub[0], o.sub[1]);
    return {
      el,
      enter(at) { H.tl.fromTo(el, { autoAlpha: 1, x: 420 }, { x: 0, duration: 0.22, ease: "power4.out", immediateRender: false }, at); },
      exit(at) { H.tl.to(el, { x: -420, duration: 0.12, ease: "power4.in" }, at - 0.12); H.hide(el, at); },
    };
  };
})();
