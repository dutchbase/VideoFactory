# Permission for production

Read this file before work that creates or changes a video, brand, style or character. It applies in Studio, chat and saved runs.

## Start each session

Before production, ask exactly:

> Do I have full permission for this session?

Offer these choices:

1. **Full permission** — production, checks, repairs and export for this session.
2. **Review each stage** — stop for the user's review after every stage.
3. **Review selected stages** — ask which stages need review, then stop at those stages.

Wait for the answer. Silence and permission from an earlier session do not count. Record the session ID, scope, choice and any later grant or revocation. Full permission ends with the current session.

Name the scope as `video:<brand>/<slug>`, `brand:<id>`, `style:<id>` or `character:<id>`. A video permission allows work on that video. It allows the video to use shared assets. It does not allow edits to those shared assets; those need permission for the named brand, style or character.

Permission events are saved with the named item: video records are under `videos/<brand>/.permissions/`; shared records are under `brands/.permissions/`, `styles/.permissions/` or `characters/.permissions/`.

Workers inherit the same session permission and named scope. They cannot broaden it. For each interactive chat session, create a fresh unique session ID and set `VF_SESSION_ID` to it for every production command. Grant permission with that same ID. Do not recover an old ID from a saved run. Studio uses a fresh ID for each browser session and checks it against the server. A saved run cannot infer permission from its settings.

## Stage completion and human review

Permission to work does not approve a stage or the final video. `--accept` records agent completion under current permission after checks pass; it is not human approval. `--ready` marks an item for human review; it does not approve it. Keep a human decision in `REVIEW.md`, tied to the exact current fingerprint and reviewer. Chat and Studio use the same review action. “Approve this” counts only when the current item and one gate are clear. Otherwise ask which gate or item.

## Paid actions

Before a paid request, ask for approval of that exact request and its known cost. A retry or changed request needs fresh approval. If the cost is unknown, stop before spending. Full permission does not cover paid actions.

Full permission still stops when a required check fails, required facts or evidence are missing, or paid approval is needed. Keep editable outputs and repair them within the approved scope. Only a person can approve publication.

## Commands

Inspect or change permission in the project terminal. Create one unique ID for this chat session. Use it for every production command in the session:

```text
VF_SESSION_ID=<session-id> python anim.py permission --scope TYPE:ID --session <session-id>
VF_SESSION_ID=<session-id> python anim.py permission --scope TYPE:ID --grant full --session <session-id> --reviewer <name>
VF_SESSION_ID=<session-id> python anim.py permission --scope TYPE:ID --grant each-stage --session <session-id> --reviewer <name>
VF_SESSION_ID=<session-id> python anim.py permission --scope TYPE:ID --grant selected-stages --stages STAGE... --session <session-id> --reviewer <name>
VF_SESSION_ID=<session-id> python anim.py permission --scope TYPE:ID --revoke --session <session-id> --reviewer <name>
```

For a command that changes the shared library, give a named shared scope. Grant that scope first. A video scope does not work here:

```text
VF_SESSION_ID=<session-id> python anim.py lib port upstream:<source>/<name> --permission-scope style:<id>
VF_SESSION_ID=<session-id> python anim.py audio index --permission-scope brand:<id>
```

Record agent completion under permission:

```text
VF_SESSION_ID=<session-id> python anim.py review <slug> <gate> --accept --expected <fingerprint> --reviewer <name> --note <text>
```

This is valid only when the current permission allows the stage. It does not create a human decision.

For human review, first mark the exact revision ready and show its review link. Then record the person's decision:

```text
VF_SESSION_ID=<session-id> python anim.py review <slug> <gate> --ready --expected <fingerprint> --reviewer <name>
VF_SESSION_ID=<session-id> python anim.py review <slug> <gate> --approve --expected <fingerprint> --reviewer <name> --note <text>
VF_SESSION_ID=<session-id> python anim.py review <slug> <gate> --changes --expected <fingerprint> --reviewer <name> --note <text>
```

The command reports the current permission or review state. Follow its output if an option is unavailable. A readiness check or automatic validation is not a human decision.
