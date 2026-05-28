# OfficeCLI Benchmark

Status: v0.4.2 P1 benchmark command.

`officecli-benchmark` runs a safe, read-only benchmark against Office files to evaluate whether OfficeCLI can improve future DOCX, XLSX, and PPTX processing.

OfficeCLI is optional. It is not required by office2md, is not used by default conversion, and is not integrated as a conversion engine.

## Command

```powershell
python -m office2md.cli officecli-benchmark INPUT_PATH OUTPUT_DIR
```

Use an explicit executable path when OfficeCLI is not on `PATH`:

```powershell
python -m office2md.cli officecli-benchmark INPUT_PATH OUTPUT_DIR --officecli-path "C:\Users\hcai\bin\officecli.exe"
```

## Options

- `--officecli-path PATH`: OfficeCLI executable path. Defaults to `officecli` on `PATH`.
- `--max-files INTEGER`: limit selected Office files.
- `--include-hidden`: include files under dot-prefixed folders.
- `--formats EXTENSIONS`: comma-separated extensions. Default: `docx,xlsx,pptx`.
- `--timeout-seconds INTEGER`: per-command timeout. Default: `60`.
- `--skip-html`: skip HTML preview generation.
- `--json`: print summary JSON.
- `--dry-run`: preview selected files and planned commands without running OfficeCLI or writing artifacts.

## Read-Only Safety

The benchmark only uses read-only OfficeCLI commands:

- `--version`
- `view FILE outline`
- `view FILE text --max-lines 200`
- `view FILE html`
- `get FILE / --depth 2 --json`
- `validate FILE`
- `view FILE issues --limit 50`

The benchmark never uses:

- `create`
- `add`
- `set`
- `remove`

For each source file, office2md computes SHA-256 before and after the OfficeCLI commands. If the checksum changes, the file is marked as a critical failure.

The benchmark does not write next to source files. All artifacts are written under `OUTPUT_DIR`.

## Input Handling

`INPUT_PATH` can be one Office file or a folder.

Directory scans include:

- `.docx`
- `.xlsx`
- `.pptx`

Temporary Office files such as `~$name.docx` are ignored. Legacy `.doc` files are not selected.

## Output Structure

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

If a command fails, the command result is still recorded in `command_results.json` and the summary.

## Diagnostics

The summary JSON and Markdown report include additive diagnostics:

- per-file result status;
- per-command exit code, timeout flag, runtime, and artifact path;
- failed command names;
- timed out command names;
- failure category;
- JSON parseability;
- HTML generation;
- checksum safety;
- advisory recommendation.

Failure categories are conservative:

- `officecli_unavailable`
- `command_failed`
- `command_timeout`
- `json_parse_failed`
- `html_not_generated`
- `checksum_changed`
- `unsupported_file`
- `unknown`

The recommendation is advisory only. It does not change conversion behavior:

- `not_evaluated`
- `diagnostic_only`
- `sidecar_candidate`
- `engine_candidate`

## Purpose

The benchmark output is evidence for a future decision. It does not change conversion behavior.

Possible future outcomes:

- do not integrate OfficeCLI;
- keep OfficeCLI as benchmark or diagnostic only;
- add optional OfficeCLI sidecar extraction;
- add an explicit optional OfficeCLI engine for selected Office formats.
