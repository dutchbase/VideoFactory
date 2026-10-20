// textcheck.js - injected only by `anim.py check`. Records every string drawn this frame as a box in frame pixels:
// canvas fillText/strokeText (through the context transform and the canvas's CSS scale) and visible DOM text.
// Idea: cth9191/animate tools/textcheck.mjs (MIT, licenses/animate-LICENSE.txt).
(() => {
  const seen = []; let unmapped = 0;
  const C = CanvasRenderingContext2D.prototype;
  for (const fn of ['fillText', 'strokeText']) {
    const orig = C[fn];
    C[fn] = function (s, x, y) {
      orig.apply(this, arguments);
      s = String(s);
      const m0 = /rgba\([^)]*,\s*([\d.]+)\)$/.exec(String(fn === 'fillText' ? this.fillStyle : this.strokeStyle));
      if (!s.trim() || this.globalAlpha * (m0 ? +m0[1] : 1) < 0.05) return;  // invisible: alpha 0 in globalAlpha or the colour
      const c = this.canvas;
      if (!c.isConnected) { unmapped++; return; }  // offscreen buffer: copied later by drawImage, cannot map
      const r = c.getBoundingClientRect(), kx = r.width / c.width, ky = r.height / c.height;
      const m = this.measureText(s), T = this.getTransform();
      const x0 = x - m.actualBoundingBoxLeft, x1 = x + m.actualBoundingBoxRight;
      const y0 = y - m.actualBoundingBoxAscent, y1 = y + m.actualBoundingBoxDescent;
      const P = [[x0, y0], [x1, y0], [x0, y1], [x1, y1]].map(([a, b]) => [r.left + (T.a * a + T.c * b + T.e) * kx, r.top + (T.b * a + T.d * b + T.f) * ky]);
      const xs = P.map((p) => p[0]), ys = P.map((p) => p[1]);
      seen.push({ s, x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys) });
    };
  }
  window.__texts = () => {
    const out = seen.splice(0), u = unmapped; unmapped = 0;
    const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n = walk.nextNode(); n; n = walk.nextNode()) {
      const s = n.textContent.trim(), el = n.parentElement;
      if (!s || !el || el.closest('#anim-bar, #vf-bar, script, style') || !el.checkVisibility({ opacityProperty: true, visibilityProperty: true })) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      const b = rg.getBoundingClientRect();
      if (b.width && b.height) out.push({ s, x0: b.left, y0: b.top, x1: b.right, y1: b.bottom });
    }
    const skip = new Set(window.CHECK_IGNORE || []);
    return { boxes: out.filter((b) => !skip.has(b.s)), unmapped: u };
  };
})();
