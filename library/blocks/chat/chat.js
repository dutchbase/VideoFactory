// Rebuilt chat app screen, without logos: empty state, typing in the input, send, streaming answer.
// Variants: "dark" (ChatGPT-like), "light" (Claude-like), "mobile" (phone layout, dark).
// The chat fills its root; the caller positions and sizes the root (and moves a camera around it).
(function () {
  window.Blocks = window.Blocks || {};
  const ARROW = '<svg viewBox="0 0 24 24"><path d="M12 19V5M5 12l7-7 7 7"/></svg>';
  window.Blocks.chat = function (H, root, opts) {
    const o = Object.assign({ variant: "dark", title: "New chat", hello: "How can I help you?",
                              placeholder: "Ask anything", frame: true }, opts || {});
    const tl = H.tl;
    const el = H.mk("div", "b-chat b-chat--" + o.variant + (o.frame ? " b-chat--frame" : ""), root);
    const bar = H.mk("div", "b-chat-bar", el);
    H.mk("span", "b-chat-burger", bar);
    H.mk("span", "b-chat-title", bar, o.title);
    const hello = H.mk("div", "b-chat-hello", el, o.hello);
    const msgs = H.mk("div", "b-chat-msgs", el);
    const input = H.mk("div", "b-chat-input", el);
    const field = H.mk("div", "b-chat-field", input);
    const ph = H.mk("span", "b-chat-ph", field, o.placeholder);
    const send = H.mk("div", "b-chat-send", input);
    send.innerHTML = ARROW;
    const h = root.clientHeight || 810;
    const centerY = -Math.round(h - 76 - h * 0.55);  // input centre at 55% of the height, like an empty chat
    let segs = [];  // typed or pasted since the last clear
    const api = { el, input, msgs, send, field };

    api.center = at => tl.set(input, { y: centerY }, at);
    api.dock = (at, dur = 0.36) => tl.to(input, { y: 0, duration: dur, ease: "power3.inOut" }, at);
    api.showHello = at => H.show(hello, at);
    api.hideHello = at => H.hide(hello, at);
    // typed text: so.hot (accent), so.block (own line), so.struck (can get a strike, see strike/untype)
    api.typeInto = (text, t0, t1, so) => {
      so = so || {};
      const seg = H.mk("span", "b-chat-seg" + (so.block ? " b-chat-line" : "") + (so.struck ? " b-struck" : ""), field);
      const spans = H.chars(seg, text, so.hot ? "b-hot" : null);
      if (so.struck) H.mk("span", "b-strike", seg);
      if (so.block) H.disp(seg, "block", t0 - 0.01);
      H.disp(ph, "none", t0 - 0.01);
      H.type(spans, t0, t1);
      const s = { el: seg, spans };
      segs.push(s);
      return s;
    };
    api.quote = (text, at) => {
      const q = H.mk("div", "b-chat-quote", field, text);
      H.disp(q, "block", at - 0.01);
      H.snap(q, at, { y: -40 }, 0.18);
      segs.push({ el: q, spans: [] });
      return q;
    };
    api.strike = (seg, at) => tl.fromTo((seg.el || seg).querySelector(".b-strike"), { scaleX: 0 },
                                        { scaleX: 1, duration: 0.2, ease: "power4.out", immediateRender: false }, at);
    api.untype = (seg, t0, t1) => {
      H.untype(seg.spans, t0, t1);
      const bar = seg.el.querySelector(".b-strike");
      if (bar) H.hide(bar, t1);
    };
    api.clearInput = at => {
      segs.forEach(s => {
        H.wipe(s.spans, at);
        if (s.el.classList.contains("b-chat-line") || s.el.classList.contains("b-chat-quote")) H.disp(s.el, "none", at);
        const bar = s.el.querySelector(".b-strike");
        if (bar) H.hide(bar, at);
      });
      segs = [];
      H.disp(ph, "inline", at);
    };
    // a user message; bo.struck: trailing text that can get a strike, bo.chips: small labels, bo.fly: px it rises from
    api.bubble = (text, at, bo) => {
      bo = bo || {};
      const b = H.mk("div", "b-chat-ub b-hide", msgs, text);
      let struck = null;
      if (bo.struck) {
        b.appendChild(document.createTextNode(" "));
        struck = H.mk("span", "b-struck", b, bo.struck);
        H.mk("span", "b-strike", struck);
      }
      if (bo.chips) {
        const c = H.mk("div", "b-chat-chips", b);
        bo.chips.forEach(t => H.mk("span", "b-chat-chip", c, t));
      }
      H.disp(b, "block", at - 0.01);
      H.snap(b, at, bo.fly ? { y: bo.fly, scale: 0.94 } : { y: 34 }, bo.fly ? 0.34 : 0.16);
      return { el: b, struck };
    };
    api.sendTo = (at, text, bo) => {
      api.clearInput(at);
      return api.bubble(text, at, Object.assign({ fly: 420 }, bo || {}));
    };
    // the assistant's answer: a short thinking dot, then the words stream in
    api.answer = (text, t0, t1) => {
      const dot = H.mk("div", "b-chat-dot b-hide", msgs);
      H.disp(dot, "block", t0 - 0.3);
      H.show(dot, t0 - 0.28);
      H.disp(dot, "none", t0);
      const a = H.mk("div", "b-chat-ans", msgs);
      H.disp(a, "block", t0 - 0.01);
      const spans = H.words(a, text);
      H.stream(spans, t0, t1);
      return spans;
    };
    api.highlight = (spans, at) => spans.forEach(s => tl.set(s, { attr: { class: "b-aw b-chat-hl" } }, at));
    api.clearMessages = at => H.disp(Array.from(msgs.children), "none", at);
    return api;
  };
})();
