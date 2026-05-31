# office2md v0.5.1-rc1 Release Notes

Status: release candidate for v0.5.1.

## Scope

v0.5.1-rc1 restores the macOS validation baseline for incremental library workflows:

- normalizes incremental source-path comparison keys case-insensitively on macOS;
- keeps moved/renamed candidate detection checksum-based after path matching;
- adds focused regression coverage for macOS path-key normalization;
- adds `pyvis` to the dev extra so full local validation includes the existing graph-related test dependency;
- includes project agent workflow files for repeatable execution/review coordination.

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

Focused temp-folder smoke confirmed:

- macOS path-case normalization classifies matching source records as unchanged;
- `scan-changes` JSON export writes parseable UTF-8 JSON;
- dry-run with `--export-json` does not write a change plan;
- source checksums are unchanged by scan operations;
- moved/renamed files with matching checksums classify as `moved_or_renamed_candidate`.

## Validation

- `.venv/bin/python -m pytest`
- `.venv/bin/python -m ruff check .`
- `.venv/bin/python -m compileall office2md/gui`
- `.venv/bin/python -m office2md.cli --help`
- `.venv/bin/python -m office2md.cli scan-changes --help`
- `.venv/bin/python -m office2md.cli update-library --help`
- `.venv/bin/python -m office2md.cli library-status --help`

Note: bare `python` is not available on this macOS shell PATH; validation was run with the project virtualenv Python.
