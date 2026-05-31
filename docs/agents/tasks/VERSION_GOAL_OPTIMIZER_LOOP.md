# VERSION_GOAL_OPTIMIZER_LOOP

## Purpose

Run one complete office2md optimizer loop:

CHECK → PLAN → OPTIMIZE → REVIEW → COMMIT → STOP.

This workflow is for ongoing project optimization and correction.

It should improve office2md in small, safe increments for:

- user friendliness
- higher efficiency
- fewer bugs
- clearer local workflows
- better agent-readiness
- safer update-library behavior
- clearer docs and validation

## Required Loop

### 1. CHECK

Inspect:

- git status
- recent git log
- current version metadata
- existing AGENTS.md and workflow files
- README and key docs
- current CLI help
- relevant tests
- recent Obsidian reports if available

Run baseline validation when practical:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m compileall office2md/gui
.venv/bin/python -m office2md.cli --help
```

For workflow files, also run when the files exist:

```bash
.venv/bin/python -m json.tool docs/agents/agent_queue.json
.venv/bin/python -m json.tool docs/agents/version_queue.json
bash -n scripts/agent_run_next.sh
bash -n scripts/agent_run_version.sh
```

Only run checks for files that exist.

### 2. PLAN

Identify up to 3 candidate tasks.

Each candidate must include:

- problem
- impact
- proposed fix
- likely files
- risk
- validation
- whether it touches protected behavior

Select exactly 1 P1 task.

Selection rules:

- prefer small, high-value, low-risk fixes
- prefer docs / CLI help / workflow / validation hardening before deeper runtime changes
- do not select broad refactors
- do not select multiple unrelated changes
- do not modify protected behavior unless the selected task explicitly requires it and includes tests

### 3. OPTIMIZE

Implement only the selected P1 task.

Keep the diff small.

Do not perform unrelated cleanup.

Do not modify source documents.

Do not modify Knowledge Packs.

Do not add AI/OCR/embedding/vector/cloud work.

Do not add unrestricted SQL or shell access.

### 4. REVIEW

Before committing:

- inspect git diff
- confirm only expected files changed
- confirm protected behaviors unchanged unless explicitly scoped
- run validation
- run task-specific smoke tests
- ensure Obsidian report is written outside the repo

### 5. COMMIT

Create exactly one local commit only if:

- validation passes
- git diff is expected
- no tag is created
- no push is performed
- version_queue.json allows final commit

Commit message:

```text
Optimize office2md workflow <version>
```

or, if version metadata was intentionally updated:

```text
Release <version>
```

Do not create tags.

Do not push.

### 6. STOP

After the commit, stop.

Do not begin another optimization loop.

## Required Report

Write a report to the Obsidian vault:

```text
/Volumes/seagate 2t/offic2md/office2md-vault/50_Releases/<date> <version> Optimizer Loop.md
```

Report:

- selected version
- baseline status
- candidate tasks
- selected P1 task
- files changed
- validation result
- smoke result
- commit hash
- git status
- confirmation: no tag
- confirmation: no push
- recommended next loop direction

## Stop Conditions

Stop without committing if:

- validation fails
- git diff includes unexpected files
- scope becomes unclear
- selected task becomes larger than one small-version change
- source documents are modified
- Knowledge Packs are modified without explicit permission
- a tag or push would be required
