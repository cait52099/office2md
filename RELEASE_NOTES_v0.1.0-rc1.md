# office2md v0.1.0-rc1 Release Notes

Release candidate for the local Office/PDF to knowledge-base-ready Markdown MVP.

## Scope

- Batch conversion CLI with `convert`, `convert-file`, and `doctor`.
- MarkItDown conversion for Office/text-like formats.
- Docling as the primary PDF engine in `--engine auto`.
- MarkItDown fallback when Docling PDF conversion fails in `--engine auto`.
- Manifest, YAML frontmatter, raw markdown, document JSON, chunks JSONL, and assets directory output.
- Phase 1.5 visual-heavy PDF support via `--render-pdf-pages`.
- Phase 1.6 Docling diagnostics via `doctor-docling` and `warmup-docling`.

## Docling Status On Current Machine

- Docling import succeeds.
- `DocumentConverter()` initialization succeeds.
- Docling PDF fixture conversion currently fails on this machine with:
  - `huggingface_hub.errors.LocalEntryNotFoundError`
  - `ConnectError`
  - Windows `WinError 10054`
- This appears to be a model download or network/proxy issue, not an office2md pipeline bug.

## Fallback Behavior

- In `--engine auto`, PDF files are attempted with Docling first.
- If Docling conversion fails, office2md falls back to MarkItDown.
- Successful fallback writes `fallback_used: true` in `manifest.json`.
- Fallback PDF output may be marked `quality_status: low_structure`.

## Technical Drawing PDF Support

For likely technical drawing PDFs such as wiring diagrams, drawings, schematics, layouts, and plans:

```bash
office2md convert-file input.pdf output --engine auto --render-pdf-pages --max-render-pages 5
```

The output includes:

- `document_kind: technical_drawing_pdf`
- `quality_status: low_structure` when structure is limited
- `assets/page_001.png`, etc.
- Markdown page image links such as `![Page 1](assets/page_001.png)`
- `document.json` pages with image paths
- page/image-based chunks instead of one large unstructured chunk

## Recommended Before v0.1.0

- Resolve Docling warm-up on the target network or configure proxy/cache settings.
- Run:

```bash
office2md doctor-docling
office2md warmup-docling
```

- Validate 2-3 representative real PDFs before tagging final `v0.1.0`.
- Keep Marker, OCR, and LLM integrations out of v0.1.0 unless explicitly promoted to a later phase.

