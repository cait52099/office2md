# v0.3.0 GUI MVP Scope

Status: GUI MVP skeleton with Library Overview, Search panel, Graph View MVP, and Build / Update Library workflow through Load Built Library.

## Purpose

v0.3.0 introduces a local GUI workflow shell around the stable office2md CLI/library capabilities. The GUI is intended to make CML125-style review workflows easier to run and inspect without changing the conversion pipeline, search behavior, ranking, token fallback, aliases, library-report scoring, runner process-control, or Office locator behavior.

## GUI MVP Scope

The MVP is a local Streamlit app that reads an existing Knowledge Library and presents workflow pages for review and validation.

Current implementation scope:

- Optional Streamlit dependency only.
- Minimal app shell with navigation.
- Library path entry in the sidebar.
- Library Overview page backed by existing `library_report()` data.
- Search page backed by existing `search_library()`, `search_library_diagnostics()`, and `search_library_facets()` behavior.
- Graph View page backed by existing `library_graph.json`.
- Build / Update Library page with Scan / Dry-run backed by existing scanner logic, Convert / Update backed by the existing PowerShell runner, Build Library backed by the existing CLI, and Load Built Library.
- Placeholder pages for later locate, evidence-package, and runner workflow panels.

The GUI Convert / Update path invokes the existing runner only; it does not change conversion behavior or runner process-control behavior.

## Pages

### Library Overview

- Accept a Knowledge Library folder or `library.db` path.
- Call existing `library_report()` functionality.
- Show key metrics:
  - `documents_count`
  - `chunks_count`
  - `entities_count`
  - `noisy_chunks_count`
  - `chunks_without_locator`
  - `page_level_pdf_documents`
- Show document kind and missing-locator summaries.

### Search

Implemented for P2 as a read-only wrapper around existing library search functions.

- Query text input.
- Limit input.
- Diagnostics and facets checkboxes.
- Context integer input for related chunks.
- Optional `output_dir` and entity filters.
- Results table with rank, document, source file, document kind, evidence type, locator, output directory, and preview.
- Diagnostics summary when enabled.
- Facet tables when enabled.
- Download button for current search JSON using the existing search export payload shape.

The panel does not change search core, ranking, aliases, token fallback, diagnostics semantics, or export JSON schema.

### Locate Document

Planned for P3. It should wrap existing `locate_document()` behavior.

### Graph View

Implemented as a read-only MVP backed by existing `library_graph.json` output.

- Loads graph nodes and edges from the selected library folder.
- Shows node count, edge count, node type distribution, and edge type distribution.
- Supports bounded rendering with max nodes defaulting to 150.
- Supports graph modes:
  - Curated Knowledge Graph: default, concept-to-concept graph built from a conservative GUI-side domain vocabulary matched against existing chunks/documents.
  - Document-Concept Graph: document and curated concept nodes only, connected by existing document/chunk concept mentions.
  - Raw Provenance Graph: debug view of raw `library_graph.json` relationships.
- Supports keyword and isolated-node filters; the raw provenance mode also supports node type filtering.
- Uses optional `pyvis` rendering when available.
- Falls back to node and edge tables if interactive rendering is unavailable.

The default Curated Knowledge Graph filters noisy raw labels such as language codes, units, pure years, generic UI/system labels, source/page/asset paths, and drawing/document codes. It hides chunk, asset, source page, locator, and raw provenance nodes. It uses curated concept labels as node labels and co-mention/co-occurrence edges with weights when available.

The keyword filter searches concept labels, aliases, document titles, and chunk context captured while building the GUI-side concept index.

The Raw Provenance Graph is retained for debugging library structure/provenance and may include chunks, assets, source pages, and low-level edge types such as `document_has_chunk`.

The Graph View does not change library builder behavior, graph export generation, search behavior, ranking, aliases, token fallback, conversion behavior, or report scoring. It does not implement graph editing, AI graph explanation, or vector/semantic graph behavior.

### Evidence Package

Planned for P4. It should help generate local validation artifacts using existing CLI/library functions and current JSON export conventions.

### Build / Update Library

P4-B Scan / Dry-run is implemented as a read-only filesystem inspection action. P4-C Convert / Update is implemented as a conservative wrapper around the existing PowerShell chunked runner. P4-D Build Library and Load Built Library are implemented as explicit user actions.

- Accepts Source Folder for original documents, Conversion Output Folder for per-document Knowledge Packs, Library Output Folder for the final searchable library, and log folder paths.
- Accepts Max files or Full directory selection.
- Shows validated defaults for skip existing, PDF page rendering, max render pages, max text pages, no OCR, and no AI.
- Uses existing scanner logic to count supported files.
- Estimates expected unique manifests with the runner-style slug/checksum collision convention.
- Counts existing `manifest.json` files in the conversion output folder when present.
- Shows whether the selected target appears complete.
- Shows warnings for OneDrive/Teams folders, network paths, legacy `.doc`, and dry-run-only behavior.
- Shows PowerShell runner and `build-library` command previews.
- Requires a safety confirmation before running Convert / Update.
- Runs only `scripts/Invoke-Office2MdChunkedConvert.ps1` for Convert / Update.
- Captures stdout, stderr, exit code, log folder, final manifest count, and failed manifest count after completion.
- Requires a separate safety confirmation before running Build Library.
- Runs `python -m office2md.cli build-library` from Conversion Output Folder to Library Output Folder.
- Captures stdout, stderr, exit code, library output file presence, and library-report counts after build.
- Load Built Library sets the GUI Library path to the Library Output Folder only when `library.db` exists.
- Warns when a selected folder does not look like a built library, including likely Conversion Output Folder mistakes.

This page does not implement one-click full workflow, delete files, or change runner process-control behavior.

### Runner Dry-run

Planned for P5. It should expose a safe dry-run workflow for the existing PowerShell runner without changing runner process-control behavior.

## Out Of Scope

- AI or MiniMax work.
- OCR.
- Embeddings or vector search.
- Cloud or network dependency.
- Office image export.
- Legacy `.doc` conversion.
- Office provenance redesign.
- Office locator behavior changes.
- Search ranking, aliases, or token fallback changes.
- Conversion behavior changes.
- Runner process-control changes.

## Dependency Strategy

Streamlit is an optional GUI dependency only:

```toml
[project.optional-dependencies]
gui = ["streamlit", "pyvis"]
```

Default install and normal CLI use must not require Streamlit or pyvis.

## Validation Strategy

- Continue running the existing test suite with default dependencies.
- Continue running `python -m ruff check .`.
- Compile the GUI package with `python -m compileall office2md/gui`.
- Manual Streamlit browser validation is optional for this skeleton and should not block CLI release work.
- Validate against an existing library path before adding write actions.

## Phased Implementation Plan

### P1 Skeleton + Library Overview

- Add optional `gui` dependency.
- Add Streamlit app shell.
- Add Library Overview page using existing `library_report()`.
- Add docs for install and launch.

### P2 Search Panel

- Add query input and result display using existing search functions.
- Preserve existing ranking, alias, token fallback, diagnostics, and export behavior.
- Status: implemented in v0.3.0 P2 work.

### P3 Graph View MVP

- Add read-only Graph View page using existing `library_graph.json`.
- Keep graph rendering bounded and local.
- Preserve library builder and graph export behavior.
- Status: implemented in v0.3.0 P3 work.

### P4 Locate Document

- Add locate-document query panel and result table using existing library functions.

### P5 Build / Update Library

- P4-B Scan / Dry-run status: implemented.
- P4-C Convert / Update status: implemented as an explicit, confirmed PowerShell runner wrapper.
- P4-D Build Library and Load Built Library status: implemented as explicit actions.
- One-click full workflow remains deferred.

### P6 Evidence Package

- Add controls to generate local evidence files using existing report/search export patterns.
- Keep output local and deterministic.

### P7 Runner Dry-run

- Add a dry-run-only interface for the existing PowerShell runner command shape.
- Do not change process-control behavior or launch real conversion from the GUI until a later review explicitly approves it.
