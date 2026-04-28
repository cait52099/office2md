# office2md v0.1.0-rc3 Release Notes

Release candidate focused on production readiness of the no-AI Knowledge Pack pipeline after small-batch real PDF validation.

## 50-File PDF Validation

Real PDF small-batch validation completed successfully:

- Success: 50
- Failed: 0
- Skipped: 0

Document kind distribution:

- `generic_pdf`: 45
- `technical_drawing_pdf`: 5

Quality status distribution:

- `low_structure`: 42
- `visual_only`: 8

Extraction status distribution:

- `text`: 42
- `image_only`: 8

## Image-Only Technical Drawings

Image-only drawing PDFs are now explicitly marked for downstream RAG and memory systems:

- `quality_status: visual_only`
- `extraction_status: image_only`
- `requires_ocr_or_vision: true`

Page images remain preserved as source evidence, and `source_map.json` keeps page-level image provenance for visual review and future OCR/vision enhancement.

## Core No-AI Knowledge Pack Path

The core pipeline remains fully usable without AI:

- No MiniMax CLI required.
- No AI API required.
- No Marker required.
- No OCR required.
- No successful Docling conversion required.

Recommended no-AI command:

```bash
office2md convert ./input ./output --recursive --profile kb
```

## Docling Fallback Status

Docling remains the preferred PDF engine in `--engine auto`, but on this machine Docling PDF conversion is still expected to fail because model download/network access is unavailable.

This is not a blocker for rc3. Auto mode falls back to MarkItDown, conversion continues, and manifests record fallback behavior.

## Optional AI Status

AI remains optional and disabled by default:

- `--use-ai` is required before any AI adapter can run.
- MiniMax is not installed or required for the core pipeline.
- Missing AI tooling does not block conversion.
- No API key or token is required for no-AI operation.

## Current Limitations

- Docling PDF conversion is blocked on this machine by network/model-download issues.
- MiniMax CLI is not installed and is not part of the core release path.
- Marker integration is not implemented.
- OCR is not implemented.
- Image-only PDFs are preserved and flagged, but text recovery requires a future OCR/vision phase.

## Suggested Local Git Commands

If this directory should become a local git release:

```bash
git init
git add .
git commit -m "Release v0.1.0-rc3"
git tag v0.1.0-rc3
```
