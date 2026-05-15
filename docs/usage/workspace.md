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
