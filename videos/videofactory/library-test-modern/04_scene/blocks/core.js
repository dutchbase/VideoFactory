// Core helpers for HyperFrames scenes: voice timing, show/hide, snap-ins, typing and streaming text.
// Every other block takes the H this returns. Style: hard snap-ins (power4), hard cuts, no fades (_shared/motion.md).
// Rules for all blocks: brand CSS vars only, class names start with b-, no ids, never assign a media source or volume (render check).
(function () {
  window.Blocks = window.Blocks || {};
  window.Blocks.core = function (tl, words) {
    const WD = words || (window.ANIM && window.ANIM.words) || [];
    const H = { tl, WD, PRE: 0.04 };
    H.ws = i => WD[i].start;  // start second of word i (ANIM.words from 03_cues/cues.js)
    H.we = i => WD[i].end;
    H.mk = (tag, cls, parent, text) => {
      const e = document.createElement(tag);
      if (cls) e.className = cls;
      if (text != null) e.textContent = text;
      if (parent) parent.appendChild(e);
      return e;
    };
    // A time as seconds: a number, "cue", "cue+0.4" or "@word" (first spoken word that starts with it). The Modern kit resolves it
    // with Modern.at; HyperFrames with cue() from hf-bridge.js.
    H.at = x => {
      if (typeof x === "number") return x;
      if (window.Modern) return window.Modern.at(x);
      const m = /^(.*?)([+-]\d*\.?\d+)?$/.exec(String(x).trim()), off = m[2] ? parseFloat(m[2]) : 0;
      if (!m[1].startsWith("@")) return window.cue(m[1]) + off;
      const w = m[1].slice(1).toLowerCase(), hit = WD.find(d => d.text.toLowerCase().replace(/[^a-z0-9']/g, "").startsWith(w));
      if (!hit) throw new Error(`core: no spoken word starts with "${w}"`);
      return hit.start + off;
    };
    // Per-frame drawing (canvas, particles): fn(p, t) with progress p 0..1 and time t, on every seek from t0 to t1.
    // Both engines seek with callbacks off, so this tweens a setter function instead of using onUpdate. fn must redraw
    // everything from p and t alone.
    H.drive = (fn, t0, t1) => {
      let v = 0;
      const box = { p(x) { if (x === undefined) return v; v = x; fn(x, t0 + x * (t1 - t0)); } };
      return tl.fromTo(box, { p: 0 }, { p: 1, duration: Math.max(1e-3, t1 - t0), ease: "none", immediateRender: false }, t0);
    };
    H.show = (el, at) => tl.set(el, { autoAlpha: 1 }, at);
    H.hide = (el, at) => tl.set(el, { autoAlpha: 0 }, at);
    H.disp = (el, d, at) => tl.set(el, { display: d }, at);
    H.snap = (el, at, from = { y: 34 }, dur = 0.16) =>
      tl.fromTo(el, { autoAlpha: 0, ...from }, { autoAlpha: 1, x: 0, y: 0, scale: 1, duration: dur, ease: "power4.out", immediateRender: false }, at);
    // typing: one span per character, shown on its time; cls "b-hot" colours it with the accent
    H.chars = (parent, text, cls) => Array.from(text, c => H.mk("span", "b-ch" + (cls ? " " + cls : ""), parent, c));
    H.type = (spans, t0, t1) => { const dt = (t1 - t0) / spans.length; spans.forEach((s, i) => tl.set(s, { display: "inline" }, t0 + i * dt)); };
    H.untype = (spans, t0, t1) => { const dt = (t1 - t0) / spans.length; spans.slice().reverse().forEach((s, i) => tl.set(s, { display: "none" }, t0 + i * dt)); };
    H.wipe = (spans, at) => tl.set(spans, { display: "none" }, at);
    // streaming: one span per word (trailing space inside, so an underline runs on); "\n\n" starts a paragraph
    H.words = (parent, text) => {
      const out = [];
      text.split("\n\n").forEach(para => {
        const p = H.mk("p", "b-p", parent), list = para.split(" ");
        list.forEach((w, i) => out.push(H.mk("span", "b-aw", p, i < list.length - 1 ? w + " " : w)));
      });
      return out;
    };
    H.stream = (spans, t0, t1) => tl.to(spans, { opacity: 1, duration: 0.03, ease: "none", stagger: (t1 - t0) / spans.length, immediateRender: false }, t0);
    // spoken words a..b-1 snap in on their own time; the word being said is the accent (allHot: all accent)
    H.say = (parent, a, b, allHot) => {
      const out = [];
      for (let i = a; i < b; i++) {
        if (i > a) parent.appendChild(document.createTextNode(" "));
        const s = H.mk("span", "b-w" + (allHot ? " b-hot" : ""), parent, WD[i].text);
        H.snap(s, Math.max(0, H.ws(i) - H.PRE), { y: 30 }, 0.12);
        if (!allHot) {
          tl.set(s, { attr: { class: "b-w b-hot" } }, Math.max(0, H.ws(i) - H.PRE));
          if (i + 1 < b) tl.set(s, { attr: { class: "b-w" } }, H.ws(i + 1) - H.PRE);
        }
        out.push(s);
      }
      return out;
    };
    return H;
  };
})();
