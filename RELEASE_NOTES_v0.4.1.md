# office2md v0.4.1 Release Notes

Status: final v0.4.1 release.

## Scope

v0.4.1 is a GUI Workspace Dashboard and product presentation polish release on top of v0.4.0.

It makes the v0.4.0 workspace traceability foundation visible in the Streamlit GUI without changing the underlying workspace CLI or conversion behavior.

This release does not implement OfficeCLI integration, add OfficeCLI as a dependency, implement Wiki editing, implement AI suggestions, add Marker integration, add AI/OCR/embedding/vector/cloud work, or change conversion, runner, build-library, search/ranking, Graph View, Obsidian export, or workspace CLI behavior.

The OfficeCLI benchmark plan exists as documentation only.

## GUI Workspace Page

The GUI includes a read-only Workspace Status page.

The page displays:

- workspace detected / not detected state;
- Workspace Root Path guidance;
- the distinction between Library Path and Workspace Root Path;
- missing expected workspace folders and manifests;
- source manifest status;
- library version status;
- output version status;
- traceability chain status;
- warning and error messages;
- optional recent history;
- downloadable workspace status JSON.

The page does not scan, convert, build, export, initialize workspaces, write manifests, or modify source or output files.

## Product Presentation

The main GUI title is now:

```text
office2md Local Knowledge Workspace
```

Sidebar labels are product-facing:

- `Library`
- `Search`
- `Knowledge Graph`
- `Build / Update`
- `Workspace Status`
- `Export`
- `Find Document`

Internal routing remains stable.

## Workspace Root Path Guidance

The Workspace Status page explains that Workspace Root Path is the folder created by `workspace-init`.

It is separate from the Library Path used by Library, Search, and Knowledge Graph.

Conversion output folders, built library folders, Obsidian export folders, and `*-office2md-output` folders are not treated as workspace roots unless `workspace-init` was run there.

When a non-workspace path is entered, the page shows expected workspace markers:

- `workspace_manifest.json`
- `source_manifest.json`
- `versions/library_versions.json`
- `versions/output_versions.json`

It also shows a suggested `workspace-init` command.

## Path Type Hints

The GUI provides read-only hints for paths that look like:

- built library folders;
- Obsidian export folders;
- conversion / Knowledge Pack-like folders;
- `*-office2md-output` folders.

These hints are guidance only. They do not run commands or modify files.

## Init-Only Workspace Guidance

An init-only workspace is valid.

The GUI allows source, library, and output counts to be zero and uses clearer empty-state wording:

- no source scan history yet;
- no library versions registered yet;
- no output versions registered yet.

The traceability display no longer shows empty arrows such as:

```text
sha256:... -> ->
```

Instead, it explains that the traceability chain is incomplete and shows the next required step.

## Guided Next Steps

For an init-only workspace, the GUI shows a suggested workflow:

1. Scan source files.
2. Register built library.
3. Register generated output.

Each step includes a command example.

## Existing Workspace CLI

The existing v0.4.0 workspace CLI remains available and unchanged:

- `workspace-init`
- `workspace-scan`
- `workspace-register-library`
- `workspace-register-output`
- `workspace-status`

## Existing Non-Workspace Functionality

Existing commands and GUI pages remain unchanged:

- `convert`
- `build-library`
- `search-library`
- `locate-document`
- `library-report`
- `export-obsidian`
- Library page
- Search page
- Knowledge Graph page
- Build / Update page
- Export page

## OfficeCLI

OfficeCLI is not integrated in v0.4.1.

The repository includes a docs-only benchmark/design plan:

- `docs/design/v042_officecli_benchmark_plan.md`

OfficeCLI remains optional, is not a dependency, and is not used at runtime.

## Validation

Final release validation includes:

- `python -m pytest`
- `python -m ruff check .`
- `python -m compileall office2md/gui`
- CLI help checks for workspace, export, conversion, library, search, locate, and report commands;
- GUI/helper init-only workspace smoke;
- GUI/helper path guidance smoke;
- GUI/helper full traceability workspace smoke;
- workspace-status JSON smoke.
