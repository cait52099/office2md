# office2md v0.2.0-rc7 Release Notes

Release candidate focused on Phase 3.0.6: CML125 full-directory validation and the chunked runner completion fix.

v0.2.0-rc7 keeps the Phase 3.0 no-AI local library scope. It does not add OCR, AI/MiniMax, embedding/vector search, Office image export, legacy `.doc` conversion, external conversion dependencies, or Phase 3.1 work.

## Full-Directory Validation

CML125 full-directory validation completed with the rc6 chunked/resume runner after fixing the runner completion condition.

- supported files: 598
- expected unique manifests: 588
- final manifests: 589
- success: 587
- failed: 2
- failed files: duplicate `Guide to find the devices..doc` legacy Word inputs
- OCR used: 0
- AI used: 0
- build-library: succeeded
- build warnings: 2, both failed legacy `.doc` manifests
- documents_count: 587
- chunks_count: 4238
- entities_count: 365
- noisy_chunks_count: 0
- search smoke tests: passed
- locate-document key tests: passed

Legacy `.doc` remains documented as known unsupported input for Phase 3.0.

## Runner Completion Fix

The runner now calculates expected unique output folders using scanner order plus the converter output-directory naming behavior. It also requires those expected output folders to contain `manifest.json`; it does not stop only because total manifest count is high enough.

This matters because duplicate source files can collapse to a shared successful output manifest, while failed duplicate legacy `.doc` files can create an extra failed manifest. The fixed condition handles both cases deterministically.

## Test Status

```bash
python -m pytest
61 passed

python -m ruff check .
All checks passed!
```

Dry-run validation:

- `-MaxFiles 3`: supported files 598, expected unique manifests 3
- `-FullDirectory`: supported files 598, expected unique manifests 588

## Explicit Non-Goals

v0.2.0-rc7 does not add:

- AI calls
- OCR
- Marker integration
- MiniMax/API integration
- embedding/vector database
- Office image export
- legacy `.doc` conversion
- external conversion dependencies
- Phase 3.1 work
