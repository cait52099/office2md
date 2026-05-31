# office2md v0.5.1 Release Notes

Status: final v0.5.1 release.

## Scope

v0.5.1 is a focused stabilization release covering the macOS validation baseline and local agent workflow reliability.

From `v0.5.1-rc1`:

- restores the macOS validation baseline;
- fixes incremental path normalization so source-path comparison keys are case-insensitive on macOS;
- keeps moved/renamed candidate detection checksum-based after path matching;
- adds focused incremental regression coverage;
- adds `pyvis` to the dev extra for the full local validation baseline.

From `v0.5.1-rc2`:

- hardens the Codex App task workflow;
- clarifies workspace root, repository root, and Obsidian vault paths;
- clarifies the `docs/agents/agent_queue.json` workflow;
- updates the Codex App prompt so it no longer hardcodes an old task;
- updates `scripts/agent_run_next.sh` so it derives the repository root from its script location while preserving `PROJECT_ROOT` override support.

## Safety

This release does not change:

- conversion behavior;
- build-library behavior;
- search ranking, aliases, or token fallback;
- runner process-control behavior;
- GUI behavior;
- Agent Gateway or MCP behavior;
- source files or Knowledge Packs.

## Validation

- `.venv/bin/python -m pytest`
- `.venv/bin/python -m ruff check .`
- `.venv/bin/python -m compileall office2md/gui`
- `.venv/bin/python -m office2md.cli --help`
- `.venv/bin/python -m office2md.cli scan-changes --help`
- `.venv/bin/python -m office2md.cli update-library --help`
- `.venv/bin/python -m office2md.cli library-status --help`
- `.venv/bin/python -m json.tool docs/agents/agent_queue.json`
- `bash -n scripts/agent_run_next.sh`

## Release Metadata

- `pyproject.toml` version: `0.5.1`
- `office2md/__init__.py` version: `0.5.1`
