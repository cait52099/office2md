# office2md v0.4.2-rc1 Release Notes

Status: release candidate for v0.4.2 P1.

## Scope

v0.4.2-rc1 adds a safe, read-only OfficeCLI benchmark harness.

This checkpoint does not implement OfficeCLI sidecar extraction, does not add `--office-engine officecli`, does not add OfficeCLI as a required dependency, does not change default conversion behavior, runner behavior, build-library behavior, search/ranking behavior, Graph View behavior, Obsidian export behavior, or workspace behavior, and does not add AI, OCR, Marker, vector, or cloud work.

## Command

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

## Optional OfficeCLI Behavior

OfficeCLI remains optional:

- no dependency was added;
- unit tests use mocked/fake subprocess behavior and do not require real OfficeCLI;
- missing OfficeCLI produces a clear CLI error;
- benchmark execution is explicit and separate from conversion.

## Read-Only Safety

The harness only plans and runs read-only OfficeCLI commands:

- `--version`
- `view FILE outline`
- `view FILE text --max-lines 200`
- `view FILE html`
- `get FILE / --depth 2 --json`
- `validate FILE`
- `view FILE issues --limit 50`

Mutating command tokens are forbidden in the benchmark command plan:

- `create`
- `add`
- `set`
- `remove`
- resident edit `open`
- resident edit `close`

For each selected source file, the benchmark computes SHA-256 before and after OfficeCLI commands. If a checksum changes, the file is marked with a critical failure. Source files are not written by office2md, and artifacts are written only under `OUTPUT_DIR`.

## Output Artifacts

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

If a command fails, command metadata is still recorded. Per-file failures do not stop the full benchmark unless OfficeCLI itself is unavailable.

## Dry-Run Behavior

`--dry-run` selects files and shows planned read-only commands without running OfficeCLI or writing artifacts.

## Real OfficeCLI Smoke

Local smoke with `C:\Users\hcai\bin\officecli.exe` version `1.0.100` against `C:\Users\hcai\Desktop\test` selected 3 files:

- summary JSON parsed;
- Markdown report existed;
- source checksums remained unchanged;
- 2 files succeeded;
- 1 file failed and was recorded per-file without stopping the benchmark;
- checksum changes: 0.

## Documentation

Updated documentation:

- `docs/design/v042_officecli_benchmark_plan.md`
- `docs/usage/officecli_benchmark.md`
- `README.md`

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
