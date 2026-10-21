# Style workshop

Follow the current session and named-style permission in [`permissions.md`](permissions.md). Stage completion and human review are separate; paid generation also needs exact managed quote approval.

1. Claim the `style-discovery` request as a real workspace agent. Read the saved prompt and the referenced public materials.
2. Open a tailored question form (Brainstormform). Save its URL with `PUT /api/creative/style/<id>/answers` using the current `expected_revision`. The dashboard can show that handoff. Save the full result after Finish, including typed `answers`, `notes`, `submittedAt`, `skipped`, `unanswered` and `hidden`. A waiting request is not a running agent.
3. Save complete text answers and an edited `brief.md`. Run its checks. Under full permission, record stage completion with `--accept`; when the current permission requires review, mark the `brief` fingerprint ready, open the returned exact `review_url` in an available browser, post that link to the user and wait for the decision on that revision.
4. Develop described materials after the brief gate, then a real sample after the materials gate. Apply the same permission rule to `materials` and `sample`. Before any paid image generation, show the exact managed request and known cost and get separate quote approval; stop if cost is unknown. A file or completed job never approves a human review gate.

The Studio routes are `GET /api/creative/style/<id>`, `GET /api/creative/style/<id>/reviews/<gate>`, `POST .../ready` and `POST .../decision`. Review writes use `expected_revision` equal to the current gate `fingerprint`. Human decisions need `decision` (`approved` or `changes-requested`), `reviewer` and `note`. Agents may record permitted stage completion, but never make a human decision.
