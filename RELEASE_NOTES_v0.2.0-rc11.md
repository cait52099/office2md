# office2md v0.2.0-rc11 Release Notes

Release candidate focused on Phase 3.1d release-readiness documentation cleanup.

v0.2.0-rc11 is docs-only. It does not change conversion logic, search code, dependencies, or validation behavior.

## Documentation Updates

Updated the README to reflect the current v0.2.0-rc10 capability set:

- document conversion and per-document Knowledge Pack output
- Knowledge Library Builder
- SQLite/FTS search
- token fallback
- facets, filters, and related-context search output
- conservative alias/normalization behavior
- chunked/resume runner for large OneDrive-backed CML125-style validation
- no OCR, AI/MiniMax, embeddings/vector search, cloud dependency, Office image export, or legacy `.doc` conversion in the validated release path

The known limitations are now stated more clearly:

- legacy `.doc` is unsupported/fragile in the validated v0.2.0 path
- Docling may fallback to MarkItDown
- Office image export is not implemented
- full-directory OneDrive conversion may need the chunked/resume runner

Also updated the rc10 release notes to avoid non-ASCII alias text rendering issues in Windows console output by describing Chinese alias coverage in ASCII-safe terms.

## Validation

```bash
python -m pytest
63 passed

python -m ruff check .
All checks passed!
```

## Explicit Non-Goals

v0.2.0-rc11 does not add:

- vector search
- embeddings
- OCR
- AI/MiniMax
- cloud or network dependency
- Office image export
- SQLite/FTS replacement
- legacy `.doc` conversion
