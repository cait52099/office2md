# office2md v0.2.3-rc1 Release Notes

v0.2.3-rc1 starts the v0.2.3 polish track with machine-readable JSON export for `library-report`.

This checkpoint does not change default `library-report` console output, library-report scoring, search core behavior, ranking, aliases, token fallback logic, conversion behavior, or runner process-control behavior.

It does not add vector search, embeddings, OCR, AI/MiniMax, cloud/network dependencies, Office image export, or legacy `.doc` conversion.

## Library Report JSON Export

`library-report --export-json PATH` is now available as an optional flag.

When enabled, `library-report` prints the normal Rich table first, writes UTF-8 pretty JSON to `PATH`, creates parent directories automatically, and then prints:

```text
export_json: <path>
```

The default output without `--export-json` remains unchanged.

## JSON Data

The export writes the existing `library_report()` result dictionary directly, so report metrics are not recalculated through a separate code path.

The JSON includes existing report fields such as:

- `documents_count`
- `chunks_count`
- `entities_count`
- `document_kind_distribution`
- `evidence_type_distribution`
- `top_entities`
- `top_batches`
- `missing_assets_summary`
- `low_quality_documents`
- `page_level_pdf_documents`
- `noisy_chunks_count`
- `chunks_without_locator`
- `noisy_documents`
- `hmi_translation_documents`
- `export_files_generated`

## Documentation

README and `docs/usage/common_workflows.md` document the new export flag, UTF-8 JSON behavior, automatic parent directory creation, and the fact that the normal report table still prints.

## Validation

```bash
python -m pytest
70 passed

python -m ruff check .
All checks passed!
```

Smoke checks passed against the existing CML125 full-directory library:

- `library-report LIBRARY_PATH` prints the normal table with no `export_json:` marker.
- `library-report LIBRARY_PATH --export-json ...\library_report_export.json` writes parseable UTF-8 JSON and prints the confirmation line.

The CML125 export recorded:

- `documents_count`: 587
- `chunks_count`: 4238
- `entities_count`: 365
- `noisy_chunks_count`: 0
- `chunks_without_locator`: 462
- `missing_assets_summary`: 0
- `low_quality_documents`: 85
- `page_level_pdf_documents`: 493

## Explicit Non-Goals

v0.2.3-rc1 does not include:

- library-report default output changes
- library-report scoring changes
- search core changes
- ranking changes
- alias changes
- token fallback logic changes
- conversion behavior changes
- runner process-control changes
- vector search
- embeddings
- OCR
- AI/MiniMax
- cloud/network dependency
- Office image export
- legacy `.doc` conversion
