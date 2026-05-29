# v0.4.9 Agent Gateway Simplification

## Purpose

v0.4.9 adds a small read-only agent gateway so users and agents do not need to manually chain:

```text
library-catalog -> library-status -> search-library -> open-chunk -> build-report-context
```

The gateway is an orchestration layer over existing helpers. It does not change conversion, build-library, search ranking, update execution, workspace behavior, GUI behavior, or OfficeCLI status.

## Commands

```powershell
python -m office2md.cli kb-list CATALOG --json
python -m office2md.cli kb-context CATALOG "query" --library LIBRARY_ID
python -m office2md.cli kb-context CATALOG "query" --libraries LIB_A,LIB_B
python -m office2md.cli kb-review CATALOG LIBRARY_ID
```

## Agent Context Schema

`kb-context` returns:

```text
office2md.agent_context.v1
```

Top-level fields:

- `request`;
- `selected_libraries`;
- `library_status`;
- `evidence`;
- `supporting_chunks`;
- `limitations`;
- `warnings`;
- `next_steps`.

Each evidence item includes, where available:

- `library_id`;
- `library_name`;
- `library_path`;
- `source_file`;
- `locator`;
- `chunk_id`;
- `document_id`;
- `document_title`;
- `document_kind`;
- `evidence_type`;
- `confidence`;
- `limitation`.

## Stale Libraries

If a selected library is stale or unknown, the gateway returns warnings and next steps. It does not update libraries automatically.

## Multi-library Behavior

Multi-library context preserves per-library provenance. Search is still executed against each selected library using the existing single-library search helper, so single-library ranking and token fallback behavior are unchanged.

## kb-review

`kb-review` summarizes update readiness for one registered library. It uses catalog metadata and existing status/update review helpers in dry-run mode only. It never runs update execution and does not write update artifacts.

## Non-Goals

v0.4.9 does not include:

- MCP implementation;
- AI-generated final answers;
- conversion behavior changes;
- build-library behavior changes;
- search ranking, aliases, or token fallback changes;
- open-chunk, locate-document, or build-report-context JSON behavior changes;
- update-library execution semantic changes;
- runner, workspace, or GUI behavior changes;
- OfficeCLI main-pipeline integration;
- embeddings or vector search;
- OCR;
- Obsidian plugin;
- write-back;
- unrestricted SQL;
- shell execution;
- automatic update;
- automatic deletion;
- watcher or background process.

OfficeCLI remains `diagnostic_only`.
