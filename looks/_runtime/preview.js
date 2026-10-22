// Look preview runtime: turns window.BrandTokens into CSS variables for one still frame.
// `anim.py looks board` injects brands/<id>/tokens.js before the page loads. Opened by hand, the page uses the neutral fallback.
// Variables: --bg --surface --raised --ink --dim --faint --line --accent --accent2 --green --danger --r0..--r7
//            --font --head --mono --hand --g0a/--g0b..--g4a/--g4b   Text: [data-brand="name"]
(function () {
  const fallback = {
    name: 'Your Brand', bg: '#111318', surface: '#1B1E26', raised: '#262A35', ink: '#F4F5F8', dim: '#C3C7D1',
    faint: '#8A90A0', line: '#333846', accent: '#4F7DF3', accent2: '#F2A93B', green: '#2ECC8A', danger: '#E0614B',
    ramp: ['#111318', '#1B1E26', '#24408F', '#4F7DF3', '#8EAAF7', '#C9D6FB', '#F4F5F8', '#FFFFFF'],
    font: '"Inter", system-ui, sans-serif', head: '"Inter", system-ui, sans-serif',
    mono: '"JetBrains Mono", ui-monospace, monospace', hand: '"Caveat", cursive',
    grads: [['#4F7DF3', '#C9D6FB'], ['#F2A93B', '#F7D79B']],
  };
  const T = Object.assign({}, fallback, window.BrandTokens || {});
  const s = document.documentElement.style;
  for (const k of ['bg', 'surface', 'raised', 'ink', 'dim', 'faint', 'line', 'accent', 'accent2', 'green', 'danger', 'font', 'head', 'mono', 'hand'])
    s.setProperty('--' + k, T[k]);
  (T.ramp || fallback.ramp).forEach((c, i) => s.setProperty('--r' + i, c));
  (T.grads || fallback.grads).forEach((g, i) => { s.setProperty(`--g${i}a`, g[0]); s.setProperty(`--g${i}b`, g[1]); });
  const W = 1280, H = 720;
  window.__seek = () => {};
  addEventListener('DOMContentLoaded', async () => {
    document.querySelectorAll('[data-brand="name"]').forEach(el => { el.textContent = T.name; });
    await document.fonts.ready;
    window.__size = { w: W, h: H };
    window.__ready = true;
  });
})();
