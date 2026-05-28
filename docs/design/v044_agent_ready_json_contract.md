# v0.4.4 Agent-Ready JSON Contract Foundation

## Purpose

office2md is evolving from a local document conversion tool into a local knowledge base backend for AI agents such as Codex, Claude Code, and VS Code-based assistants.

The planned architecture is:

```text
Raw documents
  -> office2md convert
  -> Knowledge Pack
  -> build-library
  -> library.db / library_index.json / library_graph.json
  -> stable CLI JSON interface
  -> future read-only MCP adapter
  -> evidence-first agent workflows
```

v0.4.4 should establish stable CLI/core JSON contracts before any MCP work. The CLI JSON layer is the durable interface. A future MCP server should be a thin, read-only adapter over the same core helpers and payload shapes.

## Principles

- Agent-facing output must be evidence-first.
- JSON contracts must be stable, versioned, and additive.
- CLI JSON is the source contract; future MCP adapts it without adding hidden behavior.
- Core helpers should return structured dictionaries that can be used by CLI, GUI, tests, and future MCP.
- Read operations must not alter libraries, workspaces, source files, outputs, or conversion artifacts.
- Existing search ranking, aliases, token fallback, filters, and report scoring must remain unchanged.
- Contracts should include enough provenance for an agent to cite, inspect, and reopen evidence.
- Contracts should include limitations and warnings instead of hiding uncertainty.

## Strict Non-Goals

- No embeddings or vector search.
- No OCR.
- No Obsidian plugin.
- No write-back.
- No unrestricted SQL.
- No shell execution.
- No conversion behavior changes.
- No build-library behavior changes.
- No search ranking, alias, or token fallback changes.
- No runner behavior changes.
- No workspace behavior changes.
- No OfficeCLI main-pipeline integration.
- No OfficeCLI sidecar extraction.
- No `--office-engine officecli`.
- No MCP implementation in v0.4.4.

OfficeCLI remains `diagnostic_only`.

## Evidence Packet

Agent-facing evidence should use a compact, repeated packet shape wherever possible.

Required fields:

```json
{
  "source_file": "Manual.pdf",
  "locator": "Page 12",
  "chunk_id": "manual_page_12",
  "document_id": "manual-doc",
  "document_title": "Operation Manual",
  "document_kind": "manual_pdf",
  "evidence_type": "page",
  "confidence": "available_or_null",
  "limitation": "short note or null"
}
```

Recommended additional fields when available:

```json
{
  "output_dir": "manual",
  "chunk_title": "Maintenance",
  "preview": "short text preview",
  "text": "full chunk text when explicitly opened",
  "heading_path": ["3 Operation", "3.2 Maintenance"],
  "page_number": 12,
  "slide_number": null,
  "sheet_name": null,
  "table_name": null,
  "source_map": {},
  "is_noisy": false,
  "noise_score": 0,
  "warnings": []
}
```

Field notes:

- `chunk_id` should be the reopenable evidence handle.
- `document_id` should map to the library document ID (`doc_id`) even if current internal names differ.
- `locator` should preserve existing source locator text without inventing new locator semantics.
- `confidence` should use existing confidence data when present; otherwise `null` is acceptable.
- `limitation` should be explicit when evidence lacks a locator, comes from noisy text, or is otherwise weak.

## Contract Naming

Use explicit schema names and schema versions.

Recommended top-level fields:

```json
{
  "schema_name": "office2md.search_results",
  "schema_version": "1",
  "generated_at": "ISO-8601 timestamp",
  "office2md_version": "0.4.4",
  "library_path": "path supplied or resolved",
  "warnings": [],
  "limitations": []
}
```

Planned schema names:

- `office2md.search_results.v1`
- `office2md.open_chunk.v1`
- `office2md.locate_document.v1`
- `office2md.report_context.v1`
- `office2md.library_report.v1`

Schema evolution rules:

- New fields are additive.
- Existing field meanings should not change within the same schema version.
- Existing search ranking and filtering behavior must not change when adding JSON fields.
- JSON should be UTF-8, pretty-printed, and parseable without surrounding table text.
- File exports should create parent directories when writing to `--export-json`.

## Planned JSON Contracts

### Search Results

Command shape:

```powershell
python -m office2md.cli search-library LIBRARY_DB QUERY --export-json search.json
```

Planned payload:

```json
{
  "schema_name": "office2md.search_results.v1",
  "schema_version": "1",
  "query": {},
  "diagnostics": {},
  "result_count": 0,
  "shown_count": 0,
  "results": [
    {
      "rank": 1,
      "evidence": {},
      "preview": "short text preview",
      "related_chunks": []
    }
  ],
  "warnings": [],
  "limitations": []
}
```

The implementation should reuse existing `search_library()` and `search_library_diagnostics()` behavior. It must not change ranking, aliases, token fallback, filters, or related chunk selection.

### Open Chunk

Command shape:

```powershell
python -m office2md.cli open-chunk LIBRARY_DB_OR_DIR CHUNK_ID --context 2 --export-json open_chunk.json
```

Implemented v0.4.4-rc2 payload:

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

`open-chunk` is a read-only lookup by exact `chunk_id`. It does not run search or alter ranking. Optional context uses same-document chunk proximity and source locator hints.

### Locate Document

Command shape:

```powershell
python -m office2md.cli locate-document LIBRARY_DB_OR_DIR QUERY --export-json documents.json
```

Planned payload:

```json
{
  "schema_name": "office2md.locate_document.v1",
  "schema_version": "1",
  "query": "Manual",
  "result_count": 0,
  "results": [
    {
      "document_id": "manual-doc",
      "document_title": "Operation Manual",
      "source_file": "Manual.pdf",
      "document_kind": "manual_pdf",
      "output_dir": "manual",
      "source_path": "C:/docs/Manual.pdf",
      "chunks_count": 12
    }
  ],
  "warnings": [],
  "limitations": []
}
```

The JSON polish should wrap the existing `locate_document()` result. It must not change matching, ordering, or limits.

### Build Report Context

Command shape:

```powershell
python -m office2md.cli build-report-context LIBRARY_DB QUERY --export-json report_context.json
```

Planned payload:

```json
{
  "schema_name": "office2md.report_context.v1",
  "schema_version": "1",
  "query": {},
  "evidence_packets": [],
  "coverage": {
    "documents": 0,
    "chunks": 0,
    "with_locator": 0,
    "without_locator": 0
  },
  "draft_outline": [],
  "warnings": [],
  "limitations": []
}
```

This command should build an evidence bundle for a future report draft. It should reuse existing search and related chunk helpers and should not change ranking or report scoring.

### Library Report

Existing `library-report --export-json` already writes the current report dictionary. v0.4.4 can document it as a stable agent-readable report once schema metadata is added additively.

## Future MCP Relationship

Future MCP should be read-only and should call the same core helpers as CLI commands.

Allowed future MCP operations:

- search library;
- open chunk by `chunk_id`;
- locate document;
- build report context;
- read library report.

Forbidden future MCP operations:

- mutate source documents;
- mutate Knowledge Packs;
- mutate `library.db`;
- run conversion automatically;
- run build-library automatically;
- run OfficeCLI as part of normal answers;
- execute shell commands;
- expose unrestricted SQL;
- write back to workspace/wiki/output folders.

## Agent Workflows

### Search -> Open Chunk -> Evidence-First Answer

1. Agent calls `search-library` JSON.
2. Agent selects high-quality evidence packets with locators.
3. Agent calls `open-chunk` for selected `chunk_id` values.
4. Agent answers with citations based on `source_file`, `locator`, and `chunk_id`.
5. Agent states limitations for missing locators or noisy chunks.

### Locate Document -> Open Chunk

1. Agent calls `locate-document` JSON to find a likely source document.
2. Agent searches or opens relevant chunks from that document.
3. Agent answers with document-level and chunk-level provenance.

### Build Report Context -> Report Draft

1. Agent calls `build-report-context`.
2. Agent receives grouped evidence packets and coverage information.
3. Agent drafts a troubleshooting report, SOP impact summary, supplier email, or evidence package.
4. Agent cites source files and locators for every factual claim.

## Release Slicing

Recommended v0.4.4 slicing:

- rc1: design and usage docs only.
- rc2: `open_chunk()` core helper and `open-chunk` CLI.
- rc3: `locate-document --export-json` polish and `build-report-context`.
- rc4: agent workflow examples and JSON consistency audit.
