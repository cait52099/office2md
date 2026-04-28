# office2md Release Readiness Checklist

Core no-AI path:

- [ ] `office2md --help`
- [ ] `office2md doctor`
- [ ] `office2md doctor-ai` reports AI disabled by default and does not fail if MiniMax/mmx is missing.
- [ ] `office2md convert-file input.pdf output --profile kb`
- [ ] `office2md convert ./input ./output --recursive --profile kb --max-files 5`
- [ ] `office2md convert ./input ./output --recursive --dry-run --include "*.pdf"`

Knowledge Pack files:

- [ ] `document.md`
- [ ] `document.raw.md`
- [ ] `document.json`
- [ ] `manifest.json`
- [ ] `chunks.jsonl`
- [ ] `knowledge.json`
- [ ] `entities.json`
- [ ] `source_map.json`
- [ ] `_index.md`
- [ ] `_index.json`

PDF and drawing support:

- [ ] Docling fallback behavior works when Docling model download fails.
- [ ] MarkItDown fallback writes `fallback_used: true`.
- [ ] `technical_drawing_pdf` classification works.
- [ ] `--render-pdf-pages` writes page images to assets.
- [ ] `document.json.pages` includes page text and image paths.
- [ ] `semantic_title`, `source_page`, and `locator` are separated.
- [ ] `heading_path` does not use `Page N` as the semantic title.

Optional AI behavior:

- [ ] AI is disabled by default.
- [ ] No API key or token is required for no-AI conversion.
- [ ] Missing MiniMax/mmx CLI does not block conversion.
- [ ] `--use-ai --ai-backend cli` can be tested with a mock CLI.
- [ ] AI failure does not block conversion and writes manifest warnings.

rc3 validation evidence:

- [ ] 50-file PDF validation completed with Success 50, Failed 0, Skipped 0.
- [ ] 50-file document kind distribution recorded as `generic_pdf: 45`, `technical_drawing_pdf: 5`.
- [ ] 50-file quality distribution recorded as `low_structure: 42`, `visual_only: 8`.
- [ ] 50-file extraction distribution recorded as `text: 42`, `image_only: 8`.
- [ ] Image-only PDFs are marked with `quality_status: visual_only`.
- [ ] Image-only PDFs are marked with `extraction_status: image_only`.
- [ ] Image-only PDFs are marked with `requires_ocr_or_vision: true`.
- [ ] Image-only source maps retain page image provenance.
- [ ] Optional AI remains disabled and is not required for rc3 validation.

rc4 golden sample validation:

- [ ] Functional Description full-text golden sample records `pages_count: 61`.
- [ ] Functional Description full-text golden sample records `text_pages_count: 61`.
- [ ] Functional Description full-text golden sample records `rendered_pages_count: 10`.
- [ ] Functional Description full-text golden sample records `chunks_count: 167`.
- [ ] Functional Description full-text golden sample records `page_chunks_count: 61`.
- [ ] Functional Description full-text golden sample records `searchable_page_chunks_count: 61`.
- [ ] Functional Description full-text golden sample records `section_chunks_count: 106`.
- [ ] Functional Description full-text golden sample records `section_chunks_with_body_count: 106`.
- [ ] Functional Description evidence distribution is `page: 10`, `text_page: 51`, `section: 106`.
- [ ] Wiring Diagram regression check records `pages_count: 5`, `text_pages_count: 5`, `rendered_pages_count: 5`.
- [ ] Wiring Diagram evidence distribution is `page: 5`.
- [ ] `--max-render-pages` controls image assets only.
- [ ] `--max-text-pages` controls PDF text page extraction.
- [ ] `--extract-all-page-text` extracts text from all PDF pages without rendering all page images.
- [ ] Section-aware reconstruction works for `manual_pdf`, `functional_description_pdf`, and `fault_catalog_pdf`.
- [ ] `source_map.json` supports section provenance through `section_number`, `section_title`, `source_page_start`, and `locator`.
- [ ] Chunk `evidence_type` values are documented as `page`, `text_page`, `section`, and `image`.

rc5 Office validation evidence:

- [ ] `python -m pytest -q` reports 54 passed.
- [ ] `python -m ruff check office2md tests` reports all checks passed.
- [ ] 5-file validation includes `technical_drawing_pdf: 1`.
- [ ] 5-file validation includes `manual_pdf: 1`.
- [ ] 5-file validation includes `process_development_presentation: 1`.
- [ ] 5-file validation includes `mpdp_table_xlsx: 1`.
- [ ] 5-file validation includes `release_rationale_docx: 1`.
- [ ] Wiring Diagram preserves `drawing_number=ENG-186350`.
- [ ] Wiring Diagram preserves `project_number/order_number=SY909735`.
- [ ] Wiring Diagram includes parsed `drawing_index`.
- [ ] Operation Manual Page 1 is `Title Page`.
- [ ] Operation Manual `document_type` is `operating manual`.
- [ ] PPTX chunks use `evidence_type: slide`.
- [ ] PPTX source maps include `slide_number`, `locator`, and `slide_title`.
- [ ] PPTX `document.md` includes `Presentation Summary`, `Key Project Metadata`, `Slide Index`, `Topic Outline`, `Process Development Narrative`, and `Batch Study Summary`.
- [ ] PPTX `batch_study_summary` includes `confidence`, `evidence_slides`, `evidence_snippet`, and `locators`.
- [ ] PPTX batch accuracy check records `VL322673` as `Shake stability fail`, not `pass`.
- [ ] PPTX batch accuracy check records `VL324017` as `Success` with Slide 20 evidence retained.
- [ ] PPTX batch accuracy check does not infer a result status for `VL326528` without direct evidence.
- [ ] PPTX Slide 14 `Feasibility study for Pilot Scale-up` is not classified as `Micro / Risk Assessment`.
- [ ] XLSX chunks use `evidence_type: table`.
- [ ] XLSX MPDP outputs include phase-level `table_section` chunks for PFA / Pilot / Practice / Pre-Production / Production.
- [ ] XLSX source maps include `sheet_name`, `table_name`, `row_start`, and `row_end`.
- [ ] DOCX release rationale metadata is extracted into `knowledge.json`.
- [ ] DOCX release rationale `document.md` includes `Release Summary`, `Key Release Metadata`, `Key Process Parameters`, and `Recommendation`.
- [ ] Office embedded image counts are recorded without exporting Office images.
- [ ] Office missing asset counts and warnings are recorded without blocking conversion.
- [ ] Office image references are counted and warned only; no Office embedded images are extracted in rc5.
- [ ] Real Office image extraction is deferred to Phase 2.9B.
