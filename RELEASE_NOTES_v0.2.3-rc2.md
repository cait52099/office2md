# office2md v0.2.3-rc2 Release Notes

v0.2.3-rc2 adds a docs-only demo/evidence package for validating and using the current local office2md library workflow after v0.2.3-rc1.

This checkpoint does not change code, default output, search core behavior, ranking, aliases, token fallback logic, conversion behavior, runner process-control behavior, or library-report metrics/scoring.

It does not add vector search, embeddings, OCR, AI/MiniMax, cloud/network dependencies, Office image export, or legacy `.doc` conversion.

## Demo Evidence Package

`docs/usage/demo_evidence_package.md` provides copy-paste PowerShell examples for:

- environment checks: virtual environment activation, Python version, pytest, and ruff
- `library-report`
- `library-report --export-json`
- `search-library --diagnostics-json`
- `search-library --export-json`
- `locate-document`
- `scripts/Invoke-Office2MdChunkedConvert.ps1 -MaxFiles 3 -DryRun`

`docs/usage/common_workflows.md` now links to the demo evidence package.

## CML125 Reference Evidence

The demo package records current CML125 reference evidence:

- `documents_count`: 587
- `chunks_count`: 4238
- `entities_count`: 365
- `noisy_chunks_count`: 0
- `low_quality_documents`: 85
- `page_level_pdf_documents`: 493
- supported files: 598
- expected unique manifests: 588

It also notes that `-MaxFiles 3 -DryRun` should report expected unique manifests `3` and final status `dry-run`.

## Operational Notes

The package documents:

- PowerShell UTF-8 environment variables
- quoting paths with spaces
- `--context` / `--related` requiring integer arguments
- no OCR, AI/MiniMax, embeddings/vector search, cloud services, or Office image export in the validated default path
- legacy `.doc` remaining unsupported or fragile

## Validation

```bash
python -m pytest
70 passed

python -m ruff check .
All checks passed!
```

Smoke checks passed against the existing CML125 full-directory library:

- `library-report --export-json`
- `search-library "vacuum pump fault" --limit 3 --diagnostics-json`
- `locate-document "SY909735"`
- runner `-MaxFiles 3 -DryRun`

## Explicit Non-Goals

v0.2.3-rc2 does not include:

- code changes
- runtime behavior changes
- search core changes
- ranking changes
- alias changes
- token fallback logic changes
- conversion behavior changes
- runner process-control changes
- library-report metrics or scoring changes
- vector search
- embeddings
- OCR
- AI/MiniMax
- cloud/network dependency
- Office image export
- legacy `.doc` conversion
