# office2md v0.3.0 Release Notes

Status: stable GUI MVP release.

## Highlights

- Added the optional local Streamlit GUI MVP.
- Added Library Overview backed by existing `library_report()` data.
- Added read-only Search panel backed by existing search functions.
- Added Graph View with a library-native Knowledge Graph, Document-Concept Graph, and Raw Provenance Graph debug mode.
- Added Build / Update Library workflow with explicit Scan / Dry-run, Convert / Update, Build Library, and Load Built Library steps.
- Added Output Workspace Folder UX that derives:
  - `<workspace>\conversion`
  - `<workspace>\library`
  - `<workspace>\logs`

## GUI MVP

The GUI is an optional workflow shell around existing stable office2md behavior. It does not replace or change the CLI pipeline.

Implemented pages:

- Library Overview.
- Search.
- Graph View.
- Build / Update Library.

Placeholder pages remain for future Locate Document and Evidence Package workflows.

## Build / Update Library

Users select a source folder and one Output Workspace Folder. The GUI keeps conversion outputs, the final searchable library, and logs separate:

- Convert / Update writes per-document Knowledge Packs to `<workspace>\conversion`.
- Build Library builds the searchable library into `<workspace>\library`.
- Load Built Library loads `<workspace>\library`.
- Runner logs are written under `<workspace>\logs`.

Convert / Update uses the existing PowerShell chunked runner. Build Library uses the existing `build-library` CLI. The GUI does not add one-click full workflow, automatic cleanup, or automatic deletion.

## Library-Native Knowledge Graph

The default Graph View is a library-native Knowledge Graph. It extracts concepts from the current library data, including meaningful entities, structured headers, cleaned document titles, cleaned headings, and repeated text phrases.

The default graph does not use a fixed equipment vocabulary. It filters low-value fragments such as generic cover/page labels, raw source/asset labels, contact-like fragments, pure numbers, years, units, and language codes. Sparse graphs are preferred over noisy graphs.

Document-Concept Graph remains available. Raw Provenance Graph remains available as a debug/provenance view.

## Existing CLI

The v0.3.0 release preserves existing CLI behavior:

- `convert`
- `build-library`
- `search-library`
- `locate-document`
- `library-report`

No conversion, runner process-control, search ranking, alias, token fallback, graph export generation, or library-report scoring behavior is changed by the GUI release.

## AI / OCR / Vector / Cloud Status

- AI enrichment is opt-in.
- AI is disabled by default.
- MiniMax CLI is not required for normal CLI or GUI workflows.
- No OCR is added.
- No embeddings/vector search is added.
- No cloud dependency is added.
- No Marker integration is included yet.
- No Obsidian export implementation is included yet.

## Validation Summary

The release candidate series validated:

- `python -m pytest`
- `python -m ruff check .`
- `python -m compileall office2md/gui`
- CLI help checks for convert, build-library, search-library, locate-document, and library-report.
- Small fixture workspace convert/build/load smoke.
- CML125 library report, search, and graph helper smoke.
- Interview/resume graph helper smoke confirming no fixed equipment vocabulary is forced.

