# office2md v0.2.0 Release Notes

v0.2.0 is the validated local Knowledge Pack and Knowledge Library release.

This release keeps the validated path local and no-AI by default. It does not add OCR, AI/MiniMax, embeddings/vector search, cloud/network dependencies, Office image export, or legacy `.doc` conversion.

## Final Validated Scope

v0.2.0 includes:

- Office/PDF/text-like document conversion
- per-document Knowledge Pack output
- Knowledge Library Builder
- SQLite/FTS `library.db`
- `library_index.json`
- `library_graph.json`
- Markdown portal pages
- interop exports for LlamaIndex, Haystack, txtai, and GraphRAG
- `library-report`
- `search-library`
- `locate-document`
- FTS ranking
- token fallback for zero-hit multi-term queries
- facets, filters, context, and related chunks
- conservative alias/normalization for no-hit queries
- chunked/resume PowerShell runner for large OneDrive-backed CML125-style validation

## CML125 Full-Directory Validation

Final CML125 full-directory validation completed.

- supported files: 598
- expected unique manifests: 588
- final manifests: 589
- success: 587
- failed: 2 duplicate legacy `.doc` files
- failed file family: `Guide to find the devices..doc`
- OCR used: 0
- AI used: 0
- build-library: success
- documents_count: 587
- chunks_count: 4238
- entities_count: 365
- noisy_chunks_count: 0

The two failed files are duplicate legacy `.doc` inputs and are documented as known unsupported/fragile files for this release.

## Search Validation

The validated search stack uses SQLite/FTS, not embeddings.

Search features include:

- FTS ranking that prefers locator-present chunks and stronger evidence types
- token fallback for zero-hit multi-term queries
- filters for document kind, evidence type, output directory, entity, document, exclusions, and locator presence
- optional facets
- optional related/context chunks
- conservative alias and identifier normalization after the original query returns 0 hits

Representative CML125 searches pass for exact identifiers, operational terms, HMI bilingual aliases, and common technical phrases, including `SY909735`, `1V2005`, `2M2001`, `1THLS200`, `homogenizer cooling`, `alarm history`, and CML125 HMI bilingual search terms.

Known partial search cases remain:

- `vacuum pump fault`
- `agitator temperature problem`

These are treated as data coverage, ranking, or terminology follow-ups rather than release blockers.

## Known Limitations

- No OCR in the validated path.
- No AI/MiniMax in the validated path.
- No embeddings/vector search.
- No Office image export.
- Legacy `.doc` is unsupported/fragile.
- Docling may fallback to MarkItDown.
- Some Office-derived chunks may lack locators.
- OneDrive full-directory conversion may need the chunked/resume runner.

## Validation

```bash
python -m pytest
63 passed

python -m ruff check .
All checks passed!
```

## Explicit Non-Goals

v0.2.0 does not add:

- vector search
- embeddings
- OCR
- AI/MiniMax
- cloud or network dependency
- Office image export
- SQLite/FTS replacement
- legacy `.doc` conversion
