# Golden Sample Benchmark Report

Generated for two representative Symex PDFs using the no-AI Knowledge Pack pipeline.

Commands:

```powershell
.\.venv\Scripts\office2md convert-file "<wiring diagram>" "<output>\wiring" --engine auto --profile kb --render-pdf-pages --max-render-pages 5
.\.venv\Scripts\office2md convert-file "<functional description>" "<output>\functional_description" --engine auto --profile kb --render-pdf-pages --max-render-pages 10
```

Output root:

`C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex_golden_sample_test`

## 1. Wiring Diagram

Source file:

`SY909735_Wiring diagram_Revision B_19_06_2019.pdf`

Manifest / Knowledge Pack fields:

| Field | Value |
|---|---:|
| document_kind | technical_drawing_pdf |
| quality_status | low_structure |
| extraction_status | text |
| fallback_used | true |
| pages_count | 5 |
| pages_with_text_count | 5 |
| chunks_count | 5 |
| page_chunks_count | 5 |
| searchable_page_chunks_count | 5 |
| image_only_chunks_count | 0 |
| section_chunks_count | 0 |

Assessment:

- The file is suitable for page/image evidence mode.
- `Page Index` is appropriate for this visual-heavy wiring diagram.
- `source_map.json` traces each chunk to `page_number`, `locator`, and `image_path`.
- `evidence_type` is correctly `page` for rendered pages that also contain page text.
- `commission_number` is empty; `Make Control Panel` is no longer mis-extracted.
- `drawing_number` is `ENG-186350`.
- `project_number` and `order_number` are `SY909735`.

Remaining gap:

- Page titles after the cover are still broad `Table of Contents` labels for the first rendered pages. This is acceptable for rc3/rc4 because source traceability and page text are preserved, but later visual/layout-aware enhancement could improve page semantics.

## 2. Functional Description

Source file:

`SY909735_Functional Description_23_07_19_AH.pdf`

Manifest / Knowledge Pack fields:

| Field | Value |
|---|---:|
| document_kind | functional_description_pdf |
| quality_status | low_structure |
| extraction_status | text |
| fallback_used | true |
| pages_count | 10 |
| pages_with_text_count | 10 |
| chunks_count | 116 |
| page_chunks_count | 10 |
| searchable_page_chunks_count | 10 |
| image_only_chunks_count | 0 |
| section_chunks_count | 106 |

Extracted title-page metadata:

| Field | Value |
|---|---|
| manufacturer | symex GmbH & Co. KG |
| equipment_name | Production Mixer System CML 125 |
| symex_number | SY909735 |
| customer | Esteé Lauder China |
| year_built | 2019 |
| issue | 2/8/2019 |
| revision | Rev. 1.1 |

Structural checks:

- `document_kind` is `functional_description_pdf`.
- Title heading is `# Functional Description - Production Mixer System CML 125`.
- `Revision History` is present.
- `Table of Contents` is detected.
- `Section Outline` is generated from page-level TOC text.
- `document.md` contains the expected section-aware headings:
  - `## 1 Safety`
  - `## 2 Media Supply`
  - `## 3 Operation`
  - `### 3.3 Siemens Touch Panel`
  - `## 4 System Start`
  - `## 5 Main Phases CML 125`
  - `### 5.1 Coaxial Agitator`
  - `### 5.2 Co-Twister Homogenizer`
  - `### 5.3 Pressure / Vacuum`
  - `### 5.4 Electrical Tempering`
  - `### 5.12 CIP-Advanced`
  - `### 5.13 CIP-Drain`
  - `## 6 Secondary Function`
  - `## 7 Fault Messages`
- `chunks.jsonl` contains both page chunks and section chunks.
- Section chunks use `evidence_type: section` and `provenance_status: section_from_page_text`.
- `source_map.json` supports section provenance through `section_number`, `section_title`, `source_page_start`, `locator`, and `evidence_type`.

Before / after gap:

- Before: Functional Description output was mostly page-level Markdown with TOC text preserved but not elevated into semantic sections.
- After: Functional Description output is section-aware while retaining page-level evidence chunks.
- Remaining gap: section body reconstruction is still rule-based and conservative. It promotes headings and source-page provenance, but does not yet rebuild full continuous chapter bodies across all 61 original content pages when only the first 10 pages are rendered.

## Recommendation

The no-AI pipeline is ready for an rc4 candidate focused on section-aware manual/functional PDFs, provided the release notes clearly state that section reconstruction is rule-based and depends on available page text.
