# office2md v0.3.2-rc1 Release Notes

Status: release candidate for v0.3.2 P1.

## Scope

v0.3.2-rc1 adds the Obsidian Export CLI MVP.

This checkpoint does not include a GUI export page, Marker integration, PDF/Word/HTML export, AI, OCR, embeddings, vector search, cloud features, conversion changes, runner process-control changes, build-library changes, search/ranking changes, Graph View changes, or library-report scoring changes.

## Command

```powershell
python -m office2md.cli export-obsidian LIBRARY_PATH VAULT_OUTPUT
```

`LIBRARY_PATH` accepts either a built library folder or a direct `library.db` path.

Options:

- `--overwrite`
- `--dry-run`
- `--max-concepts`
- `--max-evidence-per-concept`

## Vault Output

The export creates:

```text
VAULT_OUTPUT/
  00_Index.md
  00_Library_Report.md
  Documents/
  Concepts/
  _office2md/
    export_manifest.json
```

Document notes include YAML frontmatter, a Related Concepts section, and Obsidian `[[wikilinks]]`.

Concept notes include YAML frontmatter, a Related Documents section, and Obsidian `[[wikilinks]]`.

`_office2md/export_manifest.json` records:

- `export_type`
- `office2md_version`
- `library_path`
- `vault_output`
- `documents_exported`
- `concepts_exported`
- `warnings`
- `options`

## Concept Extraction

The exporter uses library-native concept extraction from the current built library: entities, document titles, headings, and chunk text are scored and filtered for noisy labels.

No fixed equipment vocabulary is used.

Concept quality is MVP/heuristic in this release candidate and may need tuning after real-use Obsidian vault review.

## Safety Behavior

- Non-empty output folders fail unless `--overwrite` is provided.
- `--dry-run` reports planned export counts without writing files.
- Assets are intentionally not copied in this MVP.
- If the source library contains assets, the export manifest records a warning.
- Obsidian does not need to be installed.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- CLI help checks:
  - `export-obsidian`
  - `convert`
  - `build-library`
  - `search-library`
  - `locate-document`
  - `library-report`
- Tiny fixture smoke: convert `tests/fixtures/sample.txt`, build library, export Obsidian vault, confirm expected files and manifest.
- CML125 dry-run smoke: skipped if the local CML125 library path is unavailable.
