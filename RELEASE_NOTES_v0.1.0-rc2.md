# office2md v0.1.0-rc2 Release Notes

Release candidate for the no-AI core Knowledge Pack pipeline.

## Core No-AI Knowledge Pack Path

office2md can run without MiniMax, without any AI backend, without Marker/OCR, and without successful Docling PDF conversion. The default output profile is `kb`, intended for AI memory systems, RAG pipelines, and knowledge-base ingestion.

Recommended command:

```bash
office2md convert ./input ./output --recursive --profile kb
```

## Knowledge Pack Outputs

Each converted document can produce:

- `document.md`
- `document.raw.md`
- `document.json`
- `manifest.json`
- `chunks.jsonl`
- `knowledge.json`
- `entities.json`
- `source_map.json`
- `assets/`

The output root can produce:

- `_index.md`
- `_index.json`

## technical_drawing_pdf Support

Likely drawing PDFs such as wiring diagrams, schematics, layouts, and plans are classified as `technical_drawing_pdf`.

Supported features:

- PDF page rendering to `assets/page_001.png`, etc.
- Page image references in `document.md`.
- Page/image-based chunks.
- Page-level source traceability through `source_map.json`.

Recommended drawing command:

```bash
office2md convert-file input.pdf output --profile kb --render-pdf-pages --max-render-pages 5
```

## Page-Level Text Extraction

When PDF pages are rendered with PyMuPDF, office2md also extracts page text via `page.get_text("text")`.

`document.json.pages[]` includes:

- `page_number`
- `source_page`
- `locator`
- `semantic_title`
- `image_path`
- `text`
- `text_char_count`

## semantic_title / source_page / locator

Page labels are separated from semantic headings:

- `semantic_title`: knowledge heading, such as `Cover Sheet` or `Table of Contents`.
- `source_page` / `page_number`: evidence page number.
- `locator`: display locator, such as `Page 1`.

`heading_path` uses `semantic_title` or `Untitled Source Page`; it does not use `Page N` as a semantic title.

## RAG/Memory Outputs

`chunks.jsonl` includes:

- `doc_id`
- `source_file`
- `source_path`
- `document_kind`
- `quality_status`
- `heading_path`
- `page_number`
- `locator`
- `semantic_title`
- `image_path`
- `text`
- `tags`
- `evidence_type`

`source_map.json` maps chunk IDs back to source file, page number, locator, semantic title, image path, heading path, and evidence type.

`knowledge.json` includes document-level metadata, tags, chunk counts, asset counts, page counts, and page text counts.

`entities.json` uses local rule extraction only.

## Docling Fallback Status

Docling remains the primary PDF engine in `--engine auto`, but on the current machine Docling PDF conversion fails during model download with Hugging Face connectivity errors such as:

- `huggingface_hub.errors.LocalEntryNotFoundError`
- `ConnectError`
- Windows `WinError 10054`

This does not block office2md. In `--engine auto`, PDF conversion falls back to MarkItDown and records `fallback_used: true` in `manifest.json`.

## Optional AI Backend

AI is disabled by default:

- No API key is required.
- No token is read.
- No AI API, CLI, or external command is called.
- MiniMax CLI is not required.

AI enrichment only runs when `--use-ai` is explicitly provided. AI output is additive only: it can add `ai_notes.md`, AI sections in `document.md`, and an `ai` field in `knowledge.json`. It does not overwrite source text or chunks.

## doctor-ai

`office2md doctor-ai` reports optional AI integration status.

If MiniMax/mmx is missing, the command reports `optional integration not installed` and exits successfully.

## Batch Safety Controls

New batch safety controls help avoid accidental long-running conversions:

```bash
office2md convert ./input ./output --recursive --dry-run --include "*.pdf"
office2md convert ./input ./output --recursive --max-files 5
office2md convert ./input ./output --recursive --include "*.pdf" --exclude "*backup*"
```

## Current Limitations

- Docling model download is currently blocked by network/proxy issues on this machine.
- MiniMax CLI is not installed on this machine.
- Marker integration is not implemented.
- OCR controls are not implemented.
- AI enrichment is optional and not part of the core no-AI path.

## Suggested Local Git Commands

If this directory should become a local git release:

```bash
git init
git add .
git commit -m "Release v0.1.0-rc2"
git tag v0.1.0-rc2
```

