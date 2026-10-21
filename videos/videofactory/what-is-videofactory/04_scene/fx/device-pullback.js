// Device pullback: shot A starts large (about 3x), pulls back slowly, then snaps in one frame into a device frame (cut K6); a hard cut to shot B follows.
// Rewritten from Onda DevicePullback (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  // Device sizes in stage px: bezel, outer corner radius, screen corner radius, base height under the screen.
  const DEVICE = {
    laptop: { bezel: 22, radius: 26, screen: 10, base: 34 },
    phone: { bezel: 34, radius: 76, screen: 46, base: 0 },
  };
  FX.devicePullback = function (H, from, to, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 1 : o.dur, hold = o.hold == null ? 0.6 : o.hold;
    const snapAt = at + dur, cut = snapAt + hold;
    const dev = DEVICE[o.device] || DEVICE.laptop, start = o.start == null ? 3 : o.start, ratio = K.clamp(o.ratio == null ? 0.56 : o.ratio, 0.3, 0.95);
    const fx = K.clamp(o.focus && o.focus[0] != null ? o.focus[0] : 0.5), fy = K.clamp(o.focus && o.focus[1] != null ? o.focus[1] : 0.5);
    const { w, h } = K.size(to);
    // The framed screen: as large as the stage allows with the bezel and the base around it.
    const F = Math.min((w * 0.82 - 2 * dev.bezel) / w, (h * 0.86 - 2 * dev.bezel - dev.base) / h);
    const sw = F * w, sh = F * h, totalH = sh + 2 * dev.bezel + dev.base;
    const shellTop = (h - totalH) / 2, ty = shellTop + dev.bezel + sh / 2 - h / 2;
    const s1 = F / ratio;   // the slow part ends here; the last step to F is one frame

    // The device sits under shot A: ground, bezel, base and a camera dot.
    const parent = from.parentNode;
    const wrap = document.createElement("div");
    wrap.className = "fx-device";
    const box = (cls, css) => { const d = document.createElement("div"); d.className = cls; d.style.cssText = css; wrap.appendChild(d); return d; };
    box("fx-device-ground", `background:var(--${o.ground || "cream"})`);
    const shell = box("fx-device-shell", `left:${(w - sw) / 2 - dev.bezel}px;top:${shellTop}px;width:${sw + 2 * dev.bezel}px;height:${sh + 2 * dev.bezel}px;border-radius:${dev.radius}px;background:var(--${o.frame || "line"})`);
    if (dev.base) box("fx-device-base", `left:${(w - sw) / 2 - dev.bezel - 60}px;top:${shellTop + sh + 2 * dev.bezel}px;width:${sw + 2 * dev.bezel + 120}px;height:${dev.base}px;border-radius:0 0 28px 28px;background:var(--${o.frame || "line"})`);
    else box("fx-device-dot", `left:${w / 2 - 60}px;top:${shellTop + dev.bezel / 2 - 7}px;width:120px;height:14px;border-radius:7px;background:var(--${o.ground || "cream"})`);
    parent.insertBefore(wrap, from);
    wrap.style.zIndex = "1"; from.style.zIndex = "2"; to.style.zIndex = "3";
    void shell;

    function draw(p, t) {
      if (t < snapAt) {
        // slow pull-back: scale shrinks at a constant rate (in log space), the focus point drifts to its place
        const e = K.clamp((t - at) / dur), s = start * Math.pow(s1 / start, e);
        const x0 = -start * (fx - 0.5) * w, y0 = -start * (fy - 0.5) * h;
        gsap.set(from, { scale: s, x: x0 * (1 - e), y: y0 * (1 - e) + ty * e, transformOrigin: "50% 50%" });
        from.style.clipPath = "none";
        wrap.style.visibility = "hidden";
      } else {
        // the snap: one frame, scale x ratio, the frame appears around the screen
        gsap.set(from, { scale: F, x: 0, y: ty, transformOrigin: "50% 50%" });
        from.style.clipPath = `inset(0 round ${dev.screen / F}px)`;
        wrap.style.visibility = t < cut ? "visible" : "hidden";
      }
    }
    draw(0, at);
    H.tl.fromTo(to, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.001, immediateRender: true }, cut);
    H.tl.fromTo(from, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.001, immediateRender: false }, cut);
    H.drive(draw, at, cut);
    return { wrap, snap: snapAt, cut };
  };
})();
