// Terminal: a command types itself after the prompt, then the output lines appear one by one. Rewritten from Onda Terminal (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.terminal = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at);
    const command = o.command == null ? "make video" : String(o.command);
    const lines = (o.output || []).map(l => (typeof l === "string" ? { text: l } : l));
    const typeDur = o.typeDur == null ? Math.max(0.6, command.length * 0.05) : o.typeDur;
    const lead = o.lead == null ? 0.3 : o.lead, outDelay = o.outputDelay == null ? 0.5 : o.outputDelay, stagger = o.stagger == null ? 0.35 : o.stagger;
    const { w: W } = K.size(el);
    const fs = o.size == null ? 40 : o.size, width = o.width == null ? Math.min(1500, W - 120) : o.width;

    const wrap = H.mk("div", "fx-terminal", el);
    const win = H.mk("div", "fx-terminal-win", wrap);
    win.style.cssText = `width:${width}px;font-size:${fs}px`;
    if (o.x != null || o.y != null) { wrap.style.display = "block"; win.style.position = "absolute"; win.style.left = (o.x || 0) + "px"; win.style.top = (o.y || 0) + "px"; }
    if (o.chrome !== false) {
      const bar = H.mk("div", "fx-terminal-bar", win);
      for (let i = 0; i < 3; i++) H.mk("span", "fx-terminal-dot", bar);
      if (o.title) H.mk("span", "fx-terminal-title", bar, o.title);
    }
    const body = H.mk("div", "fx-terminal-body", win);
    const row = H.mk("div", "fx-terminal-row", body);
    H.mk("span", "fx-terminal-prompt", row, o.prompt == null ? "$" : o.prompt);
    const typed = H.mk("span", "fx-terminal-cmd", row);
    const cursor = H.mk("span", "fx-terminal-cursor", row);
    const outEls = lines.map(l => {
      const d = H.mk("div", "fx-terminal-out" + (l.tone ? " fx-terminal-" + l.tone : ""), body, l.text);
      return d;
    });

    const t0 = at + lead, t1 = t0 + typeDur, tOut = t1 + outDelay;
    let last = -1;
    // the text and the cursor depend on t only: typing is linear, the cursor blinks every 0.5 s while it waits for the output
    function draw(p, t) {
      const n = Math.floor(K.clamp((t - t0) / typeDur) * command.length + 1e-9);
      if (n !== last) { typed.textContent = command.slice(0, n); last = n; }
      const typing = t < t1, waiting = t >= t1 && t < tOut;
      cursor.style.opacity = typing || (waiting && Math.floor((t - t1) / 0.5) % 2 === 0) ? "1" : "0";
    }
    draw(0, t0);
    H.drive(draw, t0, tOut);

    H.tl.fromTo(win, { autoAlpha: 0, y: 28 }, { autoAlpha: 1, y: 0, duration: 0.35, ease: "power4.out", immediateRender: true }, at);
    outEls.forEach((d, i) => H.tl.fromTo(d, { autoAlpha: 0, y: 8 }, { autoAlpha: 1, y: 0, duration: 0.18, ease: "power3.out", immediateRender: true }, tOut + i * stagger));
    return { el: win, typed, end: tOut + Math.max(0, lines.length - 1) * stagger + 0.18 };
  };
})();
