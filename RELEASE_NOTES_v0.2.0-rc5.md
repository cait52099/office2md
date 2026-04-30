# office2md v0.2.0-rc5 Release Notes

Release candidate focused on Phase 3.0.4: CML125 200-file Knowledge Library validation.

v0.2.0-rc5 keeps the Phase 3.0 no-AI local library scope. It does not add OCR, AI/MiniMax, embedding/vector search, Marker integration, API integration, Office image export, or Phase 3.1 work.

## CML125 200-File Validation

Validated with Python 3.11.9 from the CML125 source directory using:

```bash
python -m office2md.cli convert INPUT_PATH OUTPUT --recursive --engine auto --profile kb --render-pdf-pages --max-render-pages 3 --max-text-pages 10 --max-files 200 --no-force-ocr --no-use-ai --ai-backend none
```

Conversion result:

- manifests: 200
- success: 200
- failed: 0
- `ocr_used`: 0
- `ai_used`: 0

The initial convert run hit an output-pipe/tool timeout after 103 outputs. The same conversion was resumed with `--skip-existing` and redirected logs. Final output contains 200 valid successful manifests.

Manifest warnings were mainly Docling fallback caused by `LocalEntryNotFoundError / WinError 10054`. This did not indicate OCR or AI usage.

## Library Result

`office2md build-library` completed successfully:

- documents: 200
- chunks: 1751
- entities: 267
- build warnings: 0

Document kind distribution:

- `datasheet_pdf`: 112
- `component_document_pdf`: 35
- `certificate_pdf`: 25
- `manual_pdf`: 9
- `generic_pdf`: 8
- `technical_drawing_pdf`: 4
- `report_pdf`: 3
- `document`: 2
- `hmi_translation_xlsx`: 1
- `project_book_pdf`: 1

Evidence type distribution:

- `drawing_index`: 400
- `hmi_translation_group`: 138
- `hmi_translation_row`: 250
- `hmi_translation_table`: 1
- `image`: 31
- `page`: 508
- `section`: 8
- `text`: 4
- `text_page`: 411

Quality metrics:

- `low_quality_documents`: 16
- `page_level_pdf_documents`: 181
- `noisy_chunks_count`: 0
- `noisy_documents`: 0
- `chunks_without_locator`: 4
- `missing_assets_summary`: 0

## Search Smoke Tests

Search smoke tests passed for:

- `Translation`
- `SY909735`
- `CML125`
- `homogenizer cooling`
- `alarm history`
- `temperature probe`
- `1V2005`
- `2M2001`
- `CIP`
- `seal`

`homogenizer cooling` and `alarm history` continue to benefit from the Phase 3.0.3a token fallback.

## Known Follow-Up

The generated `_quality_report.md` can print an extra `_None._` after a non-empty section. This is cosmetic; database metrics and CLI summary values are correct.

## Test Status

```bash
python -m pytest
60 passed

python -m ruff check .
All checks passed!
```

## Explicit Non-Goals

v0.2.0-rc5 does not add:

- AI calls
- OCR
- Marker integration
- MiniMax/API integration
- embedding/vector database
- Office image export

Embedding/vector search remains deferred to Phase 3.1 as an optional layer on top of SQLite/FTS.
