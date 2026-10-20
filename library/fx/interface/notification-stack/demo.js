// Demo for library/fx/_demo/{modern,hf}.html?fx=interface/notification-stack. Four generic toasts arrive and dismiss themselves.
window.FX_DEMO = function (H, stage) {
  const head = document.createElement("div");
  head.textContent = "Quiet alerts, in order.";
  head.style.cssText = "position:absolute;left:100px;top:380px;width:900px;font:800 100px/1.08 var(--head);color:var(--ink)";
  stage.appendChild(head);
  FX.notificationStack(H, stage, {
    at: 0.3, stagger: 0.9, life: 2.2, margin: 80,
    toasts: [
      { title: "Export finished", body: "Two files are ready", tone: "success", meta: "now" },
      { title: "New message", body: "A note on step four", tone: "info", meta: "1m" },
      { title: "Storage is almost full", body: "Remove old files to free space", tone: "warn", meta: "2m" },
      { title: "Upload failed", body: "Trying again in a moment", tone: "error", meta: "2m" },
    ],
  });
};
