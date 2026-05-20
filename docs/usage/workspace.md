# Workspace Foundation

Initialize a local office2md workspace folder:

```powershell
python -m office2md.cli workspace-init "C:\path\to\project.office2md"
```

The MVP creates a conservative folder foundation:

```text
project.office2md/
  workspace_manifest.json
  source_manifest.json
  conversion/
  library/
  wiki/
    Concepts/
    Notes/
    Corrections/
    _suggestions/
  outputs/
    obsidian/
    reports/
    html/
    _manifests/
  logs/
  versions/
    library_versions.json
    output_versions.json
```

## Options

```powershell
python -m office2md.cli workspace-init "C:\path\to\project.office2md" --dry-run
python -m office2md.cli workspace-init "C:\path\to\project.office2md" --overwrite-manifests
```

- `--dry-run` prints planned directories and manifest files without writing anything.
- `--overwrite-manifests` replaces `source_manifest.json`, `versions/library_versions.json`, and `versions/output_versions.json` when they already exist.

## Idempotency

Running `workspace-init` twice is safe:

- missing directories are created;
- existing files are not deleted;
- `workspace_manifest.json` refreshes `updated_at`;
- existing source and version manifests are preserved unless `--overwrite-manifests` is explicitly provided.

This command creates only the workspace foundation. It does not convert documents, build a library, export outputs, edit Wiki notes, or require Git.

## Register Source Files

After initialization, register source files in the RAM traceability manifest:

```powershell
python -m office2md.cli workspace-scan "C:\path\to\project.office2md" "C:\path\to\sources"
```

`workspace-scan` discovers supported source files, records the source root, and updates `source_manifest.json` with source paths, relative paths, file sizes, modified times, and SHA-256 checksums. It does not convert files, build a library, create Knowledge Packs, or modify source files.

```powershell
python -m office2md.cli workspace-scan "C:\path\to\project.office2md" "C:\path\to\sources" --dry-run
python -m office2md.cli workspace-scan "C:\path\to\project.office2md" "C:\path\to\sources" --include-hidden
python -m office2md.cli workspace-scan "C:\path\to\project.office2md" "C:\path\to\sources" --max-files 20
```

- New files are recorded as `new`.
- Previously scanned files become `changed` when size, modified time, or checksum changes.
- Missing files are preserved in the manifest and marked `missing` rather than silently removed.
- `--dry-run` prints planned counts without writing `source_manifest.json`.
- `--max-files` records a limited scan and avoids treating unscanned historical records as missing.
- Dot-prefixed paths are excluded by default; `--include-hidden` includes supported files under those paths.

`source_manifest.json` is the first RAM/source traceability record. Later conversion, library, Wiki, and output versions can refer back to this manifest instead of treating source discovery as implicit state.

## Register a Built Library Version

After sources have been scanned and a library has been built through the normal `build-library` workflow, record that built library as a versioned workspace artifact:

```powershell
python -m office2md.cli workspace-register-library "C:\path\to\project.office2md" "C:\path\to\project.office2md\library"
```

The command accepts either a built library folder or a direct `library.db` path. It appends a record to `versions/library_versions.json` with the current source manifest hash, source counts, library file hashes, library metrics, registration time, optional label, and optional notes.

```powershell
python -m office2md.cli workspace-register-library "C:\path\to\project.office2md" "C:\path\to\library" --label "baseline"
python -m office2md.cli workspace-register-library "C:\path\to\project.office2md" "C:\path\to\library" --dry-run
```

`workspace-register-library` does not build a library, modify the library, convert files, or edit source files. It only records the relationship:

```text
source_manifest.json -> versions/library_versions.json -> built library files
```

If `source_manifest.json` contains changed or missing sources, the registration is allowed but the version record includes warnings so reviewers can see that the library was registered against a dirty source state.

## Register a Generated Output Version

After an export or report has been generated through its normal workflow, record it as a versioned output artifact:

```powershell
python -m office2md.cli workspace-register-output "C:\path\to\project.office2md" "C:\path\to\project.office2md\outputs\obsidian\vault"
```

The command accepts either a file or folder. It appends a record to `versions/output_versions.json` with output path, output type, file or folder hash summary, source linkage from the selected library version, optional label, and optional notes.

```powershell
python -m office2md.cli workspace-register-output "C:\path\to\project.office2md" "C:\path\to\vault" --label "obsidian baseline"
python -m office2md.cli workspace-register-output "C:\path\to\project.office2md" "C:\path\to\vault" --dry-run
```

`workspace-register-output` does not generate exports, modify outputs, convert files, or build libraries. It only records the relationship:

```text
source_manifest.json -> versions/library_versions.json -> versions/output_versions.json
```

If one library version exists, the output links to it automatically. If multiple library versions exist, the latest registered library version is used and a warning is recorded. If no library version exists, registration is blocked unless `--allow-missing-library-version` is provided.

Obsidian vault folders are detected when they contain `00_Index.md` and `_office2md/export_manifest.json`. When an Obsidian export manifest is present, the output version records its export type, exported document count, exported concept count, and export warnings.

## Check Workspace Status

Use `workspace-status` to inspect the current source/library/output traceability state:

```powershell
python -m office2md.cli workspace-status "C:\path\to\project.office2md"
```

The command is read-only. It does not scan sources, convert files, build libraries, generate exports, edit manifests, or modify source/output files.

The summary includes:

- workspace manifest metadata and missing expected folders/manifests;
- source counts, source root count, last scan details, and current `source_manifest.json` hash;
- latest registered library version, metrics, source manifest hash, and warnings;
- latest registered output version, linked library version, output type, file count, size, export manifest summary, and warnings;
- the latest traceability chain:

```text
source_manifest_hash -> library_version_id -> output_version_id
```

Additional options:

```powershell
python -m office2md.cli workspace-status "C:\path\to\project.office2md" --json
python -m office2md.cli workspace-status "C:\path\to\project.office2md" --show-history --limit 3
python -m office2md.cli workspace-status "C:\path\to\project.office2md" --strict
```

- `--json` prints parseable pretty JSON only.
- `--show-history` prints recent library and output versions.
- `--limit` controls how many history records are shown.
- `--strict` exits non-zero when required manifests are missing or the latest output links to a missing library version.

Warnings are informational by default. For example, `workspace-status` warns if the latest library or output was registered against a different `source_manifest.json` hash than the current workspace state.

## GUI Workspace Page

The optional Streamlit GUI includes a `Workspace` page that displays the same read-only status information as `workspace-status`.

It shows workspace, source, library version, output version, warning/error, and traceability chain summaries. It also provides a JSON download for the current status payload.

The GUI input is `Workspace Root Path`. This must be a folder created by `workspace-init`, not the sidebar Library path, not a conversion output folder, not a built library folder, and not an Obsidian export folder. If a non-workspace path is entered, the page shows the expected workspace markers and a suggested `workspace-init` command.

An init-only workspace is valid and will show empty source/library/output history until `workspace-scan`, `workspace-register-library`, and `workspace-register-output` have been run.

The GUI page does not initialize workspaces, scan sources, convert files, build libraries, generate exports, edit manifests, or modify source/output files.
