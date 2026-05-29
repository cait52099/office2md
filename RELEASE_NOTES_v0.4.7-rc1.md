# office2md v0.4.7-rc1 Release Notes

Status: release candidate for v0.4.7 Explicit update-library MVP.

## Scope

v0.4.7-rc1 adds an explicit, plan-first library update workflow:

- `update-library` CLI;
- `update_result.json` schema `office2md.update_result.v1`;
- dry-run behavior that does not write conversion output, library output, registry/state, or update result files;
- conversion of `new` and `modified` files only;
- reuse of unchanged valid Knowledge Packs;
- recording of `deleted_missing` and `stale` sources without deleting evidence;
- library rebuild through existing `build_library()`;
- refresh of `source_registry.json` and `library_state.json` after successful update;
- docs and tests for the explicit update MVP.

## Command

```powershell
python -m office2md.cli update-library SOURCE_PATH CONVERSION_OUTPUT LIBRARY_PATH --dry-run
python -m office2md.cli update-library SOURCE_PATH CONVERSION_OUTPUT LIBRARY_PATH
```

Optional plan/result paths:

```powershell
python -m office2md.cli update-library SOURCE_PATH CONVERSION_OUTPUT LIBRARY_PATH --change-plan change_plan.json
python -m office2md.cli update-library SOURCE_PATH CONVERSION_OUTPUT LIBRARY_PATH --export-plan change_plan.json
python -m office2md.cli update-library SOURCE_PATH CONVERSION_OUTPUT LIBRARY_PATH --update-result-json update_result.json
```

## Safety

- Update execution occurs only when `update-library` is explicitly run without `--dry-run`.
- Source files are never modified.
- Deleted/missing evidence is not automatically deleted.
- No row-level SQLite incremental update is implemented.
- Existing conversion and `build_library()` paths are reused.
- Search ranking, aliases, token fallback, open-chunk, locate-document, build-report-context, runner, workspace, and GUI behavior are unchanged.
- OfficeCLI remains `diagnostic_only`.

## Smoke

Temp-only smoke confirmed:

- `--dry-run` wrote no `update_result.json`;
- real temp update converted 2 files;
- unchanged Knowledge Pack reuse count was 1;
- one deleted/missing source was recorded;
- `update_result.json` parsed with schema `office2md.update_result.v1`;
- `source_registry.json` and `library_state.json` were refreshed;
- rebuilt library search found newly added evidence;
- `open-chunk` worked on the rebuilt library.

## Non-Goals

This checkpoint does not include:

- automatic update;
- background watcher;
- source file modification;
- automatic deletion of old evidence;
- row-level SQLite incremental UPSERT;
- unrestricted shell execution;
- MCP;
- embeddings or vector search;
- OCR;
- Obsidian plugin;
- write-back;
- OfficeCLI main-pipeline integration.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- `python -m compileall office2md/gui`
- `python -m office2md.cli --help`
- `python -m office2md.cli update-library --help`
- `python -m office2md.cli scan-changes --help`
- `python -m office2md.cli source-registry --help`
- `python -m office2md.cli library-status --help`
- `python -m office2md.cli search-library --help`
- `python -m office2md.cli open-chunk --help`
