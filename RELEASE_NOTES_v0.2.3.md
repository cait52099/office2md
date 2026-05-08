# office2md v0.2.3 Release Notes

v0.2.3 is a focused release-evidence and reporting polish release on top of v0.2.2. It adds machine-readable `library-report` export, a copy-paste demo/evidence package, and an Office-derived locator audit.

This release does not change search core behavior, ranking, aliases, token fallback logic, conversion behavior, runner process-control behavior, library-report metrics/scoring, or Office locator behavior.

It does not add vector search, embeddings, OCR, AI/MiniMax, cloud/network dependencies, Office image export, legacy `.doc` conversion, or broad Office provenance/locator refactoring.

## Library Report JSON Export

`library-report --export-json PATH` writes UTF-8 pretty JSON for scripts, release evidence, and automation. Parent directories are created automatically.

The normal report table still prints, and the default `library-report` output without `--export-json` remains unchanged.

The JSON export reuses the existing `library_report()` result dictionary directly. It does not recalculate metrics or scoring through a separate path.

The export includes report fields such as:

- document, chunk, and entity counts
- document kind distribution
- evidence type distribution
- top entities
- top batches
- missing assets summary
- low quality documents
- page-level PDF documents
- noisy chunks count
- chunks without locator
- noisy documents
- HMI translation documents
- generated export file names

## Demo Evidence Package

`docs/usage/demo_evidence_package.md` provides copy-paste PowerShell examples for validating the current local library workflow:

- environment checks
- `library-report`
- `library-report --export-json`
- `search-library --diagnostics-json`
- `search-library --export-json`
- `locate-document`
- runner `-MaxFiles 3 -DryRun`

`docs/usage/common_workflows.md` links to the demo evidence package.

The demo package records current CML125 reference evidence:

- `documents_count`: 587
- `chunks_count`: 4238
- `entities_count`: 365
- `noisy_chunks_count`: 0
- `low_quality_documents`: 85
- `page_level_pdf_documents`: 493
- supported files: 598
- expected unique manifests: 588

## Office-Derived Locator Audit

`docs/design/v023_office_locator_audit.md` records an audit of chunks without locator in the existing full CML125 library.

Current locator coverage:

- total chunks: 4238
- chunks with locator: 3776
- chunks without locator: 462

Missing locators by extension:

- `.docx`: 457
- `.xlsx`: 3
- `.pptx`: 2

The audit concludes that missing locators are already absent in `chunks.jsonl` and `source_map.json`; `source_map` provenance is `raw_markdown`; generic Office files fall through to `chunk_markdown()`; and the library builder preserves data correctly.

Recommendation: small report/diagnostic improvement only. v0.2.3 intentionally does not add XLSX/PPTX locator polish or broad Office locator refactoring.

## Final Validation

```bash
python -m pytest
70 passed

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

- `library-report`
- `library-report --export-json`
- `search-library "vacuum pump fault" --limit 3 --diagnostics-json`
- `search-library "vacuum pump fault" --limit 3 --export-json`
- `locate-document "SY909735"`

The final library-report JSON smoke recorded:

- `documents_count`: 587
- `chunks_count`: 4238
- `entities_count`: 365
- `noisy_chunks_count`: 0
- `chunks_without_locator`: 462
- `low_quality_documents`: 85
- `page_level_pdf_documents`: 493

Runner dry-run smoke passed for CML125 `-MaxFiles 3 -DryRun`, reporting supported files `598`, expected unique manifests `3`, attempts used `0`, and final status `dry-run`.

## Explicit Non-Goals

v0.2.3 does not include:

- new features beyond the scoped report/export/docs/audit work
- search core changes
- ranking changes
- alias changes
- token fallback logic changes
- conversion behavior changes
- runner process-control changes
- library-report metrics or scoring changes
- Office locator behavior changes
- vector search
- embeddings
- OCR
- AI/MiniMax
- cloud/network dependency
- Office image export
- legacy `.doc` conversion
- broad Office provenance or locator refactor
