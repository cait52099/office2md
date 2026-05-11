# v0.3.2 P1 Obsidian Export CLI MVP

Status: CLI MVP scope.

## Purpose

v0.3.2 P1 adds a local CLI export path from an existing built office2md Knowledge Library to an Obsidian-friendly vault folder. The export is a convenience view over the library; it does not change conversion, library building, search, ranking, graph generation, runner behavior, OCR, AI, embeddings, or cloud behavior.

## Command

```powershell
python -m office2md.cli export-obsidian LIBRARY_PATH VAULT_OUTPUT
```

`LIBRARY_PATH` may be either a built library folder or a `library.db` path.

Options:

- `--overwrite`: allow replacing an existing non-empty output folder.
- `--dry-run`: report export counts without writing files.
- `--max-concepts INTEGER`: maximum concept notes to export, default `100`.
- `--max-evidence-per-concept INTEGER`: maximum evidence snippets per concept note, default `5`.

## Output Structure

```text
VAULT_OUTPUT/
  00_Index.md
  00_Library_Report.md
  Documents/
  Concepts/
  _office2md/
    export_manifest.json
```

## Notes

Document notes include YAML frontmatter:

- `office2md_type: document`
- `office2md_id`
- `source_file`
- `document_kind`
- `created_by: office2md`

Each document note includes a Related Concepts section with Obsidian wikilinks.

Concept notes include YAML frontmatter:

- `office2md_type: concept`
- `concept`
- `match_count`
- `document_count`
- `created_by: office2md`

Each concept note includes a Related Documents section with Obsidian wikilinks.

## Concept Extraction

The export uses the same library-native concept quality approach introduced for the GUI Knowledge Graph: concepts are detected from current-library entities, document titles, headings, and chunk text, then filtered for noisy labels and low-confidence fragments.

The exporter does not use a fixed equipment vocabulary. It should work with non-equipment libraries because the concept list comes from the built library content itself.

## Safety

The exporter creates the vault output folder. If that folder already exists and is non-empty, the command fails unless `--overwrite` is provided.

The MVP does not require Obsidian to be installed.

Assets are not copied in P1. If the source library contains assets, the export manifest records a warning.

## Out Of Scope

- GUI export page.
- Marker integration.
- PDF, Word, or HTML export.
- AI, OCR, embeddings, vector search, or cloud features.
- Conversion behavior changes.
- Runner behavior changes.
- Build-library internals changes.
- Search/ranking/aliases/token fallback changes.
- Library-report scoring changes.
- Graph View behavior changes.
