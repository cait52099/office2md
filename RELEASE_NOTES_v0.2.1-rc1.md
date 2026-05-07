# office2md v0.2.1-rc1 Release Notes

Release candidate focused on v0.2.1 P1-1: optional query diagnostics for `search-library`.

This release does not change default search behavior or ranking. It does not add vector search, embeddings, OCR, AI/MiniMax, cloud/network dependencies, Office image export, or legacy `.doc` conversion.

## Query Diagnostics

Added optional CLI diagnostics:

```bash
office2md search-library ./library/library.db "vacuum pump fault" --diagnostics
```

Diagnostics explain how a query was handled without changing search results.

The diagnostics output includes:

- original query
- effective query
- mode: `fts` or `token_fallback`
- alias used, if any
- normalized query, if any
- token fallback status
- fallback tokens
- applied filters
- result count
- top evidence types
- top document kinds
- locator coverage
- short human-readable hints

Diagnostics work with aliases, normalized queries, token fallback, `--facets`, `--context`, `--output-dir`, and `--entity`.

## Validation

```bash
python -m pytest
64 passed

python -m ruff check .
All checks passed!
```

Smoke diagnostics passed against the existing CML125 full-directory library for:

- `SY909735`
- Chinese "cooling water"
- `1THLS200`
- `vacuum pump fault`
- `agitator temperature problem`
- `homogenizer cooling`
- `alarm history`

## Explicit Non-Goals

v0.2.1-rc1 does not add:

- vector search
- embeddings
- OCR
- AI/MiniMax
- cloud or network dependency
- Office image export
- default ranking changes
- legacy `.doc` conversion
