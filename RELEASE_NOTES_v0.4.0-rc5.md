# office2md v0.4.0-rc5 Release Notes

Status: release candidate for v0.4.0 P5.

## Scope

v0.4.0-rc5 adds a read-only Workspace Status command for office2md workspaces.

This checkpoint does not modify workspace files, create or update manifests, run `workspace-scan`, run conversion, run `build-library`, run `export-obsidian`, change conversion behavior, change runner behavior, change build-library internals, change search/ranking behavior, change Graph View behavior, change Obsidian export behavior, implement Wiki editing, implement AI suggestions, add Marker integration, or add AI, OCR, embedding, vector, or cloud work.

## Command

```powershell
python -m office2md.cli workspace-status WORKSPACE_PATH
```

Options:

- `--json`
- `--show-history`
- `--limit`
- `--strict`

## Read-Only Status Summary

`workspace-status` validates that `WORKSPACE_PATH` is an office2md workspace and reads:

- `workspace_manifest.json`
- `source_manifest.json`
- `versions/library_versions.json`
- `versions/output_versions.json`

It does not write files, modify manifests, run scan, run conversion, run build-library, run export, or modify source/output files.

## Summary Sections

The readable and JSON summaries include:

- workspace status;
- source manifest summary;
- library version summary;
- output version summary;
- latest traceability chain;
- warnings;
- errors.

The latest traceability chain is shown as:

```text
source_manifest_hash -> library_version_id -> output_version_id
```

## JSON Output

`--json` prints parseable pretty JSON only, with stable top-level keys:

- `workspace`
- `source_manifest`
- `library_versions`
- `output_versions`
- `traceability`
- `warnings`
- `errors`

No extra table text is printed before or after JSON output.

## History and Strict Mode

- `--show-history` prints recent library versions and output versions.
- `--limit` limits the number of history records shown.
- `--strict` returns a non-zero exit code when expected manifests are missing or the latest output links to a missing library version.
- Normal warnings do not fail the command.

## Warning Behavior

`workspace-status` warns when:

- the current `source_manifest.json` hash differs from the latest library version hash;
- the current `source_manifest.json` hash differs from the latest output version hash;
- the latest output links to a missing `library_version_id`.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- CLI help checks:
  - `workspace-init`
  - `workspace-scan`
  - `workspace-register-library`
  - `workspace-register-output`
  - `workspace-status`
  - `export-obsidian`
  - `convert`
  - `build-library`
  - `search-library`
  - `locate-document`
  - `library-report`
- temp workspace status smoke
- full source/library/output traceability smoke
- history limit smoke
