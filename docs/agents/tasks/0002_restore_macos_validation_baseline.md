# Task 0002 — Restore macOS Validation Baseline

## Role

You are an Execution Agent for office2md.

Read first:
1. `AGENTS.md`
2. `docs/agents/execution_agent.md`
3. `docs/agents/obsidian_journal_workflow.md` if present

## Project Paths

Project root:

```text
/Volumes/seagate 2t/offic2md
```

Obsidian vault:

```text
/Volumes/seagate 2t/offic2md/office2md-vault
```

## Current Context

Task 0001 performed a read-only whole-project review from the GitHub repository and found that the macOS validation baseline is not fully green.

Known result from Task 0001:
- project version: `0.5.0`
- `ruff`: passed
- `compileall office2md/gui`: passed
- CLI help: passed
- `pytest`: `211 passed, 2 failed`

P1 blockers found:
1. macOS `scan-changes` path normalization / path casing behavior may misclassify unchanged or modified files as moved / new / deleted.
2. Default `.[dev]` install does not include `pyvis`, but tests import `pyvis`, causing full pytest baseline failure.

## Goal

Restore a green macOS validation baseline with minimal, scoped changes.

The goal is not to add product features. The goal is to make local macOS validation reliable.

## Scope

Implement only what is required to fix the two baseline blockers:

1. Fix path normalization / casing handling in the incremental scan-change logic so macOS paths are compared consistently.
2. Fix the test/dev dependency baseline so full pytest does not fail due to missing `pyvis`.

Likely files:
- `office2md/incremental.py`
- `tests/test_incremental.py`
- `pyproject.toml`
- possibly docs only if needed to clarify macOS setup

## Non-goals

Do not:
- change conversion behavior
- change build-library behavior
- change search/ranking/aliases/token fallback
- change runner process-control behavior
- change GUI behavior except dependency/test baseline if necessary
- change Agent Gateway or MCP behavior
- add AI/OCR/embedding/vector/cloud work
- add unrestricted SQL
- add shell execution through agent interfaces
- modify source documents
- commit
- tag
- push

## Required Validation

Run:

```bash
python -m pytest
python -m ruff check .
python -m compileall office2md/gui
python -m office2md.cli --help
python -m office2md.cli scan-changes --help
python -m office2md.cli update-library --help
```

## Required Smoke

Use temporary folders only.

Smoke should confirm:
1. `scan-changes` does not misclassify unchanged files due to path casing / normalization on macOS.
2. JSON exports still parse.
3. Source files are not modified.
4. Existing incremental classifications still work:
   - new
   - modified
   - unchanged
   - deleted_missing
   - moved_or_renamed_candidate where applicable

## Report

Save the report to:

```text
office2md-vault/30_Codex_Reports/2026-05-31 Task 0002 Restore macOS Validation Baseline.md
```

Use this format:

```md
# Task 0002 Execution Report

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

## 6. Smoke
-

## 7. Behavior Boundaries
Confirm unchanged unless task-specific:
- conversion:
- build-library:
- search/ranking:
- runner:
- workspace:
- GUI:
- Agent Gateway / MCP:
- source files:

## 8. Git Status
-

## 9. Queue Update
Update `docs/agents/agent_queue.json`:
- mark task `0002` as `completed` if validation passes
- mark task `0002` as `blocked` if validation fails
- add a concise next task only if clearly necessary

## 10. Readiness
Ready for review/checkpoint:
Yes/No

Reason:
-
```

## Final Rules

Do not commit or tag.

Stop after this task.
