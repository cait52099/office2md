# v0.4.5 Incremental Knowledge Base Foundation

## Purpose

office2md needs an incremental foundation so users and agents can tell whether a built Knowledge Library is current relative to raw source files.

This checkpoint is intentionally conservative. It adds a registry/status/scan foundation only. It does not implement update-library, row-level SQLite updates, background watching, or automatic deletion of evidence.

## Problem

Today the workflow is explicit:

```text
raw source files -> convert -> Knowledge Packs -> build-library -> library.db
```

If new raw files are added later, agents must not assume those files are visible in search, `open-chunk`, `locate-document`, or `build-report-context`. The library only knows what has been converted and built.

## Source Registry

The proposed source registry records source file state associated with a built library:

```text
library/
  source_registry.json
```

Schema version:

```text
office2md.source_registry.v1
```

Each source record should include, where available:

- `source_id`
- `normalized_source_path`
- `source_path`
- `relative_path`
- `source_file`
- `extension`
- `size`
- `mtime_ns`
- `sha256`
- `converter`
- `converter_version`
- `profile`
- `knowledge_pack_path`
- `manifest_path`
- `status`
- `registered_at`

The registry is a traceability index. It is not a replacement for conversion manifests, Knowledge Packs, `library.db`, or workspace manifests.

## Change Plan

`scan-changes` compares a source folder against registry/library state and can write:

```text
change_plan.json
```

Schema version:

```text
office2md.change_plan.v1
```

Classifications:

- `new`: supported source file not present in the registry
- `modified`: registered source file has changed size, mtime, or checksum
- `unchanged`: registered source file appears unchanged
- `deleted_missing`: registered source file is no longer found
- `moved_or_renamed_candidate`: checksum matches a registered source at a different path
- `unsupported`: file exists but is not a supported conversion input
- `stale`: registered source exists but associated Knowledge Pack evidence is missing

Moved/renamed detection is advisory and checksum-based.

## CLI Foundation

```powershell
python -m office2md.cli library-status LIBRARY_PATH
python -m office2md.cli scan-changes SOURCE_PATH LIBRARY_PATH --dry-run
python -m office2md.cli scan-changes SOURCE_PATH LIBRARY_PATH --export-json change_plan.json
```

`library-status` is read-only. It reports whether a library is `current`, `stale`, or `unknown` based on the source registry, library documents, and optional change plan.

`scan-changes` is read-only unless explicitly writing `change_plan.json`. It does not modify source files, conversion output, Knowledge Packs, `library.db`, search indexes, or graph files.

## Agent Rules

Agents must not assume a new raw file is searchable just because it exists on disk.

Agent-safe behavior:

1. Check `library-status`.
2. If status is stale or unknown, run or request `scan-changes`.
3. Treat `change_plan.json` as a pending-work plan, not searchable evidence.
4. Use `search-library`, `open-chunk`, `locate-document`, and `build-report-context` only for evidence that is already in the built library.

## Non-Goals

v0.4.5 does not include:

- conversion behavior changes
- build-library behavior changes
- search ranking, alias, or token fallback changes
- open-chunk / locate-document / build-report-context JSON changes
- runner changes
- workspace changes
- GUI changes
- OfficeCLI pipeline integration
- MCP implementation
- embeddings or vector search
- OCR
- Obsidian plugin
- write-back
- unrestricted SQL
- shell execution
- `update-library`
- row-level SQLite incremental update
- automatic deletion of evidence
- background watcher

OfficeCLI remains `diagnostic_only`.

## Future Work

Future versions can use this foundation to design:

- explicit `update-library` workflows
- source-to-Knowledge-Pack rebuild planning
- stale evidence review
- GUI status surfaces
- read-only MCP exposure of status and change plans

