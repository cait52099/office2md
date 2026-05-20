# office2md v0.4.1-rc2 Release Notes

Status: release candidate for v0.4.1 P2.

## Scope

v0.4.1-rc2 polishes the read-only GUI Workspace page guidance so users can distinguish a workspace root from conversion, library, and export folders.

This checkpoint does not modify workspace files, create or update manifests, run `workspace-init`, run `workspace-scan`, run conversion, run `build-library`, run `export-obsidian`, change conversion behavior, change runner behavior, change build-library internals, change search/ranking behavior, change Graph View behavior, change Obsidian export behavior, implement Wiki editing, implement AI suggestions, add Marker integration, or add AI, OCR, embedding, vector, or cloud work.

## Workspace Root Path Wording

The Workspace page input is now labeled:

```text
Workspace Root Path
```

The page explains that this path must be a folder created by `workspace-init`. It is separate from the GUI Library Path used by Library Overview, Search, and Graph View.

## Path Guidance

When a path is not detected as a workspace root, the page shows the expected workspace markers:

- `workspace_manifest.json`
- `source_manifest.json`
- `versions/library_versions.json`
- `versions/output_versions.json`

The page also shows a suggested `workspace-init` command. For output-like names such as `interview-office2md-output`, the suggestion points to `interview.office2md`.

Path type hints identify:

- built library folders;
- Obsidian export folders;
- conversion / Knowledge Pack-like folders;
- `*-office2md-output` output folders.

## Init-Only Workspace Guidance

A valid init-only workspace is treated as valid, not as an error. The page shows `Workspace detected`, allows source/library/output counts to be zero, explains that scan/register history is empty, and displays next-step command hints for:

- `workspace-scan`
- `workspace-register-library`
- `workspace-register-output`

## Read-Only Behavior

The GUI Workspace page remains read-only:

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
- GUI/helper smoke for `C:\Users\hcai\Downloads\interview-office2md-output`
- GUI/helper smoke for `C:\Users\hcai\Downloads\interview.office2md`
