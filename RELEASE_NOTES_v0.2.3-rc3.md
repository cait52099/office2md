# office2md v0.2.3-rc3 Release Notes

v0.2.3-rc3 adds a docs-only Office-derived locator audit for the existing full CML125 library.

This checkpoint does not change code, conversion logic, Office locator behavior, search core behavior, ranking, aliases, token fallback logic, runner process-control behavior, or library-report metrics/scoring.

It does not add vector search, embeddings, OCR, AI/MiniMax, cloud/network dependencies, Office image export, legacy `.doc` conversion, or a broad Office provenance/locator refactor.

## Office-Derived Locator Audit

`docs/design/v023_office_locator_audit.md` records locator coverage for the existing full CML125 library:

- total chunks: 4238
- chunks with locator: 3776
- chunks without locator: 462

Missing locators by extension:

- `.docx`: 457
- `.xlsx`: 3
- `.pptx`: 2

## Missing Locator Sources

The audit identifies the current missing-locator sources:

- `Symex CML125 Purchase Agreement_0405.docx`: 227 chunks
- `Symex CML125 Purchase Agreement_to Symex_0404.docx`: 227 chunks
- `CML125 Project.xlsx`: 3 chunks
- `CML125 Area_20171129.pptx`: 1 chunk
- `New Microsoft PowerPoint Presentation.pptx`: 1 chunk
- three small DOCX sources: 1 chunk each

## Cause Analysis

The audit records that missing locators are already absent in `chunks.jsonl` and `source_map.json`; `source_map.json` records `provenance_status: raw_markdown` for these chunks.

The affected files are generic Office documents that fall through to `chunk_markdown()`. The library builder is preserving chunk/source_map data correctly and is not losing locator fields.

## Recommendation

Recommendation: E, small report/diagnostic improvement only.

The audit recommends no XLSX/PPTX locator polish yet and no broad Office locator refactor. A narrow XLSX-only polish would affect 3 chunks, and a narrow PPTX-only polish would affect 2 chunks in the current full CML125 library. The dominant missing-locator source is generic DOCX raw markdown, which would require a broader provenance design.

## Validation

```bash
python -m pytest
70 passed

python -m ruff check .
All checks passed!
```

## Explicit Non-Goals

v0.2.3-rc3 does not include:

- code changes
- runtime behavior changes
- conversion logic changes
- Office locator behavior changes
- search core changes
- ranking changes
- alias changes
- token fallback logic changes
- runner process-control changes
- library-report metrics or scoring changes
- vector search
- embeddings
- OCR
- AI/MiniMax
- cloud/network dependency
- Office image export
- legacy `.doc` conversion
- broad Office provenance or locator refactor
