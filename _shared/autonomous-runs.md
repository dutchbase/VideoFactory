# Saved video runs

A managed run saves your production settings before work starts. Its video identifier is `<brand>/<slug>`. Output filenames use only the leaf slug.

Before a saved run starts production, ask the session permission question in `_shared/permissions.md`. Save the answer with the session ID and named scope. A run cannot reuse permission from another session or widen its scope. Its workers inherit the same permission. Permission-based stage completion is recorded separately from human review decisions. Full permission still stops for failed checks, missing facts or evidence, and every paid request. Paid requests need separate approval for the exact request and known cost; retries need fresh approval.

## Start and resume

1. Create the project with `anim.py new <slug> --brand <brand>`.
2. In Studio, open the project and save its production settings. For the CLI, save the equivalent JSON below as `videos/<brand>/<slug>/run_settings.json`.
3. Save the permission answer, session ID and named scope. Use `each-stage` to stop after every stage or `selected-stages` with the review gates to stop at. Full permission allows work to continue to `ready-for-final-review`, subject to the required checks and stops below. It does not force a render-gate review. The permission record controls review pauses; run settings do not grant permission. The legacy `review_mode` field below remains required by the current settings format, but it does not grant permission or control review pauses.
4. Resume an existing record with `anim.py run <brand>/<slug> --resume <run-id>`.

Start with `anim.py run <brand>/<slug>`. An unattended start must have the saved settings file and an active permission record for the current session and video scope. Use the project's existing format (`wide` or `tall`) and language. For `selected-stages`, include the review gates in the permission record.

```json
{
  "brand": "videofactory",
  "subject": "The topic you supply",
  "intended_result": "The result you want",
  "format": "tall",
  "language": "en",
  "review_mode": "final-review-only",
  "selected_stages": [],
  "max_paid_spend": "0",
  "research": false
}
```

A missing price or required evidence stops work. Paid narration needs a verified per-request quote and separate approval. The run does not infer a provider price from the spending limit. The direct image API route accepts quoted requests. Agent and native image routes stop, because their internal request count cannot be bounded. Existing licensed assets stay available within the video's scope; editing a shared asset needs permission for its named scope.

## Saved progress

Run records are saved in `.studio/runs/` and copied to the project's `runs/<run-id>/run.json`. Paid request records are saved in `.studio/paid/`. Each stage records its current inputs, actual output and validation. Changed inputs invalidate later results. Resume uses valid output and recovers unfinished findings. A successful agent exit is not enough evidence of a valid stage. Stage completion uses the current permission and the expected fingerprint; it is separate from human review.

The pipeline covers optional research, brief, script, voice, transcript, cues, scene, checks, export and independent review. Every stage loads relevant verified lessons and records its findings, even when it finds no new lesson.

One production lock covers Studio jobs and managed runs. A child worker keeps the lock if its controller stops. Another worker cannot take over while that process is alive. Review waiting releases the lock after the worker has stopped.

## Paid media

Every request gets a saved identifier and a reservation for its maximum expected cost. Retries, variations and paid asset adaptation use the same run limit. An unknown price stops the request before spending.

If a provider may have charged an interrupted request, keep its reservation. Reconcile the actual charge before you retry. Deleting a reservation or using a new identifier is not a recovery procedure.

To recover a run in the project terminal:

1. Read the saved error. It gives the run ID and request ID. Pending request details are also in `.studio/paid/<run-id>-<request-id>.pending.json`.
2. Get the provider's maximum price for that exact request. Use the same currency as the saved run limit.
3. Save the quote with `anim.py run-quote <run-id> <request-id> --max-cost <cost> --evidence "<price source>"`. This command cannot raise the run limit.
4. Show the exact request and quoted maximum cost. Ask for approval, then save it with `anim.py run-approve <run-id> <request-id> --expected <quote-fingerprint> --reviewer <name>`. This approval applies to that request and quote only.
5. If a charge is uncertain, check the provider receipt first. Save it with `anim.py run-reconcile <run-id> <attempt-id> --actual <cost> --evidence "<receipt reference>"`.
6. If another paid attempt is needed, register its quote with `run-quote` and `--retry`, ask for approval again, and use `run-approve` with the new quote fingerprint. Every previous attempt must have a resolved charge first.
7. Resume the saved run with `anim.py run <brand>/<slug> --resume <run-id>`.

A successful call without a billing receipt keeps the full quoted upper bound as its cost. A later receipt can reconcile that estimate. Never put API keys or private billing details in the evidence text.

## Completion

Independent review must assess current frames and the actual rendered audio. All seven scores must be at least 8, with no blocking issue. The review records the hashes of the reviewed artifacts. Stale evidence cannot complete a run.

After three unsuccessful repair rounds, save `needs-attention`. Use the same state when required evidence is unavailable. Do not weaken a check to get a pass.

The final package includes the video, thumbnail, description, required credits and disclosures, and review evidence. Full permission can bring a run to `ready-for-final-review` without a render-gate approval. It does not create human approval. Export completion and publication approval are separate. Only a person can approve publication.

## Lessons and brand changes

Verified shared lessons live in `learning/`. Brand lessons live in `brands/<brand>/learning/`. Load lessons by brand, stage and failure type. Keep uncertain findings separate. Save a regression check for failures that software can detect. Brand rules and permissions need your approval.
