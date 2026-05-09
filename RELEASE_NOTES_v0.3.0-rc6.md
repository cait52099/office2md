# office2md v0.3.0-rc6 Release Notes

Status: release candidate checkpoint for GUI Build Library and Load Built Library.

## Scope

- Extended the optional Streamlit Build / Update Library page with a Build Library section.
- Added Load Built Library action.
- Clarified Source Folder, Conversion Output Folder, and Library Output Folder roles.
- Kept Convert / Update behavior from rc5 unchanged.

## Path Model

The GUI now labels the three path roles explicitly:

- Source Folder: original documents.
- Conversion Output Folder: per-document Knowledge Pack outputs.
- Library Output Folder: final searchable library with `library.db`.

The GUI states that the Conversion Output Folder is not directly readable as a Library. Users must run Build Library first, then load the Library Output Folder.

## Build Library

The Build Library section shows the exact command:

```powershell
python -m office2md.cli build-library <conversion_output> <library_output>
```

Execution requires a safety confirmation checkbox. When confirmed, the GUI invokes the existing CLI via subprocess and displays:

- stdout.
- stderr.
- exit code.
- `library.db` presence.
- `library_index.json` presence.
- `library_graph.json` presence.
- `_library.md` presence.
- `_quality_report.md` presence.
- library report counts when available.

## Load Built Library

The Load Built Library action validates that `library.db` exists in the Library Output Folder before setting the GUI Library path. If the selected folder is not a valid built library, the GUI warns that the user may have selected the Conversion Output Folder instead.

## Validation

- `python -m pytest` reports 76 passed.
- `python -m ruff check .` reports all checks passed.
- `python -m compileall office2md/gui` succeeds.
- Streamlit import check reports version 1.57.0.
- Pyvis import check succeeds.
- GUI helper import check succeeds.
- Safe temporary smoke converts `tests/fixtures/sample.txt` through the existing runner, then runs Build Library explicitly.
- Safe smoke records conversion exit code 0, final manifests 1, failed manifests 0, build-library exit code 0, and a valid temporary library with documents 1, chunks 2, entities 0.
- CML125 command preview smoke confirms the build-library command for the existing CML125 conversion/library paths without rebuilding CML125.

## Explicit Non-Goals

This checkpoint does not add or change:

- One-click full workflow.
- Automatic build-library after conversion.
- Automatic conversion before build-library.
- Automatic deletion or overwrite behavior.
- Conversion behavior.
- Runner process-control behavior.
- Build-library internals.
- Search core, ranking, aliases, or token fallback.
- Library-report metrics or scoring.
- AI/MiniMax.
- OCR.
- Embeddings/vector search.
- Cloud/network dependency.
- Direct Teams or SharePoint API integration.
- Office image export.
- Legacy `.doc` conversion.
