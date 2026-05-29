# Incremental Knowledge Base Foundation

v0.4.6 keeps the incremental workflow explicit: source registry, library state, and change plan files are inspectable UTF-8 JSON artifacts.

It does not update the library. It does not run conversion. It does not rebuild `library.db`.

## Save a Source Registry

Save the default registry under the library folder:

```powershell
python -m office2md.cli source-registry .\library --save
```

Export to a chosen path:

```powershell
python -m office2md.cli source-registry .\library --export-json .\registry\source_registry.json
```

Print JSON without writing:

```powershell
python -m office2md.cli source-registry .\library --json
```

## Check Library Status

```powershell
python -m office2md.cli library-status .\library
```

JSON output:

```powershell
python -m office2md.cli library-status .\library --json
```

Write an explicit state snapshot:

```powershell
python -m office2md.cli library-status .\library --write-state
```

Use a specific registry, state file, or change plan:

```powershell
python -m office2md.cli library-status .\library --registry .\source_registry.json --state .\library_state.json --change-plan .\change_plan.json
```

Status values:

- `current`: registered sources still match their recorded size, mtime, and checksum
- `stale`: registered sources changed, disappeared, or a change plan has pending changes
- `unknown`: no registry or source information is available

## Scan for Changes

Dry-run:

```powershell
python -m office2md.cli scan-changes .\source .\library --dry-run
```

Write a change plan:

```powershell
python -m office2md.cli scan-changes .\source .\library --export-json .\change_plan.json
```

`scan-changes` classifies files as:

- `new`
- `modified`
- `unchanged`
- `deleted_missing`
- `moved_or_renamed_candidate`
- `unsupported`
- `stale`

The command does not modify source files, conversion output, Knowledge Packs, `library.db`, search indexes, or graph files.

## Source Registry

The source registry is expected at:

```text
library/source_registry.json
```

It records normalized source paths, size, `mtime_ns`, SHA-256, converter/profile metadata where available, Knowledge Pack paths, manifest paths, and status.

If the registry is missing, status and scan commands can derive a best-effort registry from the current built library documents.

## Library State

The library state snapshot is expected at:

```text
library/library_state.json
```

It uses schema `office2md.library_state.v1` and records current/stale/unknown status, source registry presence, library DB hash when available, counts, warnings, and pending change summary if a change plan is provided.

It is a snapshot only. Refresh it before agent use.

## Explicit Update Library

v0.4.7 adds an explicit update command:

```powershell
python -m office2md.cli update-library .\source .\conversion-output .\library
```

Preview first:

```powershell
python -m office2md.cli update-library .\source .\conversion-output .\library --dry-run
```

Use or write a plan:

```powershell
python -m office2md.cli update-library .\source .\conversion-output .\library --change-plan .\change_plan.json
python -m office2md.cli update-library .\source .\conversion-output .\library --export-plan .\change_plan.json
```

`update-library` converts only `new` and `modified` files. It reuses unchanged valid Knowledge Packs, records `deleted_missing` and `stale` sources in `update_result.json`, and does not delete old evidence.

After a successful update, it rebuilds `library.db`, `library_index.json`, and `library_graph.json` using the existing `build_library()` path, then refreshes `source_registry.json` and `library_state.json`.

`update_result.json` uses schema:

```text
office2md.update_result.v1
```

## Agent Guidance

Agents must not assume new raw files are searchable until the scan/update workflow is run.

Use the built library commands for evidence already present:

```powershell
python -m office2md.cli search-library .\library\library.db "query"
python -m office2md.cli open-chunk .\library CHUNK_ID --export-json .\open_chunk.json
python -m office2md.cli build-report-context .\library "query" --export-json .\report_context.json
```

Use `change_plan.json` only as pending-work status. It is not evidence from the Knowledge Library.

Before answering, agents should check `library-status` and, when stale or unknown, inspect `source_registry.json`, `library_state.json`, and `change_plan.json`.

## Non-Goals

This foundation does not include row-level SQLite incremental updates, automatic deletion of evidence, a background watcher, MCP, embeddings, OCR, Obsidian plugin work, write-back, unrestricted SQL, shell execution, or OfficeCLI main-pipeline integration.

See `docs/design/v046_update_library_contract.md` for the original update contract and `docs/design/v047_explicit_update_library_mvp.md` for the MVP execution design.
