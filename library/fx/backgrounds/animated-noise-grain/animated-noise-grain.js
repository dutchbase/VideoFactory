// Animated noise grain: film grain over the frame on a canvas. Each frame index has its own seeded pattern (same frame, same grain).
// Rewritten from RemotionUI AnimatedNoiseGrain (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.animatedNoiseGrain = function (H, root, o = {}) {
    const K = FX.kit;
    const from = H.at(o.from == null ? 0 : o.from);
    const to = o.to == null ? ((window.ANIM && window.ANIM.meta && window.ANIM.meta.duration) || 10) : H.at(o.to);
    const fps = o.fps || 30, hold = Math.max(1, Math.round(o.hold == null ? 2 : o.hold));
    const cell = Math.max(1, Math.round(o.size == null ? 2 : o.size));
    const strength = o.opacity == null ? 0.14 : o.opacity, vig = o.vignette == null ? 0.6 : o.vignette;
    const seed = o.seed == null ? 1 : o.seed;
    const { canvas, ctx, w, h } = K.canvas(root, "fx-animated-noise-grain");
    const gw = Math.ceil(w / cell), gh = Math.ceil(h / cell);
    const tile = document.createElement("canvas");
    tile.width = gw; tile.height = gh;
    const tctx = tile.getContext("2d"), img = tctx.createImageData(gw, gh), px = img.data;
    // extra grain toward the corners: alpha gain per pixel, worked out once
    const gain = new Float32Array(gw * gh);
    for (let y = 0, i = 0; y < gh; y++) for (let x = 0; x < gw; x++, i++) {
      const dx = x / gw - 0.5, dy = y / gh - 0.5;
      gain[i] = 1 + vig * 4 * (dx * dx + dy * dy);
    }
    ctx.imageSmoothingEnabled = false;
    function draw(p, t) {
      const frame = Math.floor((t - from) * fps + 1e-6), step = Math.floor(frame / hold);
      const r = K.rand(seed * 7919 + step * 104729);   // one pattern per held step: same frame, same grain
      for (let i = 0, j = 0; i < gw * gh; i++, j += 4) {
        const v = r();
        const hi = v > 0.5;
        px[j] = px[j + 1] = px[j + 2] = hi ? 255 : 0;
        px[j + 3] = Math.min(255, Math.abs(v - 0.5) * 2 * 255 * strength * gain[i]);
      }
      tctx.putImageData(img, 0, 0);
      ctx.clearRect(0, 0, w, h);
      ctx.drawImage(tile, 0, 0, gw * cell, gh * cell);
    }
    draw(0, from);
    H.drive(draw, from, to);
    return { canvas };
  };
})();
