// Code block: syntax-highlighted code that types itself (or appears line by line). Rewritten from Onda CodeBlock (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const KEYWORDS = new Set(("const let var function return if else for while of in new class extends import export from default async await " +
    "true false null undefined this typeof as def print pass elif lambda with try catch throw yield switch case break continue").split(" "));
  // one ordered pattern: comment, string, number, word, anything else. Same text, same tokens, no async.
  const re = lang => new RegExp((lang === "py" ? "(#.*)" : "(\\/\\/.*)") + "|(\"(?:\\\\.|[^\"\\\\])*\"|'(?:\\\\.|[^'\\\\])*'|`[^`]*`)|(\\b\\d[\\d._]*\\b)|([A-Za-z_$][\\w$]*)|(\\s+|[^\\s])", "g");
  function tokenize(line, lang) {
    const out = [], rx = re(lang);
    let m;
    while ((m = rx.exec(line))) {
      if (m[1]) out.push({ t: m[1], c: "com" });
      else if (m[2]) out.push({ t: m[2], c: "str" });
      else if (m[3]) out.push({ t: m[3], c: "num" });
      else if (m[4]) out.push({ t: m[4], c: KEYWORDS.has(m[4]) ? "kw" : "id" });
      else out.push({ t: m[5], c: "p" });
    }
    return out;
  }

  FX.codeBlock = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at);
    const code = o.code == null ? "const answer = 42;" : String(o.code);
    const rows = code.split("\n");
    const by = o.by || "chars", lead = o.lead == null ? 0.3 : o.lead;
    const total = rows.reduce((n, r) => n + r.length + 1, 0);
    const typeDur = o.typeDur == null ? Math.max(1, total / 45) : o.typeDur;
    const { w: W } = K.size(el);
    const fs = o.size == null ? 40 : o.size, width = o.width == null ? Math.min(1500, W - 120) : o.width;

    const wrap = H.mk("div", "fx-code", el);
    const win = H.mk("div", "fx-code-win", wrap);
    win.style.cssText = `width:${width}px;font-size:${fs}px`;
    if (o.x != null || o.y != null) { wrap.style.display = "block"; win.style.position = "absolute"; win.style.left = (o.x || 0) + "px"; win.style.top = (o.y || 0) + "px"; }
    if (o.chrome !== false) {
      const bar = H.mk("div", "fx-code-bar", win);
      for (let i = 0; i < 3; i++) H.mk("span", "fx-code-dot", bar);
      if (o.title) H.mk("span", "fx-code-title", bar, o.title);
    }
    const body = H.mk("div", "fx-code-body", win);
    // one div per line, one span per token; the spans start empty and get their text from the clock
    const lines = rows.map((row, i) => {
      const div = H.mk("div", "fx-code-line", body);
      if (o.lineNumbers) H.mk("span", "fx-code-ln", div, String(i + 1));
      let pos = 0;
      const toks = tokenize(row, o.lang).map(tk => { const e = H.mk("span", "fx-code-" + tk.c, div); const r = { e, text: tk.t, start: pos, shown: -1 }; pos += tk.t.length; return r; });
      return { div, toks, len: row.length };
    });

    const t0 = at + lead;
    let starts = [], acc = 0;
    rows.forEach(r => { starts.push(acc); acc += r.length + 1; });
    function show(i, n) {  // show the first n characters of line i
      lines[i].toks.forEach(tk => {
        const k = Math.max(0, Math.min(tk.text.length, n - tk.start));
        if (k !== tk.shown) { tk.e.textContent = tk.text.slice(0, k); tk.shown = k; }
      });
    }
    if (by === "lines") {
      const stagger = o.stagger == null ? 0.2 : o.stagger;
      lines.forEach((l, i) => { show(i, l.len); H.tl.fromTo(l.div, { autoAlpha: 0, y: 10 }, { autoAlpha: 1, y: 0, duration: 0.2, ease: "power3.out", immediateRender: true }, t0 + i * stagger); });
    } else {
      // every character of every line shows on its own time; typing is linear
      const draw = (p, t) => {
        const n = Math.floor(K.clamp((t - t0) / typeDur) * total + 1e-9);
        lines.forEach((l, i) => show(i, Math.max(0, Math.min(l.len, n - starts[i]))));
      };
      draw(0, t0);
      H.drive(draw, t0, t0 + typeDur);
    }
    H.tl.fromTo(win, { autoAlpha: 0, y: 28 }, { autoAlpha: 1, y: 0, duration: 0.35, ease: "power4.out", immediateRender: true }, at);
    return { el: win, lines: lines.map(l => l.div), end: t0 + (by === "lines" ? rows.length * (o.stagger == null ? 0.2 : o.stagger) : typeDur) };
  };
})();
