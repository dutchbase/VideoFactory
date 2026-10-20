// Demo for library/fx/_demo/{modern,hf}.html?fx=interface/terminal. One command is typed, then three lines of output appear.
window.FX_DEMO = function (H, stage) {
  FX.terminal(H, stage, {
    at: H.at("intro+0.2"), title: "session", size: 52,
    command: "make video --format wide",
    typeDur: 1.8, outputDelay: 0.5, stagger: 0.45,
    output: ["reading script ... done", "building scenes ... done", { text: "video ready: out.mp4", tone: "green" }],
  });
};
