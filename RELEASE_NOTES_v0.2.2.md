# office2md v0.2.2 Release Notes

v0.2.2 is a focused usability polish release on top of v0.2.1. It adds machine-readable search diagnostics, search result export, runner final summary output, and CLI help wording consistency.

This release does not change search core behavior, ranking, aliases, token fallback logic, conversion behavior, runner process-control behavior, output schemas, or result ordering.

It does not add vector search, embeddings, OCR, AI/MiniMax in the validated path, cloud/network dependencies, Office image export, or legacy `.doc` conversion.

## Search Diagnostics JSON

`search-library --diagnostics-json` appends a stable machine-readable diagnostics JSON block after normal search output.

Diagnostics JSON includes:

- original query
- effective query
- mode: `fts` or `token_fallback`
- alias and normalization metadata
- token fallback status and fallback tokens
- filters
- result count and shown count
- top evidence types
- top document kinds
- locator coverage
- hints
- compact result summaries

The default output without `--diagnostics-json` remains unchanged.

## Search Result Export

`search-library --export-json PATH` writes UTF-8 pretty JSON search results for scripts, review, and release evidence. Parent directories are created automatically.

The export includes:

- query metadata
- diagnostics summary
- result count
- shown count
- results

Each exported result includes rank, chunk ID, document title, source file, document kind, evidence type, locator, output directory, and preview.

`--export-json` works with normal FTS search, token fallback, aliases/normalization, `--diagnostics`, `--diagnostics-json`, `--facets`, `--context` / `--related`, `--output-dir`, and `--entity`.

## Runner Final Summary

`scripts/Invoke-Office2MdChunkedConvert.ps1` now prints an output-only final summary for dry runs, successful runs, and max-attempts stops.

The summary includes input/output/log paths, mode, supported file count, expected unique manifest count, final manifest count, completed expected manifest count, failed manifest count, attempts used, timeout/restart count, max attempts, timeout minutes, target reached, final status, log location, and the next recommended `build-library` command.

Runner launch, timeout/retry, process-control, scanner/counting, resume, and conversion behavior are unchanged.

Known existing behavior remains: the timeout branch can print even if a manifest is produced and the target is reached. v0.2.2 does not change that process-control behavior; the final summary shows the actual target status.

## CLI Help Consistency

CLI help wording was clarified for:

- `build-library`
- `search-library --context` / `--related`
- `search-library --diagnostics-json`
- `search-library --export-json`
- conversion AI/OCR/LLM flags

No option names, defaults, output schemas, result ordering, or command behavior changed.

## Final Validation

```bash
python -m pytest
69 passed

python -m ruff check .
All checks passed!
```

Help checks passed for:

- `python -m office2md.cli convert --help`
- `python -m office2md.cli build-library --help`
- `python -m office2md.cli search-library --help`
- `python -m office2md.cli locate-document --help`
- `python -m office2md.cli library-report --help`

Compact CML125 full-library smoke checks passed for:

- `SY909735 --limit 3 --diagnostics-json`
- Chinese "cooling water" with diagnostics JSON
- `vacuum pump fault --limit 3 --diagnostics-json`
- `vacuum pump fault --limit 3 --export-json`
- `vacuum pump fault --limit 3 --diagnostics --facets --context 2 --diagnostics-json`
- `locate-document SY909735`
- `library-report`

Runner dry-run smoke passed for CML125 `-MaxFiles 3 -DryRun`, reporting supported files `598`, expected unique manifests `3`, attempts used `0`, and final status `dry-run`.

## Explicit Non-Goals

v0.2.2 does not include:

- search core changes
- ranking changes
- alias changes
- token fallback logic changes
- conversion behavior changes
- runner process-control changes
- output schema changes
- result ordering changes
- vector search
- embeddings
- OCR
- AI/MiniMax in the validated path
- cloud/network dependency
- Office image export
- legacy `.doc` conversion
