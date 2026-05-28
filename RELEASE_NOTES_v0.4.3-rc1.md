# office2md v0.4.3-rc1 Release Notes

Status: release candidate for v0.4.3 P1.

## Scope

v0.4.3-rc1 improves OfficeCLI benchmark usability and timeout-control reporting.

This checkpoint does not implement OfficeCLI sidecar extraction, does not add `--office-engine officecli`, does not add OfficeCLI as a dependency, does not change conversion behavior, runner behavior, build-library behavior, search/ranking behavior, Graph View behavior, Obsidian export behavior, or workspace behavior, and does not add AI, OCR, Marker, vector, or cloud work.

## CLI Options

The benchmark keeps existing options:

- `--skip-html`
- `--timeout-seconds`

New options:

- `--skip-structure-json`
- `--skip-issues`
- `--skip-validate`
- `--large-file-size-mb`

`--timeout-seconds` remains a per-command timeout and is reflected in the report.

## Timeout Diagnostics

The benchmark summary and report now include:

- `timeout_summary`
- `suggested_rerun_options`
- `large_file_warnings`
- `skipped_commands`

Reports include:

- option summary;
- command timeout summary;
- timeout rerun suggestions;
- expensive command hints;
- large-file warnings;
- file size in the per-file result table.

Timeout-heavy reports suggest rerun options such as:

- `--skip-structure-json`
- `--skip-html`
- `--max-files 1`
- `--timeout-seconds 120`
- `--skip-issues`
- `--skip-validate`
- benchmark smaller batches.

## Skip Behavior

Skipped commands are not run. They are recorded in summary JSON and displayed in the report option summary.

`--dry-run` still writes no artifacts.

## Safety

OfficeCLI remains optional and read-only:

- no dependency added;
- no mutating OfficeCLI command tokens;
- source SHA-256 is computed before and after;
- source checksums are checked;
- artifacts are written only under `OUTPUT_DIR`;
- per-file failures are recorded without stopping the benchmark.

## Real OfficeCLI Smoke

Default smoke with `C:\Users\hcai\bin\officecli.exe` against `C:\Users\hcai\Desktop\test` selected 3 files:

- summary JSON parsed;
- Markdown report existed;
- checksum changes: 0;
- all source checksums unchanged;
- timeout summary recorded 6 timeouts on the large XLSX;
- rerun suggestions included `--skip-structure-json`, `--skip-html`, `--max-files 1`, and `--timeout-seconds 120`;
- recommendation remained `diagnostic_only`.

Skip-heavy smoke with `--skip-html` selected 3 files:

- summary JSON parsed;
- Markdown report existed;
- `skipped_commands` recorded `html`;
- timeouts reduced from 6 to 4;
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
