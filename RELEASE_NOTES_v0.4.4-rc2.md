# office2md v0.4.4-rc2 Release Notes

Status: release candidate for v0.4.4 open-chunk foundation.

## Scope

v0.4.4-rc2 adds the first read-only agent-facing JSON command:

```powershell
python -m office2md.cli open-chunk LIBRARY_DB_OR_DIR CHUNK_ID --context 2 --export-json open_chunk.json
```

This checkpoint includes:

- `open_chunk()` core helper;
- `open-chunk` CLI command;
- `office2md.open_chunk.v1` JSON export;
- tests for helper behavior, CLI export, missing chunks, context, and unchanged search behavior;
- docs updates for the implemented command.

## Behavior

`open-chunk` is read-only and exact `chunk_id` based. It does not run search, change ranking, rebuild libraries, modify source files, or write anything except the requested `--export-json` file.

Optional `--context` returns same-document context chunks selected by existing chunk proximity and source locator hints. Context chunks do not include full text; the target chunk includes full text.

Missing `chunk_id` values fail clearly.

## JSON Contract

The export schema is:

```json
{
  "schema_version": "office2md.open_chunk.v1",
  "request": {},
  "target_chunk": {},
  "context_chunks": [],
  "evidence": {},
  "limitations": [],
  "warnings": []
}
```

Evidence fields include, where available:

- `source_file`
- `locator`
- `chunk_id`
- `document_id`
- `document_title`
- `document_kind`
- `evidence_type`
- `confidence`
- `limitation`

## Non-Goals

This checkpoint does not include:

- conversion behavior changes;
- build-library behavior changes;
- search ranking, alias, or token fallback changes;
- locate-document matching changes;
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

OfficeCLI remains `diagnostic_only`. This checkpoint does not add OfficeCLI sidecar extraction, `--office-engine officecli`, or main conversion pipeline integration.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- `python -m office2md.cli --help`
- `python -m office2md.cli open-chunk --help`
- `python -m office2md.cli search-library --help`

