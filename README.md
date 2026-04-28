# office2md

`office2md` converts Office, PDF, and text-like files into Markdown output that is easier to ingest into a knowledge base or RAG pipeline.

The current pipeline has three stages:

1. Document conversion from Office/PDF/text-like files.
2. Per-document Knowledge Pack generation with metadata, chunks, entities, manifests, and source maps.
3. Knowledge Library Builder for SQLite FTS search, JSON graph output, Markdown portal pages, and interop JSONL exports.

v0.2.0-rc1 remains local and no-AI by default. Embedding/vector search is not included in this release; Phase 3.1 is the planned place for optional embedding/vector search on top of the SQLite/FTS foundation.

## Install

Python 3.10+ is required by the upstream conversion engines. On this Windows machine, Python 3.11 is recommended:

```bash
cd office2md
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

On macOS/Linux, activate with:

```bash
source .venv/bin/activate
```

## Usage

```bash
office2md --help
office2md doctor
office2md doctor-ai
office2md doctor-docling
office2md warmup-docling
office2md convert ./input ./output --recursive
office2md convert-file ./input/example.pdf ./output
```

Engine selection:

```bash
office2md convert ./input ./output --engine auto --recursive
office2md convert ./input ./output --engine docling
office2md convert ./input ./output --engine markitdown
```

Output profiles:

```bash
office2md convert ./input ./output --profile kb
office2md convert ./input ./output --profile rag
office2md convert ./input ./output --profile memory
office2md convert ./input ./output --profile obsidian
```

The default profile is `kb`. `kb`, `rag`, and `memory` use standard Markdown image links such as `![Page 1](assets/page_001.png)`. Only `--profile obsidian` uses Obsidian wiki image links such as `![[assets/page_001.png]]`.

Visual-heavy PDF page rendering:

```bash
office2md convert ./input ./output --recursive --engine auto --render-pdf-pages --max-render-pages 3
```

Optional AI framework is disabled by default:

```bash
office2md convert ./input ./output --use-ai --ai-backend cli --ai-command "your-command"
```

Supported backend values are `none`, `http`, `openai-compatible`, `cli`, and `minimax`. The current framework does not call any AI service unless `--use-ai` is explicitly set.

Recommended production commands:

```bash
office2md convert ./input ./output --recursive --profile kb
office2md convert-file input.pdf output --profile kb --render-pdf-pages --max-render-pages 5
office2md convert-file input.pdf output --profile kb --use-ai --ai-backend cli --ai-command "<your-ai-cli-command>"
```

For functional/manual PDFs, extract all page text while rendering only a small visual sample:

```bash
office2md convert-file input.pdf output --profile kb --render-pdf-pages --max-render-pages 10 --extract-all-page-text
```

For technical drawings, keep both image rendering and text extraction bounded:

```bash
office2md convert-file input.pdf output --profile kb --render-pdf-pages --max-render-pages 5 --max-text-pages 5
```

Office Knowledge Pack examples:

```bash
office2md convert-file process-development-deck.pptx output --profile kb
office2md convert-file mpdp-table.xlsx output --profile kb
office2md convert-file release-rationale.docx output --profile kb
```

Process-development PPTX decks can produce knowledge-facing structure before the raw slide content:

- `Presentation Summary`
- `Key Project Metadata`
- `Slide Index`
- `Topic Outline`
- `Process Development Narrative`
- `Batch Study Summary`

PPTX slide chunks and source maps include `slide_number`, `slide_title`, `topic_label`, `locator`, and visual-review flags. Process-development batch summaries include `batch_id`, batch size, route/equipment, M4E parameter, result/status, `confidence`, `evidence_slides`, `locators`, and `evidence_snippet` when the evidence is present in slide text.

XLSX MPDP files can produce sheet/table provenance and phase-level `table_section` chunks for PFA, Pilot, Practice, Pre-Production, and Production. DOCX release rationale files can extract release metadata and add `Release Summary`, `Key Release Metadata`, `Key Process Parameters`, and `Recommendation` while preserving raw content.

Office image export is intentionally deferred to Phase 2.9B. Current Office outputs record `embedded_images_count`, `missing_assets_count`, and manifest warnings when image references are present, but embedded Office images are not exported.

For large real directories, inspect first and then cap the first real run:

```bash
office2md convert ./input ./output --recursive --dry-run --include "*.pdf"
office2md convert ./input ./output --recursive --max-files 5
```

Batch safety controls:

```bash
office2md convert ./input ./output --recursive --dry-run --include "*.pdf" --exclude "*backup*"
office2md convert ./input ./output --recursive --max-files 10
```

## Knowledge Library Builder

Phase 3.0 can build a local library-level database from an existing office2md output root. It does not reconvert source files and does not call AI, OCR, Marker, or external APIs.

```bash
office2md build-library ./output ./library
office2md library-report ./library
office2md search-library ./library/library.db "M4E viscosity"
```

`build-library` reads document output folders containing `manifest.json`, `knowledge.json`, `entities.json`, `source_map.json`, `chunks.jsonl`, and `document.md`. Missing optional files are recorded as warnings, and failed manifests are skipped.

Library outputs include:

- `library.db` with relational tables and SQLite FTS5 search.
- `library_manifest.json`.
- `library_index.json`.
- `library_graph.json`.
- `_library.md`, `_documents.md`, `_entities.md`, `_topics.md`, `_batches.md`, and `_quality_report.md`.
- `exports/llamaindex_documents.jsonl`.
- `exports/haystack_documents.jsonl`.
- `exports/txtai_rows.jsonl`.
- `exports/graphrag_input.jsonl`.

Interop exports are plain JSONL files. LlamaIndex, Haystack, txtai, and GraphRAG are not required dependencies.

v0.2.0-rc1 does not create embeddings or a vector database. Phase 3.1 may add optional embedding/vector search as a separate layer.

## Supported Formats

The scanner accepts `.pdf`, `.docx`, `.doc`, `.pptx`, `.ppt`, `.xlsx`, `.xls`, `.html`, `.htm`, `.txt`, `.csv`, `.json`, and `.md`.

The MVP routes PDF to Docling first, modern Office/text-like formats to MarkItDown, and old Office formats through LibreOffice when available before MarkItDown conversion. In `--engine auto` mode, a Docling PDF failure falls back to MarkItDown. Successful fallback output records `fallback_used: true` in `manifest.json`. A failed manifest is written only when all attempted engines for that file fail.

## Output Structure

Each source file writes an isolated output folder:

```text
output/
  source-file-slug/
    document.md
    document.raw.md
    document.json
    chunks.jsonl
    manifest.json
    knowledge.json
    entities.json
    source_map.json
    assets/
```

`document.md` includes YAML frontmatter with source filename, absolute path, file type, converter, converted time, checksum, and OCR flag.

`manifest.json` includes `source_file`, `source_path`, `checksum`, `engine`, `status`, `converted_at`, `warnings`, and `errors`.

`knowledge.json` captures title, summary placeholder, key metadata, tags, document kind, quality status, chunk count, asset count, and source file.

`entities.json` uses local rules only. It can identify terms such as Symex, CML125, wiring diagram, PLC, terminal, valve, motor, pump, and control panel.

`source_map.json` maps chunk IDs back to source file, page number, image path, and heading path.

The output root also includes:

```text
_index.md
_index.json
```

`_index.md` is standard Markdown by default. With `--profile obsidian`, index document links use Obsidian wiki-link syntax.

For visual-heavy PDFs such as wiring diagrams, drawings, schematics, layouts, and plans, Phase 1.5 adds lightweight structure without OCR, LLM, or Marker:

- `document_kind` identifies likely `technical_drawing_pdf` files using filename heuristics.
- `quality_status` is set to `low_structure` when a PDF fallback is used, headings are missing, or `document.json` has no useful structure.
- `--render-pdf-pages` renders PDF pages to `assets/page_001.png`, limited by `--max-render-pages`.
- technical drawing Markdown includes document classification, page image references, and extracted text.
- `document.json` includes a `pages` array with rendered image paths when page rendering is enabled.

## AI Adapter Framework

AI enrichment is opt-in. By default:

- `--use-ai` is false.
- `--ai-backend` is `none`.
- No API key is read.
- No API, CLI, or external command is called.
- No file is uploaded.
- MiniMax CLI is not required for normal operation.

When AI is enabled, enrichment is additive only. It can create `ai_notes.md`, add AI sections to `document.md`, and add an `ai` field to `knowledge.json`. It does not overwrite source text, raw Markdown, rendered assets, or chunks. If AI fails, conversion continues and the warning is written to `manifest.json`.

The CLI backend passes the prompt to `--ai-command` over stdin and reads stdout. The MiniMax adapter is a placeholder and does not hard-code an endpoint or model.

### Optional AI Integration

MiniMax CLI, if installed separately, can be used through the generic CLI adapter. It is not part of the required install path:

```bash
office2md doctor-ai
office2md convert-file input.pdf output --profile kb --use-ai --ai-backend cli --ai-command "<your-minimax-cli-command>"
```

If the MiniMax CLI is missing, `doctor-ai` reports it as an optional integration that is not installed. Core conversion, Knowledge Pack output, page rendering, chunks, source maps, and indexes still work.

## Doctor

`office2md doctor` checks Python, import availability for Docling, MarkItDown, and Marker, plus local tools such as LibreOffice, Poppler, and Tesseract.

## Common Issues

Docling and MarkItDown are external dependencies. If `doctor` reports them missing, install the project with `pip install -e ".[dev]"`.

Old `.doc`, `.ppt`, and `.xls` files require LibreOffice or `soffice` on `PATH`.

PDF conversion can fail if Docling needs model downloads or optional system libraries. In `--engine auto` mode, the converter tries MarkItDown as a fallback and records that fallback in the manifest. The batch converter records a failed manifest for that file only if fallback conversion also fails, then continues with the remaining files.

## Docling Troubleshooting

Docling may need to download models or initialize local caches the first time it processes a PDF. On company networks or unstable connections this can fail with errors such as `LocalEntryNotFoundError`, `ConnectError`, or Windows `WinError 10054`.

Run a focused diagnostic:

```bash
office2md doctor-docling
```

Run a warm-up before batch conversion:

```bash
office2md warmup-docling
```

The diagnostic prints Python and Docling version details, whether `DocumentConverter()` can be created, whether a tiny PDF fixture can be converted, a concise traceback on failure, and non-secret proxy/cache environment variables such as `HTTP_PROXY`, `HTTPS_PROXY`, `HF_HOME`, `HUGGINGFACE_HUB_CACHE`, and `TRANSFORMERS_CACHE`.

If warm-up fails, check proxy settings and retry under a stable network. `--engine auto` fallback remains available through MarkItDown, but PDF output may be marked `quality_status: low_structure`.

## Acceptance

```bash
office2md --help
office2md doctor
office2md doctor-docling
python -m pytest -q
office2md convert ./acceptance_input ./acceptance_output --recursive
office2md convert ./acceptance_input ./acceptance_output --recursive --render-pdf-pages --max-render-pages 1
```

Real Symex wiring diagram single-file check:

```powershell
.\.venv\Scripts\office2md convert-file "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex\CML125\SY909735\02. Design Documents\02. Electrical and software design\01 Wiring diagram with E-Parts list\SY909735_Wiring diagram_Revision B_preliminary_08_10_2018.pdf" "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex_phase21_test" --engine auto --profile kb --render-pdf-pages --max-render-pages 5
```

## Roadmap

Near term:

- Validate Knowledge Pack quality on representative real Symex files.
- Phase 2.9B: real Office image extraction for embedded DOCX/PPTX assets and image reference repair.
- Add MiniMax CLI-based AI enrichment for summaries, tags, entities, and page notes.
- Improve memory/RAG-oriented chunk quality.

Later:

- Marker integration.
- OCR controls.
- Image captioning.
- Table repair.

## Upstream Projects

This project intentionally delegates conversion work to established open-source engines:

- Docling: https://github.com/docling-project/docling
- MarkItDown: https://github.com/microsoft/markitdown
- Marker: https://github.com/datalab-to/marker
