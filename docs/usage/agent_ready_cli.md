# Agent-Ready CLI JSON

office2md's agent-ready interface is planned as a stable set of read-only CLI JSON contracts over built Knowledge Libraries.

The goal is to let AI agents inspect evidence before answering:

```text
search-library
  -> open-chunk
  -> evidence-first answer with source file, locator, and chunk ID
```

Future MCP support should be a read-only adapter over these same CLI/core helpers, not a separate behavior path.

## Status

v0.4.4-rc3 completes the first agent-ready JSON command set with `open-chunk`, `locate-document --export-json`, and `build-report-context`.

Current related commands:

```powershell
python -m office2md.cli search-library .\library\library.db "vacuum pump fault" --export-json .\search.json
python -m office2md.cli open-chunk .\library CHUNK_ID --context 2 --export-json .\open_chunk.json
python -m office2md.cli locate-document .\library "manual" --export-json .\documents.json
python -m office2md.cli build-report-context .\library "vacuum pump fault" --context 2 --export-json .\report_context.json
python -m office2md.cli library-report .\library --export-json .\library_report.json
```

## Evidence Packet

Agent-facing JSON should preserve enough provenance for every factual claim:

```json
{
  "source_file": "Manual.pdf",
  "locator": "Page 12",
  "chunk_id": "manual_page_12",
  "document_id": "manual-doc",
  "document_title": "Operation Manual",
  "document_kind": "manual_pdf",
  "evidence_type": "page",
  "confidence": null,
  "limitation": null
}
```

Agents should prefer evidence with a `locator`. If evidence lacks a locator, the output should say so instead of pretending the source is more precise than it is.

## Contract Principles

- JSON output should be UTF-8 and parseable without table text.
- File exports should create parent directories.
- New v0.4.4 agent payloads use `schema_version` values such as `office2md.open_chunk.v1`.
- Existing `search-library --export-json` and `library-report --export-json` are legacy exports and do not yet include schema identifiers.
- Contract changes should be additive unless a schema version changes.
- Search JSON should not change ranking, aliases, token fallback, filters, or related chunk behavior.
- `open-chunk` should be a direct read-only lookup by `chunk_id`.
- `locate-document --export-json` should wrap existing locate behavior without changing matching.
- `build-report-context` should reuse existing search/context helpers without changing ranking.

## Planned Workflows

### Evidence-First Answer

```powershell
python -m office2md.cli search-library .\library\library.db "vacuum pump fault" --export-json .\search.json
python -m office2md.cli open-chunk .\library\library.db CHUNK_ID --context 2 --export-json .\open_chunk.json
```

The agent should answer using:

- `source_file`
- `locator`
- `chunk_id`
- `document_title`
- `evidence_type`
- limitations or warnings

Minimal agent behavior:

1. Read `search.json`.
2. Pick `chunk_id` values from high-confidence, locator-backed results.
3. Open those chunks.
4. Cite `source_file`, `locator`, and `chunk_id` in the answer.
5. State any `limitation` values instead of hiding weak evidence.

### Locate a Document First

```powershell
python -m office2md.cli locate-document .\library "operation manual" --export-json .\documents.json
python -m office2md.cli open-chunk .\library CHUNK_ID --context 2 --export-json .\open_chunk.json
```

Use this workflow when the user names a document or source file.

### Build Report Context

```powershell
python -m office2md.cli build-report-context .\library "CIP pump fault" --export-json .\report_context.json
```

This command collects evidence packets, supporting chunks, diagnostics, and coverage information for report drafting. It reuses existing search behavior and should not generate unsupported claims.

Use `selected_evidence` for citations. Use `supporting_chunks` for nearby context. If `warnings` contains `no results found`, the agent should ask for a narrower query or a known document name instead of drafting a report.

## Schema Status

Current v0.4.4 agent JSON status:

| Command | JSON status |
|---|---|
| `search-library --export-json` | Legacy export, no schema identifier yet |
| `open-chunk --export-json` | `office2md.open_chunk.v1` |
| `locate-document --export-json` | `office2md.locate_document.v1` |
| `build-report-context --export-json` | `office2md.report_context.v1` |
| `library-report --export-json` | Legacy report export, no schema identifier yet |

## Future MCP

Future MCP should expose only read-only operations over the same core helpers:

- search;
- open chunk;
- locate document;
- build report context;
- read library report.

It should not expose unrestricted SQL, shell execution, write-back, conversion, build-library, OfficeCLI, OCR, embeddings, or cloud operations.

## OfficeCLI Status

OfficeCLI remains `diagnostic_only`.

Do not use OfficeCLI sidecar extraction, do not add `--office-engine officecli`, and do not integrate OfficeCLI into the main conversion pipeline based on the current benchmark evidence.
