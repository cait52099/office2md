# office2md GUI MVP

The v0.3.0 GUI MVP is a local Streamlit workflow shell around existing stable office2md library functionality.

It is optional. Normal CLI installation and usage do not require Streamlit.

## Install Optional GUI Dependency

```powershell
cd C:\Users\hcai\Downloads\office2md
.\.venv\Scripts\Activate.ps1
pip install -e ".[gui]"
```

## Launch

```powershell
python -m streamlit run office2md/gui/app.py
```

## Expected First Screen

The app opens with:

```text
office2md GUI MVP
```

Use the sidebar to enter a Knowledge Library folder path or a `library.db` path. The Library Overview page loads existing `library_report()` data and shows:

- `documents_count`
- `chunks_count`
- `entities_count`
- `noisy_chunks_count`
- `chunks_without_locator`
- `page_level_pdf_documents`

If the library path is missing or invalid, the app shows a warning instead of running any workflow.

## Current Pages

- Library Overview: implemented.
- Search: implemented as a read-only wrapper around existing library search.
- Graph View: implemented as a read-only view of existing `library_graph.json`.
- Build / Update Library: Scan / Dry-run implemented.
- Locate Document: placeholder for a future GUI step.
- Evidence Package: placeholder for a future GUI step.
- Runner Dry-run: placeholder for a future GUI step.

## Search Panel

Open the Search page from the sidebar after entering a valid Knowledge Library folder or `library.db` path.

The panel supports:

- Query text input.
- Limit input, default `5`.
- Diagnostics checkbox.
- Facets checkbox.
- Context integer input, default `0`.
- Optional output directory filter.
- Optional entity filter.

Results are displayed in a table with rank, document title, source file, document kind, evidence type, locator, output directory, and preview. If diagnostics are enabled, the panel shows mode, effective query, alias or normalization information, token fallback status and tokens, result count, shown count, locator coverage, and hints. If facets are enabled, the panel shows document kind, evidence type, source file, and output directory facets when available.

The search panel also provides a `Download search JSON` button for the current result set. The download uses the existing search export JSON payload shape; it does not change the CLI `--export-json` schema.

## Graph View

Open the Graph View page from the sidebar after entering a Knowledge Library folder or `library.db` path.

The panel loads the existing `library_graph.json` file from the selected library folder. It is read-only and does not rebuild, edit, or regenerate graph data.

The panel shows:

- Node count.
- Edge count.
- Node type distribution.
- Edge type distribution.

Controls:

- Graph mode.
- Max nodes, default `150`.
- Keyword filter.
- Show isolated nodes toggle.

Graph modes:

- Curated Knowledge Graph: default. Shows higher-value domain concepts from a conservative GUI-side vocabulary matched against existing chunk and document text. It does not show chunks, assets, source pages, locators, or raw provenance edge labels by default.
- Document-Concept Graph: shows document nodes and curated concept nodes only, connected by document-concept mention edges.
- Raw Provenance Graph: debug view of raw `library_graph.json` relationships. This may include chunks, assets, source pages, and low-level edge types such as `document_has_chunk`.

The curated graph filters noisy labels such as language codes, standalone units, pure years, generic UI/system labels, asset paths, source page labels, and low-level provenance relationships. The keyword filter searches concept labels, aliases, document titles, and chunk context, so domain terms can match even when they were not extracted as entity labels.

Large graphs are bounded by the max nodes setting before rendering. The Raw Provenance Graph also has a node type filter. When optional `pyvis` is available, the page renders an interactive graph. If rendering is unavailable or fails, the page shows fallback node and edge tables.

## Build / Update Library Scan / Dry-run

Open the Build / Update Library page from the sidebar to inspect a source folder before running conversion outside the GUI.

Inputs:

- Source folder.
- Conversion output folder.
- Library output folder.
- Log folder.
- Max files or Full directory.
- Skip existing, shown as the validated default.
- Render PDF pages, max render pages, and max text pages, shown as validated defaults.

The `Scan / Dry-run` button uses the existing scanner logic to count supported files and estimate the expected unique manifest target. It also counts existing `manifest.json` files in the conversion output folder when that folder already exists.

The dry-run page does not convert files, build a library, create output folders, delete files, or run the PowerShell runner. It shows command previews for the reviewed next steps:

```powershell
.\scripts\Invoke-Office2MdChunkedConvert.ps1 -InputPath "SOURCE" -OutputPath "CONVERSION_OUTPUT" -LogDirectory "LOGS" -MaxFiles 3 -Python .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe -m office2md.cli build-library "CONVERSION_OUTPUT" "LIBRARY_OUTPUT"
```

Warnings are shown for OneDrive/Teams synced folders, network paths, legacy `.doc` limitations, and the fact that this is a non-converting dry-run.

## Current Limitations

- The GUI does not run conversion.
- The Build / Update Library page only scans and previews commands; Convert / Update, Build Library, and Load Built Library are planned follow-up steps.
- The GUI does not change search ranking, aliases, token fallback, or diagnostics behavior.
- The GUI does not change library-report metrics or scoring.
- The GUI does not change runner process-control behavior.
- The GUI does not change library graph export generation.
- Locate-document, evidence-package generation, and runner dry-run controls are placeholders in this MVP stage.

## Explicit Non-Goals

The GUI MVP does not add AI/MiniMax, OCR, embeddings/vector search, cloud/network dependency, Office image export, legacy `.doc` conversion, or Office provenance redesign.
