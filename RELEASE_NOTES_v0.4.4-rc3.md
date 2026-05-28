# office2md v0.4.4-rc3 Release Notes

Status: release candidate for v0.4.4 agent JSON completion.

## Scope

v0.4.4-rc3 completes the first agent-ready JSON command set:

- `locate-document --export-json PATH`;
- `build-report-context` read-only CLI;
- docs and tests for the new JSON contracts.

## Locate Document JSON

`locate-document` now supports:

```powershell
python -m office2md.cli locate-document LIBRARY_DB_OR_DIR QUERY --export-json documents.json
```

The JSON schema is `office2md.locate_document.v1` and includes:

- `request`;
- `matches`;
- `limitations`;
- `warnings`.

`locate-document` matching, ordering, and limit behavior are unchanged. `doc_id` is included as additive metadata only.

## Build Report Context

New command:

```powershell
python -m office2md.cli build-report-context LIBRARY_DB QUERY --context 2 --export-json report_context.json
```

The command is read-only and reuses existing search/context/diagnostics helpers. It does not change search ranking, aliases, token fallback, or matching behavior.

The JSON schema is `office2md.report_context.v1` and includes:

- `request`;
- `diagnostics`;
- `matches`;
- `selected_evidence`;
- `supporting_chunks`;
- `coverage`;
- `limitations`;
- `warnings`.

Evidence fields include, where available:

- `source_file`;
- `locator`;
- `chunk_id`;
- `document_id`;
- `document_title`;
- `document_kind`;
- `evidence_type`;
- `confidence`;
- `limitation`.

## Non-Goals

This checkpoint does not include:

- conversion behavior changes;
- build-library behavior changes;
- search ranking, alias, or token fallback changes;
- locate-document matching behavior changes;
- runner changes;
- workspace changes;
- GUI changes;
- incremental update implementation;
- MCP implementation;
- embeddings or vector search;
- OCR;
- Obsidian plugin;
- write-back;
- unrestricted SQL;
- shell execution.

OfficeCLI remains `diagnostic_only`. This checkpoint does not add OfficeCLI sidecar extraction, `--office-engine officecli`, or main conversion pipeline integration.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- `python -m office2md.cli --help`
- `python -m office2md.cli locate-document --help`
- `python -m office2md.cli build-report-context --help`
- `python -m office2md.cli search-library --help`
- `python -m office2md.cli open-chunk --help`

