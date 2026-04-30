# office2md v0.2.0-rc4 Release Notes

Release candidate focused on Phase 3.0.3a: CML125 100-file Knowledge Library quality-report and search usability fixes.

v0.2.0-rc4 keeps the Phase 3.0 no-AI local library scope. It does not add OCR, AI/MiniMax, embedding/vector search, Marker integration, API integration, or Office image export.

## PDF Subtype Classification

Generic PDF library records now get conservative subtype refinement when the filename, title, or document preview makes the subtype obvious:

- `datasheet_pdf`
- `component_document_pdf`
- `certificate_pdf`
- `manual_pdf`
- `project_book_pdf`
- `report_pdf`

Unclear PDFs remain `generic_pdf`.

## Quality Report Refinement

The library quality report now separates searchable page-level PDFs from true low-quality documents. PDFs with page-level evidence, locators, rendered assets, and no noisy chunks are listed under `Page-Level Searchable PDFs` instead of being reported as low quality only because their source extraction remains `low_structure`.

The CML125 100-file Phase 3.0.3a report shows:

- `low_quality_documents`: 13
- `page_level_pdf_documents`: 84
- `noisy_chunks_count`: 0

## Search Fallback

`search-library` now applies a simple token fallback when a multi-term query has no exact FTS hits. It splits meaningful tokens, searches them individually, merges unique chunk results, and marks CLI output with `fallback: token`.

Validated examples:

- `homogenizer cooling` returns useful HMI/PDF hits with token fallback.
- `alarm history` returns useful HMI/PDF/report hits with token fallback.

## Test Status

```bash
python -m pytest
60 passed

python -m ruff check .
All checks passed!
```

## Explicit Non-Goals

v0.2.0-rc4 does not add:

- AI calls
- OCR
- Marker integration
- MiniMax/API integration
- embedding/vector database
- Office image export

Embedding/vector search remains deferred to Phase 3.1 as an optional layer on top of SQLite/FTS.
