# office2md v0.2.4-rc1 Release Notes

v0.2.4-rc1 starts the v0.2.4 polish track with quality and locator report detail improvements for chunks without locators.

This checkpoint is reporting/diagnostics polish only. It does not change conversion behavior, Office locator generation behavior, library-report metric/scoring semantics, search core behavior, ranking, aliases, token fallback logic, or runner process-control behavior.

It does not add vector search, embeddings, OCR, AI/MiniMax, cloud/network dependencies, Office image export, legacy `.doc` conversion, or broad Office provenance/locator refactoring.

## Locator Report Detail

`library-report` now shows additional missing-locator detail:

- total `chunks_without_locator`
- chunks without locator by document kind
- chunks without locator by evidence type
- chunks without locator by source extension
- top source files without locators

The existing report metrics remain unchanged; this is additional diagnostic detail.

## JSON Export Compatibility

`library-report --export-json PATH` keeps existing fields and adds diagnostic fields:

- `chunks_without_locator_by_document_kind`
- `chunks_without_locator_by_evidence_type`
- `chunks_without_locator_by_extension`
- `chunks_without_locator_top_sources`
- `office_raw_markdown_missing_locator_summary`

The existing JSON export fields remain present and compatible.

## Quality Report Detail

`_quality_report.md` now expands the "Chunks Without Locator" section with the same breakdowns and an Office/raw-markdown summary.

The report wording explains that missing locator data is often already absent in `source_map.json` and `chunks.jsonl` for raw-markdown inputs; the library builder preserves available locator data and does not invent missing provenance.

## Validation

```bash
python -m pytest
71 passed

python -m ruff check .
All checks passed!
```

Smoke checks passed against the existing CML125 full-directory library:

- `library-report`
- `library-report --export-json`

The CML125 locator report smoke recorded:

- `chunks_without_locator`: 462
- by document kind: `document: 462`
- by evidence type: `text: 462`
- by extension: `docx: 457`, `xlsx: 3`, `pptx: 2`
- top source: `Symex CML125 Purchase Agreement_0405.docx`, 227 chunks
- Office/raw-markdown missing locator total: 462

## Explicit Non-Goals

v0.2.4-rc1 does not include:

- metric or scoring behavior changes
- conversion behavior changes
- Office locator generation behavior changes
- search core changes
- ranking changes
- alias changes
- token fallback logic changes
- runner process-control changes
- vector search
- embeddings
- OCR
- AI/MiniMax
- cloud/network dependency
- Office image export
- legacy `.doc` conversion
- broad Office provenance or locator refactor
