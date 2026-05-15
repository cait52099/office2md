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
