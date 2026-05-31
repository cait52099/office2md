# Codex App Version Workflow Prompt

Read these files first:

1. `AGENTS.md`
2. `docs/agents/version_workflow.md`
3. `docs/agents/version_queue.json`
4. The active goal file listed in `docs/agents/version_queue.json`

Then execute the active version workflow.

If the active version mode is `optimizer_loop`, run exactly one loop:

CHECK → PLAN → OPTIMIZE → REVIEW → COMMIT → STOP.

Rules:

- Work only in the repo root from `version_queue.json`.
- Use the workspace root and Obsidian vault from `version_queue.json`.
- Create only one final local commit if validation passes and policy allows it.
- Do not create tags.
- Do not push.
- Do not modify source documents.
- Do not modify Knowledge Packs.
- Do not run multiple optimizer loops.
- Stop if validation fails.
- Stop if git diff contains unexpected files.
- Stop if scope becomes unclear.

Required validation should include, when applicable:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m compileall office2md/gui
.venv/bin/python -m office2md.cli --help
.venv/bin/python -m json.tool docs/agents/agent_queue.json
.venv/bin/python -m json.tool docs/agents/version_queue.json
bash -n scripts/agent_run_next.sh
bash -n scripts/agent_run_version.sh
```

Report the final result with:

- active version
- selected task
- files changed
- validation result
- commit hash if created
- git status
- confirmation that no tag was created
- confirmation that no push was performed
