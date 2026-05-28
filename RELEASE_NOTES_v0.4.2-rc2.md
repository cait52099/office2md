# office2md v0.4.2-rc2 Release Notes

Status: release candidate for v0.4.2 P2.

## Scope

v0.4.2-rc2 polishes OfficeCLI benchmark diagnostics and reports.

This checkpoint does not implement OfficeCLI sidecar extraction, does not add `--office-engine officecli`, does not add OfficeCLI as a dependency, does not change conversion behavior, runner behavior, build-library behavior, search/ranking behavior, Graph View behavior, Obsidian export behavior, or workspace behavior, and does not add AI, OCR, Marker, vector, or cloud work.

## Report Polish

`officecli_benchmark_report.md` now includes:

- per-file result table;
- per-command result table;
- failed files section;
- failed command details;
- `stderr` and `stdout` excerpts;
- exit code;
- timeout flag;
- runtime;
- artifact path;
- checksum safety section;
- JSON parseability section;
- HTML generation section;
- per-format DOCX/XLSX/PPTX summary.

## Summary JSON Additions

Summary JSON remains backward compatible. Existing fields remain, and these additive fields are included:

- `failure_category`
- `failed_commands`
- `timed_out_commands`
- `html_generated`
- `recommendation`
- `recommendation_reasons`

## Failure Classification

The benchmark records conservative failure categories:

- `command_timeout`
- `command_failed`
- `json_parse_failed`
- `html_not_generated`
- `checksum_changed`
- `unsupported_file`
- `unknown` reserved/documented

## Recommendation Heuristic

The benchmark records an advisory recommendation. It does not change behavior:

- `not_evaluated` for dry-run or no files processed;
- `diagnostic_only` when failures, timeouts, or checksum changes exist;
- `sidecar_candidate` only when most files produce parseable JSON and usable artifacts with unchanged checksums;
- `engine_candidate` only when all files succeed with JSON, HTML, and text-like artifacts.

## Safety

OfficeCLI remains optional and read-only:

- no dependency added;
- no mutating OfficeCLI commands;
- source SHA-256 is computed before and after;
- source checksums are checked;
- artifacts are written only under `OUTPUT_DIR`;
- per-file failures are recorded without stopping the benchmark.

## Real OfficeCLI Smoke

Local smoke with `C:\Users\hcai\bin\officecli.exe` version `1.0.100` against `C:\Users\hcai\Desktop\test` selected 3 files:

- summary JSON parsed;
- Markdown report existed;
- failed file details were visible;
- failure categories: `command_timeout`, `None`, `None`;
- recommendation: `diagnostic_only`;
- checksum changes: 0;
- all source checksums unchanged.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- CLI help checks:
  - `officecli-benchmark`
  - `workspace-status`
  - `convert`
  - `build-library`
  - `search-library`
  - `export-obsidian`
