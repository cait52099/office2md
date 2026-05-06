# office2md v0.2.0-rc6 Release Notes

Release candidate focused on Phase 3.0.5b: operational mitigation for long CML125 batch conversion stalls.

v0.2.0-rc6 keeps the Phase 3.0 no-AI local library scope. It does not add OCR, AI/MiniMax, embedding/vector search, Office image export, full-directory validation, or Phase 3.1 work.

## Chunked/Resume Conversion Runner

Added a PowerShell runner:

```text
scripts/Invoke-Office2MdChunkedConvert.ps1
```

The runner automates the manual recovery pattern proven during CML125 300-file validation:

- starts `office2md convert` with `--skip-existing`
- redirects stdout and stderr to timestamped logs
- counts generated `manifest.json` files
- stops the launched process tree if an attempt exceeds a configurable timeout
- restarts conversion until the expected manifest count is reached
- supports both `-MaxFiles` validation runs and full scanner-supported directory runs
- supports `-DryRun`

The runner uses `office2md.scanner.scan_input` to calculate the expected supported-file count, so the expected manifest count matches the converter scanner behavior.

## Operations Documentation

Added:

```text
docs/ops/cml125_batch_validation.md
```

The document explains:

- why the runner exists
- when to use it
- 300-file validation example
- full-directory validation example
- dry-run example
- OneDrive/on-demand file hydration risk

## Safety Review

The runner:

- does not delete input files
- does not modify conversion logic
- only creates output and log directories
- only kills the process tree it launched
- always uses `--skip-existing`
- keeps OCR, AI, embedding/vector search, and Office image export disabled

## Test Status

```bash
python -m pytest
60 passed

python -m ruff check .
All checks passed!
```

Dry-run validation:

- `-MaxFiles 3`: supported files 598, expected manifests 3
- `-FullDirectory`: supported files 598, expected manifests 598

## Explicit Non-Goals

v0.2.0-rc6 does not add:

- AI calls
- OCR
- Marker integration
- MiniMax/API integration
- embedding/vector database
- Office image export
- full-directory validation execution

Embedding/vector search remains deferred to Phase 3.1 as an optional layer on top of SQLite/FTS.
