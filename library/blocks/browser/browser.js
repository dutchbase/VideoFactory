// A browser window for real captures (anim.py grab / record). The address bar shows the domain only, never a path or query.
// play() shows recorded frames by switching preloaded <img> elements, so every frame is loaded before the render reads it.
(function () {
  window.Blocks = window.Blocks || {};
  window.Blocks.browser = function (H, root, o) {
    o = o || {};
    const tl = H.tl;
    const el = H.mk("div", "b-browser", root);
    const bar = H.mk("div", "b-browser-bar", el);
    for (let i = 0; i < 3; i++) H.mk("span", "b-browser-dot", bar);
    let domain = "";
    try { domain = new URL(o.url).hostname.replace(/^www\./, ""); } catch (e) { domain = ""; }
    H.mk("span", "b-browser-url", bar, domain);
    const view = H.mk("div", "b-browser-view", el);
    const inner = H.mk("div", "b-browser-inner", view);
    const img = src => { const i = H.mk("img", "b-browser-frame", inner); i.setAttribute("src", src); i.setAttribute("alt", ""); return i; };
    return {
      el, view, inner,
      // frames: paths inside 04_scene (e.g. assets/chat/f001.jpg); the last frame stays
      play(frames, fps, t0) {
        const imgs = frames.map(img);
        imgs.forEach((f, i) => {
          tl.set(f, { display: "block" }, t0 + i / fps);
          if (i + 1 < imgs.length) tl.set(f, { display: "none" }, t0 + (i + 1) / fps);
        });
        return imgs;
      },
      image(src, at) { const f = img(src); tl.set(f, { display: "block" }, at); return f; },
      // zoom to a rect of the view (px): x, y, w; h follows the view's aspect
      zoom(rect, at, dur = 0.8) {
        const s = view.clientWidth / rect.w;
        tl.to(inner, { scale: s, x: -rect.x * s, y: -rect.y * s, transformOrigin: "0 0", duration: dur, ease: "power3.inOut" }, at);
      },
    };
  };
})();
