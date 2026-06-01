# Release Notes — v0.5.11

v0.5.11 is a hotfix release for `build-library` performance and stability.
It is a single-issue change with no new features and no behavior changes
outside the identified hot loop.

## Summary

`build-library` hung indefinitely when rebuilding a real-sized library.
The hang was reproducible on a 669-manifest input and on the dedicated
diagnostic runner. Diagnostic tracebacks captured the stall inside
`_write_database` in `office2md/library.py`, at a triple-nested scan that
prepared per-document entity-mention text for the FTS5 row. The scan was
`O(n_documents × n_entities × n_entity_mentions)` and dominated the build
once the corpus was large enough.

The fix precomputes a single `(doc_id, entity_id)` set once before the
documents loop and replaces the inner `any(...)` membership check with
`O(1)` set lookup. Output semantics are preserved: each entity text
appears at most once per document in the FTS row, and the documents
FTS5 row is byte-compatible with the pre-fix output.

## Hotfix details

| Item | Value |
| --- | --- |
| Commit | `5164a8d` "Fix build-library entity mention indexing performance" |
| Files changed | `office2md/library.py`, `tests/test_library_builder.py` |
| Lines | +167 / -1 |
| New tests | 5 (multi-document entity extraction, dedup, empty-entities, end-to-end build, 50×50×50 performance regression) |
| Algorithmic complexity before | `O(n_documents × n_entities × n_entity_mentions)` |
| Algorithmic complexity after | `O(n_mentions + n_documents × n_entities)` |

## Real 669-manifest smoke evidence

| Metric | Value |
| --- | --- |
| Input | 669 Knowledge Pack manifests, 1,338 .md files |
| Output folder | `C:\Users\hcai\Documents\office2md_real_test\test_library_hotfix` (new, separate from damaged old output) |
| Elapsed | 84.3 seconds |
| `library.db` size | 100,724,736 bytes (~100 MB) |
| Documents | 669 |
| Chunks | 14,801 |
| Entities | 384 |
| `library-report` end-to-end check | OK |
| `search-library "vacuum pump fault" --limit 3` | 491 hits, top result `Project Owl 1.pptx` with relevant preview |
| `search-library "Symex" --limit 3` | 419 FTS-mode hits, top result `43DS Daily Rescue Eye Serum 2026...pptx` |
| Source folder `C:\Users\hcai\Desktop\test` last modified | 2026-05-28 14:59 (untouched) |
| Knowledge Pack manifests | 669 / 669 preserved |

## Validation

| Check | Result |
| --- | --- |
| `python -m pytest` | 226 passed in ~25 s |
| `python -m ruff check .` | All checks passed |
| `python -m compileall office2md/gui` | Succeeds |
| `python -m office2md.cli --help` | Succeeds |
| `python -m office2md.cli build-library --help` | Succeeds |
| `python -m office2md.cli search-library --help` | Succeeds |
| `python -m office2md.cli library-report --help` | Succeeds |
| `python -m office2md.cli update-library --help` | Succeeds |

## Explicit non-goals

This release does **not** include any of the following. Each was
considered and deferred to a later issue.

- No new feature implementation.
- No runtime behavior changes beyond the identified hot loop.
- No conversion behavior changes (Docling / MarkItDown / engine /
  profile / `--skip-existing` / `--with-json` / `--render-pdf-pages`
  / etc. are all unchanged).
- No build-library `--quiet`, `--log-file`, or `--progress-json`
  flags are added in this release (the v0.5.10 `update-library`
  flag pattern is the model; back-porting to `build-library` is a
  defensive follow-up, not part of this hotfix).
- No atomic-rename refactor of `library.db` (the
  `atomic-library-db-replace` backlog item; the hang is gone so the
  defensive refactor is no longer the critical path).
- No search ranking, alias, or token fallback changes.
- No update-library behavior changes (`--log-file` / `--progress-json`
  / `--quiet` added in v0.5.10 are preserved; the `--change-plan`
  dry-run flow is unchanged).
- No OfficeCLI main-pipeline integration; OfficeCLI remains
  `diagnostic_only`.
- No MCP changes; the read-only `office2md.mcp_adapter` is unchanged.
- No AI, OCR, embedding, vector, cloud, or unrestricted SQL work.
- No shell execution features added to the office2md runtime.
- No source file modification in any test path.
- No Knowledge Pack manifest modification.
- No knowledge pack regeneration in any user-facing path.

## Acknowledgements

The hang was diagnosed using a dedicated local-only diagnostic runner
(`.office2md_optimizer/diagnostics/diag_build_library.py`) that
combined `faulthandler` with periodic traceback dumps and per-stage
instrumentation. The runner is a local-only operator tool and is
excluded from git.
