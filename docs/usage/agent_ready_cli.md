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

v0.4.4-rc1 is documentation only. It does not add new commands yet.

Current related commands:

```powershell
python -m office2md.cli search-library .\library\library.db "vacuum pump fault" --export-json .\search.json
python -m office2md.cli library-report .\library --export-json .\library_report.json
python -m office2md.cli locate-document .\library "manual"
```

Planned future commands:

```powershell
python -m office2md.cli open-chunk .\library CHUNK_ID --json
python -m office2md.cli locate-document .\library "manual" --export-json .\documents.json
python -m office2md.cli build-report-context .\library "vacuum pump fault" --export-json .\report_context.json
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
- Payloads should include `schema_name`, `schema_version`, and `office2md_version` where practical.
- Contract changes should be additive unless a schema version changes.
- Search JSON should not change ranking, aliases, token fallback, filters, or related chunk behavior.
- `open-chunk` should be a direct read-only lookup by `chunk_id`.
- `locate-document --export-json` should wrap existing locate behavior without changing matching.
- `build-report-context` should reuse existing search/context helpers without changing ranking.

## Planned Workflows

### Evidence-First Answer

```powershell
python -m office2md.cli search-library .\library\library.db "vacuum pump fault" --export-json .\search.json
python -m office2md.cli open-chunk .\library\library.db CHUNK_ID --json
```

The agent should answer using:

- `source_file`
- `locator`
- `chunk_id`
- `document_title`
- `evidence_type`
- limitations or warnings

### Locate a Document First

```powershell
python -m office2md.cli locate-document .\library "operation manual" --export-json .\documents.json
python -m office2md.cli open-chunk .\library CHUNK_ID --json
```

Use this workflow when the user names a document or source file.

### Build Report Context

```powershell
python -m office2md.cli build-report-context .\library "CIP pump fault" --export-json .\report_context.json
```

This planned command should collect evidence packets and coverage information for report drafting. It should not generate unsupported claims.

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

