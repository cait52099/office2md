# office2md v0.2.2-rc2 Release Notes

v0.2.2-rc2 adds optional machine-readable search result export for `search-library`.

This checkpoint builds on the v0.2.2-rc1 diagnostics JSON conventions. It does not change default CLI output, search core behavior, ranking, aliases, token fallback logic, conversion behavior, or library build behavior.

It does not add vector search, embeddings, OCR, AI/MiniMax, cloud/network dependencies, Office image export, or legacy `.doc` conversion.

## Search Result JSON Export

`search-library --export-json PATH` is now available as an optional flag.

When enabled, `search-library` still prints the normal interactive console output and writes UTF-8 pretty JSON to the requested path. Parent directories are created automatically. The command also prints a concise confirmation line:

```text
export_json: PATH
```

If `--export-json` is combined with `--diagnostics-json`, the diagnostics JSON block remains printed last.

## Export Schema

The export JSON includes:

- `query`
- `diagnostics`
- `result_count`
- `shown_count`
- `results`

The `query` object includes:

- `original_query`
- `effective_query`
- `mode`
- `alias_used`
- `normalized_query`
- `token_fallback_used`
- `fallback_tokens`
- `filters`

The `diagnostics` object includes:

- `top_evidence_types`
- `top_document_kinds`
- `locator_coverage`
- `hints`

Each result includes:

- `rank`
- `chunk_id`
- `document_title`
- `source_file`
- `document_kind`
- `evidence_type`
- `locator`
- `output_dir`
- `preview`

## Compatibility

`--export-json` works with:

- normal FTS search
- token fallback
- alias/normalization
- `--diagnostics`
- `--diagnostics-json`
- `--facets`
- `--context` / `--related`
- `--output-dir`
- `--entity`

Default output without `--export-json` remains unchanged.

## Validation

```bash
python -m pytest
69 passed

python -m ruff check .
All checks passed!
```

Smoke export checks passed against the existing CML125 full-directory library for:

- `SY909735 --limit 3 --export-json ...search_export_sy909735.json`
- Chinese "cooling water" with alias export
- `vacuum pump fault --limit 3 --diagnostics-json --export-json ...search_export_vacuum_pump_fault.json`
- `vacuum pump fault --limit 3 --diagnostics --facets --context 2 --export-json ...search_export_vacuum_pump_fault_context.json`

## Explicit Non-Goals

v0.2.2-rc2 does not include:

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
