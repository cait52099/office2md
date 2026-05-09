# office2md v0.3.0-rc1 Release Notes

Status: release candidate checkpoint for the first GUI MVP skeleton.

## Scope

- Added a local Streamlit GUI skeleton as an optional workflow shell.
- Added `gui = ["streamlit"]` as an optional dependency only.
- Added a Library Overview page backed by the existing `library_report()` function.
- Added placeholder pages for Search, Locate Document, Evidence Package, and Runner Dry-run.
- Added GUI MVP scope and usage documentation.

## GUI MVP

The app title is `office2md GUI MVP`. The sidebar accepts a Knowledge Library folder or `library.db` path. When a valid path is provided, the Library Overview page displays key metrics from the existing library report:

- `documents_count`
- `chunks_count`
- `entities_count`
- `noisy_chunks_count`
- `chunks_without_locator`
- `page_level_pdf_documents`

If no valid library path is provided, the app shows a clear warning and does not run a workflow.

## Dependency Behavior

Streamlit is optional and installed only with:

```powershell
pip install -e ".[gui]"
```

Normal CLI install and use remain unchanged.

## Validation

- `python -m pytest` reports 71 passed.
- `python -m ruff check .` reports all checks passed.
- `python -m compileall office2md/gui` succeeds.
- Optional GUI dependency install succeeds with Streamlit 1.57.0.
- GUI helper import check succeeds.

## Explicit Non-Goals

This checkpoint does not add or change:

- Search panel implementation.
- Locate Document panel implementation.
- Evidence Package implementation.
- Runner Dry-run implementation.
- Conversion behavior.
- Search core, ranking, aliases, or token fallback.
- Library-report metrics or scoring.
- Runner process-control behavior.
- AI/MiniMax.
- OCR.
- Embeddings/vector search.
- Cloud/network dependency.
- Office image export.
- Legacy `.doc` conversion.
