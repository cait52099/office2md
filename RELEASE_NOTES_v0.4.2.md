# office2md v0.4.2 Release Notes

Status: final v0.4.2 release.

## Scope

v0.4.2 adds a read-only OfficeCLI benchmark and diagnostics workflow.

This release is for evaluation only. It does not implement OfficeCLI sidecar extraction, does not add `--office-engine officecli`, does not add OfficeCLI as a dependency, and does not change conversion, runner, build-library, search/ranking, Graph View, Obsidian export, workspace, or GUI behavior.

The current real smoke recommendation is `diagnostic_only` because one benchmark file timed out, while all source checksums remained unchanged.

## OfficeCLI Benchmark Command

New command:

```powershell
python -m office2md.cli officecli-benchmark INPUT_PATH OUTPUT_DIR
```

Options:

- `--officecli-path`
- `--max-files`
- `--include-hidden`
- `--formats`
- `--timeout-seconds`
- `--skip-html`
- `--json`
- `--dry-run`

OfficeCLI remains optional. If it is missing, the command reports a clear error. Unit tests do not require real OfficeCLI.

## Read-Only Safety

The command uses only read-only OfficeCLI operations:

- `--version`
- `view FILE outline`
- `view FILE text --max-lines 200`
- `view FILE html`
- `get FILE / --depth 2 --json`
- `validate FILE`
- `view FILE issues --limit 50`

Mutating command tokens are blocked from the benchmark command plan:

- `create`
- `add`
- `set`
- `remove`
- `open`
- `close`

For each source file, the benchmark computes SHA-256 before and after OfficeCLI commands. Checksum changes are recorded as critical failures.

The command does not write next to source files. All artifacts are written under `OUTPUT_DIR`.

## Benchmark Artifacts

The benchmark writes:

```text
OUTPUT_DIR/
  officecli_benchmark_summary.json
  officecli_benchmark_report.md
  files/
    <safe_file_id>/
      metadata.json
      outline.txt
      text.txt
      structure.json
      preview.html
      validate.txt
      issues.txt
      command_results.json
```

Per-file failures are recorded without stopping the whole benchmark.

## Diagnostics and Report Polish

The Markdown report includes:

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

Summary JSON keeps existing fields and additively includes:

- `failure_category`
- `failed_commands`
- `timed_out_commands`
- `html_generated`
- `recommendation`
- `recommendation_reasons`

## Failure Classification

Failure categories include:

- `command_timeout`
- `command_failed`
- `json_parse_failed`
- `html_not_generated`
- `checksum_changed`
- `unsupported_file`
- `unknown` reserved/documented

## Recommendation Heuristic

The recommendation is advisory only:

- `not_evaluated` for dry-run or no files;
- `diagnostic_only` for failures, timeouts, or checksum changes;
- `sidecar_candidate` only for mostly parseable, safe, usable artifacts;
- `engine_candidate` only when all files succeed with JSON, HTML, and text-like artifacts.

## Real OfficeCLI Smoke

Local smoke with `C:\Users\hcai\bin\officecli.exe` version `1.0.100` against `C:\Users\hcai\Desktop\test` selected 3 files:

- summary JSON parsed;
- Markdown report existed;
- failed file details were visible;
- failure categories: `command_timeout`, `None`, `None`;
- recommendation: `diagnostic_only`;
- checksum changes: 0;
- all source checksums unchanged;
- dry-run wrote no output artifacts.

## Validation

Final release validation includes:

- `python -m pytest`
- `python -m ruff check .`
- `python -m compileall office2md/gui`
- CLI help checks for OfficeCLI benchmark, workspace, export, conversion, library, search, locate, and report commands;
- real OfficeCLI smoke;
- dry-run smoke.
