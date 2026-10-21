(() => {
  "use strict";

  const STAGES = [
    { gate: "research", label: "Research", action: "research-init", optional: true },
    { gate: "brief", label: "Brief" },
    { gate: "script", label: "Script" },
    { gate: "voice-test", label: "Voice test", action: "voice-test" },
    { gate: "voice", label: "Voice", action: "voice" },
    { gate: "transcript", label: "Transcript", action: "transcribe" },
    { gate: "cues", label: "Storyboard", action: "cues" },
    { gate: "scene", label: "Scene", action: "check" },
    { gate: "render", label: "Export", action: "render" },
  ];
  const SILENT_GATES = new Set(["voice-test", "voice", "transcript"]);
  // Approved gate -> the agent-authored stage it unlocks (mirrors studio/agent_runs.py).
  const AGENT_NEXT = { brief: "script", transcript: "cues", cues: "scene" };
  const AGENT_INPUT = Object.fromEntries(Object.entries(AGENT_NEXT).map(([input, kind]) => [kind, input]));
  const AGENT_TASK = { script: "Write the script from the approved brief.", cues: "Author the storyboard cues from the approved transcript.", scene: "Author the scene from the approved storyboard cues." };
  const ACTIVE_JOB_STATES = new Set(["queued", "running", "cancelling"]);
  const TEXT_EXT = new Set([".md", ".txt", ".js", ".html", ".css", ".json"]);
  const VIDEO_EXT = new Set([".mp4", ".mov", ".webm"]);
  const AUDIO_EXT = new Set([".mp3", ".wav", ".m4a", ".ogg"]);
  const IMAGE_EXT = new Set([".png", ".jpg", ".jpeg", ".webp", ".gif"]);
  const state = {
    token: "", boot: null, videos: [], videosComplete: false, styles: [], requests: [], jobs: [], materials: [],
    sessionId: "", permission: new Map(), promptedScopes: new Set(),
    drafts: new Map(), files: new Map(), routeVersion: 0, pollTimer: 0, pollBusy: false,
    videoQuery: "", videoStateFilter: "all", materialQuery: "", materialKindFilter: "all", renderedPathSearch: "",
  };
  let fieldSequence = 0;
  let routeController = new AbortController();

  function make(tag, attrs = {}, children = []) {
    const element = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs || {})) {
      if (value === null || value === undefined || value === false) continue;
      if (key === "className") element.className = value;
      else if (key === "text") element.textContent = value;
      else if (key === "dataset") Object.assign(element.dataset, value);
      else if (key.startsWith("on") && typeof value === "function") element.addEventListener(key.slice(2).toLowerCase(), value);
      else if (key === "checked" || key === "disabled" || key === "hidden" || key === "required" || key === "multiple" || key === "readOnly") element[key] = Boolean(value);
      else if (key in element && !key.startsWith("aria-") && !key.startsWith("data-")) {
        try { element[key] = value; } catch { element.setAttribute(key, String(value)); }
      } else element.setAttribute(key, String(value));
    }
    const items = Array.isArray(children) ? children : [children];
    for (const child of items.flat(Infinity)) {
      if (child === null || child === undefined || child === false) continue;
      element.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
    return element;
  }

  function add(parent, ...children) {
    for (const child of children.flat(Infinity)) {
      if (child === null || child === undefined || child === false) continue;
      parent.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
    return parent;
  }

  function button(label, className = "button", action = null, type = "button") {
    return make("button", { type, className, onClick: action || undefined }, label);
  }

  function link(label, href, className = "") {
    return make("a", { href, className }, label);
  }

  function statusPill(value, label = null) {
    const key = String(value || "unknown").toLowerCase().replace(/[^a-z0-9-]+/g, "-");
    return make("span", { className: `status status-${key}` }, label || stateLabel(value));
  }

  function stateLabel(value) {
    const labels = {
      "not-started": "Not started", draft: "Draft", blocked: "Blocked", stale: "Stale",
      "awaiting-review": "Awaiting review", approved: "Approved", accepted: "Completed in this session", "changes-requested": "Changes requested",
      skipped: "Skipped by you", "not-applicable": "Not applicable", ready: "Ready for review",
      queued: "Queued", running: "Running", cancelling: "Cancelling", succeeded: "Succeeded",
      failed: "Failed", cancelled: "Cancelled", interrupted: "Interrupted", "waiting-for-agent": "Waiting for agent",
      claimed: "Claimed by agent", unknown: "Status unavailable", unchecked: "Check for changes",
    };
    return labels[value] || String(value || "Unknown").replaceAll("-", " ").replace(/\b\w/g, c => c.toUpperCase());
  }

  function apiError(data, response) {
    const detail = data && data.error;
    const error = new Error(detail && detail.message || `Request failed (${response.status}).`);
    error.code = detail && detail.code || "request";
    error.status = response.status;
    return error;
  }

  function sessionId() {
    let id = sessionStorage.getItem("vf-session-id");
    if (!/^[a-f0-9]{32}$/.test(id || "")) {
      id = crypto.randomUUID().replaceAll("-", "");
      sessionStorage.setItem("vf-session-id", id);
    }
    return state.boot?.session_nonce ? `${id}.${state.boot.session_nonce}` : "";
  }

  function writeScope(path, options) {
    if (["/api/permission"].includes(path) || /\/(cancel|decision|approve)$/.test(path)) return null;
    let body = {};
    try { body = JSON.parse(options.body || "{}"); } catch { return null; }
    if (path === "/api/jobs") return body.action === "new" ? `video:${body.options?.brand}/${body.slug}` : body.action === "native-render" ? `character:${body.slug}` : body.action === "stock-get" ? brandScope(body.slug) : videoScope(body.slug);
    if (path === "/api/requests") return body.subject ? `${body.subject.type}:${body.subject.id}` : videoScope(body.slug);
    if (path === "/api/styles") return `style:${body.id}`;
    if (path === "/api/characters") return `character:${body.id}`;
    if (path === "/api/creative") return `${body.type}:${body.id}`;
    if (path === "/api/generations") return `${body.subject_type}:${body.subject_id}`;
    if (path === "/api/materials") return body.permission_scope || null;
    if (path === "/api/files") {
      const parts = String(body.path || "").split("/");
      if (parts[0] === "videos") return parts.length > 3 && state.videos.some(video => video.video_id === `${parts[1]}/${parts[2]}`) ? `video:${parts[1]}/${parts[2]}` : videoScope(parts[1]);
      return ({ brands: "brand", styles: "style", characters: "character" })[parts[0]] + ":" + parts[1];
    }
    if (path === "/api/materials/link") return body.owner_kind === "video" ? videoScope(body.owner_id) : `${body.owner_kind}:${body.owner_id}`;
    let parts = path.split("/").filter(Boolean).map(decodeURIComponent);
    if (parts[1] === "videos") return videoScope(parts[3] && parts[3] !== "reviews" ? `${parts[2]}/${parts[3]}` : parts[2]);
    if (parts[1] === "creative") return `${parts[2]}:${parts[3]}`;
    if (parts[1] === "styles") return `style:${parts[2]}`;
    if (parts[1] === "characters") return `character:${parts[2]}`;
    return null;
  }

  function videoScope(slug) {
    if (typeof slug !== "string") return null;
    if (slug.includes("/")) return `video:${slug}`;
    const video = state.videos.find(item => item.leaf_slug === slug || item.slug === slug);
    return video?.video_id ? `video:${video.video_id}` : null;
  }

  function brandScope(slug) {
    const video = videoScope(slug);
    return video ? `brand:${video.slice(6).split("/")[0]}` : null;
  }

  async function permissionState(scope) {
    const result = await api(`/api/permission?scope=${encodeURIComponent(scope)}`);
    state.permission.set(scope, result);
    return result;
  }

  function permissionChoice(scope) {
    return new Promise(resolve => {
      const dialog = make("dialog", { className: "permission-dialog", "aria-labelledby": "permission-question" });
      const form = make("form", { method: "dialog" });
      const fieldset = make("fieldset");
      fieldset.append(make("legend", { id: "permission-question" }, "Do I have full permission for this session?"));
      fieldset.append(make("p", {}, `Scope: ${scope}. This choice applies to this browser session only.`));
      const choices = [["full", "Full permission — production, checks, repairs and export"], ["each-stage", "Review each stage"], ["selected-stages", "Review selected stages"]];
      const stageSet = make("fieldset", { className: "permission-stages", hidden: true }, [make("legend", {}, "Choose stages for review")]);
      const stages = scope.startsWith("video:") ? ["research", "brief", "script", "voice-test", "voice", "transcript", "cues", "scene", "render"]
        : scope.startsWith("style:") ? ["brief", "materials", "sample"]
        : scope.startsWith("character:") ? ["brief", "design", "identity", "rig", "animation"]
        : ["brief", "design"];
      for (const stage of stages) stageSet.append(make("label", {}, [make("input", { type: "checkbox", name: "stage", value: stage }), ` ${stage}`]));
      for (const [value, label] of choices) fieldset.append(make("label", { className: "permission-choice" }, [make("input", { type: "radio", name: "mode", value, required: true, onChange: () => { stageSet.hidden = value !== "selected-stages"; } }), ` ${label}`]));
      const error = make("p", { role: "alert", className: "form-error" });
      form.append(fieldset, stageSet, error, make("div", { className: "form-actions" }, [button("Cancel", "button", () => dialog.close()), button("Save permission", "button button-primary", null, "submit")]));
      form.addEventListener("submit", async event => {
        event.preventDefault();
        const data = new FormData(form);
        const selected = data.getAll("stage");
        if (data.get("mode") === "selected-stages" && !selected.length) { error.textContent = "Choose at least one stage."; return; }
        try {
          const result = await api("/api/permission", jsonOptions("POST", { action: "grant", scope, mode: data.get("mode"), selected_stages: data.get("mode") === "selected-stages" ? selected : [] }));
          state.permission.set(scope, result);
          dialog.close(); resolve(result);
        } catch (failure) { error.textContent = failure.message; }
      });
      dialog.addEventListener("close", () => { dialog.remove(); resolve(null); }, { once: true });
      dialog.append(form);
      document.body.append(dialog); dialog.showModal();
    });
  }

  async function ensurePermission(scope) {
    if (!scope || scope.includes("undefined")) return;
    const current = await permissionState(scope);
    if (current.active) return;
    if (!await permissionChoice(scope)) throw new Error("Permission was not granted for this session.");
  }

  function paidPanel(runId, scope) {
    const host = make("section", { className: "section rule-section", "aria-label": "Paid requests" });
    host.append(make("h2", {}, "Paid requests"));
    api(`/api/paid/${encodeURIComponent(runId)}`).then(data => {
      const pending = data.pending || [];
      const quotes = data.quotes || [];
      if (!pending.length && !quotes.length) { host.append(make("p", {}, "No exact paid request is waiting for approval.")); return; }
      for (const item of pending) {
        const existing = quotes.find(quote => quote.logical_request_id === item.request_id);
        const row = make("div", { className: "evidence-block" }, [make("h3", {}, `Request ${item.request_id}`), make("p", {}, `${item.purpose || "Paid work"} · ${JSON.stringify(item.metadata || {})}`)]);
        if (!existing) {
          const form = make("form", { className: "form-shell" });
          const cost = textInput("Verified maximum cost", { type: "number", min: "0", step: "0.01", required: true });
          const evidence = textInput("Provider quote evidence", { required: true, help: "Paste the provider price source or quote reference." });
          const status = make("p", { role: "status" });
          form.append(cost.wrapper, evidence.wrapper, button("Save quote", "button button-primary", null, "submit"), status);
          form.addEventListener("submit", async event => {
            event.preventDefault();
            try { await ensurePermission(scope); await api(`/api/paid/${runId}/${item.request_id}/quote`, jsonOptions("POST", { max_cost: cost.control.value, evidence: evidence.control.value })); await renderRoute({ focus: false }); }
            catch (error) { status.textContent = error.message; }
          });
          row.append(form);
        }
        host.append(row);
      }
      for (const quote of quotes) {
        const row = make("div", { className: "evidence-block" }, [make("h3", {}, `Quoted request ${quote.request_id}`), make("p", {}, `Known maximum cost: ${quote.max_cost}. Evidence: ${JSON.stringify(quote.evidence)}`)]);
        const status = make("p", { role: "status" });
        row.append(button("Approve this exact paid request", "button button-primary", async event => {
          event.currentTarget.disabled = true;
          try { await ensurePermission(scope); await api(`/api/paid/${runId}/${quote.request_id}/approve`, jsonOptions("POST", { expected_quote: quote.fingerprint })); status.textContent = "This exact quote is approved for this session."; }
          catch (error) { status.textContent = error.message; event.currentTarget.disabled = false; }
        }), status);
        host.append(row);
      }
    }).catch(error => host.append(notice("Paid request unavailable", error.message, "error-banner")));
    return host;
  }

  async function api(path, options = {}) {
    const headers = new Headers(options.headers || {});
    const method = String(options.method || "GET").toUpperCase();
    if (method !== "GET" && method !== "HEAD" && state.boot) await ensurePermission(writeScope(path, options));
    if (sessionId()) headers.set("X-VF-Session-ID", sessionId());
    if (method !== "GET" && method !== "HEAD" && state.token) headers.set("X-Studio-Token", state.token);
    const version = state.routeVersion;
    const reading = method === "GET" || method === "HEAD";
    const response = await fetch(path, { signal: reading ? routeController.signal : undefined, ...options, headers, cache: "no-store" });
    const type = response.headers.get("content-type") || "";
    let data = null;
    if (type.includes("json")) data = await response.json();
    else {
      const body = await response.text();
      data = body ? { message: body } : {};
    }
    if (reading && version !== state.routeVersion) throw new DOMException("Navigation changed", "AbortError");
    if (!response.ok) throw apiError(data, response);
    return data;
  }

  function jsonOptions(method, body) {
    return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  }

  function asciiJson(value) {
    return JSON.stringify(value).replace(/[^\x00-\x7f]/gu, character => {
      const codePoint = character.codePointAt(0);
      if (codePoint <= 0xffff) return `\\u${codePoint.toString(16).padStart(4, "0")}`;
      const scalar = codePoint - 0x10000;
      const high = 0xd800 + (scalar >> 10);
      const low = 0xdc00 + (scalar & 0x3ff);
      return `\\u${high.toString(16)}\\u${low.toString(16)}`;
    });
  }

  function unwrap(data, key) {
    return data && data[key] !== undefined ? data[key] : data;
  }

  function idempotencyKey() {
    if (globalThis.crypto && typeof globalThis.crypto.randomUUID === "function") return globalThis.crypto.randomUUID();
    return `studio-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  }

  function slugPath(slug) { return `/videos/${slug.split("/").map(encodeURIComponent).join("/")}`; }
  function reviewPath(slug, gate) { return `${slugPath(slug)}/review/${encodeURIComponent(gate)}`; }
  function apiVideoPath(slug) { return `/api/videos/${slug.split("/").map(encodeURIComponent).join("/")}`; }
  function ext(path) { const name = String(path || "").split(/[?#]/, 1)[0]; const ix = name.lastIndexOf("."); return ix < 0 ? "" : name.slice(ix).toLowerCase(); }
  function pathUrl(path, mode = "media") {
    const parts = String(path || "").split("/").filter(Boolean).map(part => encodeURIComponent(part));
    return `/${mode}/${parts.join("/")}`;
  }
  function workspacePreviewUrl(path) { return `/${String(path || "").split("/").filter(Boolean).map(encodeURIComponent).join("/")}`; }
  function scrollToHash(hash) {
    if (!hash) { window.scrollTo({ top: 0 }); return; }
    let id = hash.slice(1);
    try { id = decodeURIComponent(id); } catch { /* The literal fragment may still match an authored ID. */ }
    document.getElementById(id)?.scrollIntoView({ block: "start" });
  }
  function formatBytes(size) {
    if (!Number.isFinite(Number(size))) return "Size unavailable";
    const bytes = Number(size);
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KiB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MiB`;
  }
  function formatTime(value) {
    if (!value) return "Time unavailable";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "Time unavailable" : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
  }
  function shortFingerprint(value) { return value ? String(value).slice(0, 12) : "Not recorded"; }
  function isSilent(slug) { return String(slug).split("/").pop() === "silent-first-scene"; }
  function reviewFor(video, gate) { return video && video.reviews && video.reviews[gate] || { gate, state: "unchecked", ready: false, missing: [], artifacts: [], history: [] }; }
  function gateLabel(gate) { return STAGES.find(stage => stage.gate === gate)?.label || stateLabel(gate); }

  function reviewQueue(videos = state.videos) {
    const rows = [];
    for (const video of videos || []) {
      for (const stage of STAGES) {
        if (isSilent(video.slug) && SILENT_GATES.has(stage.gate)) continue;
        const review = reviewFor(video, stage.gate);
        if ((review.recorded_state || review.state) === "awaiting-review") rows.push({ video, stage, review });
      }
    }
    return rows;
  }

  function nextGate(video) {
    for (const stage of STAGES) {
      if (isSilent(video.slug) && SILENT_GATES.has(stage.gate)) continue;
      const review = reviewFor(video, stage.gate);
      if (!["approved", "accepted", "skipped", "not-applicable"].includes(review.recorded_state || review.state)) return { stage, review };
    }
    return { stage: STAGES[STAGES.length - 1], review: reviewFor(video, "render") };
  }

  function updateNavigation() {
    const queue = state.videosComplete ? reviewQueue() : [];
    const count = document.getElementById("review-count");
    count.hidden = queue.length === 0;
    count.textContent = queue.length > 99 ? "99+" : String(queue.length);
    count.setAttribute("aria-label", `${queue.length} reviews waiting`);
    const jobs = state.jobs.filter(job => ACTIVE_JOB_STATES.has(job.state));
    const rail = document.getElementById("job-rail");
    rail.hidden = jobs.length === 0;
    if (jobs.length) {
      const job = jobs[0];
      document.getElementById("job-rail-title").textContent = `${stateLabel(job.state)} · ${job.action || "Production"}`;
      document.getElementById("job-rail-meta").textContent = job.slug ? job.slug : "Workspace production";
      rail.href = `/jobs/${encodeURIComponent(job.id)}`;
    }
    const top = document.getElementById("topbar-right");
    top.replaceChildren();
    if (jobs.length) {
      const job = jobs[0];
      const a = make("a", { className: "topbar-job", href: `/jobs/${encodeURIComponent(job.id)}` }, [
        make("span", { className: "job-live-mark", "aria-hidden": "true" }),
        `${stateLabel(job.state)} · ${job.action || "Production"}`,
      ]);
      top.append(a);
    }
  }

  function setBreadcrumb(items) {
    const host = document.getElementById("breadcrumb");
    host.replaceChildren();
    items.forEach((item, index) => {
      if (index) host.append(make("span", { className: "breadcrumb-separator", "aria-hidden": "true" }));
      host.append(item.href && index < items.length - 1 ? link(item.label, item.href) : make("span", { className: "crumb-current" }, item.label));
    });
  }

  function route() {
    let parts;
    try { parts = location.pathname.split("/").filter(Boolean).map(decodeURIComponent); }
    catch { return { kind: "not-found" }; }
    if (!parts.length) return { kind: "reviews" };
    if (parts[0] === "videos" && parts[1] === "new" && parts.length === 2) return { kind: "video-new" };
    if (parts[0] === "videos" && parts.length === 1) return { kind: "videos" };
    if (parts[0] === "videos" && parts.length === 5 && parts[3] === "review") return { kind: "review", slug: `${parts[1]}/${parts[2]}`, gate: parts[4] };
    if (parts[0] === "videos" && parts.length === 3) return { kind: "video", slug: `${parts[1]}/${parts[2]}` };
    if (parts[0] === "videos" && parts[1] && parts[2] === "review" && parts[3]) return { kind: "review", slug: parts[1], gate: parts[3] };
    if (parts[0] === "videos" && parts[1] && parts.length === 2) return { kind: "video", slug: parts[1] };
    if (parts[0] === "library" && parts.length === 1) return { kind: "library" };
    if (parts[0] === "styles" && parts[1] === "new" && parts.length === 2) return { kind: "style-new" };
    if (parts[0] === "styles" && parts.length === 1) return { kind: "styles" };
    if (parts[0] === "styles" && parts[1] && parts.length === 2) return { kind: "style", id: parts[1] };
    if (parts[0] === "characters" && parts.length === 1) return { kind: "characters" };
    if (parts[0] === "characters" && parts[1] === "new" && parts.length === 2) return { kind: "character-new" };
    if (parts[0] === "characters" && parts[1] && parts.length === 2) return { kind: "character", id: parts[1] };
    if (parts[0] === "creative" && ["style", "character"].includes(parts[1]) && parts[2] && parts[3] === "review" && parts[4] && parts.length === 5) return { kind: "creative-review", type: parts[1], id: parts[2], gate: parts[4] };
    if (parts[0] === "generations" && parts[1] && parts.length === 2) return { kind: "generation", id: parts[1] };
    if (parts[0] === "settings" && parts.length === 1) return { kind: "settings" };
    if (parts[0] === "jobs" && parts.length === 1) return { kind: "jobs" };
    if (parts[0] === "jobs" && parts[1] && parts.length === 2) return { kind: "job", id: parts[1] };
    return { kind: "not-found" };
  }

  function setCurrentNav(kind) {
    const current = kind === "reviews" ? "reviews" : ["video", "video-new", "videos", "job"].includes(kind) ? "videos" : kind.startsWith("style") ? "styles" : kind.startsWith("character") ? "characters" : kind === "library" ? "library" : "";
    for (const anchor of document.querySelectorAll("[data-nav]")) {
      if (anchor.dataset.nav === current) anchor.setAttribute("aria-current", "page");
      else anchor.removeAttribute("aria-current");
    }
  }

  function routeScope(current) {
    if (["video", "review"].includes(current.kind)) return videoScope(current.slug);
    if (["style"].includes(current.kind)) return `style:${current.id}`;
    if (["character"].includes(current.kind)) return `character:${current.id}`;
    if (current.kind === "creative-review") return `${current.type}:${current.id}`;
    return null;
  }

  async function showPermissionBar(main, current) {
    const scope = routeScope(current);
    if (!scope) return;
    const stateNow = await permissionState(scope);
    if (!main.isConnected) return;
    const bar = make("section", { className: "permission-bar", "aria-label": "Session permission" });
    const label = stateNow.active ? `${scope} · ${stateNow.mode.replaceAll("-", " ")}${stateNow.selected_stages?.length ? ` · Review: ${stateNow.selected_stages.join(", ")}` : ""}` : `${scope} · No permission in this session`;
    bar.append(make("p", {}, label));
    bar.append(button(stateNow.active ? "Revoke permission" : "Choose permission", "button", async event => {
      event.currentTarget.disabled = true;
      try {
        if (stateNow.active) {
          const result = await api("/api/permission", jsonOptions("POST", { action: "revoke", scope }));
          state.permission.set(scope, result);
        } else await permissionChoice(scope);
        await renderRoute({ focus: false });
      } catch (error) { announce(error.message); event.currentTarget.disabled = false; }
    }));
    main.prepend(bar);
    if (!stateNow.active && !state.promptedScopes.has(scope)) {
      state.promptedScopes.add(scope);
      permissionChoice(scope).then(granted => { if (granted && main.isConnected) renderRoute({ focus: false }); });
    }
  }

  async function loadBootstrap() {
    const data = await api("/api/bootstrap?view=shell");
    state.boot = data;
    state.token = data.token || state.token;
    state.sessionId = sessionId();
    state.requests = Array.isArray(data.requests) ? data.requests : [];
    state.jobs = Array.isArray(data.jobs) ? data.jobs : [];
    updateNavigation();
  }

  async function loadVideos() {
    state.videos = await api("/api/videos?view=summary");
    state.videosComplete = true;
    updateNavigation();
  }

  async function loadStyles() {
    state.styles = await api("/api/styles");
  }

  async function refreshRequests() {
    state.requests = await api("/api/requests");
  }

  function loadPart(host, load) {
    const version = state.routeVersion;
    const generation = host.loadGeneration = (host.loadGeneration || 0) + 1;
    const current = () => version === state.routeVersion && generation === host.loadGeneration && host.isConnected;
    const run = async () => {
      host.replaceChildren(loadingPage("Loading this section"));
      try {
        const content = await load();
        if (!current()) return;
        host.replaceChildren(...(Array.isArray(content) ? content : [content]));
      } catch (error) {
        if (!current()) return;
        host.replaceChildren(notice("Could not load this section", error.message, "error-banner"), button("Retry section", "button", run));
      }
    };
    run();
  }

  function linkedMaterials(host, ids, ownerKind, ownerId) {
    if (!ids.length) { host.append(make("p", {}, "No materials are linked yet.")); return; }
    loadPart(host, async () => renderMaterialRows(await api(`/api/materials?ids=${encodeURIComponent(ids.join(","))}`), ids, ownerKind, ownerId));
  }

  function materialPicker(ownerKind, ownerId, onAttach) {
    const details = make("details", {}, make("summary", {}, "Attach a material"));
    const host = make("div", { className: "detail-section" });
    let opened = false;
    details.append(host);
    details.addEventListener("toggle", () => {
      if (!details.open || opened) return;
      opened = true;
      const search = textInput("Search materials", { type: "search" });
      const results = make("div");
      host.append(search.wrapper, results);
      const update = () => loadPart(results, async () => {
        const query = search.control.value;
        const page = await api(`/api/materials?view=summary&q=${encodeURIComponent(query)}${ownerKind === "video" && ownerId.includes("/") ? `&brand=${encodeURIComponent(ownerId.split("/")[0])}` : ""}`);
        if (query !== search.control.value) return [];
        return page.items.map(material => make("div", { className: "material-link-row" }, [
          make("strong", {}, material.title || material.id),
          button("Attach", "button button-small", async () => {
            try {
              await api("/api/materials/link", jsonOptions("POST", { owner_kind: ownerKind, owner_id: ownerId, material_id: material.id }));
              onAttach(material.id);
              announce("Material attached.");
              if (details.isConnected) details.open = false;
            } catch (error) { showFormError(results, error); }
          }),
        ]));
      });
      let timer;
      search.control.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(update, 150); });
      update();
    });
    return details;
  }

  async function loadVideo(slug) {
    const video = unwrap(await api(`${apiVideoPath(slug)}?view=shell`), "video");
    // Keep the cached list current so the review queue never shows a decided gate.
    const index = state.videos.findIndex(item => item.slug === video.slug);
    if (index >= 0) state.videos[index] = video; else state.videos.push(video);
    updateNavigation();
    return video;
  }

  async function loadStyle(id) {
    const [fileResponse, listResponse] = await Promise.all([
      api(`/api/styles/${encodeURIComponent(id)}`),
      api("/api/styles").catch(() => null),
    ]);
    if (listResponse) state.styles = Array.isArray(listResponse) ? listResponse : listResponse.styles || state.styles;
    const file = unwrap(fileResponse, "style");
    const summary = state.styles.find(style => style.id === id) || {};
    return {
      ...summary,
      ...file,
      id: summary.id || file.id || id,
      title: summary.title || file.title || id,
      base_kit: summary.base_kit || file.base_kit || null,
      body: summary.body ?? file.text ?? "",
      text: file.text ?? summary.body ?? "",
      materials: summary.materials || file.materials || [],
    };
  }

  function loadingPage(label = "Loading workspace") {
    return make("div", { className: "loading-state", role: "status" }, [make("span", { className: "loading-rule", "aria-hidden": "true" }), label]);
  }

  function pageIntro(title, description, actions = []) {
    const copy = make("div", { className: "page-intro-copy" }, [make("h1", {}, title), make("p", {}, description)]);
    const actionHost = make("div", { className: "page-actions" }, actions);
    return make("div", { className: "page-intro" }, [copy, actions.length ? actionHost : null]);
  }

  function sectionHeading(title, description = "", trailing = null) {
    const copy = make("div", {}, [make("h2", {}, title), description ? make("p", {}, description) : null]);
    return make("div", { className: "section-heading" }, [copy, trailing]);
  }

  function emptyState(title, description, actions = []) {
    return make("div", { className: "empty-state" }, [
      make("h3", {}, title), make("p", {}, description),
      actions.length ? make("div", { className: "page-actions" }, actions) : null,
    ]);
  }

  function notice(title, message, type = "inline-notice") {
    return make("div", { className: type, role: type === "error-banner" ? "alert" : "status" }, [make("strong", {}, title), make("p", {}, message)]);
  }

  function previewImage(path, alt, className) {
    if (!path) return null;
    return make("img", { src: pathUrl(path), alt, className, loading: "lazy", decoding: "async" });
  }

  function reviewRow(row, index) {
    const { video, stage, review } = row;
    const reason = review.state === "unchecked" ? `Recorded: ${stateLabel(review.recorded_state)}. Open to check the current revision.` : review.missing?.length ? review.missing.join(", ") : "";
    return make("article", { className: "review-row" }, [
      make("div", { className: "review-index" }, String(index + 1).padStart(2, "0")),
      make("div", { className: "review-project" }, [make("strong", {}, video.title), make("small", {}, `${video.label || "Video"} · ${video.slug}`)]),
      make("div", { className: "review-context" }, [make("strong", {}, stage.label), statusPill(review.state)]),
      make("p", { className: "review-reason" }, reason),
      link("Open review", reviewPath(video.slug, stage.gate), "text-link"),
    ]);
  }

  function queueSection(rows) {
    const section = make("section", { className: "section rule-section" }, [
      sectionHeading("Waiting for review", "Only revisions marked ready appear here.", make("span", { className: "section-count" }, `${rows.length} waiting`)),
    ]);
    if (rows.length) add(section, make("div", { className: "review-list" }, rows.map(reviewRow)));
    else add(section, emptyState("Nothing is waiting for review", "A saved file or completed job does not count as approval. An agent or successful check must mark the current revision ready first."));
    return section;
  }

  async function renderReviews(main) {
    const version = state.routeVersion;
    const actions = [link("All videos", "/videos", "button")];
    add(main, pageIntro("Reviews", "Saved work that is explicitly waiting for your decision.", actions));
    await loadVideos();
    if (version !== state.routeVersion) return;
    const queue = queueSection(reviewQueue());
    add(main, queue);
    const creativeQueue = make("section", { className: "section rule-section", hidden: true });
    add(main, creativeQueue);
    // Creative details load slowly; the video queue must not wait for them.
    loadPart(creativeQueue, async () => {
      const host = make("div");
      await window.CreativeStudio.reviewQueue(host, creativeHelpers());
      return host;
    });
    creativeQueue.hidden = false;
  }

  function videoTile(video, index) {
    const href = slugPath(video.slug);
    const frame = make("a", { className: "video-tile-frame", href, "aria-label": `Open ${video.title}` });
    if (video.thumbnail && IMAGE_EXT.has(ext(video.thumbnail))) frame.append(previewImage(video.thumbnail, `${video.title} frame`, ""));
    else frame.append(make("div", { className: "video-tile-placeholder" }, [make("strong", {}, video.label === "Setup fixture" ? "Setup fixture" : "No authored preview"), make("small", {}, video.error || "This project has no visible still yet.")]));
    const next = nextGate(video);
    return make("article", { className: "video-tile" }, [
      frame,
      make("div", { className: "video-tile-caption" }, [
        make("div", { className: "video-tile-copy" }, [link(video.title, href), make("small", {}, `${video.label || "Video"} · ${video.slug}`), make("small", {}, `Next · ${next.stage.label}`)]),
        make("span", { className: "tile-number" }, String(index + 1).padStart(2, "0")),
      ]),
      statusPill(next.review.state),
    ]);
  }

  async function renderVideos(main) {
    await loadVideos();
    if (!main.isConnected) return;
    const intro = pageIntro("Videos", "Every project in the workspace, including demos and setup fixtures.", [link("New video", "/videos/new", "button button-primary")]);
    add(main, intro);
    const toolbar = make("div", { className: "toolbar" });
    const searchId = `video-search-${++fieldSequence}`;
    const search = make("input", { id: searchId, type: "search", placeholder: "Search title or slug", value: state.videoQuery, autocomplete: "off" });
    const searchWrap = make("div", { className: "field search-field" }, [make("label", { htmlFor: searchId }, "Search videos"), search]);
    const filterId = `video-state-${++fieldSequence}`;
    const filter = make("select", { id: filterId, value: state.videoStateFilter });
    for (const [value, label] of [["all", "All review states"], ["awaiting-review", "Awaiting review"], ["stale", "Stale"], ["draft", "Draft or blocked"], ["approved", "Approved"]]) filter.append(make("option", { value }, label));
    filter.value = state.videoStateFilter;
    const filterWrap = make("div", { className: "field" }, [make("label", { htmlFor: filterId }, "Review state"), filter]);
    add(toolbar, make("div", { className: "filter-group" }, [searchWrap, filterWrap]), make("span", { className: "collection-summary", id: "video-result-count" }));
    add(main, toolbar);
    const grid = make("div", { className: "video-grid", id: "video-grid" });
    add(main, grid);
    function update() {
      state.videoQuery = search.value;
      state.videoStateFilter = filter.value;
      const query = state.videoQuery.trim().toLowerCase();
      const videos = state.videos.filter(video => {
        const text = `${video.title || ""} ${video.slug || ""} ${video.label || ""}`.toLowerCase();
        const states = Object.values(video.reviews || {}).map(review => review.recorded_state || review.state);
        return (!query || text.includes(query)) && (state.videoStateFilter === "all" || states.includes(state.videoStateFilter) || (state.videoStateFilter === "draft" && states.some(value => ["draft", "blocked", "not-started"].includes(value))));
      });
      grid.replaceChildren();
      const count = document.getElementById("video-result-count");
      if (count) count.textContent = `${videos.length} of ${state.videos.length} projects`;
      if (videos.length) grid.append(...videos.map(videoTile));
      else grid.append(emptyState(state.videos.length ? "No matching projects" : "No projects found", state.videos.length ? "Change the search or review-state filter." : "Create a project from the existing video template.", state.videos.length ? [] : [link("Create a video", "/videos/new", "button button-primary")]));
    }
    search.addEventListener("input", update);
    filter.addEventListener("change", update);
    update();
  }

  function textInput(label, opts = {}) {
    const id = opts.id || `field-${++fieldSequence}`;
    const control = make("input", {
      id, name: opts.name || id, type: opts.type || "text", value: opts.value ?? "",
      placeholder: opts.placeholder, required: Boolean(opts.required), autocomplete: opts.autocomplete || "off",
      pattern: opts.pattern, maxlength: opts.maxlength, accept: opts.accept,
    });
    const wrapper = make("div", { className: `field${opts.className ? ` ${opts.className}` : ""}` }, [make("label", { htmlFor: id }, label), control]);
    if (opts.help) wrapper.append(make("small", { className: "field-help" }, opts.help));
    return { wrapper, control };
  }

  function textArea(label, opts = {}) {
    const id = opts.id || `field-${++fieldSequence}`;
    const control = make("textarea", {
      id, name: opts.name || id, placeholder: opts.placeholder, required: Boolean(opts.required),
      rows: opts.rows || 5, maxlength: opts.maxlength,
    }, opts.value || "");
    const wrapper = make("div", { className: `field${opts.className ? ` ${opts.className}` : ""}` }, [make("label", { htmlFor: id }, label), control]);
    if (opts.help) wrapper.append(make("small", { className: "field-help" }, opts.help));
    return { wrapper, control };
  }

  function selectField(label, choices, opts = {}) {
    const id = opts.id || `field-${++fieldSequence}`;
    const control = make("select", { id, name: opts.name || id, required: Boolean(opts.required) });
    for (const choice of choices) control.append(make("option", { value: choice.value }, choice.label));
    if (opts.value !== undefined) control.value = opts.value;
    const wrapper = make("div", { className: `field${opts.className ? ` ${opts.className}` : ""}` }, [make("label", { htmlFor: id }, label), control]);
    if (opts.help) wrapper.append(make("small", { className: "field-help" }, opts.help));
    return { wrapper, control };
  }

  function checkField(label, opts = {}) {
    const id = opts.id || `field-${++fieldSequence}`;
    const input = make("input", { id, name: opts.name || id, type: "checkbox", required: Boolean(opts.required), checked: Boolean(opts.checked) });
    const wrapper = make("label", { className: "check-field", htmlFor: id }, [input, make("span", {}, label)]);
    if (!opts.className) return { wrapper, control: input };
    return { wrapper: make("div", { className: opts.className }, [wrapper]), control: input };
  }

  function stageSelect(video, currentGate = null) {
    const stages = STAGES.filter(stage => !isSilent(video.slug) || !SILENT_GATES.has(stage.gate));
    const id = `stage-select-${++fieldSequence}`;
    const select = make("select", { id, value: currentGate || stages[0]?.gate || "" });
    for (const stage of stages) select.append(make("option", { value: stage.gate }, stage.label));
    select.value = currentGate || stages[0]?.gate || "";
    select.addEventListener("change", () => { location.assign(reviewPath(video.slug, select.value)); });
    return make("div", { className: "stage-select-wrap" }, [make("label", { htmlFor: id }, "Production stage"), select]);
  }

  function pathBasename(path) { return String(path || "").split("/").filter(Boolean).pop() || String(path || ""); }

  function artifactLink(path) {
    return link(pathBasename(path), pathUrl(path, "download"), "text-link");
  }

  function renderArtifactRows(video, gate) {
    const review = reviewFor(video, gate);
    const paths = Array.from(new Set([...(video.files?.[gate] || []), ...(review.artifacts || [])]));
    if (!paths.length) return emptyState("No files recorded for this stage", "A missing file stays visible as missing; it does not count as ready.");
    const rows = paths.slice(0, 30).map(artifactListItem);
    if (paths.length > 30) rows.push(make("li", { className: "artifact-more" }, lazyPathDetails(paths.slice(30), `${paths.length - 30} more files`)));
    return make("ul", { className: "artifact-list" }, rows);
  }

  function artifactListItem(path) {
    return make("li", {}, [
      make("span", { className: "artifact-label" }, [make("strong", {}, pathBasename(path)), make("small", {}, path)]),
      make("span", { className: "artifact-actions" }, [link("Download", pathUrl(path, "download"), "text-link")]),
    ]);
  }

  function lazyPathDetails(paths, label) {
    const details = make("details", {}, make("summary", {}, label));
    let loaded = false;
    details.addEventListener("toggle", () => {
      if (!details.open || loaded) return;
      loaded = true;
      details.append(make("ul", { className: "evidence-list" }, paths.map(path => make("li", {}, [artifactLink(path), make("small", {}, path)]))));
    });
    return details;
  }

  function renderMaterialRows(materials, ids, ownerKind, ownerId) {
    const byId = new Map(materials.map(item => [item.id, item]));
    const rows = ids.map(id => byId.get(id) || { id, title: id, description: "The linked material record is missing.", rights: "unknown", error: "Material record unavailable" });
    const host = make("div", { className: "material-links" });
    if (!rows.length) host.append(make("p", {}, "No materials are linked to this project yet."));
    for (const material of rows) {
      host.append(make("div", { className: "material-link-row" }, [
        make("div", { className: "material-link-copy" }, [make("strong", {}, material.title || material.id), make("small", {}, `${material.kind || "source"} · ${material.rights || "rights unknown"}`), make("small", {}, material.description || material.error || "No description recorded.")]),
        link("Open library record", `/library?material=${encodeURIComponent(material.id)}`, "quiet-link"),
      ]));
    }
    return host;
  }

  function renderRequests(requests, slug = null) {
    const rows = slug ? requests.filter(request => request.slug === slug) : requests;
    if (!rows.length) return emptyState("No agent requests", "Requests stay in the waiting state until an agent actually claims them.");
    return make("div", { className: "request-list" }, rows.map(request => make("article", { className: "request-row" }, [
      make("div", {}, [make("strong", {}, gateLabel(request.kind)), make("br"), make("small", {}, formatTime(request.created_at))]),
      statusPill(request.state), make("p", {}, request.instructions),
      make("small", { className: "source-id" }, `Request ${request.id}`),
    ])));
  }

  function renderAgentRequestForm({ slug, kind = "script", fingerprint = "", context = "video" }) {
    const form = make("form", { className: "form-shell" });
    const kindChoices = context === "video"
      ? [{ value: "research", label: "Research synthesis" }, { value: "script", label: "Write or revise script" }, { value: "cues", label: "Author storyboard cues" }, { value: "scene", label: "Author scene" }, { value: "material", label: "Prepare new material" }]
      : context === "style"
        ? [{ value: "style-template", label: "Create or revise reusable template" }]
        : [{ value: "material", label: "Prepare or describe material" }];
    if (context === "video") kindChoices.push({ value: "review-checks", label: "Prepare export review checks" });
    const select = selectField("Request type", kindChoices, { value: kind });
    const instructions = textArea("Instructions", { required: true, rows: 4, placeholder: context === "video" ? "Describe the work, evidence, or changes needed." : "Describe the material or reusable template to prepare." });
    const message = make("div", { className: "flash-message", hidden: true, role: "status" });
    const submit = button("Create request", "button button-primary", null, "submit");
    add(form, select.wrapper, instructions.wrapper, make("div", { className: "form-actions" }, submit), message);
    form.addEventListener("submit", async event => {
      event.preventDefault();
      if (!instructions.control.value.trim()) return;
      submit.disabled = true;
      try {
        const body = { slug, kind: select.control.value, instructions: instructions.control.value.trim(), fingerprint, request_id: idempotencyKey() };
        const response = await api("/api/requests", jsonOptions("POST", body));
        const request = unwrap(response, "request");
        state.requests = [request, ...state.requests.filter(item => item.id !== request.id)];
        message.hidden = false;
        message.replaceChildren(notice("Request saved", "Waiting for an agent to claim it. The dashboard does not start agent work.", "success-banner"));
        instructions.control.value = "";
        announce("Request saved. Waiting for an agent to claim it.");
      } catch (error) { showFormError(message, error); }
      finally { submit.disabled = false; }
    });
    return form;
  }

  function launchJobForm(video) {
    const form = make("form", { className: "form-shell" });
    const actionChoices = [
      ["research-init", "Initialize research"], ["voice-check", "Check voice provider"],
      ["transcribe", "Transcribe approved voice"], ["cues", "Compile storyboard cues"],
      ["check", "Check scene"], ["stills", "Render scene stills"], ["render", "Render video"], ["thumbnail", "Render thumbnail"],
      ["stock-search", "Search stock library"], ["stock-get", "Download stock result"], ["use", "Use library reference"],
      ["capture", "Capture website page"], ["record", "Record website flow"],
    ].map(([value, label]) => ({ value, label }));
    const actionField = selectField("Production action", actionChoices, { value: "cues" });
    const optionsHost = make("div", { className: "form-grid", id: `job-options-${++fieldSequence}` });
    const message = make("div", { className: "flash-message", hidden: true, role: "status" });
    const submit = button("Run action", "button button-primary", null, "submit");
    add(form, actionField.wrapper, optionsHost, make("div", { className: "form-actions" }, submit), message);

    function renderOptions() {
      optionsHost.replaceChildren();
      const action = actionField.control.value;
      const putText = (label, name, opts = {}) => {
        const field = textInput(label, { name, required: Boolean(opts.required), placeholder: opts.placeholder, value: opts.value || "", help: opts.help, className: opts.className });
        optionsHost.append(field.wrapper);
        return field.control;
      };
      const putSelect = (label, name, items, value) => {
        const field = selectField(label, items.map(([v, l]) => ({ value: v, label: l })), { name, value });
        optionsHost.append(field.wrapper);
        return field.control;
      };
      const putCheck = (label, name, checked = false) => {
        const field = checkField(label, { name, checked });
        optionsHost.append(field.wrapper);
        return field.control;
      };
      if (["voice-test", "voice"].includes(action)) {
        const field = checkField("I confirm this may start paid voice generation for the currently saved script.", { name: "paid-confirmation" });
        const box = make("div", { className: "confirm-box span-all" }, [field.wrapper, make("small", {}, `Script revision · ${shortFingerprint(reviewFor(video, "script").fingerprint)}`)]);
        optionsHost.append(box);
        return;
      }
      if (action === "transcribe") {
        putSelect("Language", "language", [["en", "English"], ["nl", "Dutch"]], video.metadata?.language === "nl" ? "nl" : "en");
        putSelect("Speech model", "model", [["large-v3", "Large v3"], ["large-v3-turbo", "Large v3 Turbo"], ["medium", "Medium"], ["small", "Small"], ["base", "Base"], ["tiny", "Tiny"]], "large-v3");
        const hasWords = Boolean(video.files?.transcript?.some(path => path.endsWith("words.json")));
        if (hasWords) putCheck("Replace existing word timings", "replace");
      }
      if (action === "stock-search") {
        putSelect("Provider", "provider", [["all", "All configured providers"], ["pexels", "Pexels"], ["pixabay", "Pixabay"], ["unsplash", "Unsplash"], ["openverse", "Openverse"]], "all");
        putText("Search terms", "query", { required: true, placeholder: "What should the search find?", className: "span-all" });
        putSelect("Media type", "type", [["", "Any type"], ["video", "Video"], ["photo", "Photo"], ["audio", "Audio"]], "");
      }
      if (action === "stock-get") putText("Stock reference", "ref", { required: true, placeholder: "stock:provider/type/id" });
      if (action === "use") {
        putText("Library reference", "ref", { required: true, placeholder: "icon:lucide/arrow-right or graphic:..." });
        putText("Save as (optional)", "name", { placeholder: "asset-name" });
        const ref = optionsHost.querySelector('[name="ref"]');
        const interval = make("div", { className: "form-grid span-all" });
        const start = textInput("Video start (seconds)", { name: "start", type: "number", placeholder: "0" });
        const end = textInput("Video end (seconds)", { name: "end", type: "number", placeholder: "10" });
        add(interval, start.wrapper, end.wrapper);
        optionsHost.append(interval);
        const updateInterval = () => { const show = ref.value.includes("stock:") && ref.value.includes("/video/"); interval.hidden = !show; start.control.required = show; end.control.required = show; };
        ref.addEventListener("input", updateInterval); updateInterval();
      }
      if (action === "capture") {
        putText("Website URL", "url", { required: true, placeholder: "https://example.com/page", type: "url", className: "span-all" });
        putText("Capture name", "name", { required: true, placeholder: "homepage" });
        putSelect("Viewport", "breakpoint", [["mobile", "Mobile"], ["tablet", "Tablet"], ["laptop", "Laptop"], ["desktop", "Desktop"]], "laptop");
      }
      if (action === "record") {
        putText("Flow name", "name", { required: true, placeholder: "course-signup" });
        putSelect("Viewport", "breakpoint", [["mobile", "Mobile"], ["tablet", "Tablet"], ["laptop", "Laptop"], ["desktop", "Desktop"]], "laptop");
        putText("Steps file path", "steps", { required: true, placeholder: "videos/slug/01_voice/steps.txt", className: "span-all", help: "Use an existing public workspace file. Private login data is never requested here." });
      }
    }
    actionField.control.addEventListener("change", renderOptions);
    renderOptions();
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const action = actionField.control.value;
      const scriptDraft = Array.from(state.drafts.values()).some(draft => draft.path === `videos/${video.slug}/01_voice/script.md` && draft.dirty);
      const options = {};
      for (const control of optionsHost.querySelectorAll("input, select")) {
        const name = control.name;
        if (!name || name === "paid-confirmation") continue;
        if (control.type === "checkbox") { if (control.checked) options[name] = true; }
        else if (control.value !== "") options[name] = control.type === "number" ? Number(control.value) : control.value;
      }
      if (["voice-test", "voice"].includes(action)) {
        if (scriptDraft) { showFormError(message, new Error("Save the current script draft before starting voice generation.")); return; }
        const confirmed = optionsHost.querySelector('[name="paid-confirmation"]')?.checked;
        if (!confirmed) { showFormError(message, new Error("Confirm paid generation for the displayed saved script revision.")); return; }
        options.confirmation_fingerprint = reviewFor(video, "script").fingerprint;
      }
      if (action === "stock-search" && options.type) { /* type is a supported structured option */ }
      submit.disabled = true;
      try {
        const requiredGate = ({ "voice-check": "script", "voice-test": "script", voice: "script", transcribe: "voice", cues: "transcript", check: "cues", stills: "cues", render: "scene", thumbnail: "scene" })[action];
        const expectedFingerprint = requiredGate ? reviewFor(video, requiredGate).fingerprint : null;
        const response = await api("/api/jobs", jsonOptions("POST", { action, slug: video.slug, options, expected_fingerprint: expectedFingerprint, request_id: idempotencyKey() }));
        const job = unwrap(response, "job");
        rememberJob(job);
        message.hidden = false;
        message.replaceChildren(make("div", { className: "success-banner" }, [make("strong", {}, "Job queued"), make("p", {}, [link(`Open ${job.action || action} job log`, `/jobs/${encodeURIComponent(job.id)}`)])]));
        await refreshJobs();
        announce(`${stateLabel(job.state || "queued")}: ${action}`);
      } catch (error) { showFormError(message, error); }
      finally { submit.disabled = false; }
    });
    return form;
  }

  async function refreshJobs() {
    try {
      const data = await api("/api/jobs");
      setJobCollection(Array.isArray(data) ? data : Array.isArray(data.jobs) ? data.jobs : []);
      updateNavigation();
    } catch { /* The current view retains its last confirmed job state. */ }
    schedulePolling();
  }

  function setJobCollection(rows) {
    const listed = Array.isArray(rows) ? rows : [];
    const listedIds = new Set(listed.map(job => job.id));
    const recentActive = state.jobs.filter(job => ACTIVE_JOB_STATES.has(job.state) && !listedIds.has(job.id));
    state.jobs = [...recentActive, ...listed];
  }

  function rememberJob(job) {
    if (!job?.id) return;
    state.jobs = [job, ...state.jobs.filter(item => item.id !== job.id)];
    updateNavigation();
    schedulePolling();
  }

  function showFormError(container, error) {
    container.hidden = false;
    container.replaceChildren(notice("Could not complete this action", error.message || "Check the inputs and try again.", "error-banner"));
    announce(error.message || "Action failed.");
  }

  function announce(message) {
    const live = document.getElementById("announcer");
    live.textContent = "";
    requestAnimationFrame(() => { live.textContent = message; });
  }

  function managedRunForm(video) {
    const form = make("form", { className: "form-shell" });
    const blank = { value: "", label: "Choose one" };
    const brand = selectField("Brand", [blank, ...(state.boot?.brands || []).map(id => ({ value: id, label: id }))], { required: true });
    const subject = textInput("Subject", { required: true });
    const result = textArea("Intended result", { required: true });
    const format = selectField("Format", [blank, { value: "wide", label: "Wide" }, { value: "tall", label: "Tall" }], { required: true });
    const language = selectField("Language", [blank, { value: "en", label: "English" }, { value: "nl", label: "Dutch" }], { required: true });
    const review = selectField("Review mode", [blank, { value: "autonomous", label: "Automatic checks" }, { value: "final-review-only", label: "Final review only" }, { value: "selected-stages", label: "Selected stages" }], { required: true });
    const stages = textInput("Selected review stages", { placeholder: "brief, script, scene", help: "Enter stage names separated by commas. Leave empty for no stage stops." });
    const spend = textInput("Maximum paid spend", { required: true, type: "number", help: "Enter a limit. Use 0 to block paid work." });
    spend.control.min = "0"; spend.control.step = "0.01";
    const message = make("div", { role: "status" });
    add(form, make("h2", {}, "Managed production"), make("p", {}, "Save all choices before a full run starts. Paid work stays within your limit. Publishing still needs your approval."), make("div", { className: "form-grid" }, [brand.wrapper, subject.wrapper, result.wrapper, format.wrapper, language.wrapper, review.wrapper, stages.wrapper, spend.wrapper]), button("Save and start run", "button button-primary", null, "submit"), message);
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const settings = { brand: brand.control.value, subject: subject.control.value.trim(), intended_result: result.control.value.trim(), format: format.control.value, language: language.control.value, review_mode: review.control.value, selected_stages: stages.control.value.split(",").map(value => value.trim()).filter(Boolean), max_paid_spend: spend.control.value };
      try {
        await api(`${apiVideoPath(video.slug)}/production`, jsonOptions("POST", { settings }));
        message.textContent = "Run started. Refresh this page to see saved run results.";
      } catch (error) { showFormError(message, error); }
    });
    api(`${apiVideoPath(video.slug)}/production`).then(runs => {
      for (const run of runs) {
        const row = make("p", {}, `Run ${run.id}: ${run.status}${run.error ? " · " + run.error : ""}`);
        if (run.status !== "running" && run.status !== "complete") row.append(button("Resume saved run", "button", async () => {
          try { await api(`${apiVideoPath(video.slug)}/production`, jsonOptions("POST", { resume: run.id })); message.textContent = "Run resumed."; }
          catch (error) { showFormError(message, error); }
        }));
        form.append(row);
        form.append(paidPanel(run.id, `video:${video.slug}`));
      }
    }).catch(error => showFormError(message, error));
    return form;
  }

  function renderVideo(main, slug) {
    return loadVideo(slug).then(async video => {
      if (!main.isConnected) return;
      const requests = state.requests;
      const next = nextGate(video);
      setBreadcrumb([{ label: "Videos", href: "/videos" }, { label: video.title }]);
      const identity = make("div", { className: "video-identity" }, [
        make("span", {}, video.slug), make("span", {}, `${video.format || "Format not set"}${video.style ? ` · ${video.style}` : ""}`), make("span", {}, video.label || "Video"),
        video.creative_style ? make("span", {}, `Installed creative · ${video.creative_style}`) : null,
        video.legacy_style ? make("span", {}, `Project base · ${video.legacy_style}`) : null,
      ]);
      const header = make("div", { className: "video-headline" }, [
        make("div", {}, [make("h1", {}, video.title), identity]),
        make("div", { className: "page-actions" }, [link("Review next stage", reviewPath(video.slug, next.stage.gate), "button button-primary"), link("All videos", "/videos", "button")]),
      ]);
      add(main, header);
      add(main, managedRunForm(video));

      const workflow = make("section", { className: "workflow-layout" }, make("div", { className: "stage-main" }, [
        make("h2", {}, "Production path"),
        make("p", {}, isSilent(slug) ? "This setup fixture follows its explicit silent scene path; narration gates do not apply." : "Files, readiness, jobs, and your decisions are tracked separately at each stage."),
        renderVideoStages(video),
        renderNextAction(video, next),
      ]));
      add(main, workflow);

      const assets = make("section", { className: "section rule-section" }, [sectionHeading("Project files", "Authored inputs and generated outputs in this project.")]);
      const allPaths = Array.from(new Set(Object.values(video.files || {}).flat().concat(...Object.values(video.reviews || {}).map(review => review.artifacts || []))));
      if (allPaths.length) {
        const byGate = make("div", { className: "video-grid" });
        for (const stage of STAGES.filter(item => !isSilent(slug) || !SILENT_GATES.has(item.gate))) {
          const paths = Array.from(new Set([...(video.files?.[stage.gate] || []), ...(video.reviews?.[stage.gate]?.artifacts || [])]));
          if (!paths.length) continue;
          byGate.append(make("section", { className: "evidence-block" }, [make("h2", {}, stage.label), renderArtifactRows(video, stage.gate)]));
        }
        add(assets, byGate);
      } else add(assets, emptyState("No project files yet", "The project folder exists, but its authored and generated stages are still empty."));
      add(main, assets);

      const sourceSection = make("section", { className: "section rule-section" }, [sectionHeading("Linked materials", "Shared source records keep descriptions and provenance in one place.", link("Open library", "/library", "quiet-link"))]);
      const linked = make("div");
      sourceSection.append(linked, materialPicker("video", video.slug, id => {
        video.materials = Array.from(new Set([...(video.materials || []), id]));
        linkedMaterials(linked, video.materials, "video", video.slug);
      }));
      add(main, sourceSection);
      linkedMaterials(linked, video.materials || [], "video", video.slug);

      const styleHost = make("div");
      add(main, styleHost);
      loadPart(styleHost, async () => {
      await loadStyles();
      const styles = state.styles;
      const styleSection = make("section", { className: "section rule-section" }, [sectionHeading("Style recipe", "Applying a style previews its template files and preserves local changes.")]);
      const styleForm = make("form", { className: "form-actions" });
      const styleChoices = [{ value: "", label: "Choose a reusable style" }, ...styles.filter(item => item.id).map(item => ({ value: item.id, label: `${item.title || item.id} · ${item.base_kit || "base kit unavailable"}` }))];
      const styleSelect = selectField("Apply a style", styleChoices, { required: true, value: "" });
      const previewButton = button("Preview file changes", "button", null, "submit");
      add(styleForm, styleSelect.wrapper, previewButton);
      const styleFeedback = make("div", { className: "flash-message", hidden: true, role: "status" });
      const styleDiff = make("div", { hidden: true });
      styleForm.addEventListener("submit", async event => {
        event.preventDefault(); if (!styleSelect.control.value) return;
        previewButton.disabled = true; styleFeedback.hidden = false; styleFeedback.replaceChildren(loadingPage("Preparing a style update preview"));
        try {
          const response = await api(`${apiVideoPath(video.slug)}/style`, jsonOptions("POST", { style_id: styleSelect.control.value, expected_revision: video.metadata?.style_revision || null, confirm: false }));
          const proposal = unwrap(response, "proposal");
          await showStyleDiff(styleDiff, proposal, styleSelect.control.value, video.slug);
          styleDiff.hidden = false;
          styleFeedback.replaceChildren(notice("Review the affected files", `The update contains ${proposal.changes?.length || 0} file change(s). Local edits are preserved until you confirm.`, "inline-notice"));
          const confirmButton = button("Apply this style update", "button button-primary", async () => {
            confirmButton.disabled = true;
            try {
              await api(`${apiVideoPath(video.slug)}/style`, jsonOptions("POST", { style_id: styleSelect.control.value, expected_revision: proposal.revision ?? null, confirm: true }));
              if (main.isConnected) await renderRoute({ focus: false }); announce("Style update applied.");
            } catch (error) { showFormError(styleFeedback, error); }
            finally { confirmButton.disabled = false; }
          });
          const confirmRow = make("div", { className: "form-actions" }, confirmButton);
          styleDiff.append(confirmRow);
        } catch (error) { showFormError(styleFeedback, error); }
        finally { previewButton.disabled = false; }
      });
      styleSection.append(styleForm, styleFeedback, styleDiff);
      return styleSection;
      });
      const creativeHost = make("div");
      add(main, creativeHost);
      loadPart(creativeHost, async () => {
        await loadStyles();
        const host = make("div");
        await window.CreativeStudio.videoCreative(host, video, creativeHelpers());
        return host;
      });

      const requestSection = make("section", { className: "section rule-section" }, [sectionHeading("Agent requests", "Handoffs remain honest until an agent claims them.")]);
      add(requestSection, renderRequests(requests, video.slug));
      requestSection.append(make("details", {}, [make("summary", {}, "Request agent work"), renderAgentRequestForm({ slug: video.slug, fingerprint: next.review.fingerprint || "" })]));
      add(main, requestSection);

      const operations = make("section", { className: "section rule-section" }, [sectionHeading("Production jobs", "Run an allowlisted action with typed inputs and inspect its real log.")]);
      const controls = make("details", {}, make("summary", {}, "Open production actions"));
      const controlsHost = make("div");
      controls.append(controlsHost);
      let opened = false;
      controls.addEventListener("toggle", () => {
        if (!controls.open || opened) return;
        opened = true;
        loadPart(controlsHost, async () => launchJobForm(await api(apiVideoPath(video.slug))));
      });
      operations.append(controls);
      const projectJobs = state.jobs.filter(job => job.slug === video.slug).slice(0, 5);
      if (projectJobs.length) operations.append(make("div", { className: "detail-section" }, [make("h2", {}, "Recent jobs"), make("div", { className: "request-list" }, projectJobs.map(job => make("article", { className: "request-row" }, [
        make("div", {}, [link(job.action || "Production job", `/jobs/${encodeURIComponent(job.id)}`), make("br"), make("small", {}, formatTime(job.created_at))]), statusPill(job.state), make("p", {}, job.error || job.progress || "Open the job for its latest log."), make("span", { className: "source-id" }, job.id),
      ])))]));
      add(main, operations);
    });
  }

  function renderVideoStages(video) {
    const host = make("ol", { className: "stage-flow-list", "aria-label": "Stage readiness" });
    const stages = STAGES.filter(stage => !isSilent(video.slug) || !SILENT_GATES.has(stage.gate));
    for (const stage of stages) {
      const review = reviewFor(video, stage.gate);
      const next = review.missing?.length ? `Needs ${review.missing.join(", ")}` : review.state === "awaiting-review" ? "Your decision is next" : review.state === "approved" ? "Current revision approved" : review.state === "accepted" ? "Completed under session permission" : stage.optional ? "Optional research stage" : "Review the saved stage files";
      host.append(make("li", { className: "stage-flow-row", dataset: { state: review.state } }, [
        make("span", { className: "stage-flow-index", "aria-hidden": "true" }, String(stages.indexOf(stage) + 1).padStart(2, "0")),
        make("span", { className: "stage-flow-main" }, [link(stage.label, reviewPath(video.slug, stage.gate)), make("small", {}, next)]),
        make("span", { className: "stage-flow-meta" }, [statusPill(review.state), make("small", {}, review.state === "unchecked" ? `Recorded: ${stateLabel(review.recorded_state)}` : review.ready ? "Readiness checks pass" : "Not marked ready")]),
        link("Open", reviewPath(video.slug, stage.gate), "text-link"),
      ]));
    }
    return host;
  }

  function renderNextAction(video, next) {
    const review = next.review;
    let title = `Next: ${next.stage.label}`;
    let message;
    if (review.state === "awaiting-review") message = "The current saved revision is waiting for your review.";
    else if (review.state === "stale") message = "An input changed since this stage was approved. Review the current version before continuing.";
    else if (review.missing?.length) message = `Blocked by: ${review.missing.join(", ")}.`;
    else if (review.state === "approved" || review.state === "accepted") message = "All listed stages are complete.";
    else if (review.state === "unchecked") message = "Check for changes · open the stage to check the saved revision and its decisions.";
    else message = "Open the stage to edit its authored inputs, review readiness, and available next action.";
    return make("div", { className: "workflow-next" }, [make("span", { className: "workflow-next-mark", "aria-hidden": "true" }), make("div", { className: "workflow-next-copy" }, [make("strong", {}, title), make("p", {}, message), link(`Open ${next.stage.label}`, reviewPath(video.slug, next.stage.gate), "quiet-link")])]);
  }

  async function showStyleDiff(host, proposal, styleId, slug) {
    host.replaceChildren();
    if (!proposal.changes?.length) { host.append(notice("No files to apply", "The recipe has no template or style files to copy yet.")); return; }
    const title = make("h3", {}, "Proposed file changes");
    const copy = make("p", {}, "Existing files are shown beside the selected recipe. Review the text before applying.");
    const items = make("div", { className: "style-diff-list" });
    for (const change of proposal.changes) {
      const sourcePath = String(change.path).replace(`videos/${slug}/style/`, `styles/${styleId}/`);
      let before = "No current file; this will be added.";
      let after = "Selected recipe file is binary or unavailable as text.";
      const removing = change.after === null;
      const changeLabel = removing ? "Removal" : change.before ? "Update" : "Addition";
      const item = make("section", { className: "detail-section" }, [make("h3", {}, `${changeLabel} · ${change.path}`)]);
      if (change.before && TEXT_EXT.has(ext(change.path))) {
        try { before = (await api(`/api/files?path=${encodeURIComponent(change.path)}`)).text; }
        catch (error) { before = `Current file could not be read: ${error.message}`; }
      }
      if (removing) {
        after = "This file is absent from the selected recipe. Applying this change will remove it from the video snapshot.";
      } else if (TEXT_EXT.has(ext(sourcePath))) {
        try { after = (await api(`/api/files?path=${encodeURIComponent(sourcePath)}`)).text; }
        catch (error) { after = `Recipe file could not be read: ${error.message}`; }
      }
      item.append(make("div", { className: "conflict-grid" }, [
        make("div", { className: "conflict-pane" }, [make("h3", {}, removing ? "Current video file · removal" : change.before ? "Current video file" : "Current"), make("pre", {}, before)]),
        make("div", { className: "conflict-pane" }, [make("h3", {}, removing ? "Recipe result · file removed" : "Recipe file"), make("pre", {}, after)]),
      ]));
      items.append(item);
    }
    host.append(title, copy, items);
  }

  function fileIsText(path) { return TEXT_EXT.has(ext(path)); }
  function fileIsMedia(path) { const suffix = ext(path); return IMAGE_EXT.has(suffix) || VIDEO_EXT.has(suffix) || AUDIO_EXT.has(suffix); }

  async function loadDraft(path) {
    const existing = state.drafts.get(path);
    if (existing?.dirty || existing?.conflict) return existing;
    const result = unwrap(await api(`/api/files?path=${encodeURIComponent(path)}`), "file");
    const draft = { path, text: result.text || "", originalText: result.text || "", revision: result.revision ?? null, editable: result.editable !== false, dirty: false, conflict: null };
    state.drafts.set(path, draft);
    state.files.set(path, result);
    return draft;
  }

  function gateDependencies(gate) {
    const text = {
      research: "Changing research evidence asks for a fresh brief and script review.",
      brief: "Brief changes affect the script, voice, transcript, storyboard, scene, and export reviews.",
      script: "Script changes affect voice generation and every later review.",
      "voice-test": "A new test take needs its own decision before full voice generation.",
      voice: "Voice changes affect transcript, storyboard, scene, and export reviews.",
      transcript: "Word and transcript edits affect storyboard cues, scene, and export reviews.",
      cues: "Storyboard changes affect scene and export reviews.",
      scene: "Scene, style, and used-asset changes affect scene and export reviews.",
      render: "Description and package changes affect the export review.",
    };
    return text[gate] || "Current review state is based on the saved files and required upstream approvals.";
  }

  function mediaElement(path, label) {
    const suffix = ext(path);
    const url = pathUrl(path);
    if (VIDEO_EXT.has(suffix)) return make("video", { controls: true, preload: "none", src: url, "aria-label": label || pathBasename(path) });
    if (AUDIO_EXT.has(suffix)) return make("audio", { controls: true, preload: "none", src: url, "aria-label": label || pathBasename(path) });
    if (IMAGE_EXT.has(suffix)) return make("img", { src: url, alt: label || pathBasename(path), loading: "lazy", decoding: "async" });
    return null;
  }

  function renderMediaFiles(paths, video, gate, { preview = true } = {}) {
    const media = paths.filter(fileIsMedia);
    const trustedPreview = preview && gate === "scene" && video.preview ? `/videos/${video.slug.split("/").map(encodeURIComponent).join("/")}/04_scene/index.html` : null;
    if (!media.length && !trustedPreview) return null;
    const proof = make("div", { className: "media-proof" });
    if (trustedPreview) {
      proof.append(make("iframe", { src: trustedPreview, title: `${video.title} scene preview`, loading: "lazy", sandbox: "allow-scripts" }));
      proof.append(make("small", {}, media.length ? "Authored scene preview. Inspect the source stills below as well." : "Authored scene preview. Source media is under Details."));
    }
    if (media.length) {
      const shown = media.slice(0, 6).map(path => make("section", { className: "media-card" }, [make("h3", {}, pathBasename(path)), mediaElement(path, `${video.title} · ${gateLabel(gate)} · ${pathBasename(path)}`), link("Download source", pathUrl(path, "download"), "quiet-link")]));
      if (media.length > 6) shown.push(make("section", { className: "media-card" }, [make("h3", {}, "More media sources"), lazyPathDetails(media.slice(6), `${media.length - 6} additional source files`)]));
      proof.append(make("div", { className: "media-list" }, shown));
    }
    return proof;
  }

  function reviewerName() {
    try { return localStorage.getItem("studio.reviewer") || "Reviewer"; } catch { return "Reviewer"; }
  }

  function setReviewerName(value) {
    try { localStorage.setItem("studio.reviewer", value.trim() || "Reviewer"); } catch { /* The default name still applies. */ }
  }

  function reviewerField() {
    const field = textInput("Reviewer", { value: reviewerName(), maxlength: 120, help: "Recorded with each decision on this computer." });
    field.control.addEventListener("change", () => setReviewerName(field.control.value));
    return make("section", { className: "evidence-block" }, field.wrapper);
  }

  function decisionLine(reviewState, dirty = false, missing = "", override = "") {
    if (dirty) return "Save or resolve this video's draft first.";
    if (override) return override;
    if (missing && !["awaiting-review", "approved", "skipped"].includes(reviewState)) return `Not ready: ${missing}.`;
    return { "awaiting-review": "Ready for your decision.", approved: "This saved revision is approved.", accepted: "Completed under this session's permission. You can still add a human decision.", stale: "Changed since the last decision. Inspect it, then mark it ready.",
      "changes-requested": "Changes requested.", skipped: "Skipped by you." }[reviewState] || "Not ready yet. Saving edits never approves.";
  }

  // One sticky bar per review page: status on the left, the decision always in reach on the right.
  function decisionBar({ state: reviewState, missing = "", showReady = false, canReady = false, canDecide = false, canChange = canDecide, onReady, onApprove, onRequestChanges, extra = [],
    line: override = "", nextLink = null, approveModes = false, agentModes = null, onStop = null }) {
    const bar = make("section", { className: "decision-bar", "aria-label": "Review decision" });
    const message = make("div", { className: "flash-message", hidden: true, role: "status" });
    const line = make("p", { className: "decision-line", id: "decision-draft-warning" }, decisionLine(reviewState, false, missing, override));
    const panel = make("div", { className: "decision-panel", hidden: true });
    const openPanel = (prompt, submitLabel, run, missing) => {
      const open = panel.hidden ? null : panel.querySelector("textarea");
      if (open && panel.dataset.prompt === prompt) { open.focus(); return; }
      if (open?.value.trim() && !window.confirm("Discard the note you typed?")) { open.focus(); return; }
      panel.dataset.prompt = prompt;
      const field = textArea(prompt, { rows: 3, required: true, maxlength: 4000 });
      const submit = button(submitLabel, "button button-primary", () => withButton(submit, async () => {
        if (!field.control.value.trim()) throw new Error(missing);
        await run(field.control.value.trim());
      }, message));
      const cancel = button("Cancel", "button", () => { panel.hidden = true; panel.replaceChildren(); message.hidden = true; });
      panel.replaceChildren(field.wrapper, make("div", { className: "decision-actions" }, [submit, cancel]));
      panel.hidden = false;
      field.control.focus();
    };
    const actions = make("div", { className: "decision-actions" });
    for (const item of extra) actions.append(button(item.label, "button", () => openPanel(item.prompt, item.submitLabel, item.run, item.missing)));
    if (showReady) {
      const ready = button("Mark ready", "button", () => withButton(ready, onReady, message));
      ready.id = "review-ready-button"; ready.dataset.canReady = String(canReady); ready.disabled = !canReady;
      actions.append(ready);
    }
    for (const [label, mode, className] of agentModes ? [["Run agent", "auto", "button button-primary"]] : []) {
      const start = button(label, className, () => withButton(start, () => agentModes(mode), message));
      start.dataset.canDecide = "true";
      actions.append(start);
    }
    if (onStop) { const stop = button("Stop agent", "button", () => withButton(stop, onStop, message)); actions.append(stop); }
    if (nextLink) actions.append(nextLink);
    // A person may add a human decision after session completion.
    if (canDecide || canChange || (!nextLink && !agentModes && !onStop)) {
      const changes = button("Request changes", "button", () => openPanel("What should change?", "Send request", onRequestChanges, "Add a note that explains the changes requested."));
      const approve = button(approveModes ? "Approve & run agent" : "Approve", "button button-primary", () => withButton(approve, () => onApprove(approveModes ? "auto" : null), message));
      changes.id = "review-changes-button"; approve.id = "review-approve-button";
      approve.dataset.canDecide = String(canDecide); approve.disabled = !canDecide;
      changes.dataset.canDecide = String(canChange); changes.disabled = !canChange;
      actions.append(changes);
      actions.append(approve);
    }
    bar.append(make("div", { className: "decision-bar-row" }, [make("div", { className: "decision-state" }, [statusPill(reviewState), line]), actions]), panel, message);
    return { element: bar, message };
  }

  function detailsDrawer(title, sections) {
    const dialog = make("dialog", { className: "details-drawer", "aria-label": title });
    const close = button("Close", "button button-small", () => dialog.close());
    dialog.append(make("div", { className: "details-drawer-inner" }, [make("div", { className: "details-drawer-head" }, [make("h2", {}, title), close]), ...sections]));
    const toggle = button("Details", "button", () => dialog.showModal());
    toggle.setAttribute("aria-haspopup", "dialog");
    dialog.addEventListener("click", event => { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener("close", () => toggle.focus());
    return { toggle, dialog };
  }

  function renderEditor(draft, gate, refreshReview) {
    const version = state.routeVersion;
    const editor = make("textarea", { className: "output-editor", value: draft.text, spellcheck: true, readOnly: !draft.editable, "aria-label": `${gateLabel(gate)} source` });
    const save = button("Save draft", "button button-dark", async () => {
      save.disabled = true;
      try {
        if (gate === "transcript" && draft.path.endsWith("words.json")) {
          try { JSON.parse(editor.value); }
          catch { throw new Error("Word timings must remain valid JSON. The server also checks the existing timing schema before saving."); }
        }
        const result = unwrap(await api("/api/files", jsonOptions("PUT", { path: draft.path, text: editor.value, expected_revision: draft.revision })), "file");
        draft.originalText = result.text; draft.revision = result.revision; draft.dirty = draft.text !== result.text; draft.conflict = null;
        state.files.set(draft.path, result);
        if (version !== state.routeVersion) return;
        await refreshReview();
        await renderRoute({ focus: false });
        announce("Draft saved. Approval is still a separate action.");
      } catch (error) {
        if (version !== state.routeVersion) return;
        if (error.code === "conflict") {
          try { draft.conflict = unwrap(await api(`/api/files?path=${encodeURIComponent(draft.path)}`), "file"); }
          catch (readError) { draft.conflict = { text: `Latest file could not be read: ${readError.message}`, revision: null }; }
          draft.text = editor.value;
          draft.dirty = draft.text !== draft.originalText;
          await renderRoute({ focus: false });
          announce("Save conflict. Your draft is retained beside the current file.");
        } else showFormError(editor.closest(".output-panel")?.querySelector(".flash-message") || editor.parentElement, error);
      } finally { save.disabled = false; }
    });
    save.disabled = !draft.dirty || !draft.editable;
    const dirtyText = make("span", { className: "saved-revision", id: "draft-state" }, draft.dirty ? "Unsaved draft" : `Saved revision ${shortFingerprint(draft.revision)}`);
    const editorFooter = make("div", { className: "editor-footer" }, [dirtyText, make("span", {}, draft.editable ? "Explicit save required" : "Read-only generated file")]);
    const panel = make("section", { className: "output-panel" }, [
      make("div", { className: "output-heading" }, [make("div", {}, [make("h2", {}, pathBasename(draft.path)), make("p", {}, draft.path)]), save]),
      editor,
      editorFooter,
      make("div", { className: "flash-message", hidden: true, role: "status" }),
    ]);
    if (gate === "transcript" && draft.path.endsWith("transcript.md")) panel.append(make("p", { className: "inline-notice" }, "Editing transcript text does not change words.json timing data."));
    if (gate === "transcript" && draft.path.endsWith("words.json")) panel.append(make("p", { className: "inline-notice" }, "Timing edits are checked against the existing words.json schema before replacing the saved file."));
    if (draft.conflict) panel.append(renderConflict(draft));
    editor.addEventListener("input", () => {
      draft.text = editor.value;
      draft.dirty = draft.text !== draft.originalText;
      save.disabled = !draft.dirty || !draft.editable;
      dirtyText.textContent = draft.dirty ? "Unsaved draft · kept in this page" : `Saved revision ${shortFingerprint(draft.revision)}`;
    });
    return panel;
  }

  function renderConflict(draft) {
    const current = draft.conflict?.text || "The current file could not be read.";
    const retained = draft.text;
    const host = make("section", { className: "detail-section", role: "alert" }, [
      make("h2", {}, "Save conflict · your draft is retained"),
      make("p", {}, "The file changed after you opened it. Compare the current saved file with your text before choosing a recovery action."),
      make("div", { className: "conflict-grid" }, [
        make("div", { className: "conflict-pane" }, [make("h3", {}, `Current saved file · ${shortFingerprint(draft.conflict?.revision)}`), make("pre", {}, current)]),
        make("div", { className: "conflict-pane" }, [make("h3", {}, "Your retained draft"), make("pre", {}, retained)]),
      ]),
    ]);
    const actions = make("div", { className: "conflict-actions" });
    const reload = button("Use current file", "button", () => {
      draft.text = current; draft.originalText = current; draft.revision = draft.conflict?.revision ?? null; draft.dirty = false; draft.conflict = null;
      renderRoute({ focus: false }); announce("Current saved file loaded into the editor.");
    });
    const copy = button("Copy current file", "button", async () => {
      try { await navigator.clipboard.writeText(current); announce("Current file copied to clipboard."); }
      catch { announce("Clipboard access is unavailable in this browser context."); }
    });
    add(actions, reload, copy); host.append(actions);
    return host;
  }

  async function renderReview(main, slug, gate) {
    const version = state.routeVersion;
    const stage = STAGES.find(item => item.gate === gate);
    if (!stage) throw new Error("Unknown review stage.");
    const [video, reviewResult] = await Promise.all([
      loadVideo(slug), api(`${apiVideoPath(slug)}/reviews/${encodeURIComponent(gate)}`),
    ]);
    if (version !== state.routeVersion) return;
    const review = unwrap(reviewResult, "review");
    video.reviews[gate] = review;
    Object.assign(video.reviews, review.upstream || {});
    const inputGate = AGENT_INPUT[gate];
    const stageRequests = inputGate ? state.requests.filter(item => item.slug === slug && item.kind === gate) : [];
    const activeRun = stageRequests.find(item => item.state === "running");
    const lastRun = stageRequests[0];
    main.dataset.reviewSlug = slug;
    main.dataset.reviewState = review.state || "draft";
    main.dataset.reviewMissing = (review.missing || []).join(", ");
    setBreadcrumb([{ label: "Videos", href: "/videos" }, { label: video.title, href: slugPath(slug) }, { label: `${gateLabel(gate)} review` }]);
    if (isSilent(slug) && SILENT_GATES.has(gate)) {
      add(main, pageIntro(`${gateLabel(gate)} review`, "This setup fixture follows an explicit silent path."));
      add(main, notice("Not applicable to this fixture", "Voice, test-take, and transcript gates do not block the silent setup scene.", "inline-notice"));
      add(main, link("Return to the setup project", slugPath(slug), "button"));
      return;
    }

    const drawerSections = [];
    const drawer = detailsDrawer("Review details", drawerSections);
    const header = make("div", { className: "review-header" }, [
      make("div", {}, [make("h1", {}, `${video.title} · ${gateLabel(gate)}`), make("p", { className: "review-subtitle" }, `Review the saved ${gateLabel(gate).toLowerCase()} revision. Saving edits never approves them.`)]),
      make("div", { className: "review-state-block" }, [make("span", { className: "review-fingerprint" }, `REV ${shortFingerprint(review.fingerprint)}`), drawer.toggle]),
    ]);
    add(main, header);
    add(main, make("div", { className: "review-rail-bar", role: "navigation", "aria-label": "Review another production stage" }, STAGES.filter(item => !isSilent(slug) || !SILENT_GATES.has(item.gate)).map((item, index) => {
      const current = item.gate === gate;
      const a = make("a", { className: "review-rail-step", href: reviewPath(slug, item.gate), "aria-current": current ? "step" : null }, [
        make("span", { className: "review-rail-index" }, String(index + 1).padStart(2, "0")), make("span", { className: "review-rail-name" }, item.label),
      ]);
      return a;
    })));
    add(main, stageSelect(video, gate));

    const paths = Array.from(new Set([...(video.files?.[gate] || []), ...(review.artifacts || [])]));
    const textPaths = paths.filter(fileIsText);
    const downloadPaths = paths.filter(path => !fileIsText(path) && !fileIsMedia(path));
    // A scene is judged on its live preview; its many source clips are reference material.
    const previewOnly = gate === "scene" && Boolean(video.preview);
    const media = renderMediaFiles(previewOnly ? [] : paths, video, gate);
    const output = make("div", { className: "review-output" });
    if (media) output.append(media);
    let selectedDraft = null;
    if (textPaths.length) {
      const selectedPath = state.reviewFileSelection?.[`${slug}/${gate}`] || textPaths[0];
      selectedDraft = await loadDraft(textPaths.includes(selectedPath) ? selectedPath : textPaths[0]).catch(() => null);
      if (version !== state.routeVersion) return;
      if (selectedDraft) {
        if (textPaths.length > 1) {
          const fileChoice = selectField("Review file", textPaths.map(path => ({ value: path, label: pathBasename(path) })), { value: selectedDraft.path });
          fileChoice.control.value = selectedDraft.path;
          fileChoice.control.addEventListener("change", () => {
            state.reviewFileSelection ||= {};
            state.reviewFileSelection[`${slug}/${gate}`] = fileChoice.control.value;
            renderRoute({ focus: false });
          });
          output.append(make("div", { className: "toolbar" }, fileChoice.wrapper));
        }
        output.append(renderEditor(selectedDraft, gate, async () => {
          const fresh = unwrap(await api(`${apiVideoPath(slug)}/reviews/${encodeURIComponent(gate)}`), "review");
          Object.assign(review, fresh);
        }));
      }
    }
    if (activeRun) output.prepend(agentPanel(activeRun, version));
    else if (lastRun && (["failed", "cancelled"].includes(lastRun.state) || (lastRun.state === "succeeded" && !review.ready && !["awaiting-review", "approved"].includes(review.state)))) {
      output.prepend(notice(`Last agent run: ${stateLabel(lastRun.state).toLowerCase()}`, lastRun.note || "No note was recorded."));
    }
    if (!media && !textPaths.length && !activeRun) output.append(make("div", { className: "stage-preview-fallback" }, [make("strong", {}, "No review material yet"), make("p", {}, review.missing?.length ? `Readiness needs: ${review.missing.join(", ")}.` : downloadPaths.length ? "This stage only has downloadable files. Open Details to inspect them." : "This stage has no linked output yet.") ]));
    add(main, output);

    drawerSections.push(make("section", { className: "evidence-block" }, [make("h2", {}, "Readiness"), statusPill(review.ready ? "ready" : (review.state === "blocked" ? "blocked" : review.state), review.ready ? (review.state === "approved" ? "Checks passed" : "Ready for review") : null), make("p", {}, review.missing?.length ? `Needs: ${review.missing.join(", ")}.` : review.ready ? "The backend confirms the current artifacts meet this stage's readiness checks." : "This revision has not been marked ready for review.")]));
    if (review.history?.length) {
      drawerSections.push(make("section", { className: "evidence-block" }, [make("h2", {}, "Recorded decisions"), make("ul", { className: "evidence-list" }, review.history.slice().reverse().map(event => make("li", {}, [
        make("strong", {}, event.kind === "ready" ? "Marked ready" : event.kind === "skip" ? "Research skipped" : stateLabel(event.decision)),
        make("small", {}, [event.reviewer ? `${event.reviewer} · ` : "", formatTime(event.at), ` · ${shortFingerprint(event.fingerprint)}`]),
        event.note ? make("small", {}, event.note) : null,
      ])))]));
    }
    drawerSections.push(make("section", { className: "evidence-block" }, [make("h2", {}, "What this affects"), make("p", {}, gateDependencies(gate))]));
    const evidence = make("section", { className: "evidence-block" }, [make("h2", {}, "Stage files")]);
    if (paths.length) {
      const evidenceRows = paths.slice(0, 30).map(path => make("li", {}, [artifactLink(path), make("small", {}, path)]));
      if (paths.length > 30) evidenceRows.push(make("li", {}, lazyPathDetails(paths.slice(30), `${paths.length - 30} more stage files`)));
      evidence.append(make("ul", { className: "evidence-list" }, evidenceRows));
    }
    else evidence.append(make("p", {}, "No authored or generated files are recorded for this stage yet."));
    drawerSections.push(evidence);
    if (downloadPaths.length) {
      drawerSections.push(make("section", { className: "evidence-block" }, [
        make("h2", {}, "Other stage files"),
        make("ul", { className: "evidence-list" }, downloadPaths.slice(0, 30).map(path => make("li", {}, [artifactLink(path), make("small", {}, path)]))),
        downloadPaths.length > 30 ? lazyPathDetails(downloadPaths.slice(30), `${downloadPaths.length - 30} more downloadable files`) : null,
      ]));
    }
    const sourceMedia = previewOnly ? renderMediaFiles(paths, video, gate, { preview: false }) : null;
    if (sourceMedia) drawerSections.push(make("section", { className: "evidence-block" }, [make("h2", {}, "Source media"), sourceMedia]));
    const sourcePanel = make("section", { className: "evidence-block" }, [make("h2", {}, "Linked sources")]);
    const linked = make("div");
    sourcePanel.append(linked);
    drawerSections.push(sourcePanel);
    // Source metadata never delays the selected review and editor.
    requestAnimationFrame(() => { if (version === state.routeVersion) linkedMaterials(linked, video.materials || [], "video", slug); });
    if (review.legacy) drawerSections.push(make("section", { className: "evidence-block" }, make("details", {}, [make("summary", {}, "Earlier review notes"), make("p", {}, "Legacy prose is retained as history; it is not verified against this revision."), make("pre", { className: "style-diff" }, review.legacy)])));
    drawerSections.push(make("section", { className: "evidence-block" }, [make("h2", {}, "Request agent work"), make("p", {}, "The request will wait until an agent claims it."), renderAgentRequestForm({ slug, kind: stage.gate === "render" ? "review-checks" : stage.gate === "scene" ? "scene" : stage.gate === "cues" ? "cues" : stage.gate === "script" ? "script" : "research", fingerprint: review.fingerprint || "" })]));
    drawerSections.push(reviewerField());
    drawer.dialog.querySelector(".details-drawer-inner").append(...drawerSections);
    add(main, drawer.dialog);

    const decide = async (decision, note = "", rerender = true) => {
      if (hasDirtyDraft(slug)) throw new Error("Save or resolve this video's draft first.");
      const fresh = unwrap(await api(`${apiVideoPath(slug)}/reviews/${encodeURIComponent(gate)}`), "review");
      if (fresh.fingerprint !== review.fingerprint) throw new Error("Inputs changed after this page opened. Reload and inspect the current revision.");
      if (decision === "ready") await api(`${apiVideoPath(slug)}/reviews/${encodeURIComponent(gate)}/ready`, jsonOptions("POST", { expected_fingerprint: review.fingerprint }));
      else await api(`${apiVideoPath(slug)}/reviews/${encodeURIComponent(gate)}/decision`, jsonOptions("POST", { decision, reviewer: reviewerName(), note, expected_fingerprint: review.fingerprint }));
      announce(decision === "ready" ? "Current revision marked ready for review." : decision === "approved" ? "Revision approved." : "Changes requested for this saved revision.");
      if (rerender && version === state.routeVersion) await renderRoute({ focus: false });
    };
    const extra = gate === "research" ? [{ label: "Skip research…", prompt: "Reason to skip research", submitLabel: "Skip research", missing: "A reason is required to skip research.", run: async reason => {
      if (hasDirtyDraft(slug)) throw new Error("Save or resolve this video's draft first.");
      await api(`${apiVideoPath(slug)}/research/skip`, jsonOptions("POST", { reason, reviewer: reviewerName() }));
      if (version === state.routeVersion) await renderRoute({ focus: false }); announce("Research marked skipped.");
    } }] : [];
    const canRunAgent = Boolean(inputGate && ["approved", "accepted"].includes(reviewFor(video, inputGate).state) && !activeRun && !["awaiting-review", "approved", "accepted", "skipped"].includes(review.state));
    const next = ["approved", "accepted"].includes(review.state) ? nextGate(video) : null;
    let line = "";
    if (activeRun) line = `Agent is writing the ${gateLabel(gate).toLowerCase()} · since ${formatTime(activeRun.run?.started_at || activeRun.claimed_at)}.`;
    else if (canRunAgent && lastRun?.state === "waiting-for-agent" && lastRun.run?.mode === "guided") line = "Waiting for the agent in your terminal.";
    else if (canRunAgent && !review.ready) line = `No ${gateLabel(gate).toLowerCase()} yet. An agent writes it from the approved ${gateLabel(inputGate).toLowerCase()}.`;
    main.dataset.reviewLine = line;
    const bar = decisionBar({
      state: review.state, missing: (review.missing || []).join(", "), line,
      nextLink: next && next.stage.gate !== gate ? link(`Next: ${next.stage.label} →`, reviewPath(slug, next.stage.gate), "button button-primary") : null,
      // Offer the agent only when the next stage is unwritten, so re-approving never rewrites existing work.
      approveModes: Boolean(review.next_unwritten),
      agentModes: canRunAgent ? async mode => {
        if (hasDirtyDraft(slug)) throw new Error("Save or resolve this video's draft first.");
        await startAgent(slug, gate, reviewFor(video, inputGate).fingerprint, mode);
        announce(mode === "auto" ? "Agent started." : "A terminal opened for the guided agent.");
        await renderRoute({ focus: false });
      } : null,
      onStop: activeRun?.run?.mode === "auto" ? async () => {
        await api(`/api/requests/${encodeURIComponent(activeRun.id)}/cancel`, jsonOptions("POST", {}));
        await renderRoute({ focus: false });
      } : null,
      showReady: !["awaiting-review", "approved", "accepted", "skipped"].includes(review.state) && (review.ready || !canRunAgent),
      canReady: Boolean(review.ready && !["awaiting-review", "approved", "accepted", "skipped"].includes(review.state)),
      canDecide: ["awaiting-review", "accepted"].includes(review.state),
      onReady: () => decide("ready"), onRequestChanges: note => decide("changes-requested", note), extra,
      onApprove: async mode => {
        await decide("approved", "", !mode);
        if (!mode) return;
        const kind = AGENT_NEXT[gate];
        try { await startAgent(slug, kind, review.fingerprint, mode); }
        catch (error) { state.reviewFlash = { path: reviewPath(slug, kind), text: `Approved. Agent not started: ${error.message}` }; }
        if (version !== state.routeVersion) return;
        history.pushState({}, "", reviewPath(slug, kind));
        await renderRoute({ focus: true });
      },
    });
    if (state.reviewFlash?.path === location.pathname) { bar.message.hidden = false; bar.message.textContent = state.reviewFlash.text; }
    state.reviewFlash = null;
    add(main, bar.element);
    syncReviewDraftState();
  }

  // Reuses a request whose start failed earlier, so retries never pile up waiting requests.
  async function startAgent(slug, kind, fingerprint, mode) {
    const old = state.requests.find(item => item.slug === slug && item.kind === kind && item.state === "waiting-for-agent" && !item.run && item.fingerprint === fingerprint);
    const request = old || unwrap(await api("/api/requests", jsonOptions("POST", { slug, kind, instructions: AGENT_TASK[kind], fingerprint, request_id: idempotencyKey() })), "request");
    if (!old) state.requests = [request, ...state.requests];
    const started = unwrap(await api(`/api/requests/${encodeURIComponent(request.id)}/run`, jsonOptions("POST", { mode })), "request");
    state.requests = state.requests.map(item => item.id === started.id ? started : item);
    return started;
  }

  function agentPanel(request, version) {
    const log = make("pre", { className: "job-log agent-log", "aria-label": "Agent output" }, "Working. Claude prints its summary when it finishes.");
    const panel = make("section", { className: "agent-panel" }, [
      make("h2", {}, `Agent at work · ${gateLabel(request.kind)}`),
      make("p", {}, "When the agent finishes, this panel offers the updated review. Your draft stays in place."), log,
    ]);
    const openUpdated = () => {
      for (const [key, draft] of state.drafts) if (draft.path?.startsWith(`videos/${request.slug}/`) && !draft.dirty) state.drafts.delete(key);
      return renderRoute({ focus: false });
    };
    const poll = async () => {
      if (version !== state.routeVersion) return;
      try {
        const status = await api(`/api/requests/${encodeURIComponent(request.id)}/log`);
        if (version !== state.routeVersion) return;
        if (status.log) log.textContent = status.log;
        if (status.state !== "running") {
          request.state = status.state;
          panel.append(notice(`Agent ${stateLabel(status.state).toLowerCase()}`, "Open the updated review to check the saved work. Unsaved text is retained."), button("Open updated review", "button", openUpdated));
          return;
        }
      } catch { /* keep polling; the studio may be restarting */ }
      setTimeout(poll, 5000);
    };
    poll();
    return panel;
  }

  async function withButton(control, action, messageHost) {
    control.disabled = true;
    try { await action(); }
    catch (error) { showFormError(messageHost, error); }
    finally { control.disabled = false; }
  }

  function renderVideoNew(main) {
    setBreadcrumb([{ label: "Videos", href: "/videos" }, { label: "New video" }]);
    add(main, pageIntro("New video", "Start from the existing template. The brief is required before the script is written."));
    const form = make("form", { className: "form-shell" });
    const slug = textInput("Project slug", { required: true, pattern: "[a-z0-9]+(?:-[a-z0-9]+)*", maxlength: 64, placeholder: "academy-course-intro", help: "Lowercase letters, numbers, and hyphens." });
    const brand = selectField("Brand", [{ value: "", label: "Choose a brand" }, ...(state.boot?.brands || []).map(id => ({ value: id, label: id }))], { required: true });
    const audience = textInput("Audience", { required: true, placeholder: "Who should understand this video?" });
    const videoType = textInput("Video type", { required: true, placeholder: "Explainer, onboarding, social, ad…" });
    const language = selectField("Language", [{ value: "en", label: "English" }, { value: "nl", label: "Dutch" }], { required: true });
    const outcome = textArea("One outcome", { required: true, rows: 3, placeholder: "What should the viewer understand or do?", className: "span-all" });
    const format = selectField("Format", [{ value: "wide", label: "Wide · 16:9" }, { value: "tall", label: "Tall · 9:16" }], { required: true });
    const styleOptions = [{ value: "modern", label: "Modern kit (default)" }];
    for (const recipe of state.styles.filter(item => item.id && item.id !== "modern" && !item.error)) styleOptions.push({ value: `recipe:${recipe.id}`, label: `${recipe.title || recipe.id} · ${recipe.base_kit || "base kit not set"}` });
    const style = selectField("Base kit or style recipe", styleOptions, { required: true, help: "A selected recipe is snapshotted into this project when it is created." });
    const message = make("div", { className: "flash-message", hidden: true, role: "status" });
    const submit = button("Create project", "button button-primary", null, "submit");
    add(form, make("div", { className: "form-grid" }, [brand.wrapper, slug.wrapper, format.wrapper, audience.wrapper, videoType.wrapper, language.wrapper, style.wrapper, outcome.wrapper]), make("div", { className: "form-actions" }, submit), message);
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const projectSlug = slug.control.value.trim();
      if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(projectSlug)) { showFormError(message, new Error("Use lowercase letters, numbers, and hyphens in the project slug.")); return; }
      if (state.videos.some(video => video.slug === `${brand.control.value}/${projectSlug}`)) { showFormError(message, new Error("A project with this slug already exists. Choose another slug.")); return; }
      const selected = style.control.value;
      const recipe = selected.startsWith("recipe:") ? state.styles.find(item => item.id === selected.slice(7)) : null;
      const baseKit = recipe?.base_kit || selected;
      const options = {
        brief: { audience: audience.control.value.trim(), video_type: videoType.control.value.trim(), language: language.control.value, outcome: outcome.control.value.trim() },
        brand: brand.control.value, format: format.control.value, style: baseKit,
      };
      if (recipe) options.style_id = recipe.id;
      submit.disabled = true;
      try {
        const response = await api("/api/jobs", jsonOptions("POST", { action: "new", slug: projectSlug, options, expected_fingerprint: null, request_id: idempotencyKey() }));
        const job = unwrap(response, "job");
        rememberJob(job);
        if (!main.isConnected) return;
        history.pushState({}, "", `/jobs/${encodeURIComponent(job.id)}`);
        await renderRoute({ focus: true });
        announce("Project creation queued.");
      } catch (error) { showFormError(message, error); }
      finally { submit.disabled = false; }
    });
    add(main, form);
    add(main, make("section", { className: "form-section" }, [make("h2", {}, "Before the script"), make("p", {}, "The brief records audience, video type, language, and one outcome. Review it before drafting or generating voice.")]));
  }

  async function renderJob(main, jobId) {
    const response = await api(`/api/jobs/${encodeURIComponent(jobId)}`);
    const job = unwrap(response, "job");
    state.jobDetail = job;
    rememberJob(job);
    setBreadcrumb([{ label: "Videos", href: "/videos" }, { label: "Production job" }]);
    const videoLink = job.slug && job.action !== "new" ? link(job.slug, slugPath(job.slug), "quiet-link") : null;
    add(main, make("div", { className: "page-intro" }, [
      make("div", { className: "page-intro-copy" }, [make("h1", { id: "job-title" }, `${stateLabel(job.state)} · ${stateLabel(job.action)}`), make("p", { id: "job-status-copy" }, job.error || job.progress || "Production status and output are taken from the job record.")]),
      videoLink ? make("div", { className: "page-actions" }, [videoLink]) : null,
    ]));
    const summary = make("div", { className: "job-summary" }, [
      make("span", {}, [make("strong", {}, "Video"), ` ${job.slug || "Workspace"}`]),
      make("span", {}, [make("strong", {}, "Action"), ` ${job.action || "Unknown"}`]),
      make("span", {}, [make("strong", {}, "Started"), ` ${formatTime(job.created_at)}`]),
      job.exit_code === null || job.exit_code === undefined ? null : make("span", {}, [make("strong", {}, "Exit"), ` ${job.exit_code}`]),
      job.progress ? make("span", { id: "job-progress" }, [make("strong", {}, "Progress"), ` ${job.progress}`]) : make("span", { id: "job-progress" }, "No progress update reported."),
    ]);
    add(main, summary);
    const logSection = make("section", { className: "section" }, [sectionHeading("Job log", "The log contains actual command output; unknown duration stays unknown.")]);
    logSection.append(make("pre", { className: "job-log", id: "job-log", "aria-label": "Production job log" }, job.log || "No log output yet."));
    add(main, logSection);
    const outputs = Array.isArray(job.outputs) ? job.outputs : [];
    const outputSection = make("section", { className: "section rule-section" }, [sectionHeading("Outputs", "Files are linked only when the job record reports them.")]);
    if (outputs.length) {
      outputSection.append(make("ul", { className: "artifact-list" }, outputs.map(output => {
        const path = typeof output === "string" ? output : output.path || "";
        const title = typeof output === "string" ? pathBasename(output) : output.title || pathBasename(path);
        return make("li", {}, [make("span", { className: "artifact-label" }, [make("strong", {}, title), make("small", {}, path)]), make("span", { className: "artifact-actions" }, [link("Open file", pathUrl(path, fileIsMedia(path) ? "media" : "download"), "text-link")])]);
      })));
    } else outputSection.append(emptyState("No output links recorded", job.state === "failed" || job.state === "interrupted" ? "The job may have left incomplete files. Inspect its log and the project stage before retrying." : "Output links appear after the job records and validates them."));
    add(main, outputSection);
    const controls = make("div", { className: "job-next-actions" });
    const message = make("div", { className: "flash-message", hidden: true, role: "status" });
    if (ACTIVE_JOB_STATES.has(job.state)) {
      controls.append(button("Cancel job", "button button-danger", async event => {
        await withButton(event.currentTarget, async () => {
          await api(`/api/jobs/${encodeURIComponent(job.id)}/cancel`, jsonOptions("POST", {}));
          await renderRoute({ focus: false }); announce("Cancellation requested; the process stops before the lock is released.");
        }, message);
      }));
    } else if (["failed", "cancelled", "interrupted"].includes(job.state) && !["voice", "voice-test", "new"].includes(job.action)) {
      controls.append(button("Retry as a new job", "button", async event => {
        await withButton(event.currentTarget, async () => {
          const retry = await api("/api/jobs", jsonOptions("POST", { action: job.action, slug: job.slug, options: job.options || {}, expected_fingerprint: null, request_id: idempotencyKey() }));
          const record = unwrap(retry, "job"); rememberJob(record); if (!main.isConnected) return; history.pushState({}, "", `/jobs/${encodeURIComponent(record.id)}`); await renderRoute({ focus: true });
        }, message);
      }));
    }
    if (job.slug && job.action === "new") controls.append(link("Open project list", "/videos", "button"));
    if (job.slug && job.action !== "new") controls.append(link("Return to project", slugPath(job.slug), "button"));
    add(main, controls, message);
    if (job.slug && job.action === "new") {
      add(main, notice("Creation status", "The project appears in Videos once the creation job finishes. The saved brief remains part of the new project.", "inline-notice"));
    }
  }

  function kindChoices() {
    return [
      { value: "image", label: "Image" }, { value: "audio", label: "Audio" }, { value: "video", label: "Video" },
      { value: "document", label: "Document" }, { value: "logo", label: "Logo" }, { value: "reference", label: "Reference link" },
    ];
  }

  function targetChoice(label = "Attach to (optional)") {
    const choices = [{ value: "", label: "Keep unlinked for now" }];
    for (const video of state.videos) choices.push({ value: `video:${video.slug}`, label: `Video · ${video.title}` });
    for (const style of state.styles) if (style.id) choices.push({ value: `style:${style.id}`, label: `Style · ${style.title || style.id}` });
    return selectField(label, choices, { value: "" });
  }

  async function saveMaterialRecord(metadata, permissionScope, targetValue = "") {
    const response = await api("/api/materials", jsonOptions("POST", { ...metadata, permission_scope: permissionScope.trim() }));
    const material = unwrap(response, "material");
    if (targetValue) {
      const separator = targetValue.indexOf(":");
      const ownerKind = targetValue.slice(0, separator);
      const ownerId = targetValue.slice(separator + 1);
      try { await api("/api/materials/link", jsonOptions("POST", { owner_kind: ownerKind, owner_id: ownerId, material_id: material.id })); }
      catch (error) { error.materialRecord = material; throw error; }
    }
    return material;
  }

  function reportSavedMaterialLinkFailure(host, material, error) {
    host.hidden = false;
    host.replaceChildren(notice("Material saved, but not attached", `Record ${material.id} is in Library. The attachment failed: ${error.message}. You can retry from its material card.`, "error-banner"));
    refreshLibrary().catch(() => {});
  }

  function attachMaterialForm(material) {
    const form = make("form", { className: "material-actions" });
    const target = targetChoice("Attach to another video or style");
    const submit = button("Attach", "button button-small", null, "submit");
    const message = make("div", { className: "flash-message", hidden: true, role: "status" });
    add(form, target.wrapper, submit, message);
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const value = target.control.value;
      if (!value) return;
      const [owner_kind, owner_id] = value.split(":", 2);
      submit.disabled = true;
      try {
        await api("/api/materials/link", jsonOptions("POST", { owner_kind, owner_id, material_id: material.id }));
        message.hidden = false; message.replaceChildren(notice("Material attached", "The shared record is linked to that workspace item.", "success-banner"));
        announce("Material attached.");
      } catch (error) { showFormError(message, error); }
      finally { submit.disabled = false; }
    });
    return form;
  }

  function materialPreview(material) {
    const path = (material.files || []).find(fileIsMedia) || (!/^https?:/i.test(material.source || "") && fileIsMedia(material.source) ? material.source : null);
    const source = path ? mediaElement(path, material.title || material.id) : null;
    if (source) return make("div", { className: "material-thumb" }, source);
    return make("div", { className: "material-thumb" }, [make("span", { className: "material-thumb-label" }, material.error ? "Record needs attention" : `${material.kind || "Source"} · preview not available`)]);
  }

  function materialCard(material) {
    const linked = [];
    for (const slug of material.linked_videos || []) {
      const video = state.videos.find(item => item.slug === slug);
      linked.push(link(video?.title || slug, slugPath(slug)));
    }
    for (const id of material.linked_styles || []) {
      const style = state.styles.find(item => item.id === id);
      linked.push(link(style?.title || id, `/styles/${encodeURIComponent(id)}`));
    }
    const source = String(material.source || "");
    const sourceLink = /^https?:/i.test(source)
      ? make("a", { href: source, target: "_blank", rel: "noopener noreferrer", className: "quiet-link" }, "Open source link")
      : source && source !== "upload" ? link("Open source file", pathUrl(source, fileIsMedia(source) ? "media" : "download"), "quiet-link") : null;
    const attachment = make("details", {}, make("summary", {}, "Attach this material"));
    let attachLoaded = false;
    attachment.addEventListener("toggle", () => {
      if (!attachment.open || attachLoaded) return;
      attachLoaded = true;
      attachment.append(attachMaterialForm(material));
    });
    const card = make("article", { className: "material-tile", id: `material-${material.id}` }, [
      materialPreview(material),
      make("div", { className: "material-body" }, [
        make("div", { className: "material-type" }, [statusPill(material.kind || "unknown"), material.origin ? make("span", {}, `Source · ${material.origin.replaceAll("-", " ")}`) : null, material.rights === "unknown" || !material.rights ? statusPill("blocked", "Rights unknown · reuse blocked") : make("span", {}, `Rights · ${material.rights}`)]),
        make("h3", {}, material.title || material.id), make("p", {}, material.description || material.error || "No description recorded."),
        make("small", { className: "source-id" }, `${material.id}${material.tags?.length ? ` · ${material.tags.join(", ")}` : ""}`),
        sourceLink,
        make("div", { className: "material-links-inline" }, linked.length ? [make("strong", {}, "Linked to"), ...linked] : [make("span", {}, "Not linked to a video or style")]),
        material.files?.length ? make("details", {}, [make("summary", {}, `Files · ${material.files.length}`), make("ul", { className: "evidence-list" }, material.files.map(path => make("li", {}, [link(pathBasename(path), pathUrl(path, fileIsMedia(path) ? "media" : "download")), make("small", {}, path)])))]) : null,
        material.path ? materialEditDetails(material) : null,
        attachment,
      ]),
    ]);
    return card;
  }

  function materialEditDetails(material) {
    const details = make("details", { className: "material-edit" });
    const summary = make("summary", {}, "Edit source record");
    const editorHost = make("div", { className: "detail-section" });
    let loaded = false;
    details.addEventListener("toggle", async () => {
      if (!details.open || loaded) return;
      loaded = true; editorHost.replaceChildren(loadingPage("Loading source record")); details.append(editorHost);
      try {
        const draft = await loadDraft(material.path);
        editorHost.replaceChildren();
        const textarea = make("textarea", { className: "output-editor", value: draft.text, "aria-label": `Source record for ${material.title || material.id}` });
        const status = make("span", { className: "saved-revision" }, `Saved revision ${shortFingerprint(draft.revision)}`);
        const message = make("div", { className: "flash-message", hidden: true, role: "status" });
        const save = button("Save source record", "button button-dark", async () => {
          save.disabled = true;
          try {
            const updated = unwrap(await api("/api/files", jsonOptions("PUT", { path: draft.path, text: textarea.value, expected_revision: draft.revision })), "file");
            draft.originalText = updated.text; draft.revision = updated.revision; draft.dirty = draft.text !== updated.text; draft.conflict = null;
            if (!details.isConnected) return;
            if (!draft.dirty) await refreshLibrary();
            status.textContent = draft.dirty ? "Unsaved draft" : `Saved revision ${shortFingerprint(draft.revision)}`;
            announce("Source record saved.");
          } catch (error) {
            if (error.code === "conflict") {
              try { draft.conflict = unwrap(await api(`/api/files?path=${encodeURIComponent(draft.path)}`), "file"); }
              catch (readError) { draft.conflict = { text: `Current file could not be read: ${readError.message}` }; }
              draft.text = textarea.value; draft.dirty = draft.text !== draft.originalText;
              editorHost.replaceChildren(make("p", { className: "error-banner" }, "The source record changed after you opened it. Your text is retained below."), textarea, status, renderConflict(draft), message);
              showFormError(message, error);
            } else showFormError(message, error);
          } finally { save.disabled = !draft.dirty; }
        });
        textarea.addEventListener("input", () => { draft.text = textarea.value; draft.dirty = draft.text !== draft.originalText; save.disabled = !draft.dirty; status.textContent = draft.dirty ? "Unsaved draft · retained in this page" : `Saved revision ${shortFingerprint(draft.revision)}`; });
        editorHost.replaceChildren(textarea, status, make("div", { className: "form-actions" }, save), message);
      } catch (error) { editorHost.replaceChildren(notice("Could not open source record", error.message, "error-banner")); }
    });
    details.append(summary);
    return details;
  }

  function materialTargetControls() {
    const owner = targetChoice("Attach to a video or style (optional)");
    return owner;
  }

  function sharedMaterialOwner() {
    return textInput("Shared project owner", { required: true, placeholder: "brand:videofactory",
      help: "Enter a named brand, style, or character, such as brand:videofactory. A video grant does not cover shared materials." });
  }

  function uploadMaterialForm() {
    const form = make("form", { className: "form-shell" });
    const inputId = `upload-file-${++fieldSequence}`;
    const file = make("input", { id: inputId, type: "file", required: true, accept: ".png,.jpg,.jpeg,.webp,.gif,.mp4,.mov,.webm,.mp3,.wav,.m4a,.ogg,.pdf,.txt,.md,.docx,.svg" });
    const drop = make("label", { className: "upload-drop", htmlFor: inputId }, [make("strong", {}, "Choose or drop a file"), make("small", {}, "Images, audio, video, PDF, text, DOCX, and SVG. SVG and documents download safely."), file]);
    drop.addEventListener("dragover", event => { event.preventDefault(); drop.classList.add("is-dragging"); });
    drop.addEventListener("dragleave", () => drop.classList.remove("is-dragging"));
    drop.addEventListener("drop", event => {
      event.preventDefault(); drop.classList.remove("is-dragging");
      if (event.dataTransfer?.files?.length) {
        try { file.files = event.dataTransfer.files; } catch { /* The file picker remains available if assignment is restricted. */ }
      }
    });
    const title = textInput("Title", { required: true, maxlength: 200 });
    const description = textArea("Description", { required: true, rows: 3, maxlength: 2000 });
    const kind = selectField("Material type", kindChoices(), { required: true });
    const rights = textInput("Rights / permission you hold", { required: true, value: "unknown", help: "Unknown permissions block production reuse until clarified." });
    const sharedOwner = sharedMaterialOwner();
    const target = materialTargetControls();
    const progress = make("progress", { className: "upload-progress", max: 100, value: 0, hidden: true, "aria-label": "Upload progress" });
    const progressText = make("span", { className: "field-help", "aria-live": "polite" });
    const message = make("div", { className: "flash-message", hidden: true, role: "status" });
    const submit = button("Upload and describe", "button button-primary", null, "submit");
    add(form, drop, make("p", { className: "field-help" }, "Per-file limit: 20 MiB for images and documents; 500 MiB for audio and video."), make("div", { className: "form-grid" }, [title.wrapper, kind.wrapper, rights.wrapper, sharedOwner.wrapper, target.wrapper, description.wrapper]), progress, progressText, make("div", { className: "form-actions" }, submit), message);
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const chosen = file.files?.[0];
      if (!chosen) return;
      const suffix = ext(chosen.name);
      const mediaLimit = 500 * 1024 * 1024;
      const limit = VIDEO_EXT.has(suffix) || AUDIO_EXT.has(suffix) ? mediaLimit : 20 * 1024 * 1024;
      if (chosen.size > limit) { showFormError(message, new Error(`This file exceeds the ${limit === mediaLimit ? "500 MiB media" : "20 MiB image/document"} limit.`)); return; }
      submit.disabled = true; progress.hidden = false; progress.value = 0; progressText.textContent = `Uploading ${formatBytes(chosen.size)}…`;
      let uploaded = null;
      try {
        const metadata = { title: title.control.value.trim(), description: description.control.value.trim(), kind: kind.control.value, source: "upload", rights: rights.control.value.trim(), tags: [], permission_scope: sharedOwner.control.value.trim() };
        const material = uploaded = await uploadMaterial(chosen, metadata, percentage => { progress.value = percentage; progressText.textContent = `Uploading · ${percentage}%`; });
        if (target.control.value) {
          const [owner_kind, owner_id] = target.control.value.split(":", 2);
          await api("/api/materials/link", jsonOptions("POST", { owner_kind, owner_id, material_id: material.id }));
        }
        message.hidden = false; message.replaceChildren(make("div", { className: "success-banner" }, [make("strong", {}, "Upload saved"), make("p", {}, `Material ${material.id} is now in the shared library.`)]));
        await refreshLibrary(); announce("Material uploaded and described.");
      } catch (error) {
        if (uploaded && target.control.value) { reportSavedMaterialLinkFailure(message, uploaded, error); announce("Upload saved; its attachment needs another attempt."); }
        else showFormError(message, error);
      }
      finally { submit.disabled = false; }
    });
    return form;
  }

  async function uploadMaterial(file, metadata, onProgress) {
    await ensurePermission(metadata.permission_scope);
    return new Promise((resolve, reject) => {
      const request = new XMLHttpRequest();
      request.open("POST", "/api/materials/upload");
      request.setRequestHeader("X-Studio-Token", state.token);
      request.setRequestHeader("X-VF-Session-ID", sessionId());
      request.setRequestHeader("X-Material-Filename", encodeURIComponent(file.name));
      request.setRequestHeader("X-Material-Filename-Encoding", "uri");
      request.setRequestHeader("X-Material-Metadata", asciiJson(metadata));
      request.setRequestHeader("Content-Type", file.type || "application/octet-stream");
      request.upload.addEventListener("progress", event => {
        if (event.lengthComputable) onProgress(Math.min(100, Math.round(event.loaded / event.total * 100)));
      });
      request.addEventListener("load", () => {
        let result;
        try { result = JSON.parse(request.responseText || "{}"); } catch { result = {}; }
        if (request.status >= 200 && request.status < 300) resolve(unwrap(result, "material"));
        else reject(apiError(result, { status: request.status }));
      });
      request.addEventListener("error", () => reject(new Error("Upload failed because the local studio could not receive the file.")));
      request.addEventListener("abort", () => reject(new Error("Upload cancelled.")));
      request.send(file);
    });
  }

  function referenceMaterialForm() {
    const form = make("form", { className: "form-shell" });
    const url = textInput("Source URL", { type: "url", required: true, placeholder: "https://…", help: "Saved as a link only; the studio does not fetch the page." });
    const title = textInput("Title", { required: true, maxlength: 200 });
    const description = textArea("Description", { required: true, rows: 3, maxlength: 2000 });
    const rights = textInput("Rights / permission you hold", { required: true, value: "unknown", help: "Unknown permissions block production reuse until clarified." });
    const sharedOwner = sharedMaterialOwner();
    const target = materialTargetControls();
    const message = make("div", { className: "flash-message", hidden: true, role: "status" });
    const submit = button("Save link record", "button button-primary", null, "submit");
    add(form, make("div", { className: "form-grid" }, [title.wrapper, url.wrapper, rights.wrapper, sharedOwner.wrapper, target.wrapper, description.wrapper]), make("div", { className: "form-actions" }, submit), message);
    form.addEventListener("submit", async event => {
      event.preventDefault(); submit.disabled = true;
      try {
        const parsed = new URL(url.control.value);
        if (!["http:", "https:"].includes(parsed.protocol)) throw new Error("Use an HTTP or HTTPS source URL.");
        const material = await saveMaterialRecord({ title: title.control.value.trim(), description: description.control.value.trim(), kind: "reference", source: parsed.href, rights: rights.control.value.trim(), tags: [] }, sharedOwner.control.value, target.control.value);
        message.hidden = false; message.replaceChildren(notice("Link saved", `Material ${material.id} is available in Library. The source page was not fetched.`, "success-banner"));
        await refreshLibrary(); announce("Link record saved.");
      } catch (error) {
        if (error.materialRecord) { reportSavedMaterialLinkFailure(message, error.materialRecord, error); announce("Link record saved; its attachment needs another attempt."); }
        else showFormError(message, error);
      }
      finally { submit.disabled = false; }
    });
    return form;
  }

  async function existingMaterialForm() {
    const version = state.routeVersion;
    let files = [], sequence = 0;
    const form = make("form", { className: "form-shell" });
    const fileSearch = textInput("Find a public file", { type: "search", placeholder: "Filter paths by name or folder", help: "Search all public files; load 48 results at a time." });
    const source = selectField("Public workspace file", [], { required: true, help: "Only server-listed public files are available. Private and generated index records are omitted." });
    const fileCount = make("small", { className: "field-help" });
    const title = textInput("Title", { required: true, maxlength: 200 });
    const description = textArea("Description", { required: true, rows: 3, maxlength: 2000 });
    const rights = textInput("Rights / permission you hold", { required: true, value: "unknown" });
    const sharedOwner = sharedMaterialOwner();
    const target = materialTargetControls();
    const message = make("div", { className: "flash-message", hidden: true, role: "status" });
    const submit = button("Describe existing file", "button button-primary", null, "submit");
    add(form, fileSearch.wrapper, source.wrapper, fileCount, make("div", { className: "form-grid" }, [title.wrapper, rights.wrapper, sharedOwner.wrapper, target.wrapper, description.wrapper]), make("div", { className: "form-actions" }, submit), message);
    const kind = selectField("File type", [{ value: "all", label: "All types" }]);
    const next = button("Load next files", "button", () => updateFileOptions(true));
    const problem = make("div");
    form.prepend(kind.wrapper);
    form.append(next, problem);
    async function updateFileOptions(append = false) {
      const request = ++sequence;
      const oldValue = source.control.value;
      next.disabled = true;
      try {
        const page = await api(`/api/materials/files?view=summary&offset=${append ? files.length : 0}&q=${encodeURIComponent(fileSearch.control.value)}&kind=${encodeURIComponent(kind.control.value)}`);
        if (request !== sequence || version !== state.routeVersion) return;
        files = append ? [...files, ...page.items] : page.items;
        source.control.replaceChildren(...files.map(file => make("option", { value: file.path }, `${file.path} · ${formatBytes(file.size)}`)));
        if (files.some(file => file.path === oldValue)) source.control.value = oldValue;
        const oldKind = kind.control.value;
        kind.control.replaceChildren(make("option", { value: "all" }, "All types"), ...page.kinds.map(value => make("option", { value }, value)));
        kind.control.value = oldKind;
        fileCount.textContent = `${files.length} shown · ${page.total} matching public files`;
        next.hidden = files.length >= page.total;
        next.disabled = false;
        submit.disabled = !files.length;
        problem.replaceChildren();
      } catch (error) {
        if (request !== sequence || version !== state.routeVersion) return;
        problem.replaceChildren(notice("Could not load files", error.message, "error-banner"), button("Retry files", "button", () => updateFileOptions(append)));
      }
    }
    let timer;
    fileSearch.control.addEventListener("input", () => { clearTimeout(timer); ++sequence; timer = setTimeout(() => updateFileOptions(), 150); });
    kind.control.addEventListener("change", () => updateFileOptions());
    await updateFileOptions();
    form.addEventListener("submit", async event => {
      event.preventDefault(); submit.disabled = true;
      try {
        const path = source.control.value;
        const record = await saveMaterialRecord({ title: title.control.value.trim(), description: description.control.value.trim(), kind: kindFromPath(path), source: path, rights: rights.control.value.trim(), tags: [] }, sharedOwner.control.value, target.control.value);
        message.hidden = false; message.replaceChildren(notice("File described", `Material ${record.id} now points to the existing workspace file.`, "success-banner"));
        await refreshLibrary(); announce("Existing file described.");
      } catch (error) {
        if (error.materialRecord) { reportSavedMaterialLinkFailure(message, error.materialRecord, error); announce("File record saved; its attachment needs another attempt."); }
        else showFormError(message, error);
      }
      finally { submit.disabled = false; }
    });
    return form;
  }

  function kindFromPath(path) {
    const suffix = ext(path);
    if (IMAGE_EXT.has(suffix) || suffix === ".svg") return "image";
    if (AUDIO_EXT.has(suffix)) return "audio";
    if (VIDEO_EXT.has(suffix)) return "video";
    return "document";
  }

  function libraryRequestForm() {
    const form = make("form", { className: "form-shell" });
    const target = selectField("Context video", state.videos.map(video => ({ value: video.slug, label: video.title })), { required: true });
    const instructions = textArea("Material request", { required: true, rows: 4, placeholder: "Describe the image, sound, footage, or source you supply." });
    const message = make("div", { className: "flash-message", hidden: true, role: "status" });
    const submit = button("Request material preparation", "button button-primary", null, "submit");
    add(form, target.wrapper, instructions.wrapper, make("div", { className: "form-actions" }, submit), message);
    form.addEventListener("submit", async event => {
      event.preventDefault(); submit.disabled = true;
      try {
        const video = state.videos.find(item => item.slug === target.control.value);
        const next = video ? nextGate(video) : null;
        const request = unwrap(await api("/api/requests", jsonOptions("POST", { slug: target.control.value, kind: "material", instructions: instructions.control.value.trim(), fingerprint: next?.review.fingerprint || "", request_id: idempotencyKey() })), "request");
        state.requests = [request, ...state.requests.filter(item => item.id !== request.id)];
        message.hidden = false; message.replaceChildren(notice("Request saved", "Waiting for an agent to claim it.", "success-banner"));
        instructions.control.value = ""; announce("Material request saved.");
      } catch (error) { showFormError(message, error); }
      finally { submit.disabled = false; }
    });
    if (!state.videos.length) form.prepend(emptyState("A video context is required", "Create a video before requesting material preparation."));
    return form;
  }

  async function refreshLibrary() {
    if (route().kind === "library") await state.libraryRefresh?.();
  }

  async function renderLibrary(main) {
    const version = state.routeVersion;
    const queryParam = new URLSearchParams(location.search).get("material");
    setBreadcrumb([{ label: "Library" }]);
    add(main, pageIntro("Library", "Described source records, reusable assets, and links shared across videos and styles.", [
      link("Add a material", "#library-add", "button button-primary"),
      link("Ask an agent", "#library-request", "button"),
    ]));
    const search = textInput("Search title, description, type, or linked item", { type: "search", value: state.materialQuery, placeholder: "Search materials" });
    search.wrapper.classList.add("library-search");
    const kind = selectField("Material type", [{ value: "all", label: "All types" }, ...kindChoices()], { value: state.materialKindFilter });
    kind.wrapper.classList.add("library-kind-filter");
    const count = make("span", { className: "collection-summary" });
    add(main, make("div", { className: "toolbar library-toolbar" }, [make("div", { className: "filter-group" }, [search.wrapper, kind.wrapper]), count]));
    const grid = make("div", { className: "library-grid" });
    const moreHost = make("div", { className: "library-more" });
    add(main, grid, moreHost);
    let rows = [], focused = Boolean(queryParam), sequence = 0;
    async function updateMaterials(append = false) {
      const request = ++sequence;
      state.materialQuery = search.control.value;
      state.materialKindFilter = kind.control.value;
      moreHost.replaceChildren();
      try {
        if (focused) {
          const material = await api(`/api/materials/item?id=${encodeURIComponent(queryParam)}`);
          if (request !== sequence || version !== state.routeVersion) return;
          grid.classList.add("library-grid-focused");
          grid.replaceChildren(materialCard(material));
          count.textContent = "Focused record";
          search.control.disabled = kind.control.disabled = true;
          moreHost.append(button("Show all materials", "button", showAllMaterials));
          return;
        }
        const page = await api(`/api/materials?view=summary&limit=48&offset=${append ? rows.length : 0}&q=${encodeURIComponent(search.control.value)}&kind=${encodeURIComponent(kind.control.value)}`);
        if (request !== sequence || version !== state.routeVersion) return;
        rows = append ? [...rows, ...page.items] : page.items;
        state.materials = rows;
        count.textContent = `${rows.length} of ${page.total} matching records`;
        grid.classList.remove("library-grid-focused");
        if (append) grid.append(...page.items.map(materialCard));
        else grid.replaceChildren(...rows.map(materialCard));
        if (!rows.length) grid.append(emptyState("No matching materials", "Change the search or type filter, or add a material."));
        const value = kind.control.value;
        kind.control.replaceChildren(make("option", { value: "all" }, "All types"), ...page.kinds.map(value => make("option", { value }, stateLabel(value))));
        kind.control.value = value;
        if (rows.length < page.total) moreHost.append(button(`Load next ${Math.min(48, page.total - rows.length)} records`, "button", () => updateMaterials(true)));
      } catch (error) {
        if (request !== sequence || version !== state.routeVersion) return;
        moreHost.replaceChildren(notice("Could not load materials", error.message, "error-banner"), button("Retry materials", "button", () => updateMaterials(append)));
        if (focused) moreHost.append(button("Show all materials", "button", showAllMaterials));
      }
    }
    function showAllMaterials() {
      focused = false;
      search.control.disabled = kind.control.disabled = false;
      const url = new URL(location.href);
      url.searchParams.delete("material");
      history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
      updateMaterials();
    }
    state.libraryRefresh = () => version === state.routeVersion ? updateMaterials() : Promise.resolve();
    let timer;
    search.control.addEventListener("input", () => { clearTimeout(timer); ++sequence; timer = setTimeout(() => updateMaterials(), 150); });
    kind.control.addEventListener("change", () => { clearTimeout(timer); updateMaterials(); });
    await updateMaterials();
    if (version !== state.routeVersion) return;

    const create = make("section", { className: "section rule-section", id: "library-add" }, [sectionHeading("Add a material", "Every record has a type, description, source, and rights status.")]);
    create.classList.add("library-collection-anchor");
    const formHost = make("div");
    create.append(formHost);
    add(main, create);
    loadPart(formHost, async () => {
      await Promise.all([loadVideos(), loadStyles()]);
      const forms = make("div", { className: "split-forms" }, [
        make("div", {}, [make("h3", {}, "Upload a file"), uploadMaterialForm()]),
        make("div", {}, [make("h3", {}, "Save a web link"), referenceMaterialForm()]),
      ]);
      const existing = make("details", { className: "form-section" }, make("summary", {}, "Describe an existing file"));
      const existingHost = make("div");
      existing.append(existingHost);
      let opened = false;
      existing.addEventListener("toggle", () => {
        if (!existing.open || opened) return;
        opened = true;
        loadPart(existingHost, existingMaterialForm);
      });
      const agent = make("section", { className: "section rule-section", id: "library-request" }, [sectionHeading("Ask an agent to prepare material", "This creates a durable handoff; it stays waiting until an agent claims it."), libraryRequestForm()]);
      agent.classList.add("library-collection-anchor");
      const requests = state.requests.filter(request => request.kind === "material");
      if (requests.length) agent.append(renderRequestList(requests));
      return [forms, existing, agent];
    });
  }

  function styleCard(style, index) {
    const sourceVideo = (style.reference_videos || []).map(slug => state.videos.find(video => video.slug === slug))
      .find(video => video?.thumbnail);
    const sourceFrame = sourceVideo?.thumbnail;
    const sample = style.sample && (IMAGE_EXT.has(ext(style.sample)) || VIDEO_EXT.has(ext(style.sample)) || AUDIO_EXT.has(ext(style.sample)))
      ? make("div", { className: "material-thumb" }, mediaElement(style.sample, `${style.title || style.id} sample`))
      : style.sample && ext(style.sample) === ".html"
        ? make("div", { className: "material-thumb" }, make("iframe", { src: workspacePreviewUrl(style.sample), title: `${style.title || style.id} sample`, loading: "lazy", sandbox: "allow-scripts" }))
        : sourceFrame ? make("div", { className: "material-thumb style-reference-thumb" }, mediaElement(sourceFrame, `${style.title || style.id} existing source reference`))
          : make("div", { className: "style-no-frame" }, "No source frame or template sample yet");
    return make("article", { className: "video-tile" }, [
      sample,
      make("div", { className: "video-tile-caption" }, [
        make("div", { className: "video-tile-copy" }, [link(style.title || style.id, `/styles/${encodeURIComponent(style.id)}`), make("small", {}, `${style.id} · ${style.base_kit || "base kit not set"}`),
          make("small", {}, style.sample ? "Template sample" : sourceFrame ? "Existing source reference · needs review" : "No approved sample"),
          make("small", {}, `${style.materials?.length || 0} linked source records`)]),
        make("span", { className: "tile-number" }, String(index + 1).padStart(2, "0")),
      ]),
      statusPill(style.error ? "failed" : style.template_ready ? "ready" : "draft", style.error ? "Recipe needs attention" : style.template_ready ? "Template ready" : "Template needed"),
    ]);
  }

  async function renderStyles(main) {
    const [data] = await Promise.all([api("/api/styles"), loadVideos()]);
    if (!main.isConnected) return;
    state.styles = Array.isArray(data) ? data : data.styles || [];
    setBreadcrumb([{ label: "Styles" }]);
    add(main, pageIntro("Styles", "Reusable recipes and scene templates. Each video keeps its own style snapshot.", [link("New style", "/styles/new", "button button-primary")]));
    const toolbar = make("div", { className: "toolbar" });
    const search = textInput("Search style recipes", { type: "search", placeholder: "Search title, ID, or base kit" });
    const count = make("span", { className: "collection-summary" });
    add(toolbar, search.wrapper, count); add(main, toolbar);
    const workshopSection = make("section", { className: "section rule-section" }, sectionHeading("Style workshops", "Saved styles with their own prompt and review path."));
    const grid = make("div", { className: "video-grid" }); workshopSection.append(grid); add(main, workshopSection);
    const librarySection = make("details", { className: "section rule-section creative-library" },
      make("summary", {}, [make("h2", {}, "Imported reference library"), make("p", {}, "Existing guides and source frames are references, not approved motion samples.")]));
    const libraryGrid = make("div", { className: "video-grid" }); librarySection.append(libraryGrid); add(main, librarySection);
    function update() {
      const query = search.control.value.trim().toLowerCase();
      const rows = state.styles.filter(style => `${style.id || ""} ${style.title || ""} ${style.base_kit || ""}`.toLowerCase().includes(query));
      count.textContent = `${rows.length} of ${state.styles.length} styles`;
      const workshops = rows.filter(style => style.origin !== "existing-reference");
      const references = rows.filter(style => style.origin === "existing-reference");
      grid.replaceChildren(...(workshops.length ? workshops.map(styleCard) : [emptyState(state.styles.length ? "No matching workshops" : "No style workshops yet", "Create a style from your prompt.", [link("New style", "/styles/new", "button button-primary")])]));
      libraryGrid.replaceChildren(...references.map(styleCard));
      librarySection.hidden = references.length === 0;
    }
    search.control.addEventListener("input", update); update();
    const requestRows = state.requests.filter(request => request.kind === "style-template");
    if (requestRows.length) add(main, make("section", { className: "section rule-section" }, [sectionHeading("Template requests", "Waiting for an agent to claim them."), renderRequestList(requestRows)]));
  }

  function renderRequestList(requests) {
    return make("div", { className: "request-list" }, requests.map(request => make("article", { className: "request-row" }, [
      make("div", {}, [make("strong", {}, request.slug), make("br"), make("small", {}, formatTime(request.created_at))]), statusPill(request.state), make("p", {}, request.instructions), make("span", { className: "source-id" }, request.id),
    ])));
  }

  function yamlQuote(value) { return JSON.stringify(String(value || "").trim()); }

  function renderStyleNew(main) {
    setBreadcrumb([{ label: "Styles", href: "/styles" }, { label: "New style" }]);
    add(main, pageIntro("New style", "Create a reusable recipe with a base kit, visual guidance, and motion rules."));
    const form = make("form", { className: "form-shell" });
    const id = textInput("Style ID", { required: true, pattern: "[a-z0-9]+(?:-[a-z0-9]+)*", maxlength: 64, placeholder: "editorial-line", help: "Lowercase letters, numbers, and hyphens." });
    const title = textInput("Style name", { required: true, maxlength: 120, placeholder: "Editorial line" });
    const description = textArea("Description", { required: true, rows: 3, maxlength: 1000, placeholder: "What makes this recipe useful?" });
    const baseKit = selectField("Base kit", [{ value: "modern", label: "Modern kit" }], { required: true });
    const visual = textArea("Visual guidance", { required: true, rows: 4, placeholder: "Palette, type, composition, scene materials…" });
    const motion = textArea("Motion guidance", { required: true, rows: 4, placeholder: "Timing, easing, camera, transitions…" });
    const message = make("div", { className: "flash-message", hidden: true, role: "status" });
    const submit = button("Create recipe", "button button-primary", null, "submit");
    add(form, make("div", { className: "form-grid" }, [id.wrapper, title.wrapper, baseKit.wrapper, description.wrapper, visual.wrapper, motion.wrapper]), make("div", { className: "form-actions" }, submit), message);
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const styleId = id.control.value.trim();
      if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(styleId)) { showFormError(message, new Error("Use lowercase letters, numbers, and hyphens in the style ID.")); return; }
      if (state.styles.some(style => style.id === styleId)) { showFormError(message, new Error("A style with this ID already exists.")); return; }
      submit.disabled = true;
      try {
        await api("/api/styles", jsonOptions("POST", { id: styleId, title: title.control.value.trim(), base_kit: baseKit.control.value }));
        const created = unwrap(await api(`/api/styles/${encodeURIComponent(styleId)}`), "style");
        const recipeText = [
          "---", `id: ${yamlQuote(styleId)}`, `title: ${yamlQuote(title.control.value)}`, `description: ${yamlQuote(description.control.value)}`, `base_kit: ${yamlQuote(baseKit.control.value)}`, "---", "",
          `# ${title.control.value.trim()}`, "", description.control.value.trim(), "", "## Visual guidance", "", visual.control.value.trim(), "", "## Motion guidance", "", motion.control.value.trim(), "",
        ].join("\n");
        await api(`/api/styles/${encodeURIComponent(styleId)}`, jsonOptions("PUT", { text: recipeText, expected_revision: created.revision ?? null }));
        if (!main.isConnected) return;
        await loadStyles();
        history.pushState({}, "", `/styles/${encodeURIComponent(styleId)}`); await renderRoute({ focus: true });
        announce("Style recipe created and saved.");
      } catch (error) { showFormError(message, error); }
      finally { submit.disabled = false; }
    });
    add(main, form);
  }

  async function renderStyle(main, styleId) {
    const [style] = await Promise.all([loadStyle(styleId), loadVideos()]);
    if (!main.isConnected) return;
    const path = style.path || `styles/${styleId}/style.md`;
    setBreadcrumb([{ label: "Styles", href: "/styles" }, { label: style.title || styleId }]);
    add(main, make("div", { className: "page-intro" }, [
      make("div", { className: "page-intro-copy" }, [make("h1", {}, style.title || styleId), make("p", {}, `${style.id} · ${style.base_kit || "Base kit unavailable"}`)]),
      make("div", { className: "page-actions" }, [link("All styles", "/styles", "button"), link("New style", "/styles/new", "button button-primary")]),
    ]));
    if (style.error) { add(main, notice("Style recipe needs attention", style.error, "error-banner")); return; }
    const file = await loadDraft(path).catch(async () => {
      const result = await api(`/api/styles/${encodeURIComponent(styleId)}`);
      const record = unwrap(result, "style");
      const draft = { path, text: record.text || "", originalText: record.text || "", revision: record.revision ?? null, editable: record.editable !== false, dirty: false, conflict: null, styleId };
      state.drafts.set(path, draft); return draft;
    });
    const styleEditor = make("section", { className: "style-recipe" }, [make("div", { className: "output-heading" }, [make("div", {}, [make("h2", {}, "Recipe"), make("p", {}, "Editable Markdown source. Shared recipe edits do not rewrite existing video snapshots.")])])]);
    const textarea = make("textarea", { className: "textarea", value: file.text, spellcheck: true, "aria-label": `${style.title || styleId} recipe` });
    const save = button("Save recipe", "button button-dark", async () => {
      save.disabled = true;
      try {
        const response = await api(`/api/styles/${encodeURIComponent(styleId)}`, jsonOptions("PUT", { text: textarea.value, expected_revision: file.revision }));
        const updated = unwrap(unwrap(response, "style"), "file");
        file.originalText = updated.text; file.revision = updated.revision; file.dirty = file.text !== updated.text; file.conflict = null;
        if (main.isConnected) await renderRoute({ focus: false }); announce("Style recipe saved. Existing video snapshots were not changed.");
      } catch (error) {
        if (error.code === "conflict") {
          try { file.conflict = unwrap(await api(`/api/styles/${encodeURIComponent(styleId)}`), "style"); }
          catch (readError) { file.conflict = { text: `Current recipe could not be read: ${readError.message}` }; }
          file.text = textarea.value; file.dirty = file.text !== file.originalText;
          if (main.isConnected) await renderRoute({ focus: false }); announce("Style save conflict. Your draft is retained.");
        } else showFormError(styleEditor.querySelector(".flash-message"), error);
      } finally { save.disabled = !file.dirty; }
    });
    const editorFoot = make("div", { className: "editor-footer" }, [make("span", { id: "style-draft-state", className: "saved-revision" }, `Saved revision ${shortFingerprint(file.revision)}`), make("span", {}, "Explicit save required")]);
    const editorMessage = make("div", { className: "flash-message", hidden: true, role: "status" });
    save.disabled = !file.dirty;
    textarea.addEventListener("input", () => { file.text = textarea.value; file.dirty = file.text !== file.originalText; save.disabled = !file.dirty; editorFoot.firstChild.textContent = file.dirty ? "Unsaved draft · kept in this page" : `Saved revision ${shortFingerprint(file.revision)}`; });
    styleEditor.append(textarea, editorFoot, make("div", { className: "form-actions" }, save), editorMessage);
    if (file.conflict) styleEditor.append(renderConflict(file));
    const sample = make("section", { className: "evidence-block" }, [make("h2", {}, "Template sample")]);
    if (style.sample && (IMAGE_EXT.has(ext(style.sample)) || VIDEO_EXT.has(ext(style.sample)) || AUDIO_EXT.has(ext(style.sample)))) {
      sample.append(make("div", { className: "style-sample" }, mediaElement(style.sample, `${style.title || styleId} sample`)), link("Download sample", pathUrl(style.sample, "download"), "quiet-link"));
    } else if (style.sample && ext(style.sample) === ".html") {
      sample.append(make("div", { className: "style-sample" }, make("iframe", { src: workspacePreviewUrl(style.sample), title: `${style.title || styleId} template sample`, loading: "lazy", sandbox: "allow-scripts" })), link("Download template source", pathUrl(style.sample, "download"), "quiet-link"));
    } else if (style.sample) {
      sample.append(notice("Template sample is present", "This file is available for download.", "inline-notice"), link("Download sample", pathUrl(style.sample, "download"), "quiet-link"));
    } else sample.append(notice("Template sample not ready", "Request an agent to create the reusable template; no preview is invented.", "inline-notice"));
    add(main, make("div", { className: "style-layout" }, [styleEditor, make("aside", {}, sample)]));

    const materialSection = make("section", { className: "section rule-section" }, [sectionHeading("Linked materials", "References shared by style recipes.", link("Open library", "/library", "quiet-link"))]);
    materialSection.append(make("div", { className: "style-linked-materials" }));
    materialSection.append(materialPicker("style", styleId, id => {
      style.materials = Array.from(new Set([...(style.materials || []), id]));
      linkedMaterials(materialSection.querySelector(".style-linked-materials"), style.materials, "style", styleId);
    }));
    add(main, materialSection);
    linkedMaterials(materialSection.querySelector(".style-linked-materials"), style.materials || [], "style", styleId);

    const requestSection = make("section", { className: "section rule-section" }, [sectionHeading("Reusable template handoff", "The request stays waiting until a workspace agent claims it.")]);
    requestSection.append(renderAgentRequestForm({ slug: styleId, kind: "style-template", fingerprint: style.revision || "", context: "style" }));
    add(main, requestSection);

    const applySection = make("section", { className: "section rule-section" }, [sectionHeading("Apply recipe to a video", "Preview the affected files before confirming a style update.")]);
    const applyForm = make("form", { className: "form-actions" });
    const choices = state.videos.map(video => ({ value: video.slug, label: video.title }));
    const videoSelect = selectField("Target video", choices, { required: true });
    const preview = button("Preview update", "button button-primary", null, "submit");
    const message = make("div", { className: "flash-message", hidden: true, role: "status" });
    const diff = make("div", { hidden: true });
    add(applyForm, videoSelect.wrapper, preview, message, diff);
    applyForm.addEventListener("submit", async event => {
      event.preventDefault(); if (!videoSelect.control.value) return;
      preview.disabled = true; message.hidden = false; message.replaceChildren(loadingPage("Preparing update preview"));
      try {
        const video = state.videos.find(item => item.slug === videoSelect.control.value);
        const result = unwrap(await api(`${apiVideoPath(videoSelect.control.value)}/style`, jsonOptions("POST", { style_id: styleId, expected_revision: null, confirm: false })), "proposal");
        await showStyleDiff(diff, result, styleId, videoSelect.control.value); diff.hidden = false;
        message.replaceChildren(notice("Review the proposed files", `This update affects ${result.changes?.length || 0} file(s) on ${video?.title || videoSelect.control.value}.`, "inline-notice"));
        const confirm = button("Apply this recipe", "button button-primary", async () => {
          await withButton(confirm, async () => {
            await api(`${apiVideoPath(videoSelect.control.value)}/style`, jsonOptions("POST", { style_id: styleId, expected_revision: result.revision, confirm: true }));
            if (main.isConnected) await renderRoute({ focus: false }); announce("Style snapshot applied.");
          }, message);
        });
        diff.append(make("div", { className: "form-actions" }, confirm));
      } catch (error) { showFormError(message, error); }
      finally { preview.disabled = false; }
    });
    if (!choices.length) applySection.append(emptyState("No videos are available", "Create a video before applying a reusable recipe."));
    applySection.append(applyForm); add(main, applySection);
  }

  function renderJobs(main) {
    setBreadcrumb([{ label: "Production jobs" }]);
    add(main, pageIntro("Production jobs", "Queued and completed commands from this workspace."));
    const rows = state.jobs;
    if (!rows.length) add(main, emptyState("No production jobs recorded", "Start an allowlisted action from a video project to see its status and log here."));
    else add(main, make("div", { className: "request-list" }, rows.map(job => make("article", { className: "request-row" }, [
      make("div", {}, [link(job.action || "Production job", `/jobs/${encodeURIComponent(job.id)}`), make("br"), make("small", {}, `${job.slug || "Workspace"} · ${formatTime(job.created_at)}`)]), statusPill(job.state), make("p", {}, job.error || job.progress || "Open the job for its actual command output."), make("span", { className: "source-id" }, job.id),
    ]))));
  }

  function hasDirtyDraft(slug = null) {
    return Array.from(state.drafts.values()).some(draft => draft.dirty &&
      (!slug || (typeof draft.path === "string" && draft.path.startsWith(`videos/${slug}/`))));
  }

  function syncReviewDraftState() {
    const main = document.getElementById("main");
    const slug = main.dataset.reviewSlug;
    if (!slug) return;
    const dirty = hasDirtyDraft(slug);
    const warning = document.getElementById("decision-draft-warning");
    if (warning) warning.textContent = decisionLine(main.dataset.reviewState, dirty, main.dataset.reviewMissing || "", main.dataset.reviewLine || "");
    const ready = document.getElementById("review-ready-button");
    if (ready) ready.disabled = dirty || ready.dataset.canReady !== "true";
    for (const control of document.querySelectorAll(".decision-bar [data-can-decide]")) control.disabled = dirty || control.dataset.canDecide !== "true";
  }

  async function updateReviewControls(main, slug, gate, review) {
    main.dataset.reviewSlug = slug;
    main.dataset.reviewState = review.state || "draft";
    syncReviewDraftState();
  }

  async function updatePolledJob(jobId) {
    try {
      const data = unwrap(await api(`/api/jobs/${encodeURIComponent(jobId)}`), "job");
      const oldState = state.jobDetail?.state;
      state.jobDetail = data;
      state.jobs = [data, ...state.jobs.filter(job => job.id !== data.id)];
      const title = document.getElementById("job-title");
      const status = document.getElementById("job-status-pill");
      const copy = document.getElementById("job-status-copy");
      const log = document.getElementById("job-log");
      const progress = document.getElementById("job-progress");
      if (title) title.textContent = `${stateLabel(data.state)} · ${stateLabel(data.action)}`;
      if (status) status.replaceWith(statusPill(data.state));
      if (copy) copy.textContent = data.error || data.progress || "Production status and output are taken from the job record.";
      if (log) log.textContent = data.log || "No log output yet.";
      if (progress) progress.textContent = data.progress ? `Progress ${data.progress}` : "No progress update reported.";
      if (oldState && oldState !== data.state && !ACTIVE_JOB_STATES.has(data.state)) await renderRoute({ focus: false });
    } catch { /* Keep the last confirmed job display if polling is temporarily unavailable. */ }
  }

  function schedulePolling() {
    if (state.pollTimer) { clearInterval(state.pollTimer); state.pollTimer = 0; }
    if (document.hidden || !state.jobs.some(job => ACTIVE_JOB_STATES.has(job.state))) return;
    state.pollTimer = setInterval(async () => {
      if (state.pollBusy || document.hidden) return;
      state.pollBusy = true;
      try {
        const data = await api("/api/jobs");
        setJobCollection(Array.isArray(data) ? data : data.jobs || []);
        updateNavigation();
        const current = route();
        if (current.kind === "job") await updatePolledJob(current.id);
        if (!state.jobs.some(job => ACTIVE_JOB_STATES.has(job.state))) schedulePolling();
      } catch { /* The current display remains usable during a local API interruption. */ }
      finally { state.pollBusy = false; }
    }, 3500);
  }

  function creativeHelpers() {
    const version = state.routeVersion;
    return { make, add, button, link, statusPill, api, jsonOptions, unwrap, pageIntro, sectionHeading,
      notice, emptyState, textInput, textArea, selectField, checkField, loadDraft, renderEditor,
      renderConflict, mediaElement, pathUrl, showFormError, withButton, announce, setBreadcrumb,
      refreshRequests, paidPanel,
      navigate: (path, options = { focus: true }) => {
        if (version !== state.routeVersion) return Promise.resolve();
        history.pushState({}, "", path);
        return renderRoute(options);
      },
      signal: routeController.signal,
      renderRoute: options => version === state.routeVersion ? renderRoute(options) : Promise.resolve(), decisionBar, detailsDrawer, reviewerName, reviewerField, state, version: state.routeVersion };
  }

  async function renderRoute(options = {}) {
    routeController.abort();
    routeController = new AbortController();
    const version = ++state.routeVersion;
    const current = route();
    state.currentRoute = current;
    state.renderedPathSearch = `${location.pathname}${location.search}`;
    const previous = document.getElementById("main");
    const main = previous.cloneNode(false);
    previous.replaceWith(main);
    delete main.dataset.reviewSlug; delete main.dataset.reviewState; delete main.dataset.reviewMissing; delete main.dataset.reviewLine;
    main.replaceChildren(loadingPage());
    setCurrentNav(current.kind);
    document.title = current.kind === "reviews" ? "Reviews · VideoFactory" : "VideoFactory · Studio";
    if (!state.boot) {
      try { await loadBootstrap(); }
      catch (error) {
        if (version !== state.routeVersion) return;
        main.replaceChildren(pageIntro("Studio unavailable", "The local workspace did not return its dashboard data."), notice("Could not load the workspace", error.message, "error-banner"), button("Try again", "button", () => { state.boot = null; renderRoute({ focus: false }); }));
        return;
      }
    }
    try {
      if (version !== state.routeVersion) return;
      switch (current.kind) {
        case "reviews": setBreadcrumb([{ label: "Reviews" }]); await renderReviews(main); break;
        case "videos": setBreadcrumb([{ label: "Videos" }]); await renderVideos(main); break;
        case "video-new": await Promise.all([loadStyles(), loadVideos()]); if (version !== state.routeVersion) return; renderVideoNew(main); break;
        case "video": await renderVideo(main, current.slug); break;
        case "review": await renderReview(main, current.slug, current.gate); break;
        case "library": await renderLibrary(main); break;
        case "styles": await renderStyles(main); await window.CreativeStudio.families(main, creativeHelpers()); break;
        case "style-new": await window.CreativeStudio.loadFamilies(creativeHelpers()); window.CreativeStudio.newCreative(main, "style", creativeHelpers()); break;
        case "style": await loadStyles(); if (version !== state.routeVersion) return; if (!await window.CreativeStudio.styleWorkshop(main, current.id, creativeHelpers())) {
          await renderStyle(main, current.id); await window.CreativeStudio.styleExtras(main, current.id, creativeHelpers());
        } break;
        case "characters": await window.CreativeStudio.characters(main, creativeHelpers()); break;
        case "character-new": window.CreativeStudio.newCreative(main, "character", creativeHelpers()); break;
        case "character": await loadStyles(); if (version !== state.routeVersion) return; await window.CreativeStudio.character(main, current.id, creativeHelpers()); break;
        case "creative-review": await window.CreativeStudio.review(main, current, creativeHelpers()); break;
        case "generation": await window.CreativeStudio.generation(main, current.id, creativeHelpers()); break;
        case "settings": window.CreativeStudio.settings(main, creativeHelpers()); break;
        case "jobs": renderJobs(main); break;
        case "job": await renderJob(main, current.id); break;
        default:
          setBreadcrumb([{ label: "Not found" }]);
          add(main, make("div", { className: "not-found" }, [make("h1", {}, "Page not found"), make("p", {}, "The workspace URL does not match a studio page."), link("Go to reviews", "/", "button button-primary")]));
      }
    } catch (error) {
      if (version !== state.routeVersion) return;
      if (error.status === 404 || error.code === "missing") {
        main.replaceChildren(make("div", { className: "not-found" }, [make("h1", {}, "Item not found"), make("p", {}, error.message), make("div", { className: "page-actions" }, [link("Reviews", "/", "button"), link("Videos", "/videos", "button button-primary")])]));
      } else {
        main.replaceChildren(pageIntro("Could not open this page", "The studio kept the current draft in memory while the request failed."), notice("Request failed", error.message || "Try reloading this view.", "error-banner"), button("Retry", "button", () => renderRoute({ focus: false })));
      }
    }
    if (version !== state.routeVersion) return;
    main.querySelector(".loading-state")?.remove();
    try { await showPermissionBar(main, current); } catch { /* Production still checks permission at the API. */ }
    updateNavigation();
    schedulePolling();
    if (location.hash) requestAnimationFrame(() => scrollToHash(location.hash));
    if (options.focus) requestAnimationFrame(() => {
      if (version !== state.routeVersion) return;
      if (!location.hash) window.scrollTo({ top: 0 });
      main.focus({ preventScroll: true });
    });
  }

  document.addEventListener("click", event => {
    const anchor = event.target.closest("a[href]");
    if (!anchor || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || anchor.target || anchor.hasAttribute("download")) return;
    const destination = new URL(anchor.href, location.href);
    if (destination.origin !== location.origin) return;
    if (destination.pathname === location.pathname && destination.search === location.search) {
      if (destination.hash && destination.hash !== location.hash) {
        event.preventDefault();
        history.pushState({}, "", `${destination.pathname}${destination.search}${destination.hash}`);
        requestAnimationFrame(() => scrollToHash(destination.hash));
        return;
      }
      event.preventDefault();
      return;
    }
    event.preventDefault();
    if (hasDirtyDraft() && !window.confirm("Leave this page with unsaved changes? Your draft will stay here until this studio tab closes.")) return;
    history.pushState({}, "", destination.pathname + destination.search + destination.hash);
    renderRoute({ focus: true });
  });

  window.addEventListener("popstate", () => {
    const pathSearch = `${location.pathname}${location.search}`;
    if (pathSearch === state.renderedPathSearch) {
      requestAnimationFrame(() => scrollToHash(location.hash));
      return;
    }
    if (hasDirtyDraft() && !window.confirm("Leave this page with unsaved changes? Your draft will stay here until this studio tab closes.")) {
      history.pushState({}, "", state.renderedPathSearch); return;
    }
    renderRoute({ focus: true });
  });
  document.addEventListener("visibilitychange", schedulePolling);
  window.addEventListener("beforeunload", event => {
    if (!hasDirtyDraft()) return;
    event.preventDefault();
    event.returnValue = "";
  });
  document.addEventListener("input", event => {
    if (event.target.closest(".output-editor")) syncReviewDraftState();
  });

  renderRoute({ focus: false });
})();
