# office2md v0.3.0-rc3 Release Notes

Status: release candidate checkpoint for the GUI Graph View MVP.

## Scope

- Added a read-only Graph View page to the optional Streamlit GUI.
- Added `pyvis` as an optional GUI dependency only.
- Added Curated Knowledge Graph as the default graph mode.
- Added Document-Concept Graph.
- Kept Raw Provenance Graph as an explicit debug/provenance mode.
- Updated GUI MVP scope and usage docs.

## Graph Modes

### Curated Knowledge Graph

The default graph mode shows GUI-side curated concepts matched from existing library data. It filters noisy raw labels such as language codes, standalone units, pure years, generic UI/system labels, source/page/asset labels, and raw provenance edge types.

The curated graph is read-only and does not write concepts back into the library.

### Document-Concept Graph

This mode shows document nodes and curated concept nodes only, with document-concept mention edges.

### Raw Provenance Graph

This mode remains available for debugging library structure/provenance and may include chunks, assets, source pages, and low-level edge types.

## Visual Polish

- Edge labels are hidden by default.
- `Show edge labels` checkbox can explicitly show edge labels.
- Edge type and weight remain available in hover/title metadata.
- Curated graph default max nodes is reduced to 50.
- Document-Concept graph default max nodes is 80.
- Pyvis layout uses a fixed random seed, stabilization, calmer physics, capped node sizing, capped edge width, and no directed arrows.

## Validation

- `python -m pytest` reports 73 passed.
- `python -m ruff check .` reports all checks passed.
- `python -m compileall office2md/gui` succeeds.
- Streamlit import check reports version 1.57.0.
- Pyvis import check succeeds.
- GUI helper import check succeeds.
- Helper-level CML125 smoke confirms curated concept labels, hidden edge labels by default, optional visible edge labels, stabilized layout options, Document-Concept availability, and Raw Provenance availability.

## Explicit Non-Goals

This checkpoint does not add or change:

- Build/Update Library workflow.
- Locate Document panel.
- Evidence Package panel.
- Runner Dry-run panel.
- Conversion behavior.
- Search core, ranking, aliases, or token fallback.
- Library-report metrics or scoring.
- Runner process-control behavior.
- Library builder graph generation.
- AI/MiniMax.
- OCR.
- Embeddings/vector search.
- Cloud/network dependency.
- Office image export.
- Legacy `.doc` conversion.
