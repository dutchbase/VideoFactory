# Style workshop

1. Claim the `style-discovery` request as a real workspace agent. Read the saved prompt and the referenced public materials.
2. Open a tailored question form (Brainstormform). Save its URL with `PUT /api/creative/style/<id>/answers` using the current `expected_revision`. The dashboard can show that handoff. Save the full result after Finish, including typed `answers`, `notes`, `submittedAt`, `skipped`, `unanswered` and `hidden`. A waiting request is not a running agent.
3. Save complete text answers and an edited `brief.md`. Mark the current `brief` fingerprint ready, open the returned exact `review_url` in an available browser, post that link to the user and pause until the current decision appears.
4. Develop described materials after brief approval, then a real sample after materials approval. Repeat the same ready, open, link and pause protocol for `materials` and `sample`. A file or a completed job never approves a gate.

The Studio routes are `GET /api/creative/style/<id>`, `GET /api/creative/style/<id>/reviews/<gate>`, `POST .../ready` and `POST .../decision`. Review writes use `expected_revision` equal to the current gate `fingerprint`. Decisions need `decision` (`approved` or `changes-requested`), `reviewer` and `note`. You make the decision. Agents never approve on their own.
