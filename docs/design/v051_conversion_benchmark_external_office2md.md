# v0.5.1 External office2md Conversion Benchmark Design

Status: design only. No integration, dependency, CLI flag, conversion behavior, build-library behavior, search behavior, update-library behavior, Agent Gateway behavior, or MCP behavior is proposed for v0.5.1.

## Purpose

There is a separate PyPI package named `office2md` maintained at `github.com/rodgui/office2md`. It is not this repository. As of the PyPI metadata checked on 2026-05-29, the published package version is `0.5.6`, uploaded on 2026-05-25, and its README claims conversion support for `DOCX`, `XLSX`, `PPTX`, and optionally `PDF`.

The goal of this benchmark is diagnostic comparison only:

- learn whether any conversion-layer ideas are worth reproducing locally later;
- compare external Markdown output as an artifact, not as trusted project output;
- protect office2md provenance, locators, Knowledge Pack contracts, and dependency safety;
- avoid changing the current conversion pipeline while the evidence is still exploratory.

## Non-Goals

This design does not include:

- adding the external `office2md` package to `pyproject.toml`;
- installing the external package into this project's virtual environment;
- importing external package code from this repository;
- changing current conversion behavior;
- changing build-library behavior;
- changing search, ranking, alias, token fallback, or locator behavior;
- changing update-library behavior;
- changing Agent Gateway or MCP behavior;
- adding AI, OCR, embedding, vector, or cloud work;
- adding unrestricted SQL;
- adding shell execution through agent interfaces;
- creating `--office-engine external-office2md`;
- committing or tagging before review.

## External Claims To Evaluate

The external package README and PyPI metadata claim these relevant behaviors:

- DOCX conversion with converter selection: Pandoc, Mammoth, then `python-docx`;
- DOCX normalization that promotes auto-numbered section-like list items into real headings before Pandoc conversion;
- Pandoc Markdown variant control, including GFM and classic output modes;
- XLSX conversion with all-sheets or first-sheet modes;
- PPTX conversion with optional speaker-note handling;
- optional PDF conversion through Docling;
- visual QA reports with rendered comparisons;
- mirror/idempotent conversion for wiki or knowledge-base work;
- local-only privacy flags that set offline/telemetry-related environment variables;
- standalone wiki builder modes.

These claims are inputs to a benchmark plan. They are not accepted as product requirements for this repository.

## Idea Classification

| Idea | Classification | Reasoning | Allowed v0.5.1 action |
| --- | --- | --- | --- |
| Local-only/privacy flags | Borrow now | The safety concept matches this project's local/private evidence posture. It can be borrowed immediately as benchmark policy: run in a temp workspace, avoid cloud dependencies, set best-effort offline telemetry flags where available, and document that this is not an OS firewall. | Document and require for benchmark runs. No product flag change. |
| DOCX converter selection: Pandoc / Mammoth / `python-docx` | Benchmark only | Converter fallback may improve text, images, or tables, but this repository cares about provenance and stable Knowledge Pack evidence. Faster or prettier Markdown is not enough if locators and source-map quality regress. | Compare external outputs against current outputs as artifacts only. |
| DOCX auto-numbered list normalization into real headings | Benchmark only | This is the most promising conversion-layer idea because this repo has known generic DOCX raw-markdown locator and heading-quality limits. It must be tested on real SOP-like files before any local implementation is considered. | Measure heading count, heading hierarchy quality, and source checksum safety. |
| Markdown variant control: GFM/classic | Defer | Variant control may be useful for downstream consumers, but this project's output is tied to Knowledge Pack generation and existing chunking assumptions. Changing Markdown flavor could alter chunk boundaries and table parsing. | Record which variant produced each benchmark artifact. Do not add a product option yet. |
| Visual QA / rendered diff concept | Benchmark only | Rendered diffs could reveal conversion regressions that text metrics miss. They are potentially useful as optional diagnostic artifacts, but they should not gate normal conversion or require visual dependencies. | Include only as optional benchmark output when dependencies are already available in the isolated venv. |
| Mirror/idempotent conversion | Do not use | This repository already has workspace scan, source manifests, checksums, update-library planning, and Knowledge Pack output conventions. Borrowing an external mirror mode risks confusing two separate lifecycle models. | Do not integrate or model product behavior on it. At most, note whether the external benchmark skipped files. |
| PDF local ML/OCR path | Do not use | The current task explicitly excludes AI/OCR/cloud work. Optional PDFs can be smoke-tested only if required local dependencies already exist in the isolated benchmark venv, but no new OCR work should be designed. | Exclude by default. Optional smoke only, diagnostic-only. |
| Standalone wiki builder | Do not use | This project already has its own library, RAM, agent, and Obsidian/wiki-adjacent designs. External wiki building does not answer conversion provenance questions. | Do not benchmark unless a future separate wiki comparison is approved. |

## Safe Benchmark Approach

Any future benchmark scaffold must be isolated from the project environment and from source documents.

Required safety rules:

- Create a temporary benchmark root under the OS temp directory, for example `%TEMP%\office2md_external_benchmark_<timestamp>`.
- Create a temporary virtual environment inside that benchmark root.
- Install the external `office2md` package only into that temporary virtual environment.
- Never install the external package into this repository's virtual environment.
- Never add the external package to `pyproject.toml`, optional dependencies, requirements files, or project lock files.
- Run external commands with the benchmark root as the working directory, not the repository root, to avoid import-name collisions with this repository's `office2md` package.
- Copy selected input files into a temp `inputs\` folder before conversion.
- Compute SHA-256 for the original source before copy.
- Compute SHA-256 for the original source again after the external run.
- Compute SHA-256 for the copied benchmark input before and after conversion.
- Write external outputs only under a temp `outputs\external_office2md\` folder.
- Write current-project comparison outputs, if needed, only under a separate temp `outputs\current_office2md\` folder.
- Compare outputs as artifacts only; do not feed them into the main conversion pipeline.
- Preserve raw `stdout`, `stderr`, exit code, elapsed time, selected package version, command arguments, and environment flags in a benchmark manifest.
- Delete or archive the temp benchmark folder only after review; never move benchmark artifacts into a Knowledge Pack automatically.

Suggested environment guards for the benchmark process:

```powershell
$env:PYTHONNOUSERSITE = "1"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
$env:HF_DATASETS_OFFLINE = "1"
$env:HF_HUB_DISABLE_TELEMETRY = "1"
$env:DO_NOT_TRACK = "1"
```

These flags are best-effort privacy guards. They are not a substitute for running sensitive files in a network-blocked VM or container.

## Benchmark Flow

1. Select the real-file smoke set.
2. Create a temp benchmark root and temp venv outside the repository.
3. Install a pinned external package version into the temp venv.
4. Copy source files into the temp input folder.
5. Record original and copied-input SHA-256 values.
6. Run the current office2md conversion into temp comparison output, only if comparison artifacts are needed.
7. Run the external `office2md` conversion into temp external output.
8. Record command metadata and output artifacts.
9. Recompute original and copied-input SHA-256 values.
10. Mark the benchmark failed for any file whose source checksum changes.
11. Compare artifact metrics without changing any repository output.
12. Produce a short report with recommendation: diagnostic-only, local helper candidate, or do-not-use.

The benchmark runner, if implemented later, should pass arguments as structured subprocess lists. It should not build command strings, expose shell execution through an agent interface, or accept unrestricted user-provided shell fragments.

## Metrics

Record per file, per converter mode where applicable:

- success/failure;
- exit code and error category;
- elapsed time in seconds;
- output Markdown size in bytes;
- extracted image count;
- heading count;
- approximate heading-depth distribution;
- table marker count, such as Markdown table separator lines or HTML table tags;
- locator/page/sheet/slide evidence availability;
- current-project locator coverage for the same source, when current output is included;
- source SHA-256 before and after;
- copied-input SHA-256 before and after;
- output artifact SHA-256;
- whether the output can be safely adapted into a Knowledge Pack later;
- whether adaptation would require invented provenance;
- whether external output includes enough stable structure to map back to source file, page, sheet, slide, paragraph, table, or image evidence.

The benchmark should treat missing provenance as a quality failure even when the Markdown is readable.

## Recommended Real-File Smoke Set

Use copied files only. The original paths are never written to by the benchmark.

Required smoke inputs:

- 3 `DOCX` files with numbered sections or SOP-like content, preferably documents where heading styles are weak or auto-numbered list structure is common.
- 3 `PPTX` files from `C:\Users\hcai\Desktop\test`.
- 3 `XLSX` files with multiple sheets and multiple tables.

Optional smoke inputs:

- 3 `PDF` files only if the required local PDF dependencies are already available in the isolated benchmark environment.

PDFs should be skipped by default for this task because the current review excludes new AI/OCR work.

## Artifact Layout

A future isolated benchmark can write this temp-only layout:

```text
%TEMP%/office2md_external_benchmark_<timestamp>/
  venv/
  inputs/
    docx/
    pptx/
    xlsx/
    pdf/
  outputs/
    external_office2md/
    current_office2md/
  reports/
    manifest.json
    metrics.csv
    summary.md
    visual_qa/
```

The manifest should include:

- benchmark timestamp;
- Python executable path for the temp venv;
- external package name and version;
- external package source URL;
- whether Pandoc, LibreOffice, Docling, or visual dependencies were available;
- environment flags used;
- copied input path;
- original source path;
- original source SHA-256 before and after;
- copied input SHA-256 before and after;
- commands run;
- exit code, elapsed time, stdout path, stderr path;
- generated Markdown path;
- generated image paths;
- metric values;
- recommendation for each file.

## Decision Rules

- If external output is faster but loses locator/provenance, keep diagnostic-only.
- If DOCX normalization significantly improves heading quality and can be reproduced locally without dependency conflict, consider implementing this repository's own small normalization helper later.
- If visual QA is useful, consider adding it as an optional benchmark artifact only.
- Do not integrate the external package unless a future review proves provenance compatibility and dependency safety.
- Do not add `--office-engine external-office2md`.
- Do not adapt external Markdown into a Knowledge Pack unless the adapter can preserve or explicitly mark source provenance without inventing locators.

## Review Gate Before Any Implementation

Before implementing even an isolated benchmark scaffold, review should confirm:

- the external package version to test;
- where the temp benchmark root will be created;
- that the project venv is not active for external installation;
- that `pyproject.toml` and dependency metadata remain unchanged;
- that the selected files are safe to copy into a temp local folder;
- that source checksum before/after checks are mandatory;
- that artifact comparison will not alter source files, conversion output, Knowledge Packs, library databases, search indexes, update plans, Agent Gateway output, or MCP tools.

## Recommended Next Task

Implement no integration now. The next useful task is a review-only pass over this design note. If approved, a later task can add a standalone benchmark script under a clearly diagnostic path, with tests proving it writes only to a temp folder and never imports or depends on the external package at project runtime.
