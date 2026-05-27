# office2md v0.4.1-rc3 Release Notes

Status: release candidate for v0.4.1 P3.

## Scope

v0.4.1-rc3 polishes the GUI product presentation and Workspace Status wording.

This checkpoint does not integrate OfficeCLI, add new conversion engines, modify workspace files, run workspace commands automatically, run conversion, run `build-library`, run `export-obsidian`, change conversion behavior, change runner behavior, change build-library internals, change search/ranking behavior, change Graph View behavior, change Obsidian export behavior, implement Wiki editing, or add AI, OCR, Marker, embedding, vector, or cloud work.

## Product Presentation

The main GUI title is now:

```text
office2md Local Knowledge Workspace
```

Sidebar page labels are more product-like while keeping internal routing stable:

- `Library`
- `Knowledge Graph`
- `Build / Update`
- `Workspace Status`
- `Find Document`

## Workspace Status Polish

The Workspace Status page now presents the workspace summary with friendlier summary metrics and table rows instead of raw top-level debug-looking JSON blocks.

Detailed workspace data remains available through:

- `Workspace details`
- `Download workspace status JSON`

Init-only workspaces no longer show empty trace arrows such as:

```text
sha256:... -> ->
```

Instead, the page explains that the traceability chain is not complete yet and shows the next required step.

## Empty States and Next Steps

Empty source, library, and output states now use clearer wording:

- source files need `workspace-scan`;
- built libraries need `workspace-register-library`;
- generated outputs need `workspace-register-output`.

The next-step commands are shown as a guided workflow:

1. Scan source files.
2. Register built library.
3. Register generated output.

## Read-Only Behavior

The GUI remains read-only for workspace status:

- no subprocess;
- no automatic workspace initialization;
- no automatic source scan;
- no conversion;
- no build-library;
- no export;
- no manifest writes;
- no source or output file modifications.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- `python -m compileall office2md/gui`
- CLI help checks:
  - `workspace-status`
  - `workspace-init`
  - `workspace-scan`
  - `workspace-register-library`
  - `workspace-register-output`
  - `export-obsidian`
  - `convert`
  - `build-library`
  - `search-library`
  - `locate-document`
  - `library-report`
- GUI/helper smoke for `C:\Users\hcai\Downloads\interview.office2md`
- GUI/helper smoke for `C:\Users\hcai\Downloads\interview-office2md-output`
