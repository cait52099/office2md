# v0.2.3 Backlog

Baseline: `v0.2.2`

v0.2.2 is the current stable release. It completed a conservative usability polish track on top of v0.2.1:

- `search-library --diagnostics-json`
- `search-library --export-json PATH`
- chunked/resume runner final summary output
- CLI help wording consistency

v0.2.3 should stay conservative. Do not add embeddings/vector search, OCR, AI/MiniMax, cloud/network dependencies, Office image export, or legacy `.doc` conversion. Do not change search ranking, aliases, token fallback logic, conversion behavior, output schemas, result ordering, or runner process-control behavior unless a validated regression is discovered and explicitly scoped as a blocker.

## Baseline Validation

- Git status: clean on `master`
- HEAD/tag: `v0.2.2`
- Python: 3.11.9 from project `.venv`
- pytest: 69 passed
- ruff: all checks passed
- Current stable capabilities:
  - Office/PDF/text-like conversion
  - per-document Knowledge Pack output
  - Knowledge Library Builder
  - SQLite/FTS `library.db`
  - `library_index.json`
  - `library_graph.json`
  - Markdown portal
  - interop JSONL exports
  - `library-report`
  - `search-library`
  - `locate-document`
  - FTS ranking, token fallback, facets, filters, context, related chunks
  - alias/normalization
  - `search-library --diagnostics`
  - `search-library --diagnostics-json`
  - `search-library --export-json PATH`
  - chunked/resume PowerShell runner
  - runner final summary
  - common workflow docs
  - CLI help wording polish

## P0 Blockers

No P0 release blockers are currently identified for v0.2.3.

If a new validation dataset reveals a regression, the regression should become the only P0 task and should be handled before any polish work. In particular, v0.2.3 should not begin by changing search ranking, conversion routing, or runner process control.

## P1 Small High-Value Polish

### 1. `library-report --export-json`

- Problem: v0.2.2 added machine-readable search diagnostics and search results, but `library-report` still only prints a Rich table. Release evidence and automation still require scraping console output for library-level metrics.
- Proposed solution: Add optional `library-report --export-json PATH` that writes UTF-8 pretty JSON using the existing `library_report()` dictionary. Parent directories should be created automatically, matching `search-library --export-json`. Keep the normal console report unchanged except for an `export_json: <path>` confirmation line when the option is used.
- Expected files touched: `office2md/cli.py`, `tests/test_library_builder.py`, README, `docs/usage/common_workflows.md`, release notes/checklist for the checkpoint.
- Risk level: Low. The data already exists as a dictionary; this should be output serialization only.
- Validation method: Unit or CLI-style test that export JSON parses and contains document/chunk/entity counts, distributions, top entities, quality metrics, and export file names. Smoke check against the existing CML125 full library. Verify default `library-report` output without `--export-json` remains unchanged.
- v0.2.3 decision: Include.

### 2. Common Workflow / Demo Evidence Package

- Problem: v0.2.2 has strong commands and docs, but a new user still needs to stitch together a practical "convert, build, search, export, report, runner dry-run" walkthrough.
- Proposed solution: Add a concise docs-only demo package under `docs/usage/` or `docs/ops/` that gives copy-paste PowerShell commands for a small local sample workflow and a CML125 review workflow. Include expected outputs at a high level, not large embedded command output. Cover `--diagnostics-json`, `--export-json`, `library-report`, `locate-document`, and runner final summary.
- Expected files touched: `docs/usage/common_workflows.md` or a new `docs/usage/v023_demo_workflow.md`, README cross-link if needed.
- Risk level: Low. Docs-only.
- Validation method: Syntax review against CLI help; run small sample commands if feasible; pytest/ruff to keep release baseline green.
- v0.2.3 decision: Include after `library-report --export-json`.

### 3. Quality Report Detail Polish

- Problem: `_quality_report.md` remains dense for large libraries. It can be hard to distinguish actionable issues from informational counts.
- Proposed solution: Refine formatting only. Group failed manifests, low-structure documents, page-level searchable PDFs, noisy chunks, chunks without locators, and HMI translation notes. Do not change quality metrics, scoring, document classification, chunk flags, or library counts.
- Expected files touched: `office2md/library.py`, `tests/test_library_builder.py`, possibly README if report examples are added.
- Risk level: Low to medium. Low if strictly formatting-only; medium if tests depend on exact report text.
- Validation method: Fixture tests for report sections; rebuild fixture library; compare all counts before/after.
- v0.2.3 decision: Include only if it stays formatting-only and after export/docs work.

### 4. Office-Derived Locator Audit

- Problem: Some Office-derived chunks can still lack precise locators. Before changing chunk generation, the project needs a clear count of which document families and evidence types still lack locators.
- Proposed solution: Add an audit-only report or documented manual query that summarizes locator coverage by document kind and evidence type. Prefer using existing `library.db` data and existing report/export paths. Do not change chunk generation in the audit step.
- Expected files touched: possibly `office2md/library.py` if implemented as report data, `office2md/cli.py` if exposed through `library-report --export-json`, tests, docs. A docs-only audit recipe is acceptable for the first checkpoint.
- Risk level: Low if audit-only; medium if new report fields are added.
- Validation method: Fixture test for locator coverage fields if implemented; smoke check on CML125 full library; verify no chunks or source maps are regenerated.
- v0.2.3 decision: Include audit-only. Defer locator generation changes unless the audit identifies one low-risk family.

## P2 Useful But Non-Urgent Improvements

### 5. One-Family Office Locator Polish

- Problem: After audit, one Office family may have locator gaps that reduce trust in search results and `--has-locator` workflows.
- Proposed solution: If audit evidence identifies a narrow, low-risk gap, improve exactly one family using metadata already present in chunks/source maps, such as sheet/table/row for XLSX/HMI or slide number/title for PPTX. Avoid broad refactors.
- Expected files touched: `office2md/postprocess/office_structure.py`, possibly `office2md/postprocess/knowledge_pack.py`, focused tests in `tests/test_office_enhancement.py` or `tests/test_library_builder.py`, docs if user-visible.
- Risk level: Medium. Locator changes can affect source maps, chunks, tests, and search filters.
- Validation method: Fixture tests for the selected family; before/after locator coverage counts; search smoke with `--has-locator`; no conversion engine changes.
- v0.2.3 decision: Defer until audit evidence justifies one family.

### 6. Runner Usability Next Polish

- Problem: The runner final summary is useful, but operators may still need easier log review after long runs.
- Proposed solution: Consider output-only additions such as listing the last stdout/stderr log paths in final summary, or writing a tiny summary JSON/text file beside logs. Do not alter process launch, timeout, retry, or kill behavior.
- Expected files touched: `scripts/Invoke-Office2MdChunkedConvert.ps1`, `docs/ops/cml125_batch_validation.md`.
- Risk level: Low to medium. Output-only is low risk; process-control changes are out of scope.
- Validation method: Dry-run checks for `-MaxFiles 3` and `-FullDirectory`; tiny sample run; verify no change in conversion command or retry behavior.
- v0.2.3 decision: Defer unless users need log artifact handoff.

### 7. Conservative Bilingual Alias Review

- Problem: Existing bilingual aliases cover a small validated set. Additional aliases may help, but unvalidated aliases can reduce precision.
- Proposed solution: Review real query examples and diagnostics/export evidence first. Add aliases only when a term is stable, low ambiguity, and original exact search still has 0 hits. No broad synonym expansion.
- Expected files touched: `office2md/library.py`, `tests/test_library_builder.py`, README/docs only if examples change.
- Risk level: Medium. Alias changes can alter result paths and user expectations.
- Validation method: Before/after smoke set covering exact identifiers, existing bilingual aliases, weak operational queries, and no-hit identifiers such as `1THLS200`.
- v0.2.3 decision: Defer unless strong evidence is collected.

### 8. Search Export / Diagnostics Automation Examples

- Problem: v0.2.2 added machine-readable JSON, but automation examples are minimal.
- Proposed solution: Add docs with small PowerShell snippets showing how to run search exports, parse JSON, compare top result/source file, and store release evidence. Keep docs short and avoid requiring extra dependencies.
- Expected files touched: `docs/usage/common_workflows.md` or new docs file.
- Risk level: Low.
- Validation method: Command syntax review; optional smoke against fixture library or CML125 full library.
- v0.2.3 decision: Include as part of the demo workflow docs if time allows.

## P3 Deferred / Future Ideas

### 9. Legacy `.doc` Handling

- Problem: Legacy `.doc` remains unsupported/fragile in the validated path.
- Proposed solution: Keep documented as a known limitation. Future work may add preflight diagnostics or optional LibreOffice-specific handling, but v0.2.3 should not add legacy `.doc` conversion.
- Expected files touched: future converter routing, docs, tests with legacy fixtures.
- Risk level: High if conversion behavior changes.
- Validation method: Dedicated legacy Office fixture set and full regression pass.
- v0.2.3 decision: Defer.

### 10. Optional Embedding / Vector Sidecar

- Problem: Broad conceptual search may eventually benefit from semantic retrieval, but current FTS/token fallback/facets/context/export path is practical and validated.
- Proposed solution: Keep as future-only design. If revisited, it must be offline, optional, disabled by default, sidecar-based, and benchmarked against current search before implementation.
- Expected files touched: future design docs first; later optional sidecar outputs and CLI commands.
- Risk level: High due to dependencies, model choice, reproducibility, storage, and validation.
- Validation method: Separate benchmark comparing FTS, token fallback, context, diagnostics, and any hybrid approach.
- v0.2.3 decision: Defer.

### 11. OCR

- Problem: Image-only/scanned content remains inaccessible without OCR.
- Proposed solution: Keep OCR deferred. Future OCR work should be explicit, opt-in, local, and clearly reported in manifests.
- Expected files touched: future conversion options, PDF/image pipeline, dependencies, docs, tests.
- Risk level: High due to dependency footprint and variable extraction quality.
- Validation method: Dedicated OCR fixture set and explicit `ocr_used` reporting.
- v0.2.3 decision: Defer.

### 12. AI/MiniMax Enrichment

- Problem: Summaries and semantic enrichment could be useful, but the validated path intentionally remains no-AI and local.
- Proposed solution: Keep AI/MiniMax out of v0.2.3. Existing opt-in adapter framework remains outside the validated default path.
- Expected files touched: future AI docs/tests only if a separate opt-in track is reopened.
- Risk level: High for privacy, reproducibility, validation, and governance.
- Validation method: Separate opt-in validation with AI disabled by default.
- v0.2.3 decision: Defer.

### 13. Office Image Export

- Problem: Office outputs record embedded image and missing asset counts, but embedded Office images are not exported.
- Proposed solution: Keep Office image export deferred. Future work needs dedicated design for DOCX/PPTX asset extraction, Markdown reference repair, deduplication, and visual validation.
- Expected files touched: future Office postprocessors, asset handling, manifest fields, tests, docs.
- Risk level: High because output assets and Markdown references change.
- Validation method: Office image fixture set and visual asset checks.
- v0.2.3 decision: Defer.

### 14. Marker Integration Expansion

- Problem: Marker may improve some PDF outputs, but it adds dependency and validation complexity beyond the current stable no-AI path.
- Proposed solution: Keep Marker as optional/future. Do not change default routing or release validation around Marker in v0.2.3.
- Expected files touched: future converter routing, docs, tests.
- Risk level: Medium to high.
- Validation method: Dedicated PDF benchmark comparing Docling, MarkItDown fallback, and Marker.
- v0.2.3 decision: Defer.

## Recommended First v0.2.3 Task

Start with `library-report --export-json`.

Reason: it mirrors the successful v0.2.2 search export pattern, exposes already computed `library_report()` data, does not affect search ranking/conversion/runner behavior, and gives automation a complete machine-readable path for both search-level and library-level evidence.

Suggested order:

1. Add `library-report --export-json PATH`.
2. Add workflow/demo docs for conversion, build, report export, search export, diagnostics JSON, locate-document, and runner dry-run.
3. Add or document locator coverage audit using existing library data.
4. Apply formatting-only quality report polish if still useful.
5. Revisit one-family Office locator polish only if audit evidence clearly supports it.

## Explicitly Deferred From v0.2.3

- embeddings/vector search
- OCR
- AI/MiniMax
- cloud/network dependency
- Office image export
- legacy `.doc` conversion
- broad synonym expansion
- search ranking changes
- alias changes without strong evidence
- token fallback logic changes
- conversion behavior changes
- runner process-control changes
- broad Office locator refactor
