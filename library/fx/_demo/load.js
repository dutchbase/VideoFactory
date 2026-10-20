// Loads one fx part into a demo page: library/fx/_demo/{modern,hf}.html?fx=<category>/<id>&format=wide|tall&brand=<brand>.
// The part's demo.js sets window.FX_DEMO = (H, stage) => {...} and may set window.FX_DEMO_DURATION (seconds).
window.FXDemo = (function () {
  const q = new URLSearchParams(location.search);
  const fx = q.get("fx") || "";
  if (!/^[a-z0-9-]+\/[a-z0-9-]+$/.test(fx)) throw new Error("fx demo: add ?fx=<category>/<id> to the URL");
  const id = fx.split("/")[1];
  const tall = q.get("format") === "tall";
  const stage = document.getElementById("stage");
  stage.dataset.width = tall ? 1080 : 1920;
  stage.dataset.height = tall ? 1920 : 1080;
  stage.dataset.format = tall ? "tall" : "wide";  // modern.js read the size before this file ran
  const add = (tag, attrs, optional) => new Promise((res, rej) => {
    const e = Object.assign(document.createElement(tag), attrs);
    e.onload = () => res(e);
    e.onerror = () => (optional ? res(null) : rej(new Error("fx demo: cannot load " + (attrs.src || attrs.href))));
    document.head.appendChild(e);
  });
  const base = "../" + fx + "/";
  function load() {
    const files = (window.FX_PARTS || {})[fx];
    if (!files) return Promise.reject(new Error("fx demo: " + fx + " is not in parts.js. Run: python anim.py lib index"));
    return files.reduce((chain, f) => chain.then(() => (f.endsWith(".css")
      ? add("link", { rel: "stylesheet", href: "../../" + f }) : add("script", { src: "../../" + f }))), Promise.resolve())
      .then(() => add("script", { src: base + "demo.js" }));
  }
  return { id, fx, stage, load, duration: () => window.FX_DEMO_DURATION || window.ANIM.meta.duration };
})();
