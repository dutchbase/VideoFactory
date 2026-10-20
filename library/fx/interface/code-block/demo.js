// Demo for library/fx/_demo/{modern,hf}.html?fx=interface/code-block. Eight lines of sample code type themselves.
window.FX_DEMO = function (H, stage) {
  FX.codeBlock(H, stage, {
    at: H.at("intro+0.2"), title: "total.js", size: 48, lineNumbers: true,
    typeDur: 3.2,
    code: [
      "// add up a list of prices",
      "const rate = 25;",
      "",
      "function total(items) {",
      "  let sum = 0;",
      "  for (const n of items) sum += n * rate;",
      "  return sum;",
      "}",
    ].join("\n"),
  });
};
