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

v0.2.0-rc1 Knowledge Library validation evidence:

- [ ] `python -m pytest -q` reports 55 passed.
- [ ] `python -m ruff check office2md tests` reports all checks passed.
- [ ] `office2md build-library` succeeds on the 5-file output root.
- [ ] `library.db` is created with documents, chunks, entities, entity_mentions, assets, relations, documents_fts, and chunks_fts.
- [ ] `library_manifest.json` is created with schema version, input root, counts, warnings count, exports count, and release label.
- [ ] `library_index.json` is created with document/evidence distributions and top entities.
- [ ] `library_graph.json` is created with document/entity/chunk/topic/batch/asset nodes.
- [ ] Markdown portal files are created: `_library.md`, `_documents.md`, `_entities.md`, `_topics.md`, `_batches.md`, `_quality_report.md`.
- [ ] `library-report` prints document kind distribution, evidence type distribution, top entities, top batches, missing assets, low quality documents, and export files.
- [ ] `search-library` returns relevant results for `M4E viscosity`.
- [ ] `search-library` returns relevant results for `VL324017`.
- [ ] `search-library` returns relevant results for `SY909735`.
- [ ] `exports/llamaindex_documents.jsonl` is generated.
- [ ] `exports/haystack_documents.jsonl` is generated.
- [ ] `exports/txtai_rows.jsonl` is generated.
- [ ] `exports/graphrag_input.jsonl` is generated.
- [ ] Each interop export has one row per chunk on the 5-file validation set.
- [ ] Original office2md output root is not modified by `build-library`.
- [ ] LlamaIndex, Haystack, txtai, and GraphRAG are not required dependencies.
- [ ] No AI, OCR, Marker, API, embedding/vector database, or Office image export is used in Phase 3.0.

v0.2.0-rc2 HMI translation and search usability validation evidence:

- [ ] `python -m pytest -q` reports 56 passed.
- [ ] `python -m ruff check office2md tests` reports all checks passed.
- [ ] HMI translation XLSX is detected as `document_kind: hmi_translation_xlsx`.
- [ ] HMI translation XLSX records `quality_status: structured_with_noise`.
- [ ] HMI single-file v2 output includes `hmi_translation_table`, `hmi_translation_group`, and `hmi_translation_row` chunks.
- [ ] HMI group chunks are reduced from 594 to 138 on the CML125 validation sample.
- [ ] HMI row chunks remain available with 250 row chunks.
- [ ] HMI chunks without locator are 0.
- [ ] HMI `document.md` does not include searchable base64-like Internal ID strings.
- [ ] HMI `document.md` does not include repeated `NaN` or all-empty `ref` columns.
- [ ] HMI group headings do not use field/control-level path tokens such as `Textfeld`, `TextField`, `Bildbaustein`, or `Symbolisches EA-Feld`.
- [ ] Library-level chunks are reduced from 1327 to 871 on the CML125 20-file validation library.
- [ ] Library-level `top_entities` aggregates `SY909735` by `normalized_text` and merges `project_number` plus `order_number`.
- [ ] `_library.md` Key Entities lists `SY909735` only once.
- [ ] `_quality_report.md` reports noisy chunks, HMI translation documents, raw text chunks, and chunks without locator.
- [ ] `_quality_report.md` includes search recommendations for HMI translation, drawing index evidence, and excluding translation documents.
- [ ] `locate-document` works with a library output directory.
- [ ] `locate-document` works with `library.db`.
- [ ] `locate-document "Translation"` returns `hmi_translation_xlsx`, 389 chunks, and output directory `copy-of-sy909735-translation-chinese-ver-1`.
- [ ] `search-library` supports `--limit` and `--offset`.
- [ ] `search-library` supports `--kind hmi_translation_xlsx`.
- [ ] `search-library` supports `--evidence drawing_index`.
- [ ] `search-library` supports `--exclude-doc Translation`.
- [ ] `search-library` supports `--has-locator`.
- [ ] `search-library "PLC" --kind hmi_translation_xlsx --limit 20` returns HMI translation results with locators.
- [ ] `search-library "PLC" --evidence drawing_index --kind technical_drawing_pdf --limit 20` returns drawing index results.
- [ ] `search-library "CIP" --exclude-doc Translation --has-locator --limit 20` excludes HMI translation results.
- [ ] `search-library "SY909735" --limit 20` returns relevant CML125/SY909735 results.
- [ ] Windows PowerShell note documents that Office temporary files `~$*` are skipped automatically and that `--exclude "~$*"` should be avoided for now.
- [ ] No AI, OCR, Marker, API, embedding/vector database, or Office image export is used in Phase 3.0.1.

v0.2.0-rc3 100-file validation and duplicate-ID checkpoint evidence:

- [ ] `python -m pytest` reports 57 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] CML125 100-file conversion completes with Success 100, Failed 0, Skipped 0.
- [ ] 100-file manifests record `ocr_used: false` and `ai_used: false`.
- [ ] `office2md build-library` succeeds on the CML125 100-file output root with duplicate checksum files present.
- [ ] 100-file library reports documents 100, chunks 1205, entities 261, warnings 0.
- [ ] 100-file evidence distribution is `drawing_index: 400`, `hmi_translation_group: 138`, `hmi_translation_row: 250`, `hmi_translation_table: 1`, `image: 27`, `page: 248`, `text: 4`, `text_page: 137`.
- [ ] 100-file quality report records noisy chunks 0 and chunks without locator 4.
- [ ] Duplicate checksum outputs receive unique library document IDs without changing non-duplicate document IDs.
- [ ] Duplicate chunk IDs receive unique library chunk IDs while preserving source-map evidence and locators.
- [ ] 100-file review library records 100 distinct document IDs and 1205 distinct chunk IDs.
- [ ] `search-library` smoke tests pass for Translation, SY909735, homogenizer, and alarm.
- [ ] No AI, OCR, Marker, API, embedding/vector database, or Office image export is used in Phase 3.0.2.

v0.2.0-rc4 Phase 3.0.3a quality/search checkpoint evidence:

- [ ] `python -m pytest` reports 60 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] CML125 100-file Phase 3.0.3a library report records `low_quality_documents: 13`.
- [ ] CML125 100-file Phase 3.0.3a library report records `page_level_pdf_documents: 84`.
- [ ] CML125 100-file Phase 3.0.3a library report records `noisy_chunks_count: 0`.
- [ ] Generic PDF subtype refinement classifies obvious datasheet, component, certificate, manual, project book, and report PDFs while leaving uncertain PDFs as `generic_pdf`.
- [ ] Search fallback marks multi-term token fallback in CLI output.
- [ ] `search-library "homogenizer cooling"` returns useful hits with `fallback: token`.
- [ ] `search-library "alarm history"` returns useful hits with `fallback: token`.
- [ ] No AI, OCR, Marker, API, embedding/vector database, or Office image export is used in Phase 3.0.3a.

v0.2.0-rc5 Phase 3.0.4 200-file validation checkpoint evidence:

- [ ] Python version is 3.11.9.
- [ ] `python -m pytest` reports 60 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] CML125 200-file conversion records 200 manifests, 200 success, and 0 failed.
- [ ] CML125 200-file manifests record OCR used 0 and AI used 0.
- [ ] Initial convert hit output-pipe/tool timeout after 103 outputs, then resumed with `--skip-existing` and redirected logs; final output is valid.
- [ ] Manifest warnings are mainly Docling fallback caused by `LocalEntryNotFoundError / WinError 10054`, not OCR or AI usage.
- [ ] `office2md build-library` succeeds with build warnings 0.
- [ ] 200-file library reports documents 200, chunks 1751, entities 267.
- [ ] 200-file document kind distribution is `datasheet_pdf: 112`, `component_document_pdf: 35`, `certificate_pdf: 25`, `manual_pdf: 9`, `generic_pdf: 8`, `technical_drawing_pdf: 4`, `report_pdf: 3`, `document: 2`, `hmi_translation_xlsx: 1`, `project_book_pdf: 1`.
- [ ] 200-file evidence distribution is `drawing_index: 400`, `hmi_translation_group: 138`, `hmi_translation_row: 250`, `hmi_translation_table: 1`, `image: 31`, `page: 508`, `section: 8`, `text: 4`, `text_page: 411`.
- [ ] 200-file quality metrics are `low_quality_documents: 16`, `page_level_pdf_documents: 181`, `noisy_chunks_count: 0`, `noisy_documents: 0`, `chunks_without_locator: 4`, `missing_assets_summary: 0`.
- [ ] Search smoke tests pass for Translation, SY909735, CML125, homogenizer cooling, alarm history, temperature probe, 1V2005, 2M2001, CIP, and seal.
- [ ] Minor `_quality_report.md` extra `_None._` formatting issue is noted as cosmetic follow-up.
- [ ] No AI, OCR, Marker, API, embedding/vector database, Office image export, full-directory validation, or Phase 3.1 work is included.

v0.2.0-rc6 Phase 3.0.5b operational runner checkpoint evidence:

- [ ] `python -m pytest` reports 60 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `scripts/Invoke-Office2MdChunkedConvert.ps1` supports `-DryRun`.
- [ ] Runner does not delete input files and only creates output/log directories.
- [ ] Runner starts `office2md convert` with `--skip-existing`.
- [ ] Runner redirects stdout and stderr to timestamped logs.
- [ ] Runner checks generated `manifest.json` files against expected output folders and compares against expected unique manifest count.
- [ ] Runner stops only the process tree it launched when an attempt exceeds timeout.
- [ ] Runner supports `-MaxFiles` and `-FullDirectory`.
- [ ] Runner uses `office2md.scanner.scan_input` plus output-directory naming behavior to calculate supported file count and expected unique manifest count.
- [ ] `-MaxFiles 3 -DryRun` reports supported files 598 and expected manifests 3.
- [ ] `-FullDirectory -DryRun` reports supported files 598 and expected unique manifests 588 for the CML125 full source.
- [ ] `docs/ops/cml125_batch_validation.md` documents why the runner exists, when to use it, 300-file and full-directory examples, and OneDrive/on-demand hydration risk.
- [ ] Legacy `.doc` failures remain documented as known unsupported files; no legacy Word conversion dependency is introduced.
- [ ] No AI, OCR, Marker, API, embedding/vector database, Office image export, full-directory validation, or Phase 3.1 work is included.

v0.2.0-rc7 Phase 3.0.6 full-directory validation and runner completion checkpoint evidence:

- [ ] `python -m pytest` reports 61 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] CML125 full-directory validation completes with supported files 598.
- [ ] Runner calculates expected unique manifests 588.
- [ ] Final conversion output contains 589 manifests.
- [ ] Final conversion records 587 success and 2 failed.
- [ ] Failed files are duplicate legacy `Guide to find the devices..doc` inputs.
- [ ] Legacy `.doc` is documented as known unsupported for Phase 3.0.
- [ ] Full-directory manifests record OCR used 0 and AI used 0.
- [ ] `office2md build-library` succeeds.
- [ ] Build warnings are 2, both failed legacy `.doc` manifests.
- [ ] Full-directory library reports documents 587, chunks 4238, entities 365.
- [ ] Full-directory quality metrics include `noisy_chunks_count: 0`.
- [ ] Search smoke and locate-document key checks pass.
- [ ] Runner completion fix requires expected output folders to contain `manifest.json`, not just total manifest count.
- [ ] `-MaxFiles 3 -DryRun` reports supported files 598 and expected unique manifests 3.
- [ ] `-FullDirectory -DryRun` reports supported files 598 and expected unique manifests 588.
- [ ] No AI, OCR, Marker, API, embedding/vector database, Office image export, legacy `.doc` conversion, external conversion dependency, or Phase 3.1 work is included.

v0.2.0-rc8 Phase 3.1a FTS search usability checkpoint evidence:

- [ ] `python -m pytest` reports 62 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] Default `search-library` remains SQLite/FTS based and does not require new flags.
- [ ] Ranking adjustments prefer locator-present chunks and stronger evidence types without removing valid hits.
- [ ] Exact lookups pass for `SY909735`, `1V2005`, and `2M2001`.
- [ ] Token fallback still works for `homogenizer cooling` and `alarm history`.
- [ ] Search output reports mode as `fts` or `token_fallback`.
- [ ] Optional `--facets` works and does not affect default search.
- [ ] Optional `--context` / `--related` works and does not affect default search.
- [ ] Optional `--output-dir` and repeatable `--entity` filters work.
- [ ] Smoke checks pass against the existing CML125 full-directory library for `temperature probe`, `S7-300`, `Operating Manual`, `seal`, and `CIP`.
- [ ] No vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, or SQLite/FTS replacement is included.

v0.2.0-rc10 Phase 3.1c conservative FTS polish checkpoint evidence:

- [ ] `python -m pytest` reports 63 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] Original `search-library` query is tried first.
- [ ] Alias and normalization run only after the original query returns 0 hits.
- [ ] CLI output reports alias or normalized query use.
- [ ] Exact lookups pass without alias/normalization for `SY909735`, `1V2005`, `2M2001`, and `S7-300`.
- [ ] Weak query smoke checks improve for `1THLS200`, `冷却水`, `报警历史`, `密封液`, `操作手册`, `CIP sequence`, `cooling circuit issue`, and `user password`.
- [ ] Existing token fallback still works for `homogenizer cooling` and `alarm history`.
- [ ] Known partial queries remain documented: `vacuum pump fault` and `agitator temperature problem`.
- [ ] No vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, SQLite/FTS replacement, or aggressive synonym expansion is included.

v0.2.0-rc11 Phase 3.1d release-readiness docs checkpoint evidence:

- [ ] `python -m pytest` reports 63 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] README reflects current v0.2.0 capabilities: Knowledge Pack, Library Builder, SQLite/FTS search, token fallback, facets/context/filters, alias/normalization, and chunked/resume runner.
- [ ] README states no OCR, AI/MiniMax, embeddings/vector search, cloud dependency, Office image export, or legacy `.doc` conversion in the validated release path.
- [ ] Known limitations are documented: legacy `.doc` unsupported/fragile, Docling fallback to MarkItDown, Office image export not implemented, and OneDrive full-directory conversion may require the runner.
- [ ] rc10 release notes avoid non-ASCII alias rendering issues in Windows console output.
- [ ] No code changes are included.

v0.2.0 final release evidence:

- [ ] `python -m pytest` reports 63 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] Final validated scope includes Office/PDF/text-like conversion, per-document Knowledge Pack, Knowledge Library Builder, SQLite/FTS `library.db`, `library_index.json`, `library_graph.json`, Markdown portal, interop exports, `library-report`, `search-library`, and `locate-document`.
- [ ] Final search scope includes FTS ranking, token fallback, facets, filters, context/related chunks, and alias/normalization for no-hit queries.
- [ ] Chunked/resume PowerShell runner is included for large OneDrive-backed CML125-style validation.
- [ ] CML125 full-directory validation completed with supported files 598, expected unique manifests 588, final manifests 589, success 587, and failed 2 duplicate legacy `.doc` files.
- [ ] Full-directory validation records OCR used 0 and AI used 0.
- [ ] Full-directory library build succeeds with documents 587, chunks 4238, entities 365, and noisy chunks 0.
- [ ] Known limitations are documented: no OCR, no AI/MiniMax in validated path, no embeddings/vector search, no Office image export, legacy `.doc` unsupported/fragile, Docling fallback to MarkItDown, some Office-derived chunks may lack locators, and OneDrive full-directory conversion may need the runner.
- [ ] Final release notes are written in `RELEASE_NOTES_v0.2.0.md`.
