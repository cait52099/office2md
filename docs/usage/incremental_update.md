# Incremental Knowledge Base Foundation

v0.4.5 adds read-only status and scan commands for checking whether a built Knowledge Library may be stale relative to raw source files.

It does not update the library. It does not run conversion. It does not rebuild `library.db`.

## Check Library Status

```powershell
python -m office2md.cli library-status .\library
```

JSON output:

```powershell
python -m office2md.cli library-status .\library --json
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

## Agent Guidance

Agents must not assume new raw files are searchable until the scan/update workflow is run.

Use the built library commands for evidence already present:

```powershell
python -m office2md.cli search-library .\library\library.db "query"
python -m office2md.cli open-chunk .\library CHUNK_ID --export-json .\open_chunk.json
python -m office2md.cli build-report-context .\library "query" --export-json .\report_context.json
```

Use `change_plan.json` only as pending-work status. It is not evidence from the Knowledge Library.

## Non-Goals

This foundation does not include `update-library`, row-level SQLite incremental updates, automatic deletion of evidence, a background watcher, MCP, embeddings, OCR, Obsidian plugin work, write-back, unrestricted SQL, shell execution, or OfficeCLI main-pipeline integration.

