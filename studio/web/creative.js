/* Creative workshop pages share the Studio shell and its guarded API helpers. */
window.CreativeStudio = (() => {
  const actions = ["idle", "blink", "talk", "point", "present", "wave", "sit", "stand", "computer", "happy", "puzzled", "surprised", "disappointed", "hold-prop", "present-prop"];
  const views = ["front", "three-quarter-right"];
  const key = (type, id) => `${type}/${id}`;
  const path = (type, id) => `/creative/${type}/${encodeURIComponent(id)}`;
  const reviewUrl = (type, id, gate) => `${path(type, id)}/review/${encodeURIComponent(gate)}`;
  const read = (h, url, options) => h.api(url, options).then(data => {
    if (h.version !== h.state.routeVersion) throw new Error("Navigation changed");
    return h.unwrap(data);
  });
  const section = (h, title, detail = "") => h.make("section", { className: "section rule-section" }, h.sectionHeading(title, detail));
  const actionsRow = (h, ...items) => h.make("div", { className: "form-actions" }, items);
  const text = (h, label, value = "") => h.make("p", {}, [h.make("strong", {}, `${label}: `), String(value || "—")]);
  const apiPath = (type, id) => `/api/creative/${type}/${encodeURIComponent(id)}`;
  const refresh = async (h) => { if (h.version !== h.state.routeVersion) return; await h.refreshRequests(); await h.renderRoute({ focus: false }); };
  function message(h) { return h.make("div", { className: "flash-message", hidden: true, role: "status" }); }
  function imageRoute(h, transparent) {
    const route = h.selectField("Image generation route", [
      { value: "native", label: "Native OpenAI image tool · agent handoff" },
      { value: "codex-cli", label: "Codex CLI · preferred for Claude" },
      { value: "openai-api", label: "OpenAI API · setup and billing acknowledgement required" },
    ], { value: "native" });
    const model = h.selectField("OpenAI API image model", [
      { value: "", label: "Choose the exact API model" },
      { value: "gpt-image-2", label: "gpt-image-2 · opaque output" },
      { value: "gpt-image-1.5", label: "gpt-image-1.5 · supports transparency" },
    ], {});
    const sync = () => { model.wrapper.hidden = route.control.value !== "openai-api"; };
    route.control.addEventListener("change", sync); sync();
    return { wrappers: [route.wrapper, model.wrapper], selected() {
      if (route.control.value !== "openai-api") return { transport: route.control.value };
      if (!model.control.value) throw new Error("Choose an exact OpenAI API image model for this batch.");
      if (transparent && model.control.value !== "gpt-image-1.5")
        throw new Error("Transparent character art needs the explicitly selected gpt-image-1.5 API model.");
      return { transport: route.control.value, image_model: model.control.value };
    } };
  }
  function task(h, label, call, host, after = null) {
    const control = h.button(label, "button button-primary", async () => {
      await h.withButton(control, async () => { await call(); if (after) await after(); else await refresh(h); }, host);
    });
    return control;
  }
  function fileLink(h, relative, label = null) {
    const route = /\.(?:js|html|css)$/i.test(relative) ? "source" : "download";
    const anchor = h.link(label || relative.split("/").at(-1), h.pathUrl(relative, route), "quiet-link");
    anchor.download = relative.split("/").at(-1);
    return anchor;
  }
  function image(h, relative, alt) {
    return h.make("figure", { className: "creative-frame" }, [h.make("img", { src: h.pathUrl(relative), alt, loading: "lazy" }), h.make("figcaption", {}, [alt, " · ", fileLink(h, relative, "Download original")])]);
  }
  function workshopPreview(h, row) {
    if (row.error) return h.notice("Character record unavailable", row.error, "error-banner");
    const next = row.brief_state === "approved" ? ["Prepare three concepts", `/characters/${encodeURIComponent(row.id)}#three-concepts`]
      : row.brief_state === "awaiting-review" ? ["Review character brief", reviewUrl("character", row.id, "brief")]
      : ["Resume character brief", `/characters/${encodeURIComponent(row.id)}#brief`];
    if (!row.preview) return h.make("div", { className: "character-no-art" }, [
      h.make("p", {}, "No saved artwork yet."),
      h.link(next[0], next[1], "quiet-link"),
    ]);
    const label = { "in-scene": "Canonical in-scene reference", sheet: "Canonical sheet", concept: "Saved concept" }[row.preview.kind];
    const figure = image(h, row.preview.path, `${row.title} · ${label}`);
    figure.querySelector("figcaption").prepend(`${label} · ${row.preview.state} · `);
    return figure;
  }
  function gateList(h, type, id, reviews) {
    const list = h.make("div", { className: "creative-gates" });
    for (const [gate, review] of Object.entries(reviews)) list.append(h.make("div", { className: "creative-gate" }, [
      h.link(gate.replaceAll(":", " · "), reviewUrl(type, id, gate)), h.statusPill(review.state),
      h.make("small", {}, review.missing?.length ? review.missing.join(", ") : "Current evidence available"),
    ]));
    return list;
  }
  function advanced(h, label, ...nodes) {
    return h.make("details", { className: "creative-advanced" }, [h.make("summary", {}, `Advanced · ${label}`), ...nodes]);
  }
  function rememberFields(h, id, fields) {
    const draftKey = `creative:fields:${id}`;
    const draft = h.state.drafts.get(draftKey) || { path: draftKey, values: {}, dirty: false };
    h.state.drafts.set(draftKey, draft);
    for (const [name, field] of Object.entries(fields)) {
      if (Object.hasOwn(draft.values, name)) {
        if (field.control.type === "checkbox") field.control.checked = draft.values[name];
        else field.control.value = draft.values[name];
      }
      const save = () => { draft.values[name] = field.control.type === "checkbox" ? field.control.checked : field.control.value; draft.dirty = true; };
      field.control.addEventListener("input", save);
      field.control.addEventListener("change", save);
    }
  }
  function guidedStages(main, h, type, id, detail, stages, selected = "") {
    const current = stages.find(stage => detail.reviews[stage.gate]?.state !== "approved") || stages.at(-1);
    const available = stages.find(stage => stage.id === selected)?.id || stages.find(stage => `#${stage.id}` === location.hash)?.id || current.id;
    const nav = h.make("nav", { className: "creative-progress", "aria-label": `${type} workshop stages` });
    const buttons = new Map();
    const show = (id, focus = false) => {
      for (const stage of stages) {
        stage.panel.hidden = stage.id !== id;
        const button = buttons.get(stage.id);
        if (stage.id === id) button.setAttribute("aria-current", "step"); else button.removeAttribute("aria-current");
      }
      if (focus) stages.find(stage => stage.id === id)?.panel.querySelector("h2")?.focus();
    };
    for (const stage of stages) {
      stage.panel.id = stage.id;
      stage.panel.classList.add("creative-stage-panel");
      const button = h.button(stage.label, "creative-progress-step", () => {
        history.pushState({}, "", `${location.pathname}${location.search}#${stage.id}`);
        show(stage.id, true);
      });
      button.append(h.statusPill(stage.status || detail.reviews[stage.gate]?.state || "draft"));
      buttons.set(stage.id, button); nav.append(button);
    }
    main.append(nav, ...stages.map(stage => stage.panel));
    show(available);
    const version = h.state.routeVersion;
    window.addEventListener("popstate", () => {
      if (version !== h.state.routeVersion) return;
      show(stages.find(stage => `#${stage.id}` === location.hash)?.id || current.id);
    });
  }
  function stageLead(h, title, instruction, you, agent, action = null) {
    return h.make("div", { className: "creative-stage-lead" }, [h.make("h2", { tabIndex: -1 }, title),
      h.make("p", {}, instruction), h.make("p", { className: "creative-stage-roles" }, `You: ${you} · Agent: ${agent}`),
      action ? actionsRow(h, action) : null]);
  }
  function briefInstruction(h, type, id, detail) {
    if (detail.reviews.brief.state === "approved") return "The saved brief is approved. Continue to the next stage.";
    if (detail.reviews.brief.state === "awaiting-review" || detail.reviews.brief.ready) return "Check the saved brief and make the human review decision.";
    if (detail.workshop?.form_url) return "Open the questions, then review the saved brief when the agent marks it ready.";
    const request = h.state.requests.find(item => item.subject?.type === type && item.subject?.id === id);
    return request ? "Ask your agent to continue the saved request and prepare your brief."
      : "No current agent request appears here. Copy a message for your agent to recover this workshop.";
  }
  function briefAction(h, type, id, detail) {
    if (detail.reviews.brief.state === "awaiting-review") return h.link("Review saved brief", reviewUrl(type, id, "brief"), "button button-primary");
    if (detail.reviews.brief.state === "approved") return h.link("View approved brief", reviewUrl(type, id, "brief"), "button button-primary");
    if (detail.reviews.brief.ready) return h.link("Check saved brief", reviewUrl(type, id, "brief"), "button button-primary");
    if (detail.workshop?.form_url) return h.make("a", { href: detail.workshop.form_url, target: "_blank", rel: "noopener noreferrer", className: "button button-primary" }, "Open questions");
    const request = h.state.requests.find(item => item.subject?.type === type && item.subject?.id === id);
    const handoff = request
      ? `Please continue the ${type} workshop for ${id}. Studio: ${location.origin}. Request ID: ${request.id}. Check the saved request, ask me the questions, save the full answers and an editable brief, then send me the exact review link. Wait for my decision before moving on.`
      : `Please help me resume the ${type} workshop for ${id}. Studio: ${location.origin}. I cannot see a current agent request. Check this saved workshop and its request history, help me recover the next step, then ask me the questions and save the full answers and an editable brief. Send me the exact review link when ready and wait for my decision.`;
    const fallback = h.make("textarea", { className: "textarea creative-copy-fallback", readOnly: true, rows: 4, value: handoff, hidden: true, "aria-label": "Request to copy manually" });
    const copy = h.button(request ? "Copy request for agent" : "Copy message for agent", "button button-primary", async () => {
      try { await navigator.clipboard.writeText(handoff); copy.textContent = "Copied · paste in agent chat"; }
      catch { fallback.hidden = false; fallback.select(); copy.textContent = "Select and copy the request below"; }
    });
    return h.make("div", { className: "creative-copy" }, [copy, fallback]);
  }
  function briefHandoff(h, type, id, detail) {
    if (detail.workshop?.form_url || detail.reviews.brief.ready || ["awaiting-review", "approved"].includes(detail.reviews.brief.state)) return null;
    const request = h.state.requests.find(item => item.subject?.type === type && item.subject?.id === id);
    if (!request) return h.make("p", { className: "creative-handoff" }, "No current agent request appears in Studio. Copy the message above into your agent chat to recover this workshop.");
    return request.state === "waiting-for-agent" ? h.make("p", { className: "creative-handoff" }, `Request ${request.id} · waiting for an agent. Paste the copied request into your agent chat.`) : null;
  }
  async function dirtyFile(h, relative, title) {
    const draft = await h.loadDraft(relative);
    const block = section(h, title, "Saved source. Edits require an explicit save and current revision.");
    block.append(h.renderEditor(draft, "creative", async () => {}));
    return block;
  }
  function newCreative(main, type, h) {
    const isStyle = type === "style";
    h.setBreadcrumb([{ label: isStyle ? "Styles" : "Characters", href: isStyle ? "/styles" : "/characters" }, { label: isStyle ? "New style" : "New character" }]);
    main.append(h.pageIntro(isStyle ? "New style" : "New character", "Start with your own prompt. The agent request waits until claimed, and the saved brief then goes to human review."));
    const form = h.make("form", { className: "form-shell" });
    const draftKey = `creative:new:${type}`;
    const draft = h.state.drafts.get(draftKey) || { name: "", id: "", prompt: "", family: "", editedId: false, dirty: false };
    h.state.drafts.set(draftKey, draft);
    const id = h.textInput("ID", { required: true, pattern: "[a-z0-9]+(?:-[a-z0-9]+)*", maxlength: 64, value: draft.id, help: "File name for this draft. You can edit it before creation." });
    const title = h.textInput("Name", { required: true, maxlength: 120, value: draft.name });
    const prompt = h.textArea("Your prompt", { required: true, rows: 8, maxlength: 20000, value: draft.prompt, placeholder: isStyle ? "Describe the look, setting, source references, motion and intended videos." : "Describe identity, personality, role and intended scenes." });
    const families = h.state.families || [];
    const family = isStyle ? h.selectField("Style family", [{ value: "", label: "Choose a style family" }, ...families.map(row => ({ value: row.id, label: row.title }))], { required: true, value: draft.family, help: "Choose the drawing and rendering family for this style." }) : null;
    prompt.wrapper.classList.add("span-all");
    const note = message(h);
    const submit = h.button(isStyle ? "Create style draft" : "Create character draft", "button button-primary", null, "submit");
    const slug = value => value.normalize("NFKD").toLowerCase().replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 64).replace(/-$/g, "");
    title.control.addEventListener("input", () => { if (!draft.editedId) id.control.value = slug(title.control.value); draft.name = title.control.value; draft.id = id.control.value; draft.dirty = true; });
    id.control.addEventListener("input", () => { draft.editedId = true; draft.id = id.control.value; draft.dirty = true; });
    prompt.control.addEventListener("input", () => { draft.prompt = prompt.control.value; draft.dirty = true; });
    family?.control.addEventListener("change", () => { draft.family = family.control.value; draft.dirty = true; });
    h.add(form, h.make("div", { className: "form-grid" }, [title.wrapper, prompt.wrapper, family?.wrapper, id.wrapper]),
      h.make("p", { className: "form-help" }, "Create saves your prompt and a draft request. A real agent claims the request, gathers answers, and prepares a brief for your review."), actionsRow(h, submit), note);
    form.addEventListener("submit", async event => {
      event.preventDefault(); submit.disabled = true;
      try {
        const selected = families.find(item => item.id === family?.control.value);
        if (isStyle && !selected) throw new Error("Choose a style family before creating this draft.");
        const metadata = isStyle ? { title: title.control.value.trim(), family_id: selected.id, base_kit: selected.base_kit,
          renderer: selected.renderer, supported_formats: selected.supported_formats, reference_videos: selected.reference_videos,
          references: selected.references, origin: "user-authored" } : { title: title.control.value.trim(), description: prompt.control.value.trim().slice(0, 500) };
        await h.api("/api/creative", h.jsonOptions("POST", { type, id: id.control.value.trim(), prompt: prompt.control.value, metadata }));
        h.state.drafts.delete(draftKey);
        await h.refreshRequests();
        await h.navigate(isStyle ? `/styles/${id.control.value.trim()}` : `/characters/${id.control.value.trim()}`);
      } catch (error) { h.showFormError(note, error); }
      finally { submit.disabled = false; }
    });
    main.append(form);
  }
  async function families(main, h) {
    await loadFamilies(h);
    const block = h.make("details", { className: "section rule-section creative-library" },
      h.make("summary", {}, [h.make("h2", {}, "Style family guides"), h.make("p", {}, "Existing guides, reference videos and renderer readiness.")]));
    const grid = h.make("div", { className: "creative-catalog" });
    for (const family of h.state.families) {
      const variants = h.state.styles.filter(style => style.family_id === family.id);
      const guidance = (family.body || "").split(/\n\s*\n/).map(paragraph => paragraph.trim())
        .filter(paragraph => paragraph && !paragraph.startsWith("#"));
      const sourceVideo = (family.reference_videos || []).map(slug => h.state.videos.find(item => item.slug === slug))
        .find(item => item?.thumbnail);
      const article = h.make("article", { className: "creative-family" }, [h.make("h3", {}, family.title), h.make("p", {}, family.description),
        ...(sourceVideo ? [image(h, sourceVideo.thumbnail, `${family.title} existing source reference`)] : []),
        ...guidance.map(paragraph => h.make("p", {}, paragraph)),
        text(h, "Renderer", family.renderer), text(h, "Formats", family.supported_formats?.join(", ")),
        h.make("div", { className: "creative-links" }, variants.length ? variants.map(style => h.link(style.title || style.id, `/styles/${style.id}`, "quiet-link")) : "No variant yet"),
      ]);
      for (const video of family.reference_videos || []) {
        const source = h.state.videos.find(item => item.slug === video);
        article.append(h.link(`Reference video · ${source?.title || video}`, `/videos/${video}`, "quiet-link"));
      }
      for (const reference of family.references || [])
        article.append(fileLink(h, reference, `Source · ${reference.split("/").at(-1)}`));
      grid.append(article);
    }
    block.append(grid); main.append(block);
  }
  async function loadFamilies(h) {
    const data = await read(h, "/api/style-families");
    h.state.families = Array.isArray(data) ? data : data.families || [];
  }
  async function styleExtras(main, id, h) {
    const style = h.state.styles.find(item => item.id === id);
    if (!style || style.error) return;
    const sources = section(h, "Source references", "Existing frames, guides and videos are references for this style; they are not approved samples.");
    const links = h.make("div", { className: "creative-links" });
    for (const reference of style.references || [])
      links.append(fileLink(h, reference, `Source · ${reference.split("/").at(-1)}`));
    for (const slug of style.reference_videos || []) {
      const video = h.state.videos.find(item => item.slug === slug);
      links.append(h.link(`Reference video · ${video?.title || slug}`, `/videos/${slug}`, "quiet-link"));
    }
    sources.append(links);
    if (links.children.length) main.append(sources);
    const block = section(h, "Legacy recipe", "This recipe predates the workshop. Its source stays available; a new named variant starts a reviewed workflow.");
    block.append(h.link("Start named variant", "/styles/new", "button button-primary")); main.append(block);
  }
  async function styleWorkshop(main, id, h) {
    const detail = await read(h, apiPath("style", id));
    if (detail.workshop?.state === "legacy") return false;
    const style = h.state.styles.find(item => item.id === id) || { title: id };
    h.setBreadcrumb([{ label: "Styles", href: "/styles" }, { label: style.title || id }]);
    main.append(h.pageIntro(style.title || id, "A saved prompt becomes a reviewed brief, materials and real motion samples."));
    const briefPanel = h.make("section");
    briefPanel.append(stageLead(h, "Brief", briefInstruction(h, "style", id, detail),
      "answer questions and review the brief", "claim the request and save answers", briefAction(h, "style", id, detail)));
    const styleHandoff = briefHandoff(h, "style", id, detail);
    if (styleHandoff) briefPanel.append(styleHandoff);
    await workshopForm(briefPanel, "style", id, detail, h);
    const materialPanel = h.make("section");
    materialPanel.append(stageLead(h, "Materials and references", detail.reviews.brief.state === "approved" ? "Describe the source material and inspect its rights before review." : "Approve the brief before preparing materials.",
      "review source choices", "save material evidence", detail.reviews.materials.state === "awaiting-review" ? h.link("Review materials", reviewUrl("style", id, "materials"), "button button-primary") : null));
    for (const reference of style.references || [])
      materialPanel.append(fileLink(h, reference, `Source · ${reference.split("/").at(-1)}`));
    for (const slug of style.reference_videos || []) materialPanel.append(h.link(`Reference video · ${slug}`, `/videos/${slug}`, "quiet-link"));
    await materials(materialPanel, id, detail, h);
    const batchHost = h.make("div"); await batches(batchHost, "style", id, h);
    materialPanel.append(advanced(h, "image batches and source registration", batchHost));
    const samplePanel = h.make("section");
    samplePanel.append(stageLead(h, "Samples", detail.reviews.materials.state === "approved" ? "Review each claimed format as a real 12-second motion sample." : "Approve materials before rendering samples.",
      "check motion and decide", "render each claimed sample", detail.reviews.sample.state === "awaiting-review" ? h.link("Review samples", reviewUrl("style", id, "sample"), "button button-primary") : null));
    await samples(samplePanel, id, detail, h);
    guidedStages(main, h, "style", id, detail, [
      { id: "brief", label: "Brief", gate: "brief", panel: briefPanel },
      { id: "materials", label: "Materials", gate: "materials", panel: materialPanel },
      { id: "samples", label: "Samples", gate: "sample", panel: samplePanel },
    ]);
    return true;
  }
  async function workshopForm(main, type, id, detail, h) {
    const folder = type === "style" ? `styles/${id}/01_brief` : `characters/${id}/01_design`;
    const [answersFile, briefFile] = await Promise.all(["answers.json", "brief.md"].map(name => read(h, `/api/files?path=${encodeURIComponent(`${folder}/${name}`)}`).catch(error => {
      if (error.status === 404 || error.code === "missing") return { text: "" };
      throw error;
    })));
    const draftKey = `creative:${key(type, id)}:workshop`;
    const existing = h.state.drafts.get(draftKey);
    const draft = existing?.dirty ? existing : { path: `${folder}/answers.json`, answers: answersFile.text || "{}",
      brief: briefFile.text || "", formUrl: detail.workshop.form_url || "", dirty: false };
    h.state.drafts.set(draftKey, draft);
    const block = section(h, "Saved brief and workshop source", "The agent saves full answers and a plain brief before human review.");
    const form = h.make("form", { className: "form-shell" });
    const url = h.textInput("Brainstormform URL", { type: "url", value: draft.formUrl, placeholder: "https://…" });
    const answers = h.textArea("Full answers JSON", { rows: 10, value: draft.answers, spellcheck: false });
    const brief = h.textArea("Editable brief", { rows: 6, value: draft.brief });
    const note = message(h);
    const save = h.button("Save workshop", "button", null, "submit");
    for (const control of [url.control, answers.control, brief.control]) control.addEventListener("input", () => {
      Object.assign(draft, { formUrl: url.control.value, answers: answers.control.value, brief: brief.control.value, dirty: true });
    });
    h.add(form, brief.wrapper, url.wrapper, answers.wrapper, actionsRow(h, save), note);
    form.addEventListener("submit", async event => {
      event.preventDefault(); save.disabled = true;
      try {
        const payload = { answers: JSON.parse(answers.control.value), brief: brief.control.value,
          expected_revision: detail.revision };
        if (url.control.value.trim()) payload.form_url = url.control.value.trim();
        await h.api(`${apiPath(type, id)}/answers`, h.jsonOptions("PUT", payload));
        draft.dirty = false; h.state.drafts.delete(draftKey); await refresh(h);
      } catch (error) {
        if (error.code === "conflict") {
          try { const current = await read(h, `${apiPath(type, id)}`);
            const saved = await read(h, `/api/files?path=${encodeURIComponent(`${folder}/brief.md`)}`);
            detail.revision = current.revision; note.hidden = false;
            note.replaceChildren(h.make("strong", {}, `Saved revision changed (${current.revision.slice(0, 12)}). Your edits are retained. Compare this saved brief before retrying:`),
              h.make("pre", { className: "creative-evidence-text" }, saved.text || "No saved brief."));
          } catch (readError) { h.showFormError(note, readError); }
        } else h.showFormError(note, error);
      }
      finally { save.disabled = false; }
    });
    if (briefFile.text?.trim() && !detail.reviews.brief.missing?.includes("completed brief"))
      block.append(h.make("pre", { className: "creative-evidence-text" }, briefFile.text));
    block.append(advanced(h, "agent controls · editable brief, answers and form link", form),
      advanced(h, "original prompt", await dirtyFile(h, `${folder}/prompt.md`, "Original prompt")));
    const related = h.state.requests.filter(request => request.subject?.type === type && request.subject?.id === id).slice(0, 12);
    if (related.length) block.append(advanced(h, "request history and IDs", h.make("div", { className: "creative-gates" }, related.map(request => h.make("div", { className: "creative-gate" }, [
      h.make("strong", {}, request.kind), h.statusPill(request.state), h.make("small", {}, request.instructions),
      h.make("code", {}, `.venv/bin/python anim.py studio-request ${request.id} --claim <agent>`),
    ])))));
    main.append(block);
  }
  async function materials(main, id, detail, h) {
    const block = section(h, "Materials and references", "Describe intended use and rights. Website inspection captures static HTML/CSS; motion needs separate recorded evidence.");
    const [plan, library] = await Promise.all([read(h, `${apiPath("style", id)}/materials-plan`), read(h, "/api/materials")]);
    const rows = Array.isArray(library) ? library : library.materials || [];
    block.append(text(h, "Setting", plan.setting), text(h, "Environment", plan.environment));
    for (const materialId of plan.linked_materials || []) {
      const material = rows.find(item => item.id === materialId);
      block.append(h.link(`${material?.title || materialId} · ${material?.rights || "rights unknown"}`, `/library?material=${encodeURIComponent(materialId)}`, "quiet-link"));
    }
    const form = h.make("form", { className: "form-shell" });
    const route = h.selectField("Source route", [...plan.options.map(item => ({ value: item.route, label: item.route })),
      { value: "website", label: "Public website inspection" }], { required: true });
    const description = h.textArea("Material request and intended scene use", { required: true, rows: 4, maxlength: 2000 });
    const url = h.textInput("Public website URL, for website route", { type: "url" });
    rememberFields(h, `style/${id}/materials`, { route, description, url });
    const note = message(h), submit = h.button("Create source request", "button button-primary", null, "submit");
    h.add(form, route.wrapper, description.wrapper, url.wrapper, actionsRow(h, submit), note);
    form.addEventListener("submit", async event => {
      event.preventDefault(); submit.disabled = true;
      try { await h.api(`${apiPath("style", id)}/materials-request`, h.jsonOptions("POST", {
        route: route.control.value, description: description.control.value, url: url.control.value.trim() || null,
        expected_revision: plan.input_revision })); h.state.drafts.delete(`creative:fields:style/${id}/materials`); await refresh(h);
      } catch (error) { h.showFormError(note, error); } finally { submit.disabled = false; }
    });
    submit.disabled = detail.reviews.brief.state !== "approved";
    block.append(form);
    block.append(h.link("Browse or add source material", "/library#library-add", "quiet-link"));
    main.append(block);
  }
  async function samples(main, id, detail, h) {
    const block = section(h, "Style samples", "Only claimed formats appear here. Each preview is a real render job read from saved output.");
    const formats = h.state.styles.find(item => item.id === id)?.supported_formats || [];
    if (!formats.length) block.append(h.notice("No sample format claimed", "Set a supported format before preparing a sample."));
    for (const format of formats) {
      let status = await read(h, `${apiPath("style", id)}/sample/${format}`).catch(error => ({ state: "unavailable", error: error.message }));
      let badge = h.statusPill(status.state || "draft");
      const row = h.make("div", { className: "creative-gate" }, [h.make("strong", {}, format), badge]);
      const note = message(h);
      const stateText = h.make("small");
      let inFlight = false;
      let prepare;
      const sync = () => {
        const nextBadge = h.statusPill(status.state || "draft");
        badge.replaceWith(nextBadge); badge = nextBadge;
        stateText.textContent = status.error || (status.state === "missing" ? "Sample missing. Prepare it again to retry." : "");
        stateText.hidden = !stateText.textContent;
        prepare.disabled = inFlight || !detail.reviews.materials.ready || detail.reviews.materials.state !== "approved" || status.state === "rendering";
      };
      const showSample = () => {
        const file = `styles/${id}/03_sample/${format}/sample.mp4`;
        if (!row.querySelector("video")) row.append(h.mediaElement(file, `${format} style sample`), fileLink(h, file, "Download sample"));
      };
      if (status.ready) showSample();
      let timer = 0;
      const poll = async () => {
        if (h.version !== h.state.routeVersion) { clearInterval(timer); return; }
        try {
          status = await read(h, `${apiPath("style", id)}/sample/${format}`);
          if (status.ready) showSample();
          sync();
          if (status.state !== "rendering") { clearInterval(timer); timer = 0; }
        } catch (error) {
          status = { state: "unavailable", error: `Could not refresh ${format} sample: ${error.message}` };
          sync(); clearInterval(timer); timer = 0;
        }
      };
      if (status.state === "rendering") timer = setInterval(poll, 3500);
      prepare = h.button(`Prepare ${format} sample`, "button button-primary", async () => {
        if (inFlight) return;
        inFlight = true; sync();
        try {
          await h.api(`${apiPath("style", id)}/sample/${format}`, h.jsonOptions("POST", { expected_revision: detail.reviews.materials.fingerprint }));
          await poll();
          if (status.state === "rendering" && !timer) timer = setInterval(poll, 3500);
        } catch (error) { h.showFormError(note, error); }
        finally { inFlight = false; sync(); }
      });
      row.append(stateText, prepare, note);
      sync();
      block.append(row);
    }
    main.append(block);
  }
  async function characters(main, h) {
    h.setBreadcrumb([{ label: "Characters" }]);
    main.append(h.pageIntro("Characters", "Reviewed character workshops.", [h.link("New character", "/characters/new", "button button-primary")]));
    const list = await read(h, "/api/characters");
    const rows = Array.isArray(list) ? list : list.characters || [];
    const workshops = rows.filter(row => row.origin === "character-workshop");
    const card = row => h.make("article", { className: "creative-family" }, [
      workshopPreview(h, row),
      h.make("h3", {}, h.link(row.title || row.id, `/characters/${row.id}`)),
      h.statusPill(row.error ? "failed" : row.identity_state || "draft"),
      h.make("p", {}, row.error || row.description || "No profile description yet."),
      h.make("small", {}, "Character workshop"),
    ]);
    const workshopSection = section(h, "Character workshops", "Create from a prompt or resume saved creative review.");
    workshopSection.append(workshops.length ? h.make("div", { className: "creative-catalog" }, workshops.map(card)) : h.emptyState("No character workshops yet", "Create one from your prompt.", [h.link("New character", "/characters/new", "button button-primary")]));
    main.append(workshopSection);
  }
  async function character(main, id, h) {
    const list = await read(h, "/api/characters");
    const rows = Array.isArray(list) ? list : list.characters || [];
    const workshop = rows.find(item => item.id === id && item.origin === "character-workshop");
    h.setBreadcrumb([{ label: "Characters", href: "/characters" }, { label: id }]);
    const detail = await read(h, `/api/characters/${encodeURIComponent(id)}`);
    const type = "character";
    main.append(h.pageIntro(detail.profile.title || id, detail.profile.description || "Character workshop", [h.link("New character", "/characters/new", "button")]));
    const catalogRow = workshop;
    const preview = catalogRow?.preview ? workshopPreview(h, catalogRow) : h.notice("No saved artwork yet",
      detail.reviews.brief.state === "approved" ? "The brief is approved. Prepare three concepts next." : "Review the saved brief before preparing concepts.");
    const briefPanel = h.make("section");
    briefPanel.append(stageLead(h, "Brief", briefInstruction(h, type, id, detail),
      "answer questions and review the exact brief", "claim the request and save answers", briefAction(h, type, id, detail)));
    const characterHandoff = briefHandoff(h, type, id, detail);
    if (characterHandoff) briefPanel.append(characterHandoff);
    if (detail.workshop?.state && (detail.workshop.state !== "waiting-for-agent" || h.state.requests.some(item => item.subject?.type === type && item.subject?.id === id)))
      briefPanel.append(h.statusPill(detail.workshop.state));
    if (detail.workshop?.state) await workshopForm(briefPanel, type, id, detail, h);
    briefPanel.append(advanced(h, "character profile source", await dirtyFile(h, `characters/${id}/character.md`, "Character profile")));
    const conceptPanel = h.make("section");
    conceptPanel.append(stageLead(h, "Three concepts", detail.reviews.brief.state === "approved" ? "Prepare three real concepts, then select one for review." : "Approve the saved brief before preparing concepts.",
      "compare and select artwork", "prepare and register the image batch"));
    conceptPanel.append(preview);
    const concepts = section(h, "Three concepts", "A completed OpenAI batch supplies three real candidates. Select one before design review.");
    concepts.id = "three-concepts";
    const conceptPrompt = h.textArea("Concept request prompt", { rows: 4, value: detail.profile.description || "" });
    rememberFields(h, `character/${id}/concept`, { conceptPrompt });
    const conceptRoute = imageRoute(h, false);
    const conceptNote = message(h);
    concepts.append(conceptPrompt.wrapper, advanced(h, "generation route and model", ...conceptRoute.wrappers), actionsRow(h, task(h, "Prepare three-image batch", async () => {
      const state = detail.reviews.brief;
      const batch = await read(h, "/api/generations", h.jsonOptions("POST", {
        id: `concept-${crypto.randomUUID().slice(0, 12)}`, subject_type: "character", subject_id: id,
        purpose: "character-concepts", prompt: conceptPrompt.control.value, references: [], transparent: false,
        image_count: 3, input_revision: state.fingerprint, ...conceptRoute.selected(),
      }));
      h.state.drafts.delete(`creative:fields:character/${id}/concept`);
      await h.navigate(`/generations/${batch.id}`);
    }, conceptNote)), conceptNote);
    concepts.querySelector(".button-primary").disabled = detail.reviews.brief.state !== "approved";
    const cards = h.make("div", { className: "creative-catalog" });
    for (const candidate of detail.candidates || []) {
      const card = h.make("article", { className: "creative-family" }, [image(h, candidate.path, `Candidate ${candidate.id}`),
        h.make("h3", {}, candidate.id), candidate.selected ? h.statusPill("selected") : task(h, "Select candidate", () => h.api(`/api/characters/${id}/candidate`, h.jsonOptions("PUT", { candidate_id: candidate.id, expected_revision: detail.reviews.design.fingerprint })), conceptNote)]);
      cards.append(card);
    }
    concepts.append(cards);
    const conceptBatch = h.textInput("Completed concepts batch ID", { placeholder: "concept-…" });
    const replaceConcepts = detail.candidate_revision ? h.checkField("Replace saved candidates after changing the brief or requesting changes; preserve earlier artwork and review history") : null;
    concepts.append(advanced(h, "register completed concepts", conceptBatch.wrapper, ...(replaceConcepts ? [replaceConcepts.wrapper] : []), task(h, "Register three candidates", () => h.api(`/api/characters/${id}/candidates`, h.jsonOptions("POST", {
      generation_id: conceptBatch.control.value.trim(), expected_revision: detail.reviews.brief.fingerprint,
      replace_revision: detail.candidate_revision, confirm_replace: replaceConcepts?.control.checked === true,
    })), conceptNote)));
    concepts.querySelector("details .button-primary").disabled = detail.reviews.brief.state !== "approved";
    conceptPanel.append(concepts, h.link("Review selected concept", reviewUrl(type, id, "design"), "quiet-link"));
    const identity = section(h, "Canonical identity", "The selected concept leads to a sheet and in-scene reference. Save exact appearance locks with the completed two-image batch.");
    if (detail.reference_set) {
      identity.append(h.make("div", { className: "creative-catalog" }, [image(h, detail.reference_set.sheet, "Canonical front and three-quarter-right sheet"), image(h, detail.reference_set.in_scene, "Canonical in-scene reference")]));
      for (const [label, value] of Object.entries(detail.reference_set.appearance)) identity.append(text(h, label, value));
    }
    const identityNote = message(h);
    const identityRoute = imageRoute(h, false);
    identity.append(advanced(h, "generation route and model", ...identityRoute.wrappers));
    identity.append(task(h, "Prepare identity batch", async () => {
      const batch = await read(h, `/api/characters/${id}/identity/generation`, h.jsonOptions("POST", identityRoute.selected()));
      await h.navigate(`/generations/${batch.id}`);
    }, identityNote), identityNote);
    identity.querySelector(".button-primary").disabled = detail.reviews.design.state !== "approved";
    const form = h.make("form", { className: "form-shell" });
    const batchId = h.textInput("Completed identity batch ID", { required: true });
    const locks = Object.fromEntries(["hair", "eyes", "face", "proportions", "clothing"].map(name => [name, h.textInput(`${name[0].toUpperCase()}${name.slice(1)} lock`, { required: true, value: detail.reference_set?.appearance?.[name] || "" })]));
    rememberFields(h, `character/${id}/identity`, { batchId, ...locks });
    const replaceIdentity = detail.reference_revision ? h.checkField("Replace saved identity after changing the selected concept or requesting changes; preserve earlier artwork and review history") : null;
    const save = h.button("Register identity references", "button button-primary", null, "submit");
    h.add(form, batchId.wrapper, ...Object.values(locks).map(field => field.wrapper), ...(replaceIdentity ? [replaceIdentity.wrapper] : []), actionsRow(h, save));
    form.addEventListener("submit", async event => {
      event.preventDefault(); save.disabled = true;
      try { await h.api(`/api/characters/${id}/identity/reference-set`, h.jsonOptions("PUT", {
        generation_id: batchId.control.value.trim(), constraints: Object.fromEntries(Object.entries(locks).map(([name, field]) => [name, field.control.value.trim()])),
        expected_revision: detail.reviews.design.fingerprint,
        replace_revision: detail.reference_revision, confirm_replace: replaceIdentity?.control.checked === true,
      })); h.state.drafts.delete(`creative:fields:character/${id}/identity`); await refresh(h); } catch (error) { h.showFormError(identityNote, error); } finally { save.disabled = false; }
    });
    save.disabled = detail.reviews.design.state !== "approved";
    identity.append(advanced(h, "register identity and appearance locks", form));
    const identityPanel = h.make("section");
    identityPanel.append(stageLead(h, "Identity", detail.reviews.design.state === "approved" ? "Check the real sheet and in-scene image together." : "Approve a selected concept before identity images are prepared.",
      "review consistency", "prepare and register both images"), identity, h.link("Review identity", reviewUrl(type, id, "identity"), "quiet-link"));
    const variantPanel = h.make("section");
    variantPanel.append(stageLead(h, "Variants and actions", detail.reviews.identity.state === "approved" ? "Choose a reviewed style, then inspect each saved action." : "Approve the identity pair before making style variants.",
      "review each action", "prepare variant art and exports"));
    await variants(variantPanel, id, detail, h);
    const batchHost = h.make("div"); await batches(batchHost, "character", id, h);
    conceptPanel.append(advanced(h, "all image batches", batchHost));
    guidedStages(main, h, type, id, detail, [
      { id: "brief", label: "Brief", gate: "brief", panel: briefPanel },
      { id: "three-concepts", label: "Three concepts", gate: "design", panel: conceptPanel },
      { id: "identity", label: "Identity", gate: "identity", panel: identityPanel },
      { id: "variants", label: "Variants and actions", gate: "identity", status: detail.variants?.length && detail.variants.every(item => item.state === "approved") ? "approved" : "draft", panel: variantPanel },
    ], new URLSearchParams(location.search).has("variant") ? "variants" : "");
  }
  async function variants(main, id, detail, h) {
    const block = section(h, "Style variants and animation", "The master identity stays fixed. Each action needs current exports in both views and a separate decision from you.");
    for (const variant of detail.variants || []) {
      const row = h.make("article", { className: "creative-family" }, [h.make("h3", {}, variant.id), h.statusPill(variant.state), text(h, "Style", variant.style_id), image(h, variant.artwork.path, `${variant.id} two-view artwork`)]);
      row.append(h.link("Open animation playground", `/characters/${id}?variant=${encodeURIComponent(variant.id)}`, "button button-primary"));
      block.append(row);
    }
    const form = h.make("form", { className: "form-shell" });
    const name = h.textInput("Variant ID", { required: true, pattern: "[a-z0-9]+(?:-[a-z0-9]+)*" });
    const style = h.selectField("Reviewed style", h.state.styles.map(row => ({ value: row.id, label: row.title || row.id })), { required: true });
    const prompt = h.textArea("Variant art prompt", { required: true, rows: 4 });
    const mono = h.checkField("Explicit monochrome exception", { checked: false });
    rememberFields(h, `character/${id}/variant`, { name, style, prompt, mono });
    const variantRoute = imageRoute(h, true);
    const note = message(h), create = h.button("Prepare variant batch", "button button-primary", null, "submit");
    h.add(form, name.wrapper, style.wrapper, prompt.wrapper, advanced(h, "generation route and exception", mono.wrapper, ...variantRoute.wrappers), actionsRow(h, create), note);
    form.addEventListener("submit", async event => {
      event.preventDefault(); create.disabled = true;
      try { const batch = await read(h, `/api/characters/${id}/variants/${name.control.value.trim()}/generation`, h.jsonOptions("POST", {
        style_id: style.control.value, prompt: prompt.control.value, monochrome_exception: mono.control.checked,
        ...variantRoute.selected(),
      })); h.state.drafts.delete(`creative:fields:character/${id}/variant`); await h.navigate(`/generations/${batch.id}`);
      } catch (error) { h.showFormError(note, error); } finally { create.disabled = false; }
    });
    block.append(form);
    create.disabled = detail.reviews.identity.state !== "approved";
    const register = h.make("form", { className: "form-shell" });
    const target = h.textInput("Variant ID to register", { required: true });
    const batch = h.textInput("Completed variant batch ID", { required: true });
    const styleId = h.selectField("Style in approved batch", h.state.styles.map(row => ({ value: row.id, label: row.title || row.id })), { required: true });
    const monochrome = h.checkField("Monochrome exception in approved batch", { checked: false });
    const replaceVariant = h.checkField("Replace saved variant art for this ID; preserve earlier artwork and review history");
    const registerButton = h.button("Register variant art", "button button-primary", null, "submit");
    h.add(register, target.wrapper, batch.wrapper, styleId.wrapper, monochrome.wrapper, replaceVariant.wrapper, actionsRow(h, registerButton));
    register.addEventListener("submit", async event => {
      event.preventDefault(); registerButton.disabled = true;
      try { await h.api(`/api/characters/${id}/variants/${target.control.value.trim()}`, h.jsonOptions("POST", {
        manifest: { generation_id: batch.control.value.trim(), style_id: styleId.control.value, views,
          appearance: detail.reference_set.appearance, monochrome_exception: monochrome.control.checked },
        expected_revision: detail.reviews.identity.fingerprint,
        replace_revision: detail.variants?.find(item => item.id === target.control.value.trim())?.revision,
        confirm_replace: replaceVariant.control.checked,
      })); await refresh(h); } catch (error) { h.showFormError(note, error); } finally { registerButton.disabled = false; }
    });
    registerButton.disabled = detail.reviews.identity.state !== "approved" || !detail.reference_set;
    block.append(advanced(h, "register completed variant art", register), note); main.append(block);
    const selected = new URLSearchParams(location.search).get("variant");
    if (selected && detail.variants?.some(item => item.id === selected)) await playground(main, id, selected, detail, h);
  }
  function nativePlayback(main, id, variant, detail, h, native) {
    const nativePanel = section(h, "Native Synfig project", "Editable native projects are rendered to transparent PNG frames. Studio plays a checkerboard MP4 made from those same frames.");
    if (native.error) nativePanel.append(h.notice("Native source needs repair", native.error));
    if (!native.available) {
      nativePanel.append(h.make("p", {}, native.registered ? "The active native source needs repair. Previously validated clips remain available below." :
        native.candidate ? "Native rig candidate is saved for your review. Action rendering waits for its approval and activation." :
        "No registered native project yet. Calibration drafts remain separate from the reviewed rig."));
      if (native.candidate) {
        nativePanel.append(h.statusPill(native.review), h.link("Review native rig candidate", reviewUrl("character", id, `rig:${variant}`), "quiet-link"));
      }
    }
    else nativePanel.append(h.statusPill(native.review), h.link("Review native rig", reviewUrl("character", id, `rig:${variant}`), "quiet-link"));
    if (native.registered) {
      if (!native.bindings.length) nativePanel.append(h.make("p", {}, "No action and expression has a verified native project binding yet."));
      for (const binding of native.bindings) {
        const row = h.make("article", { className: "creative-evidence" }, [h.make("h3", {}, `${binding.action} · ${binding.expression} · ${binding.view}`)]);
        if (binding.expression === "neutral") row.append(h.link("Review native action", reviewUrl("character", id, `animation:${variant}:${binding.action}`), "quiet-link"));
        const clip = binding.render?.clip;
        if (clip) {
          row.append(h.make("p", {}, binding.render.current ? "Current native clip · cached playback available" : "Previous native clip · source changed; render a replacement to review the current source."));
          row.append(h.mediaElement(clip.preview, `${binding.action} native preview`));
          row.append(fileLink(h, `${clip.path}/render.json`, "Download frame manifest"));
        }
        const note = message(h);
        const run = task(h, "Render native clip", async () => {
          const job = await read(h, `/api/characters/${id}/variants/${variant}/native/render`, h.jsonOptions("POST", {
            view: binding.view, action: binding.action, expression: binding.expression,
            expected_fingerprint: detail.reviews[`rig:${variant}`]?.fingerprint, request_id: crypto.randomUUID(),
          }));
          await h.navigate(`/jobs/${encodeURIComponent(job.id)}`);
        }, note);
        run.disabled = !native.available || native.review !== "approved" || !!binding.render?.error;
        row.append(actionsRow(h, run), note);
        nativePanel.append(row);
      }
    }
    if (native.candidate && !native.source_matches) {
      const note = message(h);
      const activate = task(h, "Activate approved native rig", () => h.api(`/api/characters/${id}/variants/${variant}/native/activate`,
        h.jsonOptions("POST", { expected_fingerprint: detail.reviews[`rig:${variant}`]?.fingerprint })), note);
      activate.disabled = native.review !== "approved";
      nativePanel.append(actionsRow(h, activate), note);
    }
    main.append(nativePanel);
  }
  async function playground(main, id, variant, detail, h) {
    let capabilities = null;
    try {
      capabilities = await read(h, `/api/characters/${id}/variants/${variant}/capabilities`);
    } catch (error) { capabilities = { authored: { actions: [] }, supported: { actions: [] }, error: error.message }; }
    const native = capabilities.native || { available: false, registered: false, bindings: [] };
    if (native.registered) { nativePlayback(main, id, variant, detail, h, native); return; }
    const authored = capabilities.authored.actions;
    const supported = capabilities.supported.actions.map(item => item.id);
    const block = section(h, `${variant} playground`, "The preview uses the same Character.load/draw engine as exported frames. Missing art or action data stays unavailable.");
    const action = h.selectField("Available action", supported.map(value => ({ value, label: value })), {});
    const view = h.selectField("View", views.map(value => ({ value, label: value })), {});
    const expression = h.selectField("Expression", [{ value: "", label: "Action default" }], {});
    const prop = h.selectField("Prop", [{ value: "", label: "None" }], {});
    const speed = h.selectField("Speed", [{ value: "0.25", label: "0.25×" }, { value: "0.5", label: "0.5×" }, { value: "1", label: "1×" }, { value: "2", label: "2×" }], { value: "1" });
    const scrub = h.make("input", { type: "range", min: "0", max: "4", step: "0.01", value: "0", "aria-label": "Scrub character time" });
    const level = h.make("input", { type: "range", min: "0", max: "1", step: "0.01", value: "0", "aria-label": "Manual speech level" });
    const audioFile = h.make("input", { type: "file", accept: "audio/*", "aria-label": "Local speech audio" });
    const audio = h.make("audio", { controls: true });
    const canvas = h.make("canvas", { className: "creative-canvas", width: 420, height: 420, "aria-label": "Character preview" });
    const status = h.make("p", { role: "status" }, "Loading saved character pack…");
    const play = h.button("Play", "button", () => { playing = !playing; previous = 0; play.textContent = playing ? "Pause" : "Play"; schedule(); });
    const reload = h.button("Reload saved pack", "button", () => h.renderRoute({ focus: false }));
    const frame = h.button("Download this frame", "button", () => {
      const anchor = document.createElement("a"); anchor.download = `${id}-${variant}-${loadedAction}-${view.control.value}-${Math.round(time * 1000)}.png`;
      anchor.href = canvas.toDataURL("image/png"); anchor.click();
    });
    action.control.disabled = !supported.length; frame.disabled = true; play.disabled = true;
    const source = h.make("div", { className: "creative-links" });
    const controls = h.make("div", { className: "creative-controls" }, [action.wrapper, view.wrapper, expression.wrapper, prop.wrapper, speed.wrapper,
      h.make("label", {}, ["Time ", scrub]), h.make("label", {}, ["Speech level ", level]), h.make("label", {}, ["Local audio ", audioFile]), audio]);
    block.append(controls, actionsRow(h, play, frame, reload), canvas, status, source);
    main.append(block);
    let character = null, loadedAction = null, loadMessage = null, loading = false, engineRevision = null, disposed = false, playing = false, time = 0, previous = 0, analyser = null, audioContext = null, audioUrl = null, loadSequence = 0, raf = 0;
    const routeVersion = h.state.routeVersion;
    let mounted = false;
    const active = () => routeVersion === h.state.routeVersion && (!mounted || block.isConnected);
    const stop = () => {
      if (disposed) return;
      disposed = true;
      ++loadSequence; cancelAnimationFrame(raf); raf = 0; character?.dispose(); character = null;
      audio.pause(); if (audioUrl) URL.revokeObjectURL(audioUrl); audioContext?.close();
      document.removeEventListener("visibilitychange", visibility);
      observer.disconnect();
    };
    const observer = new MutationObserver(() => { if (block.isConnected) mounted = true; else if (!active()) stop(); });
    observer.observe(document.body, { childList: true, subtree: true });
    const draw = () => {
      if (!character) return;
      const ctx = canvas.getContext("2d"); ctx.clearRect(0, 0, canvas.width, canvas.height);
      let speechLevel = Number(level.value);
      if (analyser && !audio.paused) {
        const values = new Uint8Array(analyser.fftSize); analyser.getByteTimeDomainData(values);
        speechLevel = Math.min(1, Math.sqrt(values.reduce((sum, value) => sum + ((value - 128) / 128) ** 2, 0) / values.length) * 5);
      }
      try {
        const result = character.draw(ctx, time, { action: loadedAction, view: view.control.value,
          expression: expression.control.value || undefined, prop: prop.control.value || undefined, speechLevel });
        frame.disabled = loading || !result.available;
        status.textContent = loadMessage || (result.available ? `${loadedAction} · ${view.control.value} · ${time.toFixed(2)} s · ${result.expression} · ${result.mouth}` : `Unavailable: ${result.reason}`);
      } catch (error) { playing = false; audio.pause(); frame.disabled = true; play.textContent = "Play"; status.textContent = `Preview error: ${error.message}`; }
    };
    const schedule = () => { if (!raf && active() && !document.hidden && (playing || !audio.paused)) raf = requestAnimationFrame(animate); };
    const animate = stamp => {
      raf = 0;
      if (!active()) { stop(); return; }
      if (playing && character) {
        time += Math.min((stamp - (previous || stamp)) / 1000, 0.1) * Number(speed.control.value);
        const duration = character.manifest.actions[loadedAction]?.duration || 4;
        if (!character.manifest.actions[loadedAction]?.loop) time = Math.min(time, duration);
        else time %= duration;
        if (!character.manifest.actions[loadedAction]?.loop && time >= duration) { playing = false; play.textContent = "Play"; }
        scrub.value = String(time);
      }
      previous = stamp; draw(); schedule();
    };
    const visibility = () => { previous = 0; if (document.hidden) { cancelAnimationFrame(raf); raf = 0; } else { draw(); schedule(); } };
    document.addEventListener("visibilitychange", visibility);
    const syncProps = () => {
      const selected = prop.control.value;
      const available = Object.keys(character?.manifest.views[view.control.value]?.rig?.props || {});
      prop.control.replaceChildren(h.make("option", { value: "" }, "None"), ...available.map(value => h.make("option", { value }, value)));
      if (available.includes(selected)) prop.control.value = selected;
    };
    const syncExpressions = () => {
      const selected = expression.control.value;
      const available = Object.keys(character?.manifest.views[view.control.value]?.rig?.expressions || {});
      expression.control.replaceChildren(h.make("option", { value: "" }, "Action default"), ...available.map(value => h.make("option", { value }, value)));
      if (available.includes(selected)) expression.control.value = selected;
    };
    for (const control of [view.control, expression.control, prop.control, speed.control]) control.addEventListener("change", () => {
      if (control === view.control) { syncProps(); syncExpressions(); }
      draw();
    });
    level.addEventListener("input", draw);
    const loadAction = async selected => {
      const sequence = ++loadSequence, previousAction = loadedAction;
      loading = true; frame.disabled = true;
      loadMessage = `Loading ${selected}…`; status.textContent = loadMessage;
      try {
        const manifest = await read(h, `/api/characters/${id}/variants/${variant}/actions/${selected}/manifest`);
        if (engineRevision !== manifest.engine_sha256) await new Promise((resolve, reject) => {
          const script = h.make("script", { src: `/_runtime/character.js?revision=${manifest.engine_sha256}`,
            onLoad: () => { script.remove(); resolve(); },
            onError: () => { script.remove(); reject(new Error("Character renderer failed to load.")); } });
          document.head.append(script);
        });
        const loaded = await window.Character.load(manifest);
        if (!active() || sequence !== loadSequence || selected !== action.control.value) {
          loaded.dispose(); return;
        }
        const old = character; character = loaded; loadedAction = selected; engineRevision = manifest.engine_sha256; old?.dispose(); loadMessage = null; loading = false;
        time = 0; scrub.value = "0"; scrub.max = String(manifest.actions[selected].duration);
        canvas.width = manifest.canvas[0]; canvas.height = manifest.canvas[1];
        frame.disabled = false; play.disabled = false; syncProps(); syncExpressions();
        source.replaceChildren(h.link("Download compiled manifest", `/api/characters/${id}/variants/${variant}/actions/${selected}/manifest`, "quiet-link"));
        draw();
        schedule();
      } catch (error) { if (sequence === loadSequence && active()) {
        if (previousAction) action.control.value = previousAction;
        loading = false; loadMessage = `Action unavailable: ${error.message}`; draw(); status.textContent = loadMessage;
      } }
    };
    action.control.addEventListener("change", () => loadAction(action.control.value));
    scrub.addEventListener("input", () => { time = Number(scrub.value); playing = false; play.textContent = "Play"; draw(); });
    for (const event of ["play", "pause", "ended"]) audio.addEventListener(event, () => { previous = 0; draw(); schedule(); });
    audioFile.addEventListener("change", async () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      const file = audioFile.files?.[0]; if (!file) return;
      audioUrl = URL.createObjectURL(file); audio.src = audioUrl;
      try {
        audioContext ||= new AudioContext();
        if (!analyser) { analyser = audioContext.createAnalyser(); analyser.fftSize = 256;
          const source = audioContext.createMediaElementSource(audio); source.connect(analyser); analyser.connect(audioContext.destination); }
        await audioContext.resume();
      } catch (error) { status.textContent = `Audio analysis unavailable: ${error.message}`; }
    });
    try {
      if (capabilities.error) throw new Error(capabilities.error);
      if (!supported.length) throw new Error("No available actions yet. Add an action to motions.json.");
      if (!active()) { stop(); return; }
      await loadAction(action.control.value);
      if (character) {
        view.control.replaceChildren(...Object.keys(character.manifest.views).map(value => h.make("option", { value }, value)));
        syncProps(); syncExpressions();
      }
    } catch (error) { status.textContent = `Pack unavailable: ${error.message}`; frame.disabled = true; play.disabled = true; }
    const pack = section(h, "Pack source and action exports", "Assets, rig and motions are authored source. Generated previews and frame indexes are read-only.");
    const artRoute = imageRoute(h, true);
    pack.append(...artRoute.wrappers);
    for (const filename of ["assets.json", "rig.json", "motions.json"]) {
      try { pack.append(await dirtyFile(h, `characters/${id}/03_animation/${variant}/${filename}`, filename)); }
      catch { pack.append(h.notice(`${filename} missing`, "Create the authored pack source before exporting frames.")); }
    }
    for (const name of actions) {
      const gate = `animation:${variant}:${name}`;
      const saved = supported.includes(name);
      const row = h.make("div", { className: "creative-gate" }, [h.make("strong", {}, name),
        saved ? h.statusPill(detail.reviews[gate]?.state || "draft") : h.make("small", {}, authored.includes(name) ? "Authored · pack needs repair" : "Planned · no authored motion"),
        saved ? h.link("Review", reviewUrl("character", id, gate), "quiet-link") : null]);
      const note = message(h);
      row.append(task(h, "Request part art", async () => {
        const result = await read(h, `/api/characters/${id}/variants/${variant}/actions/${name}/prepare`,
          h.jsonOptions("POST", artRoute.selected()));
        await h.navigate(`/generations/${result.id}`);
      }, note));
      for (const perspective of saved ? views : []) row.append(task(h, `Export ${perspective}`, () => h.api(`/api/characters/${id}/variants/${variant}/actions/${name}/export`, h.jsonOptions("POST", {
        view: perspective, fps: 30, prop: prop.control.value || null,
      })), note));
      row.append(note); pack.append(row);
    }
    main.append(advanced(h, "pack source and action exports", pack));
    nativePlayback(main, id, variant, detail, h, capabilities.native || { available: false, bindings: [] });
  }
  async function review(main, route, h) {
    const { type, id, gate } = route;
    const state = await read(h, `${apiPath(type, id)}/reviews/${encodeURIComponent(gate)}`);
    const back = type === "style" ? `/styles/${id}` : `/characters/${id}`;
    h.setBreadcrumb([{ label: type === "style" ? "Styles" : "Characters", href: type === "style" ? "/styles" : "/characters" },
      { label: id, href: back }, { label: gate.replaceAll(":", " · ") }]);
    const historySection = h.make("section", { className: "evidence-block" }, [h.make("h2", {}, "Recorded decisions"), state.history?.length
      ? h.make("div", { className: "creative-gates" }, state.history.map(item => h.make("p", {}, `${item.at} · ${item.kind} · ${item.decision || "ready"} · ${item.reviewer || "agent"} ${item.note || ""}`)))
      : h.make("p", {}, "No decisions are recorded for this gate yet.")]);
    const drawer = h.detailsDrawer("Review details", [historySection, h.reviewerField()]);
    main.append(h.pageIntro(`${id} · ${gate.replaceAll(":", " · ")}`, "Human decision for this exact saved revision.", [h.link("Back to workshop", back, "button"), drawer.toggle]), drawer.dialog);
    const evidence = section(h, "Saved evidence", `Revision ${state.fingerprint}`);
    evidence.querySelector(".section-heading p").classList.add("creative-fingerprint");
    for (const relative of state.artifacts || []) {
      const row = h.make("article", { className: "creative-evidence" }, [h.make("div", { className: "creative-evidence-head" }, [
        h.make("strong", {}, relative), fileLink(h, relative, "Download saved file"),
      ])]);
      if (/\.(md|txt|json|js|html|css)$/i.test(relative)) {
        try {
          let saved;
          if (/\.(js|html|css)$/i.test(relative)) {
            const response = await fetch(h.pathUrl(relative, "source"), { cache: "no-store", signal: h.signal });
            if (!response.ok) throw new Error("Saved source is unavailable.");
            saved = await response.text();
            if (h.version !== h.state.routeVersion) throw new Error("Navigation changed");
          } else saved = (await read(h, `/api/files?path=${encodeURIComponent(relative)}`)).text;
          const savedText = h.make("pre", { className: "creative-evidence-text" }, saved);
          row.append(/\.json$/i.test(relative) ? advanced(h, "raw JSON", savedText) : savedText);
        } catch (error) { row.append(h.notice("Saved text unavailable", error.message)); }
      } else if (/\.(png|jpg|jpeg|webp|gif|mp3|wav|m4a|ogg|mp4|webm|mov)$/i.test(relative)) {
        row.append(h.mediaElement(relative, relative.split("/").at(-1)));
      } else row.append(h.make("p", {}, "Download this saved file to inspect it."));
      evidence.append(row);
    }
    main.append(evidence);
    const call = (suffix, body) => h.api(`${apiPath(type, id)}/reviews/${encodeURIComponent(gate)}/${suffix}`, h.jsonOptions("POST", body)).then(() => refresh(h));
    const decide = (decision, note = "") => call("decision", { decision, reviewer: h.reviewerName(), note, expected_revision: state.fingerprint });
    const bar = h.decisionBar({
      state: state.state, missing: state.ready ? "" : (state.missing || []).join(", "),
      showReady: ["draft", "stale"].includes(state.state), canReady: Boolean(state.ready),
      canDecide: Boolean(state.ready) && ["awaiting-review", "changes-requested"].includes(state.state),
      canChange: Boolean(state.ready) && ["awaiting-review", "approved", "changes-requested"].includes(state.state),
      onReady: () => call("ready", { expected_revision: state.fingerprint }),
      onApprove: () => decide("approved"), onRequestChanges: note => decide("changes-requested", note),
    });
    main.append(bar.element);
  }
  async function batches(main, type, id, h) {
    const block = section(h, "Generation batches", "Each image batch has its own purpose, prompt, references, route, cost gate and output record.");
    const all = await read(h, "/api/generations");
    const mine = all.filter(item => item.subject_type === type && item.subject_id === id);
    if (mine.length) block.append(h.make("div", { className: "creative-gates" }, mine.map(item => h.make("div", { className: "creative-gate" }, [
      h.link(`${item.purpose} · ${item.id}`, `/generations/${item.id}`), h.statusPill(item.state), h.make("small", {}, `${item.image_count} image(s) · ${item.transport}`),
    ]))));
    else block.append(h.emptyState("No image batches", "Approved upstream creative work is needed before a generated batch can be prepared."));
    if (type === "style") {
      const detail = await read(h, `${apiPath("style", id)}`);
      const form = h.make("form", { className: "form-shell" });
      const prompt = h.textArea("Style material image prompt", { required: true, rows: 5 });
      const route = imageRoute(h, false);
      const refs = h.textInput("Reference material IDs, comma separated", { placeholder: "Existing image material IDs" });
      rememberFields(h, `style/${id}/batch`, { prompt, refs });
      const note = message(h), submit = h.button("Prepare one-image batch", "button button-primary", null, "submit");
      h.add(form, prompt.wrapper, ...route.wrappers, refs.wrapper, actionsRow(h, submit), note);
      form.addEventListener("submit", async event => {
        event.preventDefault(); submit.disabled = true;
        try {
          const batch = await read(h, "/api/generations", h.jsonOptions("POST", {
            id: `style-${crypto.randomUUID().slice(0, 12)}`, subject_type: "style", subject_id: id, purpose: "style-material",
            prompt: prompt.control.value, references: refs.control.value.split(",").map(value => value.trim()).filter(Boolean).map(material_id => ({ material_id, role: "style reference" })),
            transparent: false, image_count: 1, input_revision: detail.reviews.brief.fingerprint, ...route.selected(),
          })); h.state.drafts.delete(`creative:fields:style/${id}/batch`); await h.navigate(`/generations/${batch.id}`);
        } catch (error) { h.showFormError(note, error); } finally { submit.disabled = false; }
      });
      block.append(form);
    }
    main.append(block);
  }
  async function generation(main, id, h) {
    let record = await read(h, `/api/generations/${id}`);
    h.setBreadcrumb([{ label: "Generation batch" }, { label: id }]);
    main.append(h.pageIntro(`${record.purpose} · ${id}`, "An approved batch permits one real OpenAI generation route. Outputs remain separate from creative approval.",
      [h.link("Open subject", record.subject_type === "style" ? `/styles/${record.subject_id}` : `/characters/${record.subject_id}`, "button")]));
    const detail = section(h, "Batch facts");
    let status = h.statusPill(record.state);
    const reportedModel = text(h, "Reported image model", record.image_model || "unknown");
    detail.append(status, text(h, "Provider", record.provider), text(h, "Route", record.transport),
      text(h, "Requested API model", record.transport === "openai-api" ? record.requested_image_model || "unspecified" : "not applicable"),
      text(h, "Transparent output", record.transparent ? "yes" : "no"), reportedModel,
      text(h, "Purpose", record.purpose), text(h, "Count", record.image_count), text(h, "Prompt", record.prompt),
      text(h, "Context", record.context ? JSON.stringify(record.context) : "none"));
    for (const reference of record.resolved_references || []) {
      detail.append(text(h, "Reference", `${reference.material_id} · ${reference.role}`));
      for (const item of reference.images || []) detail.append(image(h, item.path, reference.role));
    }
    const outputHost = h.make("div", { className: "creative-catalog" });
    for (const output of record.outputs || []) outputHost.append(image(h, output.path, `Generated output ${output.path.split("/").at(-1)}`));
    detail.append(outputHost);
    const errorHost = h.make("div"); detail.append(errorHost);
    const receipt = h.make("p"); detail.append(receipt);
    main.append(detail);
    const controls = section(h, "Batch review and execution", "This batch's saved authorization and execution state.");
    const stateMessage = h.make("p"); controls.append(stateMessage);
    let timer = 0;
    let approve, run, approvalFields, billingField, runFields, nativeRegistration;
    const showRecord = next => {
      record = next;
      const badge = h.statusPill(record.state); status.replaceWith(badge); status = badge;
      reportedModel.replaceChildren(h.make("strong", {}, "Reported image model: "), String(record.image_model || "unknown"));
      outputHost.replaceChildren(...(record.outputs || []).map(output => image(h, output.path, `Generated output ${output.path.split("/").at(-1)}`)));
      errorHost.replaceChildren(...(record.last_error ? [h.notice("Last run stopped", record.last_error, "error-banner")] : []));
      receipt.textContent = record.approved_by ? `Batch approved by ${record.approved_by} · ${record.approved_at || "date unavailable"}` : "";
      stateMessage.replaceChildren();
      if (record.state === "completed") {
        stateMessage.append(record.subject_type === "character"
          ? "Generation completed. Batch approval authorized generation; finished artwork is reviewed with the character rig before use."
          : "Generation completed. Batch approval authorized generation; finished artwork is reviewed with the style before use.");
        if (record.subject_type === "character" && record.context?.variant_id)
          stateMessage.append(" ", h.link("Inspect character rig and action reviews", `/characters/${record.subject_id}?variant=${encodeURIComponent(record.context.variant_id)}#variants`, "quiet-link"));
      } else if (record.state === "superseded") {
        stateMessage.append("This batch was superseded.");
        if (record.superseded_by) stateMessage.append(" ", h.link("Open replacement batch", `/generations/${encodeURIComponent(record.superseded_by)}`, "quiet-link"));
      }
      if (approvalFields) approvalFields.hidden = record.state !== "awaiting-batch-approval";
      if (approve) approve.disabled = record.state !== "awaiting-batch-approval";
      if (runFields) runFields.hidden = !["approved", "partial"].includes(record.state);
      if (run) run.disabled = !["approved", "partial"].includes(record.state);
      if (nativeRegistration) nativeRegistration.hidden = !["approved", "partial"].includes(record.state);
    };
    const poll = async () => {
      if (h.version !== h.state.routeVersion) { clearInterval(timer); return; }
      try {
        showRecord(await read(h, `/api/generations/${id}`));
        if (record.state !== "running") clearInterval(timer);
      } catch { /* Keep the last confirmed batch record. */ }
    };
    if (record.state === "running") timer = setInterval(poll, 3500);
    const reviewer = h.textInput("Batch reviewer", { required: true });
    const billing = h.checkField("I acknowledge OpenAI API billing for this exact batch");
    billingField = h.make("div", {}, billing.wrapper);
    billingField.hidden = record.transport !== "openai-api";
    const note = message(h);
    approve = task(h, "Approve this batch", () => h.api(`/api/generations/${id}/approve`, h.jsonOptions("POST", {
      reviewer: reviewer.control.value, billing_acknowledged: billing.control.checked,
    })), note);
    approve.disabled = record.state !== "awaiting-batch-approval";
    run = task(h, record.transport === "native" ? "Show native handoff" : "Run approved batch", async () => {
      if (record.transport !== "native") timer ||= setInterval(poll, 3500);
      const result = await read(h, `/api/generations/${id}/run`, h.jsonOptions("POST", { transport: record.transport }));
      if (result.handoff) {
        showRecord(result); note.hidden = false;
        note.replaceChildren(h.notice("Native agent handoff", `${result.handoff} Output folder: ${result.output_dir}. Register only files returned by a real image tool call, with its actual tool results.`));
      }
      else await poll();
    }, note, async () => {});
    run.disabled = !["approved", "partial"].includes(record.state);
    approvalFields = h.make("div", {}, [reviewer.wrapper, billingField, actionsRow(h, approve)]);
    runFields = h.make("div", {}, actionsRow(h, run));
    controls.append(approvalFields, runFields, note);
    if (record.transport === "native") {
      const form = h.make("form", { className: "form-shell" });
      const outputs = h.textArea("Actual generated output paths JSON", { rows: 3, value: "[]" });
      const provenance = h.textArea("Actual native tool result JSON", { rows: 4, value: '{"provider":"openai","transport":"native","coordinator":"","image_tool_used":true,"tool_results":[]}' });
      form.append(h.make("p", {}, "An agent registers byte-identical saved tool images and the corresponding real tool result records. This form cannot create image bytes or approval."));
      const save = h.button("Register native tool outputs", "button button-primary", null, "submit");
      h.add(form, outputs.wrapper, provenance.wrapper, actionsRow(h, save));
      form.addEventListener("submit", async event => {
        event.preventDefault(); save.disabled = true;
        try { await h.api(`/api/generations/${id}/outputs`, h.jsonOptions("POST", { outputs: JSON.parse(outputs.control.value), provenance: JSON.parse(provenance.control.value) })); await refresh(h); }
        catch (error) { h.showFormError(note, error); } finally { save.disabled = false; }
      });
      nativeRegistration = advanced(h, "register native tool outputs", form);
      controls.append(nativeRegistration);
    }
    showRecord(record);
    main.append(controls);
  }
  function settings(main, h) {
    h.setBreadcrumb([{ label: "Settings" }]);
    main.append(h.pageIntro("Settings and agent handoff", "Studio runs locally. Creative requests wait until a real agent claims them."));
    const block = section(h, "How agents work", "Codex and Claude follow the same saved-file and human-review contracts.");
    block.append(h.make("ol", {}, [
      h.make("li", {}, "Open the current request and read its subject, input revision and instructions."),
      h.make("li", {}, "Open Brainstormform, save the full answers and editable brief, then mark the exact gate ready."),
      h.make("li", {}, "Open or post the exact Studio review URL, wait for the reviewer's decision, and continue only after approval."),
      h.make("li", {}, "Generated image batches need their own approval. A native handoff registers only actual image tool files and results."),
    ]));
    block.append(h.make("pre", { className: "job-log" }, ".venv/bin/python anim.py studio-request <id> --claim <agent>\n.venv/bin/python anim.py studio-request <id> --finish succeeded --note 'Saved and linked exact review URL'"));
    block.append(fileLink(h, "_shared/dashboard-review.md", "Video review protocol"));
    main.append(block);
  }
  async function videoCreative(main, video, h) {
    const block = section(h, "Reviewed creative snapshot", "Install a current approved style and selected character actions into this video. Inspect every changed file before applying.");
    const choices = h.state.styles.filter(style => style.id && style.origin !== "existing-reference").map(style => ({ value: style.id, label: `${style.title || style.id} · ${style.renderer}` }));
    const style = h.selectField("Style variant", [{ value: "", label: "Choose an approved variant" }, ...choices], { required: true });
    const characters = await read(h, "/api/characters");
    const rows = (Array.isArray(characters) ? characters : characters.characters || []).filter(item => item.origin === "character-workshop");
    const character = h.selectField("Character", [{ value: "", label: "No character" }, ...rows.map(item => ({ value: item.id, label: item.title || item.id }))], {});
    const variant = h.selectField("Character style variant", [{ value: "", label: "Select character first" }], {});
    const action = h.selectField("Approved actions", actions.map(value => ({ value, label: value })), {});
    action.control.multiple = true; action.control.size = 6;
    const selected = [];
    const selectedList = h.make("div", { className: "creative-gates" });
    const note = message(h), proposalHost = h.make("div", { className: "creative-gates" });
    character.control.addEventListener("change", async () => {
      variant.control.replaceChildren(h.make("option", { value: "" }, "Choose a variant"));
      if (!character.control.value) return;
      try { const detail = await read(h, `/api/characters/${character.control.value}`);
        for (const item of detail.variants || []) variant.control.append(h.make("option", { value: item.id }, `${item.id} · ${item.style_id}`));
      } catch (error) { h.showFormError(note, error); }
    });
    const addCharacter = h.button("Add character actions", "button", () => {
      const chosen = Array.from(action.control.selectedOptions, option => option.value);
      if (!character.control.value || !variant.control.value || !chosen.length) { h.showFormError(note, new Error("Choose a character, variant and at least one action.")); return; }
      selected.push({ character_id: character.control.value, variant_id: variant.control.value, actions: chosen });
      const entry = selected.at(-1);
      const row = h.make("div", { className: "creative-gate" }, [h.make("span", {}, `${character.control.value} · ${variant.control.value} · ${chosen.join(", ")}`),
        h.button("Remove", "button button-small", () => { selected.splice(selected.indexOf(entry), 1); row.remove(); })]);
      selectedList.append(row);
    });
    const preview = h.button("Preview snapshot changes", "button button-primary", async () => {
      await h.withButton(preview, async () => {
        const result = await read(h, `/api/videos/${video.slug}/creative`, h.jsonOptions("POST", { style_id: style.control.value, characters: selected, confirm: false }));
        proposalHost.replaceChildren(h.notice("Proposed files", `${result.changes.length} change(s); ${result.protected.length} protected local edit(s).`));
        for (const change of result.changes) proposalHost.append(h.make("p", {}, `${change.protected ? "Protected · " : ""}${change.path} · ${change.before || "new"} → ${change.after || "removed"}`));
        const apply = task(h, "Apply reviewed snapshot", () => h.api(`/api/videos/${video.slug}/creative`, h.jsonOptions("POST", {
          style_id: style.control.value, characters: selected, expected_revision: result.revision, confirm: true,
        })), note);
        apply.disabled = result.protected.length > 0;
        proposalHost.append(apply);
      }, note);
    });
    block.append(style.wrapper, character.wrapper, variant.wrapper, action.wrapper, actionsRow(h, addCharacter, preview), selectedList, proposalHost, note);
    main.append(block);
  }
  async function reviewQueue(host, h) {
    const current = () => h.version === h.state.routeVersion;
    const rows = await read(h, "/api/creative?view=summary");
    const entries = rows.flatMap(item => Object.entries(item.reviews || {})
      .filter(([, review]) => review.recorded_state === "awaiting-review")
      .map(([gate]) => ({ ...item, gate })));
    if (!current()) return;
    if (!entries.length) { host.remove(); return; }
    host.append(h.sectionHeading("Creative decisions", `${entries.length} saved revision(s) waiting for your decision.`));
    host.append(h.make("div", { className: "review-list" }, entries.slice(0, 30).map((item, index) => h.make("article", { className: "review-row" }, [
      h.make("div", { className: "review-index" }, String(index + 1).padStart(2, "0")),
      h.make("div", { className: "review-project" }, [h.make("strong", {}, item.title), h.make("small", {}, `${item.type} · ${item.id}`)]),
      h.make("div", { className: "review-context" }, [h.make("strong", {}, item.gate.replaceAll(":", " · ")), h.statusPill("unchecked")]),
      h.make("p", { className: "review-reason" }, ""),
      h.link("Open review", reviewUrl(item.type, item.id, item.gate), "text-link"),
    ]))));
    host.hidden = false;
  }
  return { newCreative, loadFamilies, families, styleExtras, styleWorkshop, characters, character, review, batches, generation, settings, videoCreative, reviewQueue };
})();
