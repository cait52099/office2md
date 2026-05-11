# office2md v0.3.0-rc7 Release Notes

Status: release candidate checkpoint for Output Workspace Folder UX, Load Built Library session handling, and Library-Native Knowledge Graph quality improvements.

## Scope

- Reworked the Build / Update Library page around one user-facing Output Workspace Folder.
- Preserved explicit Convert / Update, Build Library, and Load Built Library actions.
- Fixed Load Built Library Streamlit session-state handling.
- Reworked the default Graph View to use library-native concepts only.
- Added a GUI-side concept quality layer to reduce noisy graph nodes.

## Output Workspace Folder

The GUI now asks users for:

- Source Folder: original documents.
- Output Workspace Folder: parent folder for generated outputs.

The GUI derives internal folders:

- `<workspace>\conversion`: per-document Knowledge Pack outputs.
- `<workspace>\library`: final searchable library with `library.db`.
- `<workspace>\logs`: runner logs.

Convert / Update uses `<workspace>\conversion` and `<workspace>\logs`. Build Library uses `<workspace>\conversion` as input and `<workspace>\library` as output. Load Built Library loads `<workspace>\library`.

The GUI warns when the workspace already exists and is not empty because old conversion manifests may be included. Nothing is deleted automatically.

## Load Built Library

Load Built Library now uses a pending session value and rerun flow instead of mutating the Library path widget key after the widget is instantiated. This avoids the Streamlit session-state exception seen during manual review.

The GUI also warns when a selected Library path looks like a conversion output folder instead of a built library.

## Library-Native Knowledge Graph

The default Graph View is now `Knowledge Graph`.

It does not use a fixed equipment vocabulary by default. Concepts are extracted from the current library only, using:

- Explicit entities when meaningful.
- Structured headers.
- Cleaned document titles.
- Cleaned headings.
- Repeated meaningful text phrases.

The concept quality layer filters or down-ranks low-value fragments, including:

- `Cover`, `Sheet`, and `Cover Sheet`.
- `Private confidential`.
- `Liang private`.
- `Selection new`.
- `Caner sheet`.
- raw asset/source/page labels.
- pure numbers, years, units, language codes, and contact-like fragments.

The graph preserves useful library-native concepts when supported by the library, such as interview/resume/case concepts from the interview library and CML125 concepts from the CML125 library. It avoids false splits such as `HPLC` becoming `PLC` and `Participated` becoming `CIP`.

Document-Concept Graph remains available. Raw Provenance Graph remains available as a debug/provenance view.

## Validation

- `python -m pytest` reports 77 passed.
- `python -m ruff check .` reports all checks passed.
- `python -m compileall office2md/gui` succeeds.
- Streamlit import check reports version 1.57.0.
- Pyvis import check succeeds.
- GUI helper import check succeeds.
- Interview/resume library smoke confirms requested noisy labels are absent, equipment preset terms are not forced, and useful library-native concepts such as Food science, Drug discovery, Quality risk, Packaging Selection, and Risk Level can appear when supported by the library.
- CML125 library smoke confirms the Knowledge Graph still renders and does not show raw provenance noise in the default graph.
- Safe temporary workspace smoke confirms derived conversion/library/log paths, Convert / Update through the existing runner, explicit Build Library, and a valid loadable `<workspace>\library`.

## Explicit Non-Goals

This checkpoint does not add or change:

- One-click full workflow.
- Automatic build-library after conversion.
- Automatic conversion before build-library.
- Automatic deletion or cleanup.
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
