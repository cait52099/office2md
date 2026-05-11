# office2md v0.3.1 Release Notes

Status: patch release after the v0.3.0 tag.

## Scope

This patch fixes release documentation consistency after the v0.3.0 tag.

## Changes

- Added the missing `RELEASE_NOTES_v0.3.0.md` file referenced by README.
- Restored README wording required by production-readiness checks:
  - `AI enrichment is opt-in`
  - `MiniMax CLI is not required`
- Updated package metadata version to `0.3.1`.
- Updated the release checklist with v0.3.1 patch evidence.

## Behavior

No runtime behavior changed.

This patch does not change:

- Conversion behavior.
- Runner process-control behavior.
- Build-library internals.
- Search core, ranking, aliases, or token fallback.
- Graph View behavior.
- Library-report metrics or scoring.
- Marker integration.
- Obsidian export.
- AI/MiniMax behavior.
- OCR.
- Embeddings/vector search.
- Cloud/network behavior.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- `python -m compileall office2md/gui`
- CLI help checks for convert, build-library, search-library, locate-document, and library-report.

