# Version Workflow Agent — office2md

## Purpose

This workflow is for completing one small office2md version from planning to final local commit.

Default policy:
- plan automatically
- execute scoped tasks automatically when safe
- review after each task
- create one final version commit only
- do not tag
- do not push

This workflow is intended for local Codex CLI automation or Codex App-assisted execution.

## Required Paths

Default workspace root:

```text
/Volumes/seagate 2t/offic2md
```

Default Git repo root:

```text
/Volumes/seagate 2t/offic2md/repo
```

Default Obsidian vault:

```text
/Volumes/seagate 2t/offic2md/office2md-vault
```

Always verify actual paths before changing files.

## Commit Policy

Use final-only commit by default.

Allowed:
- one final local commit when the whole version goal is complete

Not allowed by default:
- checkpoint commits
- tags
- push
- remote changes

Commit message format:

```text
Release <version>
```

Example:

```text
Release v0.5.2
```

## Version Workflow State Machine

A version moves through these states:

1. `planned`
2. `task_ready`
3. `task_running`
4. `task_done`
5. `version_review_ready`
6. `version_commit_ready`
7. `committed`
8. `blocked`

Stop on `blocked`.

## Optimizer Loop Mode

When `docs/agents/version_queue.json` sets:

```json
"mode": "optimizer_loop"
```

run exactly one small improvement loop:

```text
CHECK -> PLAN -> OPTIMIZE -> REVIEW -> COMMIT -> STOP
```

The optimizer loop is for ongoing office2md improvement and correction. It should favor small, high-value changes that improve user friendliness, efficiency, bug reduction, agent workflow usability, large-folder update workflow, JSON contract clarity, or source-file safety.

Default optimizer-loop rules:
- identify up to three candidate tasks
- select exactly one P1 task
- keep the selected task small and bounded
- prefer docs, workflow, CLI help, validation, and UX hardening before deeper runtime changes
- create exactly one final local commit only if validation passes and policy allows it
- do not create tags
- do not push
- stop after the commit

The optimizer loop must not:
- run multiple loops in one invocation
- perform broad refactors
- modify source documents
- modify Knowledge Packs without explicit permission
- add AI/OCR/embedding/vector/cloud work
- add unrestricted SQL or shell access
- change protected behaviors unless explicitly scoped and tested

## Automation Safety Gates

Automation may continue to the next task only when:
- current task validation passed
- git diff only includes expected files
- no protected behavior changed unless scoped
- queue status is updated
- next task is explicitly marked `ready_for_execution`
- task does not allow tag or push

Automation must stop before final commit unless the version workflow explicitly sets:

```json
"allow_final_commit": true
```

Automation must never tag or push.

## Protected Behaviors

Do not change unless explicitly scoped:
- conversion behavior
- build-library behavior
- search ranking
- search aliases
- token fallback
- runner process-control behavior
- workspace behavior
- GUI behavior
- Agent Gateway behavior
- MCP adapter behavior
- existing JSON schema semantics
- source files
- Knowledge Packs

## Final Version Review Requirements

Before the final commit:

1. Inspect `git status` and `git diff --stat`.
2. Confirm all changes match the version goal.
3. Confirm no unrelated product changes.
4. Run validation:

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

5. Run task-specific smoke tests.
6. Update release notes/checklist if scoped.
7. Commit only if all review requirements pass.
8. Do not tag.
9. Do not push.

## Required Version Report

Write a final version report to the Obsidian vault:

```text
office2md-vault/50_Releases/<date> <version> Local Commit.md
```

Include:
- version goal
- tasks completed
- files changed
- validation results
- smoke results
- final commit hash
- git status
- confirmation that no tag or push was performed
- recommended next version direction
