# office2md v0.3.0-rc5 Release Notes

Status: release candidate checkpoint for the GUI Convert / Update panel.

## Scope

- Extended the optional Streamlit Build / Update Library page with a Convert / Update section.
- Added execution wrapper for the existing PowerShell chunked conversion runner.
- Kept `build-library` as a preview/manual next command only.
- Updated GUI usage and design documentation.

## Convert / Update Panel

The Convert / Update section shows:

- Exact PowerShell runner command.
- Source folder.
- Conversion output folder.
- Log folder.
- MaxFiles or FullDirectory mode.
- Timeout minutes.
- Max attempts.
- Skip-existing status.
- Render option defaults.
- No OCR and no AI notes.

Execution requires an explicit safety confirmation checkbox. When confirmed, the GUI invokes:

```powershell
scripts/Invoke-Office2MdChunkedConvert.ps1
```

The GUI captures and displays:

- stdout.
- stderr.
- exit code.
- log folder.
- final manifest count.
- failed manifest count.

## Validation

- `python -m pytest` reports 75 passed.
- `python -m ruff check .` reports all checks passed.
- `python -m compileall office2md/gui` succeeds.
- Streamlit import check reports version 1.57.0.
- Pyvis import check succeeds.
- GUI helper import check succeeds.
- Safe temporary MaxFiles 1 runner smoke exits 0, creates output/log folders through the runner, records final manifest count 1, and failed manifest count 0.
- CML125 command preview smoke generates a MaxFiles 3 command with selected paths, `-TimeoutMinutes 45`, `-MaxAttempts 20`, and `-MaxFiles 3` without executing CML125 conversion.

## Explicit Non-Goals

This checkpoint does not add or change:

- Build Library execution.
- Load Built Library.
- One-click full workflow.
- Runner script behavior.
- Runner process-control behavior.
- Conversion behavior.
- Scanner behavior.
- Output directory naming behavior.
- Search core, ranking, aliases, or token fallback.
- Library-report metrics or scoring.
- Library builder behavior.
- AI/MiniMax.
- OCR.
- Embeddings/vector search.
- Cloud/network dependency.
- Direct Teams or SharePoint API integration.
- Office image export.
- Legacy `.doc` conversion.
