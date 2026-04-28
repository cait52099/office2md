# office2md v0.1.0-rc4 Release Notes

Release candidate focused on full-page PDF text extraction and section-aware manual/functional Knowledge Packs while keeping image rendering bounded.

## Full-Page PDF Text Extraction

PDF text extraction is now decoupled from PDF page image rendering:

- `--max-render-pages` controls only rendered page images in `assets/`.
- `--max-text-pages` controls how many PDF pages are read with `page.get_text("text")`.
- `--extract-all-page-text` extracts text from every PDF page without rendering every page as an image.

This allows manual and functional-description PDFs to build searchable section-aware Knowledge Packs without producing large image asset folders.

## New CLI Options

```bash
office2md convert-file input.pdf output --profile kb --render-pdf-pages --max-render-pages 10 --extract-all-page-text
office2md convert-file input.pdf output --profile kb --render-pdf-pages --max-render-pages 5 --max-text-pages 5
```

## Functional Description Golden Sample

Command shape:

```bash
office2md convert-file "<Functional Description PDF>" "<output>\functional_description_fulltext" --engine auto --profile kb --render-pdf-pages --max-render-pages 10 --extract-all-page-text
```

Validation result:

- `pages_count`: 61
- `text_pages_count`: 61
- `rendered_pages_count`: 10
- `chunks_count`: 167
- `page_chunks_count`: 61
- `searchable_page_chunks_count`: 61
- `section_chunks_count`: 106
- `section_chunks_with_body_count`: 106

Evidence distribution:

- `page`: 10
- `text_page`: 51
- `section`: 106

Section-aware reconstruction covers the document from `1 Safety` through `7 Fault Messages`, with section provenance available through `source_map.json`.

## Wiring Diagram Regression Check

Command shape:

```bash
office2md convert-file "<Wiring Diagram PDF>" "<output>\wiring" --engine auto --profile kb --render-pdf-pages --max-render-pages 5 --max-text-pages 5
```

Validation result:

- `pages_count`: 5
- `text_pages_count`: 5
- `rendered_pages_count`: 5

Evidence distribution:

- `page`: 5

The technical drawing page-evidence path remains stable and is not affected by section-aware manual reconstruction.

## Provenance Model

Chunks and source maps now distinguish:

- `page`: rendered page image plus searchable page text.
- `text_page`: searchable page text without a rendered image.
- `section`: section-aware chunk reconstructed from page text.
- `image`: image-only page evidence.

## No-AI Core Path

rc4 remains a no-AI release candidate:

- No MiniMax required.
- No AI API required.
- No OCR required.
- No Marker required.

AI remains optional and disabled by default.

## Docling Fallback Status

Docling remains the preferred PDF engine in `--engine auto`, but on this machine Docling PDF conversion is still expected to fail because model download/network access is unavailable.

This is not a blocker. Auto mode falls back to MarkItDown, conversion continues, and manifests record fallback behavior.

## Suggested Local Git Commands

If this directory should become a local git release:

```bash
git init
git add .
git commit -m "Release v0.1.0-rc4"
git tag v0.1.0-rc4
```
