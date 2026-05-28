# office2md v0.4.3 Release Notes

Status: final v0.4.3 release.

## Scope

v0.4.3 is an OfficeCLI benchmark usability and timeout-control polish release.

This release does not implement OfficeCLI sidecar extraction, does not add `--office-engine officecli`, does not add OfficeCLI as a dependency, and does not change conversion, runner, build-library, search/ranking, Graph View, Obsidian export, workspace, or GUI behavior.

The current benchmark evidence remains `diagnostic_only`, not sidecar extraction or future engine adoption.

## Timeout and Usability Options

The `officecli-benchmark` command keeps existing options and adds clearer controls for timeout-heavy benchmark runs:

- `--skip-html`
- `--skip-structure-json`
- `--skip-issues`
- `--skip-validate`
- `--large-file-size-mb`
- `--timeout-seconds`, documented as a per-command timeout

These options only affect the benchmark command plan. They do not change conversion behavior.

## Report and JSON Additions

Summary JSON additively includes:

- `timeout_summary`
- `suggested_rerun_options`
- `large_file_warnings`
- `skipped_commands`

Markdown reports include:

- option summary;
- command timeout summary;
- timeout rerun suggestions;
- expensive command hints;
- large-file warnings;
- file size in the per-file result table.

Timeout-heavy reports can suggest rerun options such as `--skip-structure-json`, `--skip-html`, `--max-files 1`, `--timeout-seconds 120`, `--skip-issues`, `--skip-validate`, and benchmarking smaller batches.

## Safety

OfficeCLI remains optional and read-only:

- no dependency added;
- no mutating OfficeCLI command tokens are used;
- source SHA-256 is computed before and after commands;
- checksum changes are recorded;
- artifacts are written only under `OUTPUT_DIR`;
- per-file failures are recorded without stopping the benchmark;
- dry-run writes no artifacts.

## Real OfficeCLI Smoke

Default smoke with `C:\Users\hcai\bin\officecli.exe` against `C:\Users\hcai\Desktop\test` selected 3 files:

- summary JSON parsed;
- Markdown report existed;
- files succeeded: 2;
- files failed: 1;
- checksum changes: 0;
- all source checksums unchanged;
- timeout summary recorded 6 command timeouts on the large XLSX;
- recommendation remained `diagnostic_only`.

Light smoke with `--skip-html --skip-structure-json` selected 3 files:

- summary JSON parsed;
- Markdown report existed;
- `skipped_commands` recorded `html` and `structure`;
- files succeeded: 2;
- files failed: 1;
- timeout summary recorded 4 command timeouts;
- checksum changes: 0;
- all source checksums unchanged.

Dry-run smoke selected 2 files and wrote no output directory or artifacts.

## Validation

Final release validation included:

- `python -m pytest`
- `python -m ruff check .`
- `python -m compileall office2md/gui`
- CLI help checks for `officecli-benchmark`, `workspace-status`, `convert`, `build-library`, `search-library`, and `export-obsidian`
