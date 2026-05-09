# v0.3.0 GUI MVP Scope

Status: first GUI planning and skeleton step.

## Purpose

v0.3.0 introduces a local GUI workflow shell around the stable office2md CLI/library capabilities. The GUI is intended to make CML125-style review workflows easier to run and inspect without changing the conversion pipeline, search behavior, ranking, token fallback, aliases, library-report scoring, runner process-control, or Office locator behavior.

## GUI MVP Scope

The MVP is a local Streamlit app that reads an existing Knowledge Library and presents workflow pages for review and validation.

Initial implementation scope:

- Optional Streamlit dependency only.
- Minimal app shell with navigation.
- Library path entry in the sidebar.
- Library Overview page backed by existing `library_report()` data.
- Placeholder pages for later workflow panels.

The GUI does not run conversion in the first step.

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

Planned for P2. It should wrap existing `search_library()` behavior without changing search core, ranking, aliases, or token fallback.

### Locate Document

Planned for P3. It should wrap existing `locate_document()` behavior.

### Evidence Package

Planned for P4. It should help generate local validation artifacts using existing CLI/library functions and current JSON export conventions.

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
gui = ["streamlit"]
```

Default install and normal CLI use must not require Streamlit.

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

### P3 Locate Document

- Add locate-document query panel and result table using existing library functions.

### P4 Evidence Package

- Add controls to generate local evidence files using existing report/search export patterns.
- Keep output local and deterministic.

### P5 Runner Dry-run

- Add a dry-run-only interface for the existing PowerShell runner command shape.
- Do not change process-control behavior or launch real conversion from the GUI until a later review explicitly approves it.
