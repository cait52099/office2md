# office2md v0.2.2-rc1 Release Notes

v0.2.2-rc1 starts the v0.2.2 polish track with machine-readable diagnostics for `search-library`.

This checkpoint does not change default CLI output, search core behavior, ranking, aliases, token fallback logic, conversion behavior, or library build behavior.

It does not add vector search, embeddings, OCR, AI/MiniMax, cloud/network dependencies, Office image export, or legacy `.doc` conversion.

## Machine-Readable Search Diagnostics

`search-library --diagnostics-json` is now available as an optional flag.

When enabled, `search-library` prints the normal interactive output first, then appends:

```text
diagnostics_json:
{
  ...
}
```

The JSON block is stable, simple, and intended for scripts, release evidence, and search diagnostics comparisons.

The default output without `--diagnostics-json` remains unchanged.

## JSON Fields

The diagnostics JSON includes:

- `original_query`
- `effective_query`
- `mode`
- `alias_used`
- `normalized_query`
- `token_fallback_used`
- `fallback_tokens`
- `filters`
- `result_count`
- `shown_count`
- `top_evidence_types`
- `top_document_kinds`
- `locator_coverage`
- `hints`
- `results`

Each compact result summary includes:

- `rank`
- `chunk_id`
- `document_title`
- `source_file`
- `document_kind`
- `evidence_type`
- `locator`
- `output_dir`

## Compatibility

`--diagnostics-json` works with:

- normal search table output
- `--diagnostics`
- `--facets`
- `--context` / `--related`
- `--output-dir`
- `--entity`
- alias/normalization
- token fallback

The JSON is appended after normal tables so existing interactive output remains readable.

## Validation

```bash
python -m pytest
68 passed

python -m ruff check .
All checks passed!
```

Smoke checks passed against the existing CML125 full-directory library for:

- `SY909735 --diagnostics-json`
- Chinese "cooling water" with alias diagnostics JSON
- `1THLS200 --diagnostics-json`
- `vacuum pump fault --diagnostics-json`
- `agitator temperature problem --diagnostics-json`
- `SY909735 --diagnostics --diagnostics-json`
- `vacuum pump fault --diagnostics --facets --context 2 --diagnostics-json`

## Explicit Non-Goals

v0.2.2-rc1 does not include:

- search core changes
- ranking changes
- alias changes
- token fallback logic changes
- vector search
- embeddings
- OCR
- AI/MiniMax
- cloud/network dependency
- Office image export
- legacy `.doc` conversion
