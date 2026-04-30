# office2md v0.2.0-rc2 Release Notes

Release candidate focused on Phase 3.0.1: HMI translation XLSX structured handling and library search usability.

v0.2.0-rc2 keeps the v0.2.0 Knowledge Library Builder foundation and adds targeted polish for noisy PLC/HMI translation workbooks. It does not change the `convert` or `convert-file` main flow for other document types.

## Phase 3.0.1 HMI Translation XLSX Handling

PLC/HMI translation workbooks such as `*_Translation_Chinese*.xlsx` are detected as:

- `document_kind: hmi_translation_xlsx`
- `quality_status: structured_with_noise`

Detection uses source file names and workbook structure such as `Category`, `ViewPath`, `Internal ID`, `en-GB`, and `zh-CN` headers, plus HMI screen/path patterns.

HMI Knowledge Packs now use structured chunk evidence:

- `hmi_translation_table`
- `hmi_translation_group`
- `hmi_translation_row`

Noisy fields are kept out of searchable Markdown/chunk text:

- long `Internal ID` values
- base64-like strings
- all-empty `ref` columns
- repeated `NaN`
- repeated full HMI `ViewPath` strings

The HMI group rule now groups by screen/function area instead of field/control paths. On the CML125 validation sample, HMI group chunks were reduced from 594 to 138 while preserving 250 row chunks and row-level locators.

## Entity and Search Polish

Library `top_entities` are now aggregated by `normalized_text` for display. For example, `SY909735` is shown once with merged entity types:

- `project_number`
- `order_number`

The underlying `entities` and `entity_mentions` tables still preserve the original entity types.

`search-library` now supports practical filters for mixed technical libraries:

- `--limit`
- `--offset`
- `--kind`
- `--evidence`
- `--doc` / `--document`
- `--exclude-doc`
- `--has-locator`

Search output includes source file, output directory, chunk ID, evidence type, locator, and a cleaned preview. Noisy chunks are retained but ranked lower.

## locate-document

New command:

```bash
office2md locate-document <library_db_or_output_dir> "Translation"
```

It prints matching document title, source file, document kind, output directory, source path, and chunk count.

## Quality Report Enhancements

`_quality_report.md` and `library-report` now include:

- noisy chunk counts
- noisy documents
- HMI translation documents
- raw text chunk counts
- chunks without locator
- search recommendations for HMI translation, drawing index, and document exclusion filters

## Windows PowerShell Note

The scanner automatically skips Office temporary files whose names start with `~$`. In PowerShell, avoid passing `--exclude "~$*"` for now because quoting and wildcard expansion can be confusing. Run without that exclude unless a project-specific pattern is required.

## CML125 20-File Validation

Validated with the CML125 20-file output root.

Library result:

- documents: 20
- chunks: 871
- entities: 102
- warnings: 0

Document kind distribution:

- `generic_pdf`: 13
- `document`: 2
- `hmi_translation_xlsx`: 1
- `technical_drawing_pdf`: 4

Evidence type distribution:

- `drawing_index`: 400
- `hmi_translation_group`: 138
- `hmi_translation_row`: 250
- `hmi_translation_table`: 1
- `image`: 19
- `page`: 42
- `text`: 4
- `text_page`: 17

HMI single-file validation:

- `document_kind: hmi_translation_xlsx`
- `quality_status: structured_with_noise`
- HMI group chunks: 138
- HMI row chunks: 250
- HMI chunks without locator: 0
- no base64-like Internal ID strings in `document.md`
- no repeated `NaN` in `document.md`

Search validation:

- `PLC --kind hmi_translation_xlsx --limit 20`
- `PLC --evidence drawing_index --kind technical_drawing_pdf --limit 20`
- `CIP --exclude-doc Translation --has-locator --limit 20`
- `SY909735 --limit 20`

`locate-document "Translation"` returns the HMI translation document as `hmi_translation_xlsx` with 389 chunks and output directory `copy-of-sy909735-translation-chinese-ver-1`.

## Test Status

```bash
python -m pytest -q
56 passed

python -m ruff check office2md tests
All checks passed!
```

## Explicit Non-Goals

v0.2.0-rc2 does not add:

- AI calls
- OCR
- Marker integration
- MiniMax/API integration
- embedding/vector database
- Office image export

Embedding/vector search remains deferred to Phase 3.1 as an optional layer on top of SQLite/FTS.
