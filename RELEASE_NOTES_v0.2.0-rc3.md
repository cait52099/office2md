# office2md v0.2.0-rc3 Release Notes

Release candidate focused on Phase 3.0.2: CML125 100-file Knowledge Library validation and duplicate document/chunk ID handling.

v0.2.0-rc3 keeps the Phase 3.0 no-AI local library scope. It does not add OCR, AI/MiniMax, embedding/vector search, Marker integration, API integration, or Office image export.

## Duplicate ID Fix

The 100-file CML125 validation set includes duplicate source files with identical checksums. Previous library builds derived `doc_id` from checksum, so duplicate files could generate the same `documents.doc_id` and fail with:

```text
UNIQUE constraint failed: documents.doc_id
```

Library normalization now keeps non-duplicate IDs unchanged and adds a stable output-folder-based suffix only when a duplicate document ID or chunk ID is encountered. Source-map lookup still uses the original chunk ID before assigning the unique library chunk ID, preserving evidence, locator, and provenance metadata.

## CML125 100-File Validation

Validated from the CML125 100-file output root generated with:

```bash
python -m office2md.cli convert INPUT_PATH OUTPUT --recursive --engine auto --profile kb --render-pdf-pages --max-render-pages 3 --max-text-pages 10 --max-files 100 --no-force-ocr --no-use-ai --ai-backend none
```

Conversion result:

- success: 100
- failed: 0
- skipped: 0
- `ocr_used`: false for 100 manifests
- `ai_used`: false for 100 manifests

Library result:

- documents: 100
- chunks: 1205
- entities: 261
- warnings: 0

Document kind distribution:

- `generic_pdf`: 86
- `document`: 2
- `hmi_translation_xlsx`: 1
- `technical_drawing_pdf`: 11

Evidence type distribution:

- `drawing_index`: 400
- `hmi_translation_group`: 138
- `hmi_translation_row`: 250
- `hmi_translation_table`: 1
- `image`: 27
- `page`: 248
- `text`: 4
- `text_page`: 137

Quality metrics:

- noisy chunks: 0
- chunks without locator: 4
- distinct document IDs: 100 of 100
- distinct chunk IDs: 1205 of 1205

Smoke tests passed for:

- `Translation`
- `SY909735`
- `homogenizer`
- `alarm`

## Test Status

```bash
python -m pytest
57 passed

python -m ruff check .
All checks passed!
```

## Explicit Non-Goals

v0.2.0-rc3 does not add:

- AI calls
- OCR
- Marker integration
- MiniMax/API integration
- embedding/vector database
- Office image export

Embedding/vector search remains deferred to Phase 3.1 as an optional layer on top of SQLite/FTS.
