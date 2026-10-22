# Image 03 Export

Read `_shared/permissions.md` first. Needs a passed `brief` review.

**Inputs.** `02_design/` and the sizes in `01_brief/brief.md`.

**Job.** `python anim.py image export <brand>/<slug>` renders `design.html` once per size in Chromium and writes `03_export/<size-id>.png` at the exact pixel size. `--only <ids>` exports a part. In the same pass it checks each image and writes `report.json`:

- fails: a page error, text or logo outside the safe area, text that overflows its box, a picture that did not load, a brand font that failed to load, a wrong pixel size;
- warns: low contrast of a heading against the background around it.

A failure stops the run. Fix the design and export again. A design edit after an export makes the report stale. A full export removes images of sizes the brief no longer names.

**Output.** `03_export/*.png`, `03_export/report.json`.

**Human check.** Look at every PNG at its real size, and the small ones (profile pictures) at phone size. Then `python anim.py image review <brand>/<slug> final`; mark ready, then approve with `--approve --reviewer NAME --expected <fingerprint>`. Only a person approves publication. This package does not upload or post.
