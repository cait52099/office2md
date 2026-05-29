# v0.4.7 Explicit update-library MVP

## Purpose

v0.4.7 adds an explicit, plan-first `update-library` workflow on top of the v0.4.5/v0.4.6 incremental foundation.

The goal is to let a human or agent safely refresh a built Knowledge Library after source files change, without adding automatic watchers, row-level SQLite updates, or source-file modification.

## Command

```powershell
python -m office2md.cli update-library SOURCE_PATH CONVERSION_OUTPUT LIBRARY_PATH
```

Useful options:

```powershell
python -m office2md.cli update-library SOURCE_PATH CONVERSION_OUTPUT LIBRARY_PATH --dry-run
python -m office2md.cli update-library SOURCE_PATH CONVERSION_OUTPUT LIBRARY_PATH --change-plan change_plan.json
python -m office2md.cli update-library SOURCE_PATH CONVERSION_OUTPUT LIBRARY_PATH --export-plan change_plan.json
python -m office2md.cli update-library SOURCE_PATH CONVERSION_OUTPUT LIBRARY_PATH --update-result-json update_result.json
```

## Workflow

1. Load an explicit `change_plan.json`, or run the same scan logic used by `scan-changes`.
2. Convert only `new` and `modified` source files through existing conversion code paths.
3. Reuse unchanged valid Knowledge Packs.
4. Preserve `deleted_missing` evidence and record missing sources in `update_result.json`.
5. Rebuild `library.db`, `library_index.json`, and `library_graph.json` using existing `build_library()` behavior.
6. Write `update_result.json`.
7. Refresh `source_registry.json` and `library_state.json` after a successful update.

## update_result.json

Schema:

```text
office2md.update_result.v1
```

The result records:

- source path;
- conversion output path;
- library path;
- dry-run status;
- change plan schema and counts;
- planned conversions and reused packs;
- converted files;
- missing sources;
- unsupported sources;
- rebuilt library summary;
- written registry/state/result files;
- warnings and limitations.

## Safety Rules

- `update-library` never runs automatically.
- `--dry-run` does not write conversion output, library files, registry, state, or update result.
- Source files are never modified.
- Deleted or missing sources are marked, not deleted from evidence.
- Stale sources are recorded for review and are not converted automatically.
- Existing conversion and `build_library()` paths are reused.
- Search ranking, aliases, token fallback, open-chunk, locate-document, build-report-context, workspace, GUI, and OfficeCLI status are unchanged.

## Non-Goals

v0.4.7 does not include:

- background watcher;
- automatic update;
- automatic deletion of old evidence;
- row-level SQLite incremental UPSERT;
- unrestricted shell execution;
- MCP;
- embeddings or vector search;
- OCR;
- Obsidian plugin;
- write-back;
- OfficeCLI main-pipeline integration.

OfficeCLI remains `diagnostic_only`.
