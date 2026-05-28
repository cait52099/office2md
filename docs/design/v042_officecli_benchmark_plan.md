# v0.4.2 OfficeCLI Benchmark Plan

Status: design with v0.4.2 P1 benchmark harness.

Implementation note: v0.4.2 P1 adds a read-only `officecli-benchmark` harness for this plan. It remains optional, does not change conversion behavior, and does not add OfficeCLI as a dependency.

v0.4.2 P2 adds report diagnostics and an advisory recommendation heuristic. These additions are reporting-only and do not change conversion behavior or promote OfficeCLI to an engine.

v0.4.3 P1 adds benchmark usability controls for timeout-heavy files, including skip options for expensive read-only commands, timeout summaries, rerun suggestions, and large-file warnings. These changes remain benchmark-only.

## Purpose

This benchmark evaluates whether `C:\Users\hcai\bin\officecli.exe` version `1.0.100` can improve office2md Office document processing for `DOCX`, `XLSX`, and `PPTX` files.

The benchmark is intended to answer practical integration questions before any product code is added:

- whether OfficeCLI extracts useful Office structure that current conversion misses;
- whether its output is stable, parseable, and traceable enough for Knowledge Packs;
- whether it can improve locators, diagnostics, previews, or quality checks;
- whether it can run safely without modifying source files.

## Integration Principle

OfficeCLI must remain optional.

It must not become a required dependency for office2md. It must not replace the current conversion path by default. Any future integration should be additive, feature-gated, and easy to skip when OfficeCLI is not installed.

The default office2md conversion behavior should remain unchanged unless a later benchmark proves a narrow, explicit OfficeCLI mode is worth adding.

## Candidate Use Cases

The benchmark should test OfficeCLI only for read-oriented Office document support:

- `DOCX` heading, paragraph, table, and style extraction;
- `XLSX` sheet, table, cell, and formula extraction;
- `PPTX` slide, shape, table, and notes extraction;
- HTML preview snapshot generation;
- stable locator extraction for pages, sheets, slides, cells, paragraphs, or shapes;
- Office quality diagnostics;
- Office structure validation.

These use cases should be compared with current office2md output. The goal is not just "more text"; the goal is better structure, better locators, better diagnostics, or better evidence quality.

## Non-Goals

This benchmark does not include:

- default replacement of the current conversion engine;
- a required OfficeCLI dependency;
- automatic modification of Office files;
- `create`, `add`, `set`, or `remove` OfficeCLI commands;
- AI writeback;
- cloud dependency;
- Marker integration.

The benchmark should not change conversion behavior, runner behavior, library building, search, graph behavior, Obsidian export, workspace manifests, or version registration.

## Benchmark Safety Rules

Office files must be treated as source evidence. The benchmark must be read-only.

Rules:

- Run on copied files or read-only source paths.
- Compute source `SHA-256` before each OfficeCLI command group.
- Compute source `SHA-256` after each OfficeCLI command group.
- Confirm the source checksum is unchanged.
- Only use read-only OfficeCLI commands:
  - `view`
  - `get`
  - `query`
  - `validate`
- Never use mutating commands:
  - `create`
  - `add`
  - `set`
  - `remove`
- Capture `stdout`, `stderr`, exit code, and runtime for every command.
- Keep raw command outputs as benchmark artifacts for later inspection.

If a source checksum changes at any point, the benchmark run should be marked failed and the file should be excluded from further testing until the cause is understood.

## Commands To Test

First confirm the installed OfficeCLI version:

```powershell
C:\Users\hcai\bin\officecli.exe --version
```

For each benchmark file, test:

```powershell
C:\Users\hcai\bin\officecli.exe view FILE outline
C:\Users\hcai\bin\officecli.exe view FILE text --max-lines 200
C:\Users\hcai\bin\officecli.exe view FILE html
C:\Users\hcai\bin\officecli.exe get FILE / --depth 2 --json
C:\Users\hcai\bin\officecli.exe validate FILE
C:\Users\hcai\bin\officecli.exe view FILE issues --limit 50
```

The benchmark harness should treat `FILE` as data and avoid string-built shell commands where practical. Command arguments should be passed as structured subprocess arguments in any future implementation.

## Benchmark Input Set

Use a small but representative input set:

- existing small test fixtures;
- `DOCX` files with headings and tables;
- `XLSX` files with sheets, formulas, and tabular regions;
- `PPTX` files with slides, shapes, tables, and speaker notes;
- interview or resume Office files if available locally;
- CML125 Office files if available locally.

The input set should include both simple fixtures and real-world files. Real-world files are needed to judge whether OfficeCLI improves practical conversion quality, but they should be handled carefully because they may be large or sensitive.

## Metrics

Record these metrics for each command and each file:

- success or failure;
- text completeness;
- heading preservation;
- table preservation;
- sheet locator quality;
- slide locator quality;
- JSON parseability;
- HTML preview generation;
- runtime;
- error message quality;
- checksum unchanged;
- comparison with current office2md output.

Comparison with current office2md output should focus on concrete improvements:

- new usable text not currently captured;
- better heading or table structure;
- better sheet, slide, cell, paragraph, or shape locators;
- clearer validation or issue diagnostics;
- more stable sidecar data for traceability.

## Proposed Future Architecture

Any future OfficeCLI support should be optional and layered:

1. OfficeCLI capability smoke.
2. OfficeCLI benchmark harness.
3. OfficeCLI JSON / HTML sidecar extraction.
4. Optional `--office-engine officecli` only after the benchmark passes.

The initial implementation, if approved later, should likely start with diagnostics and sidecars rather than replacing conversion. This keeps the existing conversion path stable while allowing OfficeCLI output to be inspected and compared.

## Sidecar Output Idea

If OfficeCLI proves useful, it could produce optional sidecars inside each Knowledge Pack:

```text
Knowledge Pack/
  officecli/
    outline.txt
    text.txt
    structure.json
    preview.html
    issues.txt
    validate.txt
    manifest.json
```

The `manifest.json` sidecar should record:

- OfficeCLI executable path;
- OfficeCLI version;
- command list;
- source file path;
- source SHA-256 before and after;
- command exit codes;
- runtime;
- generated sidecar files;
- warnings or errors.

Sidecars should be treated as derived diagnostic evidence. They should not overwrite source files or replace the existing Knowledge Pack schema by default.

## Decision Outcomes

The benchmark should lead to one of four decisions:

### A. Do Not Integrate

Choose this if OfficeCLI output is unreliable, hard to parse, too slow, mutates files, or does not improve quality enough to justify maintenance.

### B. Keep As Benchmark / Diagnostic Only

Choose this if OfficeCLI is useful for inspection but not stable enough for production Knowledge Pack generation.

### C. Optional OfficeCLI Sidecar Extraction

Choose this if OfficeCLI reliably adds structure, diagnostics, or previews that are useful as supplemental artifacts without changing primary conversion behavior.

### D. Optional OfficeCLI Engine For Specific Office Formats

Choose this only if OfficeCLI consistently outperforms the current path for specific Office formats and can produce stable, traceable, read-only output. This should require an explicit option such as `--office-engine officecli`; it should not become the default without a separate design and review.

## Review Gate Before Implementation

Before any code is implemented, review should confirm:

- the command set is read-only;
- checksum verification is part of the benchmark;
- benchmark artifacts are written outside source folders;
- OfficeCLI remains optional;
- no current conversion behavior changes are required;
- no mutating OfficeCLI command is included.
