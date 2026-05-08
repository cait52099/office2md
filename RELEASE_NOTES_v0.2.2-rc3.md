# office2md v0.2.2-rc3 Release Notes

v0.2.2-rc3 adds output-only final summary polish to the chunked/resume PowerShell runner.

This checkpoint does not change process-control behavior, timeout/retry logic, scanner/counting logic, conversion behavior, search behavior, ranking, aliases, or token fallback logic.

It does not add vector search, embeddings, OCR, AI/MiniMax, cloud/network dependencies, Office image export, or legacy `.doc` conversion.

## Runner Final Summary

`scripts/Invoke-Office2MdChunkedConvert.ps1` now prints a final summary for dry runs, successful runs, and max-attempts stops.

The final summary includes:

- input path
- output path
- log directory
- mode
- supported file count
- expected unique manifest count
- final manifest count
- completed expected manifest count
- failed manifest count
- attempts used
- timeout/restart count
- max attempts
- timeout minutes per attempt
- target reached
- final status
- log location
- next recommended `build-library` command

Dry-run summaries report `Final status: dry-run` and `Attempts used: 0`.

Successful summaries report `Final status: success` when the target is reached and no failed manifests are detected. If failed manifests are detected after target completion, the summary reports `Final status: needs review`.

Max-attempt summaries still follow the existing throw behavior. The new summary is printed before the existing max-attempts error.

## Known Runner Behavior

Existing timeout/process behavior is intentionally unchanged. In small smoke runs, the timeout branch can print even when a manifest is produced and the target is reached. v0.2.2-rc3 does not change that process-control behavior. The final summary still shows the completed expected manifest count, timeout/restart count, target status, and final status so the run is easier to review.

## Documentation

`docs/ops/cml125_batch_validation.md` now documents the final summary and explicitly states that it is output-only reporting.

## Validation

```bash
python -m pytest
69 passed

python -m ruff check .
All checks passed!
```

Manual runner validation:

- CML125 `-MaxFiles 3 -DryRun` prints final summary with supported files `598`, expected unique manifests `3`, attempts used `0`, and final status `dry-run`.
- CML125 `-FullDirectory -DryRun` prints final summary with supported files `598`, expected unique manifests `588`, attempts used `0`, and final status `dry-run`.
- Small real `-MaxFiles 1` run against `tests/fixtures/sample.txt` prints final summary with expected manifests `1`, completed expected manifests `1/1`, failed manifests `0`, target reached `True`, and final status `success`.

## Explicit Non-Goals

v0.2.2-rc3 does not include:

- process-control changes
- timeout/retry logic changes
- scanner/counting logic changes
- conversion behavior changes
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
