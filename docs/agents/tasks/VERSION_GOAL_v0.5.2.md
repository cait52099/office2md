# Version Goal — v0.5.2

## Version

v0.5.2

## Goal

Improve the local version workflow so one small version can be planned, executed, reviewed, and locally committed through a file-driven process.

This version should not add product features. It should harden the agent workflow itself.

## Why This Matters

The project now needs repeatable small-version upgrades without manually writing a new prompt at every step. The workflow should support Codex App use and, when available, Codex CLI automation.

## Scope

Allowed changes:
- add version workflow documentation
- add a machine-readable version workflow queue
- add Codex App prompt for running a version workflow
- add optional CLI runner script for one-version automation
- update AGENTS.md with version workflow policy if needed

Expected files or areas:
- `AGENTS.md`
- `docs/agents/version_workflow.md`
- `docs/agents/version_queue.json`
- `docs/agents/tasks/VERSION_GOAL_TEMPLATE.md`
- `scripts/codex_app_run_version_prompt.md`
- `scripts/agent_run_version.sh`
- Obsidian workflow/release notes

## Non-goals

Do not:
- implement product feature changes
- change conversion behavior
- change build-library behavior
- change search/ranking/aliases/token fallback
- change runner process-control behavior
- change GUI behavior
- change Agent Gateway or MCP behavior
- modify source files or Knowledge Packs
- tag
- push

## Commit Policy

- final local commit only
- no checkpoint commits
- no tag
- no push

Commit message:

```text
Release v0.5.2
```

## Validation

Required:

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

## Smoke Tests

- Confirm `version_queue.json` parses.
- Confirm version workflow paths use repo root `/Volumes/seagate 2t/offic2md/repo` and vault `/Volumes/seagate 2t/offic2md/office2md-vault`.
- Confirm the Codex App prompt does not hardcode one old task number.
- Confirm final workflow policy says no tag and no push.

## Final Report Path

```text
/Volumes/seagate 2t/offic2md/office2md-vault/50_Releases/2026-05-31 v0.5.2 Local Commit.md
```
