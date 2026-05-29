# office2md v0.4.7 Release Notes

Status: final v0.4.7 release.

## Scope

v0.4.7 adds the Explicit `update-library` MVP:

- `update-library` CLI;
- dry-run / plan-first workflow;
- conversion of `new` and `modified` files only;
- reuse of unchanged valid Knowledge Packs;
- recording of `deleted_missing` and `stale` sources without deleting evidence;
- rebuild of `library.db`, `library_index.json`, and `library_graph.json` using existing `build_library()`;
- `update_result.json` schema `office2md.update_result.v1`;
- refresh of `source_registry.json` and `library_state.json` after successful update;
- docs and tests for explicit update behavior.

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
- `--dry-run` writes no `update_result.json`.
- Source files are never modified.
- Deleted/missing evidence is not automatically deleted.
- No row-level SQLite incremental update is implemented.
- No watcher or background update is implemented.
- Existing conversion and `build_library()` paths are reused.
- Search ranking, aliases, token fallback, open-chunk, locate-document, build-report-context, runner, workspace, and GUI behavior are unchanged.
- OfficeCLI remains `diagnostic_only`.

## Smoke

Temp update smoke confirmed:

- `--dry-run` wrote no `update_result.json`;
- real temp update converted 2 files;
- unchanged Knowledge Pack reuse count was 1;
- one deleted/missing source was recorded;
- `update_result.json` parsed with schema `office2md.update_result.v1`;
- `source_registry.json` and `library_state.json` were refreshed;
- rebuilt library search found newly added evidence;
- `open-chunk` worked on the rebuilt library.

Real-source dry-run smoke against `C:\Users\hcai\Desktop\test` confirmed:

- source snapshot remained unchanged;
- 1216 source files were scanned;
- 76 PPTX files were present;
- change plan counts were `new=667`, `modified=0`, `unchanged=3`, `deleted_missing=0`, `moved_or_renamed_candidate=0`, `unsupported=546`, `stale=0`;
- PPTX classifications were `unchanged=3`, `new=73`;
- `source_registry.json`, `change_plan.json`, and `library-status --json` schemas parsed;
- `update-library --dry-run` wrote no `update_result.json`;
- dry-run did not modify temp conversion or temp library output.

## Non-Goals

This release does not include:

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
