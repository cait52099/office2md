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
- Build / Update Library: Scan / Dry-run, Convert / Update runner execution, Build Library, and Load Built Library implemented.
- Workspace: implemented as a read-only view of existing workspace status and traceability manifests.
- Export: Obsidian vault export implemented using the existing local exporter.
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

- Knowledge Graph: default. Shows library-native concepts detected from the current library's entities, document titles, headings, and chunk text. It does not apply a fixed equipment vocabulary, and it does not show chunks, assets, source pages, locators, or raw provenance edge labels by default.
- Document-Concept Graph: shows document nodes and detected concept nodes only, connected by document-concept mention edges.
- Raw Provenance Graph: debug view of raw `library_graph.json` relationships. This may include chunks, assets, source pages, and low-level edge types such as `document_has_chunk`.

The default graph filters noisy labels such as language codes, standalone units, pure years, generic UI/system labels, asset paths, source page labels, contact-like fragments, cover/page titles, and low-level provenance relationships. It prefers explicit entities, structured headers, cleaned document titles, cleaned headings, and repeated meaningful text phrases. Low-confidence title/text fragments are hidden; sparse graphs are preferable to noisy graphs. The keyword filter searches concept labels, document titles, headings, and chunk context, so terms can match when they appear in library content even if they were not extracted as entity labels.

Large graphs are bounded by the max nodes setting before rendering. The Raw Provenance Graph also has a node type filter. When optional `pyvis` is available, the page renders an interactive graph. If rendering is unavailable or fails, the page shows fallback node and edge tables.

## Build / Update Library

Open the Build / Update Library page from the sidebar to inspect a source folder, run conversion through the existing PowerShell chunked runner, build a searchable library, and load the built library into the GUI.

Inputs:

- Source Folder: original documents.
- Output Workspace Folder: parent folder for conversion outputs, final library, and logs.
- Max files or Full directory.
- Skip existing, shown as the validated default.
- Render PDF pages, max render pages, and max text pages, shown as validated defaults.

The GUI derives internal folders under the Output Workspace Folder:

- `conversion`: per-document Knowledge Pack outputs.
- `library`: final searchable library with `library.db`.
- `logs`: runner logs.

For example, if Source Folder is `C:\Data\Interview` and Output Workspace Folder is `C:\Data\Interview-office2md-output`, the GUI uses `C:\Data\Interview-office2md-output\conversion`, `C:\Data\Interview-office2md-output\library`, and `C:\Data\Interview-office2md-output\logs`.

The `Scan / Dry-run` button uses the existing scanner logic to count supported files and estimate the expected unique manifest target. It also counts existing `manifest.json` files in the conversion output folder when that folder already exists.

The Conversion Output Folder is not directly readable as a Library. It contains one Knowledge Pack per document. Run Build Library first, then load the Library Output Folder.

If the Output Workspace Folder already exists and is not empty, the GUI warns that old conversion manifests can be included when reusing an old workspace. A new empty workspace is recommended for each source collection. The GUI does not delete anything automatically.

The Scan / Dry-run action does not convert files, build a library, create output folders, delete files, or run the PowerShell runner. It shows command previews for the reviewed next steps:

```powershell
.\scripts\Invoke-Office2MdChunkedConvert.ps1 -InputPath "SOURCE" -OutputPath "CONVERSION_OUTPUT" -LogDirectory "LOGS" -TimeoutMinutes 45 -MaxAttempts 20 -MaxFiles 3 -Python .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe -m office2md.cli build-library "CONVERSION_OUTPUT" "LIBRARY_OUTPUT"
```

The Convert / Update section runs only after the safety confirmation checkbox is selected. It invokes `scripts/Invoke-Office2MdChunkedConvert.ps1`, captures stdout and stderr after completion, shows the exit code, shows the log folder, and summarizes final and failed manifest counts from the conversion output folder.

Convert / Update does not run `build-library` and does not load a built library.

The Build Library section runs only after its own safety confirmation checkbox is selected. It invokes:

```powershell
python -m office2md.cli build-library "CONVERSION_OUTPUT" "LIBRARY_OUTPUT"
```

After completion, it shows stdout, stderr, exit code, and a library summary that checks for `library.db`, `library_index.json`, `library_graph.json`, `_library.md`, and `_quality_report.md`.

The Load Built Library button sets the GUI Library path to `<workspace>\library` only if `library.db` exists. If the selected folder is not a valid built library, the GUI warns that the user may have selected the Conversion Output Folder instead.

Recommended practice:

- Run Scan / Dry-run first.
- Test with `MaxFiles 1` or `MaxFiles 3` before using Full directory.
- Run Convert / Update.
- Run Build Library.
- Click Load Built Library.
- Ensure OneDrive/Teams files are available offline.
- Expect Streamlit to be busy while the runner is active.

Warnings are shown for OneDrive/Teams synced folders, network paths, legacy `.doc` limitations, dry-run behavior, and no OCR/no AI defaults.

## Workspace

Open the Workspace page from the sidebar after creating a workspace with `workspace-init`.

The Workspace page is read-only. It displays the same traceability summary as:

```powershell
python -m office2md.cli workspace-status "WORKSPACE_PATH"
```

Inputs:

- Workspace Root Path.
- Show history.
- History limit, default `5`.

The Workspace Root Path must be the folder created by `workspace-init`. It is separate from the GUI sidebar Library path. The Library path is used by Library Overview, Search, and Graph View; the Workspace Root Path is used by Workspace traceability status.

Existing conversion output folders, built library folders, and Obsidian export folders are not automatically workspaces. If the path is not detected as a workspace, the page shows the expected workspace markers:

- `workspace_manifest.json`
- `source_manifest.json`
- `versions/library_versions.json`
- `versions/output_versions.json`

It also shows a suggested command such as:

```powershell
python -m office2md.cli workspace-init "C:\Users\hcai\Downloads\interview.office2md"
```

The page shows:

- workspace detection status, path, created time, updated time, missing folders, and missing manifests;
- source counts, source root count, last scan, and changed/missing source warnings;
- latest library version ID, registration time, label, source manifest hash, metrics, and warnings;
- latest output version ID, registration time, output type, label, linked library version, source manifest hash, file count, size, export manifest summary, and warnings;
- traceability chain: `source_manifest_hash -> library_version_id -> output_version_id`;
- recent library/output version history when enabled.

The page also provides `Download workspace status JSON`.

An init-only workspace is valid. It will show empty source/library/output history until you run scan/register commands. The page displays next-step examples for:

```powershell
python -m office2md.cli workspace-scan WORKSPACE_PATH SOURCE_PATH
python -m office2md.cli workspace-register-library WORKSPACE_PATH LIBRARY_PATH
python -m office2md.cli workspace-register-output WORKSPACE_PATH OUTPUT_PATH
```

It does not run `workspace-init`, run `workspace-scan`, convert files, build libraries, generate Obsidian exports, edit manifests, or modify source/output files.

## Export

Open the Export page from the sidebar after loading a valid Knowledge Library folder or `library.db` path.

The Export page generates an Obsidian-compatible local vault folder. Obsidian does not need to be installed to run the export; the generated folder can be opened in Obsidian later.

Inputs:

- Current Library Path, defaulted from the loaded GUI library path.
- Obsidian Vault Output Folder.
- Max Concepts, default `100`.
- Max Evidence Per Concept, default `5`.
- Overwrite existing output.
- Dry-run.

Actions:

- Preview Export: always runs dry-run behavior and shows planned document count, concept count, warnings, and the expected output structure without writing files.
- Export to Obsidian: calls the existing exporter and displays counts plus the parsed `_office2md/export_manifest.json` summary after a real export.

The page shows the equivalent CLI command for review:

```powershell
python -m office2md.cli export-obsidian "LIBRARY_PATH" "VAULT_OUTPUT"
```

The MVP does not copy assets. Concept extraction is heuristic and library-native, so real-use tuning may still be needed.

## Current Limitations

- The GUI can run Convert / Update only through the existing PowerShell runner.
- The GUI can run Build Library as a separate explicit step.
- The GUI can load a built Library Output Folder after `library.db` exists.
- The GUI Workspace page is read-only and does not update workspace manifests.
- One-click full workflow is not implemented.
- The GUI does not change search ranking, aliases, token fallback, or diagnostics behavior.
- The GUI does not change library-report metrics or scoring.
- The GUI does not change runner process-control behavior.
- The GUI does not change library graph export generation.
- Locate-document, evidence-package generation, and runner dry-run controls are placeholders in this MVP stage.
- Obsidian export uses the existing exporter; it does not require Obsidian to be installed and does not copy assets in this MVP.

## Explicit Non-Goals

The GUI MVP does not add AI/MiniMax, OCR, embeddings/vector search, cloud/network dependency, Office image export, legacy `.doc` conversion, or Office provenance redesign.
