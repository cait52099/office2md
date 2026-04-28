# office2md v0.2.0-rc1 Release Notes

Release candidate focused on Phase 3.0: Knowledge Library Builder + Interop Exports.

v0.2.0-rc1 extends office2md from per-document Knowledge Pack output into a local library-level database for search, graph inspection, reporting, and downstream RAG interoperability. It does not change `convert` or `convert-file`.

## Phase 3.0 Knowledge Library Builder

New commands:

- `office2md build-library <input_output_root> <library_output_dir>`
- `office2md search-library <library_db> "<query>"`
- `office2md library-report <library_db_or_output_dir>`

`build-library` reads existing office2md output folders. It does not reconvert source files and does not modify the original output root.

## Library Outputs

`build-library` writes:

- `library.db`
- `library_manifest.json`
- `library_index.json`
- `library_graph.json`
- `_library.md`
- `_documents.md`
- `_entities.md`
- `_topics.md`
- `_batches.md`
- `_quality_report.md`
- `exports/llamaindex_documents.jsonl`
- `exports/haystack_documents.jsonl`
- `exports/txtai_rows.jsonl`
- `exports/graphrag_input.jsonl`

## SQLite Schema and FTS

`library.db` includes relational tables for:

- `documents`
- `chunks`
- `entities`
- `entity_mentions`
- `assets`
- `relations`

It also creates SQLite FTS5 tables:

- `documents_fts`
- `chunks_fts`

`search-library` searches document title/source/type/tags/entities plus chunk title/text/heading/locator.

## JSON Index and Graph

`library_index.json` summarizes:

- document count
- chunk count
- entity count
- document kind distribution
- evidence type distribution
- top entities
- per-document metadata

`library_graph.json` includes document, chunk, entity, topic, batch, and asset nodes. Edges are generated only from existing `knowledge.json`, `entities.json`, `chunks.jsonl`, and `source_map.json` evidence.

## Markdown Portal

The Markdown portal provides human-readable library entry points:

- `_library.md`: summary, distributions, key entities, topics, batches, and quality issues.
- `_documents.md`: documents grouped by `document_kind`.
- `_entities.md`: entities grouped by type and linked to documents.
- `_topics.md`: PPTX topics, manual sections, drawing index topics, and table phases.
- `_batches.md`: batch IDs with documents, locators, confidence, and snippets.
- `_quality_report.md`: failed/missing/low-quality/asset/entity/locator issues.

## Interop Exports

Plain JSONL exports are generated for downstream systems:

- `llamaindex_documents.jsonl`
- `haystack_documents.jsonl`
- `txtai_rows.jsonl`
- `graphrag_input.jsonl`

These are export files only. LlamaIndex, Haystack, txtai, and GraphRAG are not required dependencies and are not imported or called by office2md.

## 5-File Validation

Validated with the existing 5-file output root:

- `SY909735_Wiring diagram_Revision B_19_06_2019.pdf`
- `Operation manual EN.pdf`
- `43DS-LS Daily Rescue Eye Serum 20260417.pptx`
- `43DS MPDP.xlsx`
- `43DS-00-M01U PPPBC release rational.docx`

Build result:

- documents: 5
- chunks: 329
- entities: 108
- warnings: 0
- each interop export: 329 rows

Document kind distribution:

- `release_rationale_docx`: 1
- `process_development_presentation`: 1
- `mpdp_table_xlsx`: 1
- `manual_pdf`: 1
- `technical_drawing_pdf`: 1

Evidence type distribution:

- `batch_study`: 11
- `drawing_index`: 69
- `page`: 6
- `section`: 81
- `slide`: 33
- `table`: 1
- `table_section`: 5
- `text`: 18
- `text_page`: 96
- `topic`: 9

Search validation:

- `M4E viscosity` returns DOCX process adjustment and PPTX M4E/spec evidence.
- `VL324017` returns PPTX batch study evidence at Slide 20.
- `SY909735` returns Operation Manual and wiring/manual evidence.

## Test Status

```bash
python -m pytest -q
55 passed

python -m ruff check office2md tests
All checks passed!
```

## Explicit Non-Goals

v0.2.0-rc1 does not add:

- AI calls
- OCR
- Marker integration
- MiniMax/API integration
- embedding/vector database
- Office image export

Embedding/vector search is deferred to Phase 3.1 as an optional layer on top of SQLite/FTS.
