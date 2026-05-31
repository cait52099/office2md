# office2md v0.5.1-rc2 Release Notes

Status: release candidate for v0.5.1.

## Scope

v0.5.1-rc2 hardens the local Codex App task workflow:

- clarifies workspace root versus repository root in agent guidance;
- points the agent queue at the actual local repository root;
- adds a concise Execution Agent workflow guide;
- makes the CLI helper derive its default repository root from the script location while preserving `PROJECT_ROOT` override support;
- updates the reusable Codex App prompt to run the first `ready_for_execution` task from the queue instead of a stale hardcoded task ID;
- records Task 0004 as completed after validation passed.

## Safety

This release candidate does not change:

- conversion behavior;
- build-library behavior;
- search ranking, aliases, or token fallback;
- runner process-control behavior;
- GUI behavior;
- Agent Gateway or MCP behavior;
- source files or Knowledge Packs.

## Smoke

Workflow smoke confirmed:

- `docs/agents/agent_queue.json` parses as JSON;
- Task 0004 was the single ready task before completion and its task file existed;
- `scripts/agent_run_next.sh` resolves the default repository root to `/Volumes/seagate 2t/offic2md/repo`;
- `scripts/codex_app_run_next_prompt.md` no longer names completed task `0002` as the current task;
- no commit, tag, push, product conversion, source modification, or Knowledge Pack modification occurred during execution.

## Validation

- `.venv/bin/python -m pytest`
- `.venv/bin/python -m ruff check .`
- `.venv/bin/python -m compileall office2md/gui`
- `.venv/bin/python -m office2md.cli --help`
- `.venv/bin/python -m json.tool docs/agents/agent_queue.json`
- `bash -n scripts/agent_run_next.sh`
