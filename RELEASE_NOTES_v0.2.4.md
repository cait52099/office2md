# office2md v0.2.4 Release Notes

v0.2.4 is a focused quality/reporting polish release on top of v0.2.3. It improves locator diagnostics in `library-report`, `library-report --export-json`, and `_quality_report.md`.

This release does not change conversion behavior, Office locator generation behavior, library-report metric/scoring semantics, search core behavior, ranking, aliases, token fallback logic, or runner process-control behavior.

It does not add vector search, embeddings, OCR, AI/MiniMax, cloud/network dependencies, Office image export, or legacy `.doc` conversion.

## Locator Report Detail

`library-report` now includes additional missing-locator detail:

- total `chunks_without_locator`
- chunks without locator by document kind
- chunks without locator by evidence type
- chunks without locator by source extension
- top source files without locators

This is reporting/diagnostics polish only. It does not change how locators are generated, scored, or used.

## JSON Export Compatibility

`library-report --export-json PATH` keeps the existing JSON fields and adds only additive missing-locator diagnostic fields:

- `chunks_without_locator_by_document_kind`
- `chunks_without_locator_by_evidence_type`
- `chunks_without_locator_by_extension`
- `chunks_without_locator_top_sources`
- `office_raw_markdown_missing_locator_summary`

Existing JSON consumers can continue using the previous fields.

## Quality Report Detail

`_quality_report.md` now expands the "Chunks Without Locator" section with the same breakdowns and an Office/raw-markdown summary.

The wording notes that missing locator data is often already absent in `source_map.json` and `chunks.jsonl` for raw-markdown inputs. The library builder preserves available locator data and does not invent missing provenance.

## Final Validation

```bash
python -m pytest
71 passed

python -m ruff check .
All checks passed!
```

Help checks passed for:

- `python -m office2md.cli convert --help`
- `python -m office2md.cli build-library --help`
- `python -m office2md.cli search-library --help`
- `python -m office2md.cli locate-document --help`
- `python -m office2md.cli library-report --help`

Compact CML125 full-library smoke checks passed for:

- `library-report`
- `library-report --export-json`
- `search-library "vacuum pump fault" --limit 3 --diagnostics-json`
- `search-library "vacuum pump fault" --limit 3 --export-json`
- `locate-document "SY909735"`

The final CML125 library-report JSON smoke recorded:

- `documents_count`: 587
- `chunks_count`: 4238
- `entities_count`: 365
- `chunks_without_locator`: 462
- `chunks_without_locator_by_document_kind`: `document: 462`
- `chunks_without_locator_by_evidence_type`: `text: 462`
- `chunks_without_locator_by_extension`: `docx: 457`, `xlsx: 3`, `pptx: 2`
- top source: `Symex CML125 Purchase Agreement_0405.docx`, 227 chunks
- `noisy_chunks_count`: 0
- `page_level_pdf_documents`: 493

## Explicit Non-Goals

v0.2.4 does not include:

- new features beyond scoped reporting/diagnostics polish
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
