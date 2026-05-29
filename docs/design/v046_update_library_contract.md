# v0.4.6 Source Registry Persistence and Update Plan Foundation

## Purpose

v0.4.6 strengthens the incremental foundation by making registry, state, and change plan files explicit artifacts that agents and humans can inspect before deciding whether a library is current.

This is still not an update execution release. It does not implement `update-library`, row-level SQLite updates, automatic deletion, or a watcher.

## Explicit Files

All files are UTF-8 pretty JSON and parent directories are created when writing.

```text
library/
  source_registry.json
  library_state.json
  change_plan.json
```

### source_registry.json

Schema:

```text
office2md.source_registry.v1
```

The registry records the source files known to a built library:

- normalized source path;
- source path and relative path;
- file name and extension;
- size;
- `mtime_ns`;
- SHA-256;
- converter/profile metadata where available;
- Knowledge Pack path;
- manifest path;
- status.

### library_state.json

Schema:

```text
office2md.library_state.v1
```

The library state file is a snapshot of `library-status`. It records the status, counts, pending changes if provided, source registry path, and library DB hash when available.

It is not evidence and it is not an update operation. Agents should refresh status/scan before relying on an old state snapshot.

### change_plan.json

Schema:

```text
office2md.change_plan.v1
```

The change plan records pending source changes:

- `new`;
- `modified`;
- `unchanged`;
- `deleted_missing`;
- `moved_or_renamed_candidate`;
- `unsupported`;
- `stale`.

Deleted/missing sources are marked and preserved in the plan. They are not automatically removed from the library. Moved/renamed matches are checksum-based candidates, not authoritative edits.

## CLI Foundation

```powershell
python -m office2md.cli source-registry LIBRARY_PATH --save
python -m office2md.cli source-registry LIBRARY_PATH --export-json registry.json
python -m office2md.cli library-status LIBRARY_PATH --write-state
python -m office2md.cli scan-changes SOURCE_PATH LIBRARY_PATH --export-json change_plan.json
python -m office2md.cli library-status LIBRARY_PATH --change-plan change_plan.json
```

`library-status` reads registry/state/change plan signals when available and reports `current`, `stale`, or `unknown`.

## Agent Contract

Agents must determine whether raw sources have pending changes before answering:

1. Run or inspect `library-status`.
2. If status is `unknown` or `stale`, inspect `source_registry.json`, `library_state.json`, and/or `change_plan.json`.
3. Treat `change_plan.json` as pending-work status, not library evidence.
4. Use `search-library`, `open-chunk`, `locate-document`, or `build-report-context` only for facts already present in the built library.

## update-library Contract

v0.4.7 implements the first explicit MVP of this contract. The command:

- accepts an explicit `change_plan.json` or scans first;
- rebuilds Knowledge Packs for `new` and `modified` files;
- preserves deleted/missing evidence and records it in `update_result.json`;
- records stale sources for review rather than converting them automatically;
- treats moved/renamed candidates as review items and reuses existing packs;
- rebuilds the library through controlled existing build paths;
- writes an update result and refreshes source registry/library state after success.

## Non-Goals

v0.4.6 does not include:

- `update-library` execution;
- row-level SQLite incremental update;
- automatic deletion of evidence;
- watcher or background update;
- conversion behavior changes;
- build-library behavior changes;
- search ranking, alias, or token fallback changes;
- open-chunk / locate-document / build-report-context behavior changes;
- runner changes;
- workspace changes;
- GUI changes;
- OfficeCLI pipeline integration;
- MCP implementation;
- embeddings or vector search;
- OCR;
- Obsidian plugin;
- write-back;
- unrestricted SQL;
- shell execution.

OfficeCLI remains `diagnostic_only`.
