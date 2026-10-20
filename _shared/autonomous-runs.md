# Saved video runs

A managed run saves your production settings before work starts. Its video identifier is `<brand>/<slug>`. Output filenames use only the leaf slug.

## Start and resume

1. Create the project with `anim.py new <slug> --brand <brand>`.
2. In Studio, open the project and save its production settings. For the CLI, save the equivalent JSON below as `videos/<brand>/<slug>/run_settings.json`.
3. Select `autonomous`, `final-review-only` or `selected-stages`. For selected stages, list the stages where work must stop for your review.
4. Resume an existing record with `anim.py run <brand>/<slug> --resume <run-id>`.

Start with `anim.py run <brand>/<slug>`. An unattended start must have the saved settings file. Use the project's existing format (`wide` or `tall`) and language. For `selected-stages`, fill `selected_stages` with the required review gates.

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

A missing price or review artifact stops work. Paid narration needs a verified per-request quote. The run does not infer a provider price from the spending limit. The direct image API route accepts quoted requests. Agent and native image routes stop, because their internal request count cannot be bounded. Existing licensed assets stay available.

## Saved progress

Run records are saved in `.studio/runs/` and copied to the project's `runs/<run-id>/run.json`. Paid request records are saved in `.studio/paid/`. Each stage records its current inputs, actual output and validation. Changed inputs invalidate later results. Resume uses valid output and recovers unfinished findings. A successful agent exit is not enough evidence of a valid stage.

The pipeline covers optional research, brief, script, voice, transcript, cues, scene, checks, export and independent review. Every stage loads relevant verified lessons and records its findings, even when it finds no new lesson.

One production lock covers Studio jobs and managed runs. A child worker keeps the lock if its controller stops. Another worker cannot take over while that process is alive. Review waiting releases the lock after the worker has stopped.

## Paid media

Every request gets a saved identifier and a reservation for its maximum expected cost. Retries, variations and paid asset adaptation use the same run limit. An unknown price stops the request before spending.

If a provider may have charged an interrupted request, keep its reservation. Reconcile the actual charge before you retry. Deleting a reservation or using a new identifier is not a recovery procedure.

To recover a run in the project terminal:

1. Read the saved error. It gives the run ID and request ID. Pending request details are also in `.studio/paid/<run-id>-<request-id>.pending.json`.
2. Get the provider's maximum price for that exact request. Use the same currency as the saved run limit.
3. Save the quote with `anim.py run-quote <run-id> <request-id> --max-cost <cost> --evidence "<price source>"`. This command cannot raise the run limit.
4. If a charge is uncertain, check the provider receipt first. Save it with `anim.py run-reconcile <run-id> <attempt-id> --actual <cost> --evidence "<receipt reference>"`.
5. If another paid attempt is needed, register its quote with `run-quote` and `--retry`. Every previous attempt must have a resolved charge first.
6. Resume the saved run with `anim.py run <brand>/<slug> --resume <run-id>`.

A successful call without a billing receipt keeps the full quoted upper bound as its cost. A later receipt can reconcile that estimate. Never put API keys or private billing details in the evidence text.

## Completion

Independent review must assess current frames and the actual rendered audio. All seven scores must be at least 8, with no blocking issue. The review records the hashes of the reviewed artifacts. Stale evidence cannot complete a run.

After three unsuccessful repair rounds, save `needs-attention`. Use the same state when required evidence is unavailable. Do not weaken a check to get a pass.

The final package includes the video, thumbnail, description, required credits and disclosures, and review evidence. Export completion and publication approval are separate. Agents never approve publication.

## Lessons and brand changes

Verified shared lessons live in `learning/`. Brand lessons live in `brands/<brand>/learning/`. Load lessons by brand, stage and failure type. Keep uncertain findings separate. Save a regression check for failures that software can detect. Brand rules and permissions need your approval.
