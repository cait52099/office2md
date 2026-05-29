# office2md v0.4.8-rc1 Release Notes

Status: release candidate for v0.4.8 Multi-library Agent Access and Update Review Foundation.

## Scope

v0.4.8-rc1 adds additive review and catalog foundations:

- additive `update-library` review fields;
- `update-library --review-report` Markdown export;
- `library-catalog` CLI;
- library catalog schema `office2md.library_catalog.v1`;
- multi-library agent access design and usage docs;
- tests for review summaries, review reports, and catalog JSON.

## Update Review

`update-library` now includes additive result fields:

- `review_summary`;
- `large_folder_warnings`;
- `next_steps`.

The optional review report writes Markdown only:

```powershell
python -m office2md.cli update-library SOURCE_PATH CONVERSION_OUTPUT LIBRARY_PATH --dry-run --review-report update_review.md
```

This does not change update execution semantics. `update-library` still converts only `new` and `modified` files, reuses unchanged valid Knowledge Packs, records deleted/missing/stale sources without deleting evidence, and rebuilds via existing `build_library()`.

## Library Catalog

New command:

```powershell
python -m office2md.cli library-catalog libraries.json --add-library LIBRARY_PATH --library-id lib-a --library-name "Library A"
python -m office2md.cli library-catalog libraries.json --json
```

Schema:

```text
office2md.library_catalog.v1
```

Catalog records include:

- `library_id`;
- `library_name`;
- `library_path`;
- `source_root`;
- `registered_at`.

The catalog is for routing and provenance only. It does not modify source files, library databases, indexes, graphs, or evidence.

## Agent Provenance

Evidence from any library should preserve:

- `library_id`;
- `library_name`;
- `library_path`;
- `source_file`;
- `locator`;
- `chunk_id`;
- `document_id`.

Existing single-library commands remain compatible. Multi-library search execution is not implemented in this checkpoint.

## Smoke

Temp smoke confirmed:

- review report creation;
- `update_result.json` remains schema `office2md.update_result.v1`;
- update converted 2 files, reused 1 Knowledge Pack, and recorded 1 missing source;
- rebuilt search and `open-chunk` still worked;
- catalog JSON parsed with schema `office2md.library_catalog.v1`.

Real-source dry-run/review smoke against `C:\Users\hcai\Desktop\test` confirmed:

- source snapshot remained unchanged;
- 1216 files were scanned;
- 76 PPTX files were present;
- plan counts were `new=667`, `modified=0`, `unchanged=3`, `deleted_missing=0`, `moved_or_renamed_candidate=0`, `unsupported=546`, `stale=0`;
- review report was created;
- no `update_result.json` was written;
- temp conversion and library outputs were unchanged by dry-run.

## Non-Goals

This checkpoint does not include:

- multi-library search execution;
- MCP implementation;
- conversion behavior changes;
- build-library behavior changes;
- search ranking, alias, or token fallback changes;
- open-chunk, locate-document, or build-report-context behavior changes;
- update-library execution semantic changes;
- runner, workspace, or GUI behavior changes;
- OfficeCLI main-pipeline integration;
- embeddings or vector search;
- OCR;
- Obsidian plugin;
- write-back;
- unrestricted SQL;
- shell execution;
- automatic deletion;
- watcher or background update.

OfficeCLI remains `diagnostic_only`.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- `python -m compileall office2md/gui`
- `python -m office2md.cli --help`
- `python -m office2md.cli update-library --help`
- `python -m office2md.cli library-catalog --help`
- `python -m office2md.cli scan-changes --help`
- `python -m office2md.cli search-library --help`
- `python -m office2md.cli open-chunk --help`
