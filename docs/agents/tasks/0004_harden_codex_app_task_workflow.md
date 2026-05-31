# Task 0004 — Harden Codex App Task Workflow

## Role

You are an Execution Agent for office2md.

Read first:
1. `AGENTS.md`
2. `docs/agents/execution_agent.md` if present
3. `docs/agents/obsidian_journal_workflow.md` if present

## Project Paths

Project root:

```text
/Volumes/seagate 2t/offic2md/repo
```

Obsidian vault:

```text
/Volumes/seagate 2t/offic2md/office2md-vault
```

## Current Context

`v0.5.1-rc1` is complete and local-only. Validation baseline is green:

- pytest: 214 passed
- ruff: passed
- compileall: passed
- CLI help: passed
- focused smoke: passed

The repo now has a file-driven agent queue, a shell helper, and a Codex App prompt. During the v0.5.1-rc2 planning pass, two workflow usability issues were found:

1. `docs/agents/agent_queue.json` and `scripts/agent_run_next.sh` still point at `/Volumes/seagate 2t/offic2md`, but the actual repo root for this local checkout is `/Volumes/seagate 2t/offic2md/repo`.
2. `scripts/codex_app_run_next_prompt.md` is hardcoded to task `0002`, so it is stale as soon as the next task is added.

This creates friction and avoidable failure for every future Execution Agent task.

## Goal

Make the local Codex App / queue-driven task workflow reliable for the actual repo checkout and reusable for future ready tasks.

This is a workflow reliability optimization only. It must not change office2md product runtime behavior.

## Scope

Implement the smallest changes needed so a fresh Execution Agent can discover and run the first `ready_for_execution` task from `docs/agents/agent_queue.json` without stale paths or stale task IDs.

Expected files:

- `docs/agents/agent_queue.json`
- `scripts/agent_run_next.sh`
- `scripts/codex_app_run_next_prompt.md`
- optionally `docs/agents/execution_agent.md` if adding a concise local execution guide is useful
- optionally an Obsidian execution report under `office2md-vault/30_Codex_Reports/`

Recommended implementation direction:

- Set queue `project_root` to `/Volumes/seagate 2t/offic2md/repo`.
- Keep `obsidian_vault` as `/Volumes/seagate 2t/offic2md/office2md-vault`.
- Make `scripts/agent_run_next.sh` derive its default project root from the script location, or read it from the queue, so it is not brittle if the checkout lives under `repo`.
- Update the Codex App prompt so it tells Codex to read the queue and run the first `ready_for_execution` task, not a hardcoded completed task.
- Preserve the current safety policy: no auto commit, no auto tag, no auto push, stop after one task.

## Non-goals

Do not:

- change conversion behavior
- change build-library behavior
- change search/ranking/aliases/token fallback
- change update-library execution semantics
- change runner process-control behavior for product conversion runners
- change workspace behavior
- change GUI behavior
- change Graph View behavior
- change Obsidian export behavior
- change Agent Gateway or MCP behavior
- change existing JSON schema semantics beyond additive/queue workflow metadata if needed
- add embeddings, OCR, AI enrichment, cloud dependency, OfficeCLI integration, or external packages
- modify source documents or Knowledge Packs
- commit
- tag
- push

## Required Validation

Run:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m compileall office2md/gui
.venv/bin/python -m office2md.cli --help
```

Also run targeted workflow checks:

```bash
.venv/bin/python -m json.tool docs/agents/agent_queue.json
bash -n scripts/agent_run_next.sh
```

If `.venv/bin/python` is unavailable, use the project Python that is available and report the substitution.

## Required Smoke

Do not launch a long-running Codex task automatically.

Perform a safe smoke check that proves:

1. `docs/agents/agent_queue.json` parses as JSON.
2. The queue has exactly one next task with `status: ready_for_execution` unless the task file explicitly changes that policy.
3. The ready task file exists under the repo root.
4. The helper script would resolve the repo root to `/Volumes/seagate 2t/offic2md/repo`.
5. The Codex App prompt no longer references the completed task `0002` as the current task.
6. No commit, tag, push, product conversion, source modification, or Knowledge Pack modification occurs.

## Report

Save the report to:

```text
/Volumes/seagate 2t/offic2md/office2md-vault/30_Codex_Reports/2026-05-31 Task 0004 Harden Codex App Task Workflow.md
```

Use this format:

```md
# Task 0004 Execution Report

## 1. Task
- Current checkpoint:
- Task:
- Scope:

## 2. Files Changed
-

## 3. Implementation Summary
-

## 4. Tests Added or Updated
-

## 5. Validation
- pytest:
- ruff:
- compileall:
- CLI help:
- queue JSON:
- shell syntax:

## 6. Smoke
-

## 7. Behavior Boundaries
Confirm unchanged unless task-specific:
- conversion:
- build-library:
- search/ranking:
- update-library execution semantics:
- product runner process control:
- workspace:
- GUI:
- Obsidian export:
- Agent Gateway / MCP:
- source files / Knowledge Packs:

## 8. Git Status
-

## 9. Queue Update
Update `docs/agents/agent_queue.json`:
- mark task `0004` as `completed` if validation passes
- mark task `0004` as `blocked` if validation fails
- do not add a next task unless clearly necessary

## 10. Readiness
Ready for review/checkpoint:
Yes/No

Reason:
-
```

## Final Rules

Do not commit or tag.

Stop after this task.
