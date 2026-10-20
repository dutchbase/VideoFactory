# Studio performance verification

Measured on 2026-10-18 with a separate Studio server on port 8799. The Studio changes were in the working tree. Existing local video and workspace changes were kept.

## Browser results

| Width | Route | Before: reload median | After: reload median | After: slowest reload | After: navigation p95 |
|---|---|---:|---:|---:|---:|
| 1440 px | Settings | 14.33 s | 157 ms | 192 ms | 58 ms |
| 1440 px | Script review (long script) | 15.74 s | 264 ms | 483 ms | 188 ms |
| 1440 px | Library (48 records) | 23.95 s | 281 ms | 482 ms | 184 ms |
| 390 px | Settings | 10.23 s | 159 ms | 263 ms | 122 ms |
| 390 px | Script review (long script) | 17.37 s | 267 ms | 284 ms | 188 ms |
| 390 px | Library (48 records) | 26.10 s | 296 ms | 481 ms | 201 ms |

All measured routes meet the limits: useful content within 1 second, repeated navigation p95 below 500 ms, and the first 48 library records within 1 second. Useful content means the settings content, a nonempty script editor, or actual material records. A loading indicator does not count.

Method: the same three routes before and after. Before: two reloads and two in-page navigations for each route and width. After: twenty reloads and twenty in-page navigations for each route and width. p95 is the nearest-rank 95th percentile. A reload starts a fresh page load, with HTTP caching disabled by Studio. The server's bounded five-second overview cache stays active. Each in-page measurement starts from Settings, or from Videos when measuring Settings. The baseline used the original Python server process and the saved original `app.js` and `creative.js`. A process check before the final series found no render, transcription, voice, FFmpeg or Whisper process. The workspace held more than 9,000 library records at the final measurements.

Browser: Chromium 139.0.7258.5, headless, virtual screen 1920×1080 at 60 Hz. Viewports were 1440×1000 and 390×1000. Functional narrow tests also used 390×844. No external publishing was exercised. A first pass exposed eager hidden attachment forms and synchronous thumbnail decoding. Both were fixed before the final timings. The narrow layout was checked by eye, including the title, editor and decision controls.

## Correctness and boundaries

- The shell bootstrap avoids video, review, style and library scans. Compact video and creative summaries read metadata and recorded events and show an "unchecked" label. They do not assert current approval.
- Materials and files share one inventory, with 48-result pages, exact type filters, full-inventory search and direct ID lookups. File and attachment forms load when opened. One missing linked record does not hide the other records.
- The process cache is bounded to 128 entries and five seconds. Concurrent reads share one refresh. Writes invalidate the workspace, including refreshes in flight. External file changes appear after expiry.
- Review events, dependencies and file lists are shared only within one read call, keyed by function, workspace, subject and gate. The existing file-hash cache is the only file-hashing cache.
- Saves keep revision conflicts. Decisions and production actions check current inputs without the overview caches. Path traversal, private paths, symlinks and generated-source write protection stay guarded.
- Navigation cancels reads, detaches the abandoned route and checks its version before updates. Writes continue. Clean editors reread saved text. Dirty drafts and text entered during a save survive. Agent completion offers the updated review without replacing the focused editor. Secondary failures have local retry controls.

Reproduce the timings with the project's Python toolchain and Playwright browser cache:

```sh
.venv/bin/python tests/benchmark_studio.py --rounds 20
```

Use an isolated test server on port 8799, without competing renders or transcription. The benchmark is read-only and prints JSON. Default API responses stay available without `view=summary` or `view=shell`.

## Regression checks

- Backend tests cover shell isolation, paging, search, type filters, direct records, request and process cache boundaries, expiry, concurrent refresh, external edits, write invalidation, stale approval and paid-voice rejection, privacy and generated-file protections, and creative snapshot behaviour.
- Browser cases cover shell-only Settings, cancelled reads during navigation, retained editor focus and dirty drafts on agent completion, per-section retry, external save conflict, the latest clean script on return, writes that finish after navigation, typing during an in-flight save, library pagination and search, and the lazy file inventory.
- No new framework, dependency, database, external service, production render or publishing action was introduced.
