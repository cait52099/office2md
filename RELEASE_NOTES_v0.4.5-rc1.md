# office2md v0.4.5-rc1 Release Notes

Status: release candidate for v0.4.5 Incremental Knowledge Base Foundation.

## Scope

v0.4.5-rc1 adds a conservative read-only foundation for detecting whether a built Knowledge Library may be stale relative to raw source files:

- source registry helpers;
- `library-status` CLI;
- `scan-changes` CLI;
- `change_plan.json` export;
- incremental update design and usage docs;
- tests for registry, change classification, status reporting, and unchanged search/open-chunk behavior.

## Source Registry

The source registry schema is `office2md.source_registry.v1`.

Source records track, where available:

- normalized source path;
- source path and relative path;
- file name and extension;
- size;
- `mtime_ns`;
- SHA-256;
- converter and profile metadata;
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

It can also emit JSON:

```powershell
python -m office2md.cli library-status LIBRARY_PATH --json
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

It is read-only by default. The only write behavior in this checkpoint is explicit `change_plan.json` export:

```powershell
python -m office2md.cli scan-changes SOURCE_PATH LIBRARY_PATH --export-json change_plan.json
```

The change plan schema is `office2md.change_plan.v1`.

## Agent Guidance

Agents must not assume new raw files are searchable until an explicit scan/update workflow has been run. `change_plan.json` is pending-work status, not evidence from the built Knowledge Library.

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
- `python -m office2md.cli --help`
- `python -m office2md.cli library-status --help`
- `python -m office2md.cli scan-changes --help`
- `python -m office2md.cli search-library --help`
- `python -m office2md.cli open-chunk --help`

