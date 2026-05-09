# office2md v0.3.0-rc2 Release Notes

Status: release candidate checkpoint for the GUI Search panel.

## Scope

- Added a read-only Streamlit Search panel to the optional GUI.
- Wrapped existing `search_library()`, `search_library_diagnostics()`, and `search_library_facets()` behavior.
- Added Search controls for query, limit, diagnostics, facets, context, output directory filter, and entity filter.
- Added result table, diagnostics display, facet display, related chunk display, and search JSON download.
- Updated GUI MVP scope and usage docs.

## Search Panel

The Search page displays:

- Rank.
- Document title.
- Source file.
- Document kind.
- Evidence type.
- Locator.
- Output directory.
- Preview.

When diagnostics are enabled, the panel displays mode, effective query, alias/normalization fields, token fallback status and tokens, result count, shown count, locator coverage, and hints.

When facets are enabled, the panel displays document kind, evidence type, source file, and output directory facets when available.

When context is greater than `0`, related chunks are displayed in a separate table.

## JSON Download

The `Download search JSON` button uses the existing CLI search export payload shape. This checkpoint does not change the CLI `--export-json` schema.

## Validation

- `python -m pytest` reports 72 passed.
- `python -m ruff check .` reports all checks passed.
- `python -m compileall office2md/gui` succeeds.
- GUI helper import check succeeds.
- Streamlit import check reports version 1.57.0.
- Helper-level CML125 smoke checks pass for `vacuum pump fault`, Chinese `cooling water`, and `SY909735`.

## Explicit Non-Goals

This checkpoint does not add or change:

- Locate Document GUI implementation.
- Evidence Package GUI implementation.
- Runner Dry-run GUI implementation.
- Conversion behavior.
- Search core, ranking, aliases, token fallback, or diagnostics semantics.
- CLI search export JSON schema.
- Library-report metrics or scoring.
- Runner process-control behavior.
- AI/MiniMax.
- OCR.
- Embeddings/vector search.
- Cloud/network dependency.
- Office image export.
- Legacy `.doc` conversion.
