// image-size.js - one design, many sizes. Load first, before brand/tokens.js and runtime/player.js.
// `python anim.py image export` opens design.html?render&size=WxH&safe=top,right,bottom,left&shape=rect|circle&id=<size-id>&layout=<class>.
// Open design.html?size=1584x396&guides in a browser to preview one size with the safe area drawn.
// It sets on #stage: data-width/height, the class vf-image, a layout class (is-avatar, is-banner, is-wide, is-square,
// is-portrait, is-tall: from the safe area, the same rule as studio/images.py ratio_class), shape-rect|shape-circle,
// data-size=<size-id>, and the CSS variables --w --h --u (short side of the safe area / 100) and --safe-top/right/bottom/left.
// design.js reads the same facts from window.VF_IMAGE.
(() => {
  const q = new URLSearchParams(location.search);
  const stage = document.getElementById('stage');
  if (!stage) return;
  const m = /^(\d{2,4})x(\d{2,4})$/.exec(q.get('size') || '');
  const W = m ? +m[1] : +stage.dataset.width || 1080;
  const H = m ? +m[2] : +stage.dataset.height || 1080;
  const [top, right, bottom, left] = (q.get('safe') || '0,0,0,0').split(',').map((v) => Math.max(0, +v || 0));
  const shape = q.get('shape') === 'circle' ? 'circle' : 'rect';
  let box = { x: left, y: top, w: W - left - right, h: H - top - bottom };
  if (shape === 'circle') {  // a round crop keeps content inside the square that fits in the circle
    const d = Math.min(box.w, box.h), s = d * Math.SQRT1_2;
    box = { x: box.x + (box.w - s) / 2, y: box.y + (box.h - s) / 2, w: s, h: s };
  }
  const r = box.w / box.h;
  const layouts = ['is-avatar', 'is-banner', 'is-wide', 'is-square', 'is-portrait', 'is-tall'];
  const cls = layouts.includes(q.get('layout')) ? q.get('layout') : shape === 'circle' ? 'is-avatar' : r >= 2.4 ? 'is-banner' : r > 1.15 ? 'is-wide' : r >= 0.87 ? 'is-square' : r >= 0.62 ? 'is-portrait' : 'is-tall';
  const id = q.get('id') || '';

  stage.dataset.width = W;
  stage.dataset.height = H;
  if (id) stage.dataset.size = id;
  stage.classList.add('vf-image', cls, 'shape-' + shape);
  const css = { '--w': W, '--h': H, '--u': Math.min(box.w, box.h) / 100,
    '--safe-top': box.y, '--safe-left': box.x, '--safe-right': W - box.x - box.w, '--safe-bottom': H - box.y - box.h };
  for (const [k, v] of Object.entries(css)) stage.style.setProperty(k, v + 'px');

  if (q.has('guides')) {
    const g = document.createElement('div');
    g.className = 'vf-safe';
    stage.appendChild(g);
  }
  window.ANIM = window.ANIM || { meta: { duration: 1 }, cueList: [] };  // a still has no cues
  window.VF_IMAGE = { id, w: W, h: H, box, cls, shape, guides: q.has('guides') };
})();
