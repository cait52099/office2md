# office2md v0.2.1-rc2 Release Notes

Release candidate focused on v0.2.1 P1-2: narrow token fallback ranking improvements for `search-library`.

This release does not add aliases for the reviewed weak queries and does not change exact FTS behavior when FTS returns hits. It does not add vector search, embeddings, OCR, AI/MiniMax, cloud/network dependencies, Office image export, or legacy `.doc` conversion.

## Search Fallback Improvements

Token fallback now gathers a bounded internal candidate pool before applying the display `--limit`. This reduces cases where useful evidence is missed because each token search only collected a small number of candidates.

Fallback ranking now prefers chunks matching more query tokens before applying the existing locator, evidence type, and noise preferences.

For failure-intent token fallback queries, a narrow `fault_catalog_pdf` boost is applied only when tokens include terms such as `fault`, `error`, `alarm`, `problem`, or `trouble`. This boost is fallback-only and does not affect normal FTS results.

## CML125 Search Smoke Improvements

Against the existing CML125 full-directory library:

- `vacuum pump fault --limit 10 --diagnostics` now returns `Faults and measures catalog_SY909735_AH.pdf`, Page 3 as rank 1.
- `agitator temperature problem --limit 10 --diagnostics` now returns `Faults and measures catalog_SY909735_AH.pdf`, Page 5 and Page 8 as ranks 1 and 2.
- `vacuum pump --limit 10 --diagnostics` remains exact FTS.
- `SY909735`, `1V2005`, and `2M2001` remain exact FTS.
- Chinese "cooling water" alias behavior remains unchanged.
- `1THLS200` identifier normalization behavior remains unchanged.

Default CLI output without `--diagnostics` remains the normal search table.

## Validation

```bash
python -m pytest
67 passed

python -m ruff check .
All checks passed!
```

## Explicit Non-Goals

v0.2.1-rc2 does not add:

- vector search
- embeddings
- OCR
- AI/MiniMax
- cloud or network dependency
- Office image export
- legacy `.doc` conversion
- broader aliases or aggressive synonym expansion
- exact FTS ranking changes
