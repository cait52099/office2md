# office2md v0.3.0-rc4 Release Notes

Status: release candidate checkpoint for the GUI Build / Update Library Scan / Dry-run panel.

## Scope

- Added a Build / Update Library page to the optional Streamlit GUI.
- Implemented Scan / Dry-run only.
- Used existing `office2md.scanner.scan_input()` scanner logic.
- Added runner and `build-library` command previews.
- Updated GUI usage and design documentation.

## Scan / Dry-run Panel

The panel accepts:

- Source folder.
- Conversion output folder.
- Library output folder.
- Log folder.
- MaxFiles or FullDirectory selection.
- Skip-existing default.
- Render PDF pages default.
- Max render pages and max text pages defaults.

The panel reports:

- Supported file count.
- Selected target file count.
- Expected unique manifest count.
- Existing manifest count.
- Completed expected manifest count.
- Failed manifest count.
- Target completion status.

Warnings are shown for OneDrive/Teams synced folders, network paths, legacy `.doc` limitations, no OCR/no AI defaults, and the dry-run-only behavior.

## Command Previews

The page shows preview commands for:

- `scripts/Invoke-Office2MdChunkedConvert.ps1`
- `python -m office2md.cli build-library`

These commands are not executed by the GUI in this checkpoint.

## Validation

- `python -m pytest` reports 74 passed.
- `python -m ruff check .` reports all checks passed.
- `python -m compileall office2md/gui` succeeds.
- Streamlit import check reports version 1.57.0.
- Pyvis import check succeeds.
- GUI helper import check succeeds.
- Helper-level CML125 smoke confirms supported files 598, MaxFiles 3 target 3, MaxFiles 3 expected unique manifests 3, full-directory expected unique manifests 588, existing manifests 589, and full-directory completed expected manifests 588.

## Explicit Non-Goals

This checkpoint does not add or change:

- Convert / Update execution.
- Build Library execution.
- Load Built Library.
- GUI conversion execution.
- GUI build-library execution.
- Conversion behavior.
- Runner process-control behavior.
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
