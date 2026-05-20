# office2md v0.4.0-rc4 Release Notes

Status: release candidate for v0.4.0 P4.

## Scope

v0.4.0-rc4 adds manual Output Version Registration for office2md workspaces.

This checkpoint does not change Obsidian export behavior, automatically run `export-obsidian`, change conversion behavior, change runner behavior, change build-library internals, change search/ranking behavior, change Graph View behavior, implement Wiki editing, implement AI suggestions, add Marker integration, or add AI, OCR, embedding, vector, or cloud work.

## Command

```powershell
python -m office2md.cli workspace-register-output WORKSPACE_PATH OUTPUT_PATH
```

Options:

- `--dry-run`
- `--label`
- `--notes`
- `--output-type`
- `--library-version-id`
- `--output-version-id`
- `--allow-missing-library-version`

## Output Version Registration

`workspace-register-output` validates that `WORKSPACE_PATH` is an office2md workspace and that `OUTPUT_PATH` exists as a file or folder.

The command appends a record to:

```text
versions/output_versions.json
```

It does not generate exports, call `export-obsidian`, modify output files, or remove previous output version records.

## Output Version Record

Each output version record includes:

- `output_version_id`
- `registered_at`
- `office2md_version`
- `workspace_path`
- `output_path`
- `output_type`
- `label`
- `notes`
- `library_version_id`
- `source_manifest_hash`
- `source_counts`
- `output_files`
- `export_manifest`
- `warnings`

## Hashes and Output Detection

- File outputs record SHA-256, `file_count = 1`, and total size.
- Folder outputs record recursive file count, total size, and stable folder SHA-256.
- Folder SHA-256 uses sorted relative paths plus each file hash.
- Known output layouts record recognized files.
- A folder with `00_Index.md` and `_office2md/export_manifest.json` is detected as `obsidian_vault`.
- Obsidian export manifests are parsed when present.
- Export type, exported document count, exported concept count, and export warnings are recorded when available.

## Library Linkage

- Explicit `--library-version-id` links to that library version.
- If one library version exists, it is used automatically.
- If multiple library versions exist, the latest `registered_at` is used and a warning is recorded.
- If no library version exists, registration is blocked by default.
- `--allow-missing-library-version` records the output with a warning and without library/source linkage.

## Dry-Run Behavior

`--dry-run` builds the planned output version record and prints that `versions/output_versions.json` was not written. Existing output version history remains unchanged.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- CLI help checks:
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
- temp workspace/source/library/Obsidian export smoke
- second output registration append smoke
- dry-run no-write smoke
