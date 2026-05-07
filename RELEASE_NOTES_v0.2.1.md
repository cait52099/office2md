# office2md v0.2.1 Release Notes

v0.2.1 is a focused usability release on top of the validated v0.2.0 release. It improves `search-library` diagnostics, narrow token fallback ranking for two validated weak query patterns, quality report wording, CLI help text, and common workflow documentation.

This release does not add vector search, embeddings, OCR, AI/MiniMax, cloud/network dependencies, Office image export, or legacy `.doc` conversion.

## Search Diagnostics

`search-library --diagnostics` is now available as an optional flag. It explains query handling without changing default output or search behavior.

Diagnostics include:

- original query
- effective query
- mode: `fts` or `token_fallback`
- alias or normalization use
- token fallback status and fallback tokens
- applied filters
- result count
- top evidence types
- top document kinds
- locator coverage
- human-readable hints

Diagnostics work with aliases, normalized queries, token fallback, `--facets`, `--context`, `--output-dir`, and `--entity`.

## Token Fallback Ranking

Token fallback now gathers a bounded internal candidate pool before applying display `--limit`. This makes fallback less sensitive to small display limits.

Fallback ranking now prefers chunks matching more query tokens before applying existing locator, evidence type, and noise preferences.

For failure-intent fallback queries, `fault_catalog_pdf` receives a narrow fallback-only boost when tokens include terms such as `fault`, `error`, `alarm`, `problem`, or `trouble`. This does not affect normal FTS results.

Validated CML125 improvements:

- `vacuum pump fault --limit 10 --diagnostics` returns `Faults and measures catalog_SY909735_AH.pdf`, Page 3 as rank 1.
- `agitator temperature problem --limit 10 --diagnostics` returns `Faults and measures catalog_SY909735_AH.pdf`, Page 5 and Page 8 as ranks 1 and 2.
- Exact FTS remains unchanged for `SY909735`, `1V2005`, `2M2001`, and `vacuum pump`.
- Alias/normalization behavior remains unchanged for Chinese "cooling water" and `1THLS200`.

## Usability Polish

Quality report empty-state wording is clearer for explicit count sections:

- page-level searchable PDFs with count `0` report that no page-level searchable PDFs were detected.
- noisy chunks with count `0` report that no noisy chunks were detected.

Added `docs/usage/common_workflows.md` with PowerShell examples for:

- single document conversion
- directory conversion
- `build-library`
- `library-report`
- `search-library` basic queries
- `search-library --diagnostics`
- `search-library --facets`
- `search-library --context 2`
- `search-library --output-dir`
- `search-library --entity`
- `locate-document`
- CML125 / OneDrive full-directory validation with the chunked/resume runner

CLI help wording was lightly clarified for `convert`, `build-library`, `search-library`, `locate-document`, and `library-report`. No CLI behavior changed.

## Final Validation

```bash
python -m pytest
67 passed

python -m ruff check .
All checks passed!
```

Representative help commands passed:

- `python -m office2md.cli convert --help`
- `python -m office2md.cli build-library --help`
- `python -m office2md.cli search-library --help`
- `python -m office2md.cli locate-document --help`
- `python -m office2md.cli library-report --help`

Compact CML125 full-library smoke checks passed for:

- `SY909735 --diagnostics`
- Chinese "cooling water" with alias diagnostics
- `1THLS200 --diagnostics`
- `vacuum pump fault --diagnostics`
- `agitator temperature problem --diagnostics`

## Explicit Non-Goals

v0.2.1 does not include:

- vector search
- embeddings
- OCR
- AI/MiniMax in the validated path
- cloud/network dependency
- Office image export
- legacy `.doc` conversion
- broadened aliases
- changes to exact FTS behavior
