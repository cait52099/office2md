# v0.2.3 Office-Derived Locator Audit

Status: audit only.

Baseline checkpoint: `v0.2.3-rc2`.

Validated against the existing full CML125 library:

```text
C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex_CML125_library_full
```

No conversion, search, ranking, alias, token fallback, runner, library-report scoring, OCR, AI, embedding/vector, cloud, Office image export, or legacy `.doc` behavior was changed.

## Baseline Validation

Use the project virtual environment Python. The system Python on this workstation is Python 3.9 and cannot collect this project because the codebase uses Python 3.10+ union type syntax.

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

Observed:

- Python: 3.11.9
- pytest: 70 passed
- ruff: all checks passed

## Locator Coverage Summary

Full CML125 library chunk counts:

| Metric | Count |
| --- | ---: |
| total chunks | 4238 |
| chunks with locator | 3776 |
| chunks without locator | 462 |

Missing locator breakdown by document kind:

| document_kind | chunks without locator |
| --- | ---: |
| document | 462 |

Missing locator breakdown by evidence type:

| evidence_type | chunks without locator |
| --- | ---: |
| text | 462 |

Missing locator breakdown by source extension:

| extension | chunks without locator |
| --- | ---: |
| `.docx` | 457 |
| `.xlsx` | 3 |
| `.pptx` | 2 |

All chunks without locator are Office-derived generic `document` chunks with `evidence_type: text`.

## Missing Locator Sources

| Source file | output_dir | kind | evidence | extension | missing chunks | Sample preview |
| --- | --- | --- | --- | --- | ---: | --- |
| `Symex CML125 Purchase Agreement_0405.docx` | `symex-cml125-purchase-agreement-0405` | `document` | `text` | `.docx` | 227 | `"Personal Data" means any information ...` |
| `Symex CML125 Purchase Agreement_to Symex_0404.docx` | `symex-cml125-purchase-agreement-to-symex-0404` | `document` | `text` | `.docx` | 227 | `"Personal Data" means any information ...` |
| `CML125 Project.xlsx` | `cml125-project` | `document` | `text` | `.xlsx` | 3 | `## 2017-10-23 ... What / Who / Due Date / Status ...` |
| `CML125 Area_20171129.pptx` | `cml125-area-20171129` | `document` | `text` | `.pptx` | 1 | `<!-- Slide number: 1 --> ...` |
| `New Microsoft PowerPoint Presentation.pptx` | `new-microsoft-powerpoint-presentation` | `document` | `text` | `.pptx` | 1 | `<!-- Slide number: 1 --> ...` |
| `Symex CML125 User group and Password.docx` | `symex-cml125-user-group-and-password` | `document` | `text` | `.docx` | 1 | `USER / PASSWORD / LOG OFF TIME ...` |
| `机械密封 - Copy.docx` | `ji-jie-mi-feng-copy` | `document` | `text` | `.docx` | 1 | `锅体内部Vessel ... Mechanical Seal ...` |
| `机械密封.docx` | `ji-jie-mi-feng` | `document` | `text` | `.docx` | 1 | `锅体内部Vessel ... Mechanical Seal ...` |

The historically noted files are present:

- `CML125 Project.xlsx`: 3 chunks without locator.
- `CML125 Area_20171129.pptx`: 1 chunk without locator.

They are not the dominant source of missing locators in the current full library. The two purchase agreement DOCX files account for 454 of 462 missing locators.

## Source Artifact Inspection

For each missing-locator Office source, the generated output folder contains:

- `manifest.json`
- `knowledge.json`
- `chunks.jsonl`
- `source_map.json`

The relevant output root is:

```text
C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex_CML125_validation_full
```

Inspection summary:

| Source family | chunks.jsonl locators | source_map locators | source_map status | manifest engine | knowledge sections |
| --- | ---: | ---: | --- | --- | ---: |
| Purchase agreement DOCX x2 | 0 / 454 | 0 / 454 | `raw_markdown` | `markitdown` | 0 |
| Other DOCX x3 | 0 / 3 | 0 / 3 | `raw_markdown` | `markitdown` | 0 |
| Generic XLSX x1 | 0 / 3 | 0 / 3 | `raw_markdown` | `markitdown` | 0 |
| Generic PPTX x2 | 0 / 2 | 0 / 2 | `raw_markdown` | `markitdown` | 0 |

Example source_map record for these chunks:

```json
{
  "locator": null,
  "evidence_type": "text",
  "provenance_status": "raw_markdown",
  "slide_number": null,
  "sheet_name": null,
  "table_name": null,
  "row_start": null,
  "row_end": null
}
```

## Cause Analysis

The missing locator cause is not library build loss. The library builder preserves chunk/source_map locator fields when present.

The missing locator cause is upstream Office chunk generation for generic Office documents:

1. The affected Office files are classified as generic `document`.
2. `build_office_chunks()` returns structured chunks only for recognized Office families:
   - `process_development_presentation`
   - `mpdp_table_xlsx`
   - `hmi_translation_xlsx`
   - `release_rationale_docx`
3. Generic Office documents fall back to `chunk_markdown()`.
4. `chunk_markdown()` creates text chunks from headings and body text only. It does not infer slide, sheet, row, paragraph, or section locators.
5. `build_source_map()` then correctly records these chunks as `provenance_status: raw_markdown` with `locator: null`.

Per-source conclusions:

| Source | Cause |
| --- | --- |
| `Symex CML125 Purchase Agreement_0405.docx` | MarkItDown raw markdown fallback; generic DOCX has no paragraph/page locator extraction. |
| `Symex CML125 Purchase Agreement_to Symex_0404.docx` | Same as above. |
| `CML125 Project.xlsx` | Generic XLSX is not HMI/MPDP; sheet-like headings exist in markdown, but no structured sheet/table locator is emitted for generic XLSX. |
| `CML125 Area_20171129.pptx` | Generic PPTX is not process-development; slide number comments exist in markdown, but no generic PPTX slide chunking is applied. |
| `New Microsoft PowerPoint Presentation.pptx` | Same generic PPTX raw markdown path. |
| `Symex CML125 User group and Password.docx` | Generic DOCX raw markdown path. |
| `机械密封*.docx` | Generic DOCX raw markdown path with embedded/base64 image references; no Office image export or paragraph locator extraction in validated path. |

## Recommendation

Recommendation: **E. small report/diagnostic improvement only**, with no locator behavior change in v0.2.3 P1-3.

Reasoning:

- A narrow XLSX-only polish would affect only 3 chunks in the full CML125 library.
- A narrow PPTX-only polish would affect only 2 chunks in the full CML125 library.
- The dominant missing-locator source is generic DOCX raw markdown: 457 chunks.
- Fixing generic DOCX locators properly would require a broader Office locator design, likely paragraph/section/page provenance from Office structure or converter metadata. That is outside this audit scope and should not be slipped in as a small polish.
- The current behavior is internally consistent: generic raw markdown chunks do not claim source locators that were not extracted.

Recommended next action:

- Do not change conversion or Office locator behavior yet.
- Add a future small report/diagnostic improvement if useful: expose missing-locator counts by source extension/source file in `library-report --export-json` or a separate audit command/report section.
- Keep any future XLSX/PPTX locator inference scoped and test-backed only if there is a specific user workflow where 3 XLSX chunks or 2 PPTX chunks materially matter.

If a later narrow code change is requested:

| Option | Likely files touched | Expected behavior change | Risk | Tests needed | Why not broad refactor |
| --- | --- | --- | --- | --- | --- |
| C. XLSX-only polish | `office2md/postprocess/office_structure.py`, `tests/test_office_enhancement.py` | Generic XLSX markdown headings could receive `Sheet: <heading>` locators where headings clearly represent sheets. | Medium: MarkItDown headings may not always be sheet names. | Fixture with generic XLSX markdown; assert locator and source_map fields; regression for HMI/MPDP unchanged. | Limited to generic `.xlsx`, no DOCX/PPTX/parser overhaul. |
| D. PPTX-only polish | `office2md/postprocess/office_structure.py`, `tests/test_office_enhancement.py` | Generic PPTX markdown with `<!-- Slide number: N -->` could produce slide chunks with `Slide N` locators. | Medium: might split existing generic text chunks and alter search granularity. | Fixture with generic PPTX slide comments; assert slide locators; regression for process-development PPTX unchanged. | Limited to generic `.pptx`, no Office image export or broad parser work. |
| E. report/diagnostic only | `office2md/library.py`, `office2md/cli.py`, tests/docs | Report missing locators by source extension/source file without changing chunks. | Low. | Report JSON/schema test; smoke against CML125 library. | Reporting only; no conversion or search behavior change. |

For v0.2.3, prefer E only if another checkpoint is needed; otherwise document the limitation and defer locator behavior changes.
