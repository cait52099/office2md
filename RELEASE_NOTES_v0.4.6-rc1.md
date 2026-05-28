# office2md v0.4.6-rc1 Release Notes

Status: release candidate for v0.4.6 Source Registry Persistence and Update Plan Foundation.

## Scope

v0.4.6-rc1 makes incremental status artifacts explicit and persistent:

- `source-registry` CLI;
- `source_registry.json` save/export/JSON workflow;
- `library_state.json` schema and helpers;
- `library-status --write-state`;
- additive state fields in `library-status`;
- update-library contract docs only;
- docs and tests for registry, state, plan, and status behavior.

## Source Registry Persistence

New command:

```powershell
python -m office2md.cli source-registry LIBRARY_PATH --save
python -m office2md.cli source-registry LIBRARY_PATH --export-json source_registry.json
python -m office2md.cli source-registry LIBRARY_PATH --json
```

`source-registry` writes only when `--save` or `--export-json` is explicit.

The registry schema remains:

```text
office2md.source_registry.v1
```

## Library State

New state schema:

```text
office2md.library_state.v1
```

`library-status` can now write an explicit state snapshot:

```powershell
python -m office2md.cli library-status LIBRARY_PATH --write-state
```

It can also read explicit registry, state, and change plan files:

```powershell
python -m office2md.cli library-status LIBRARY_PATH --registry source_registry.json --state library_state.json --change-plan change_plan.json
```

The `library-status` JSON schema remains compatible as `office2md.library_status.v1`; new state fields are additive.

## Change Plan Compatibility

`change_plan.json` remains schema-compatible:

```text
office2md.change_plan.v1
```

Deleted/missing sources are marked rather than removed. Moved/renamed matches remain checksum-based candidates.

## Update-Library Contract Docs

`docs/design/v046_update_library_contract.md` documents a future update contract only. This checkpoint does not implement update execution.

## Real-Source Smoke

Real-source smoke against `C:\Users\hcai\Desktop\test` confirmed:

- source folder snapshot remained unchanged;
- `source_registry.json` parsed with schema `office2md.source_registry.v1`;
- `scan-changes --dry-run --json` parsed with schema `office2md.change_plan.v1`;
- `scan-changes --export-json` wrote parseable UTF-8 JSON;
- `library_state.json` parsed with schema `office2md.library_state.v1`;
- temporary PPTX library state classified 3 PPTX files as unchanged and 73 PPTX files as new.

## Non-Goals

This checkpoint does not include:

- `update-library` execution;
- row-level SQLite incremental update;
- automatic deletion;
- watcher or background update;
- source file modification;
- conversion output modification;
- library DB/index/graph/evidence modification;
- conversion behavior changes;
- build-library behavior changes;
- search ranking, alias, or token fallback changes;
- open-chunk, locate-document, or build-report-context behavior changes;
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
- `python -m office2md.cli source-registry --help`
- `python -m office2md.cli library-status --help`
- `python -m office2md.cli scan-changes --help`

