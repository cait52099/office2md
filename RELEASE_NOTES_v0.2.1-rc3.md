# office2md v0.2.1-rc3 Release Notes

Release candidate focused on v0.2.1 P1-3: usability polish for quality reporting, common workflow documentation, and CLI help text.

This release does not change search ranking, token fallback logic, aliases, OCR behavior, AI/MiniMax behavior, embeddings/vector search, cloud/network dependencies, Office image export, or legacy `.doc` conversion.

## Quality Report Formatting

`_quality_report.md` now uses clearer empty-state wording for explicit count sections:

- page-level searchable PDFs with count `0` report that no page-level searchable PDFs were detected.
- noisy chunks with count `0` report that no noisy chunks were detected.

This is a cosmetic reporting change only. It does not change quality metrics or scoring.

## Common Workflow Docs

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

The workflow doc also records positional command syntax, PowerShell UTF-8 environment variables, `--context` integer usage, and the no OCR/AI/embedding default path.

## CLI Help Wording

CLI help text was lightly clarified for:

- `convert`
- `build-library`
- `search-library`
- `locate-document`
- `library-report`

No CLI behavior changed.

## Validation

```bash
python -m pytest
67 passed

python -m ruff check .
All checks passed!
```

Representative help commands were checked successfully:

- `python -m office2md.cli convert --help`
- `python -m office2md.cli build-library --help`
- `python -m office2md.cli search-library --help`
- `python -m office2md.cli locate-document --help`
- `python -m office2md.cli library-report --help`
