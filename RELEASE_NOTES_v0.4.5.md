# office2md v0.4.5 Release Notes

Status: final v0.4.5 release.

## Scope

v0.4.5 adds the Incremental Knowledge Base Foundation:

- source registry helpers;
- `library-status` CLI;
- `scan-changes` CLI;
- `change_plan.json` export;
- Windows-safe JSON console output for `--json`;
- incremental update design and usage docs;
- real-source smoke validation against `C:\Users\hcai\Desktop\test`.

## Source Registry

The source registry schema is:

```text
office2md.source_registry.v1
```

Source records track, where available:

- normalized source path;
- source path and relative path;
- file name and extension;
- size;
- `mtime_ns`;
- SHA-256;
- converter/profile metadata;
- Knowledge Pack path;
- manifest path;
- status.

If `source_registry.json` is missing, `library-status` and `scan-changes` can derive a best-effort registry from the built library document table.

## Library Status

New command:

```powershell
python -m office2md.cli library-status LIBRARY_PATH
```

The command is read-only and reports `current`, `stale`, or `unknown`.

JSON output uses schema:

```text
office2md.library_status.v1
```

## Scan Changes

New command:

```powershell
python -m office2md.cli scan-changes SOURCE_PATH LIBRARY_PATH --dry-run
```

`scan-changes` compares source files against registry/library state and classifies:

- `new`;
- `modified`;
- `unchanged`;
- `deleted_missing`;
- `moved_or_renamed_candidate`;
- `unsupported`;
- `stale`.

It is read-only except explicit change plan export:

```powershell
python -m office2md.cli scan-changes SOURCE_PATH LIBRARY_PATH --export-json change_plan.json
```

The change plan schema is:

```text
office2md.change_plan.v1
```

`--export-json` remains UTF-8 pretty JSON and creates parent directories.

## Windows-Safe JSON Output

CLI JSON-only output now writes UTF-8 bytes through `stdout.buffer` when available. This avoids Windows GBK console `UnicodeEncodeError` failures for large JSON payloads with non-ASCII paths.

This covers:

- `scan-changes --json`;
- `library-status --json`;
- other CLI JSON-only summary output paths.

## Real-Source Smoke

Real-source smoke against `C:\Users\hcai\Desktop\test` confirmed:

- source folder snapshot remained unchanged;
- `library-status --json` parsed with schema `office2md.library_status.v1`;
- `scan-changes --dry-run --json` parsed with schema `office2md.change_plan.v1`;
- `scan-changes --export-json` wrote parseable UTF-8 JSON;
- source folder contained 1216 files and 76 PPTX files;
- temporary PPTX library state classified 3 PPTX files as unchanged and 73 PPTX files as new.

## Non-Goals

This release does not include:

- `update-library`;
- row-level SQLite incremental update;
- automatic deletion of evidence;
- watcher or background update;
- source file modification;
- conversion output modification;
- library DB/index/graph/evidence modification;
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
- `python -m compileall office2md/gui`
- `python -m office2md.cli --help`
- `python -m office2md.cli library-status --help`
- `python -m office2md.cli scan-changes --help`
- `python -m office2md.cli search-library --help`
- `python -m office2md.cli open-chunk --help`
- `python -m office2md.cli locate-document --help`
- `python -m office2md.cli build-report-context --help`
