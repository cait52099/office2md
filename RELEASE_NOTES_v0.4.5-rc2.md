# office2md v0.4.5-rc2 Release Notes

Status: release candidate for v0.4.5 Windows-safe JSON console output polish.

## Scope

v0.4.5-rc2 fixes a Windows console encoding issue found during real-source smoke testing:

- `scan-changes --dry-run --json` could fail on a GBK console when printing large JSON containing non-ASCII paths.
- JSON file export already wrote UTF-8 correctly and remains unchanged.

## Fix

CLI JSON-only output now uses a shared safe JSON print helper. When available, it writes UTF-8 bytes directly to `stdout.buffer`, avoiding Windows console text encoding failures.

The same safe JSON print path is used by:

- `scan-changes --json`;
- `library-status --json`;
- other CLI JSON-only summary output paths.

## Unchanged Behavior

This checkpoint does not change:

- scan classification logic;
- source registry schema;
- `change_plan.json` schema;
- `library-status` semantics;
- `--export-json` UTF-8 pretty JSON file behavior;
- parent directory creation for JSON exports.

## Real-Source Smoke

Real-source smoke against `C:\Users\hcai\Desktop\test` confirmed:

- `scan-changes --dry-run --json` succeeds and parses;
- `scan-changes --export-json` still writes parseable UTF-8 JSON;
- source folder snapshot is unchanged;
- `library-status --json` returns schema `office2md.library_status.v1`;
- `scan-changes` returns schema `office2md.change_plan.v1`.

The real source folder contained 1216 files, including 76 PPTX files. The smoke classified the temporary PPTX library state as 3 unchanged PPTX files and 73 new PPTX files.

## Non-Goals

This checkpoint does not include:

- source file modification;
- conversion output modification;
- library DB/index/graph/evidence modification;
- `update-library`;
- row-level SQLite incremental update;
- automatic deletion;
- watcher or background update;
- conversion behavior changes;
- build-library behavior changes;
- search ranking, alias, or token fallback changes;
- runner changes;
- workspace changes;
- GUI changes;
- MCP implementation;
- embeddings or vector search;
- OCR;
- Obsidian plugin;
- write-back;
- unrestricted SQL;
- shell execution.

OfficeCLI remains `diagnostic_only`.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- `python -m office2md.cli scan-changes --help`
- `python -m office2md.cli library-status --help`

