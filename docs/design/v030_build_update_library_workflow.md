# v0.3.0 Build / Update Library Workflow Design

Status: P4-A design committed; P4-B Scan / Dry-run, P4-C Convert / Update runner wrapper, and P4-D Build Library / Load Built Library implemented.

## Purpose

The current GUI can open and inspect an existing Knowledge Library. Users also need a guided way to start from a target folder of source files, process those files locally, build a library, and then load that library into the GUI.

The workflow has two distinct entry points:

- Open Existing Library: select an already-built `library.db` or Knowledge Library folder and inspect it with Library Overview, Search, and Graph View.
- Build / Update Library from Source Folder: select a source folder plus one output workspace, convert or update the processed outputs, build the Knowledge Library, then load the built library.

The build/update workflow should wrap existing stable office2md behavior. It must not change conversion logic, search behavior, library-report scoring, runner process-control, or library graph generation.

## Supported Source Types

Supported source paths are local filesystem paths visible to Windows:

- Local folders.
- OneDrive or Teams synced local folders.
- Network share or UNC paths if they are accessible in the current Windows session.

Out of scope for v0.3.0:

- Direct Teams API integration.
- Direct SharePoint API integration.
- Cloud sync management or file hydration management.
- Any network/cloud dependency beyond reading paths already mounted or synced by Windows.

## Output Model

The GUI should ask users for one output workspace and derive internal folders from it:

- Source folder: original files to scan and convert.
- Output workspace folder: user-facing parent folder for all generated outputs.
- Conversion output folder: `<workspace>\conversion`, containing office2md per-document outputs, manifests, chunks, and source maps.
- Library output folder: `<workspace>\library`, containing the built Knowledge Library with `library.db`, `library_index.json`, `library_graph.json`, portal Markdown, and exports.
- Logs folder: `<workspace>\logs`, containing conversion and runner logs.
- Evidence/export folder: optional later destination for reports, search exports, and validation evidence.

These folders may be local, synced, or network paths, but local folders are recommended for conversion outputs and logs. Reusing a non-empty workspace is allowed but should warn users that old conversion manifests can be included. The GUI must not delete anything automatically.

## Conservative Incremental Strategy

The first GUI implementation should use the existing scanner and `convert --skip-existing` behavior.

Expected behavior:

- New files are processed into the conversion output folder.
- Existing processed outputs with manifests are skipped.
- Failed manifests remain visible and should not be hidden.
- The library is built from the conversion output root after conversion/update.
- Existing library output can be reused only after an explicit user action and warning.

Out of scope for the first version:

- Deleting output for source files that were deleted.
- Strong modified-file synchronization unless already supported safely by existing conversion behavior.
- Automatic cleanup of old libraries or stale conversion outputs.
- Detecting every rename/replace case with perfect accuracy.

Known risks:

- Renamed source files may produce new output folders while old outputs remain.
- Modified files may be skipped if existing output detection considers them already processed.
- Failed manifests from earlier runs should remain visible until a later explicit retry/cleanup design exists.
- OneDrive placeholders or locked files can stall or fail conversion.

## GUI Page Proposal

Page name: Build / Update Library

Inputs:

- Source folder.
- Output workspace folder.
- Max files.
- Dry-run.
- Skip existing.
- Render PDF pages.
- Max render pages.
- Max text pages.
- No OCR / no AI defaults.

Buttons:

- Scan / Dry-run.
- Convert / Update.
- Build Library.
- Load Built Library.

Optional future button:

- Run Full Workflow.

The first implementation should keep buttons explicit. Users should see what step is about to run and where logs will be written.

## Execution Strategy

Two implementation approaches are possible.

Approach A: call existing Python functions directly where available.

- Pros: easier structured progress display; fewer shell quoting issues; easier to share in-process objects.
- Cons: long conversions can block the Streamlit process; process cancellation and timeout handling are harder; it bypasses the already-validated runner behavior for long jobs.

Approach B: call existing CLI commands or the PowerShell runner where safer.

- Pros: reuses the validated operational command shape; logs are naturally captured; `--skip-existing` and runner restart behavior remain unchanged; safer for long-running conversions.
- Cons: progress is mostly log-based; subprocess quoting and environment handling require care; GUI has to poll logs rather than hold direct Python objects.

Recommendation for v0.3.0 MVP:

- Use CLI/PowerShell runner for scan/dry-run and conversion/update.
- Use existing `build-library` CLI or `build_library()` only for the shorter build step after conversion output exists.
- Prefer showing the exact command and log paths before execution.

This is the safer approach because conversion is the long-running and failure-prone step, especially for OneDrive or large PDF folders.

## Long-Running Task Handling

The GUI should avoid pretending conversion is instantaneous.

Initial behavior:

- Use explicit buttons for each step.
- Show generated command text before running.
- Write logs to the selected log folder.
- Display log paths and recent log output.
- Keep failures visible.
- Avoid hiding subprocess return codes.
- Avoid launching a full workflow automatically in the first implementation.

Later improvements can add polling, progress summaries, and cancellation controls after the command/log contract is stable.

## Teams / OneDrive Considerations

The GUI should warn users when source paths appear to be OneDrive, Teams, or network paths:

- Files should be available offline before conversion.
- Cloud placeholders can stall or fail when large files hydrate on demand.
- Sync locking can temporarily block reads.
- Network paths can be slow, unavailable, or locked.
- The safest pattern is to keep conversion outputs and logs in explicit local folders.

The GUI should not attempt to manage sync state or call cloud APIs.

## Safety Rules

- Never delete source files.
- Do not auto-delete old conversion output in the first version.
- Do not overwrite an existing library output without warning.
- Prefer explicit output folders over hidden defaults.
- Keep OCR disabled by default.
- Keep AI/MiniMax disabled by default.
- Do not add embeddings/vector search.
- Do not add Office image export.
- Do not add legacy `.doc` conversion.

## Validation Plan

Minimum validation for implementation:

- Dry-run with `MaxFiles 3` against CML125.
- Convert/update a small fixture or a very small `MaxFiles` subset.
- Build library from the conversion output.
- Load the built library in the GUI.
- Run `python -m pytest`.
- Run `python -m ruff check .`.
- Run `python -m compileall office2md/gui`.

For CML125 dry-run validation, the expected runner pattern is:

```powershell
.\scripts\Invoke-Office2MdChunkedConvert.ps1 `
  -InputPath "SOURCE_PATH" `
  -OutputPath "CONVERSION_OUTPUT_FOLDER" `
  -LogDirectory "LOG_FOLDER" `
  -MaxFiles 3 `
  -DryRun
```

Then the build-library step should use:

```powershell
python -m office2md.cli build-library "CONVERSION_OUTPUT_FOLDER" "LIBRARY_OUTPUT_FOLDER"
```

## Implementation Phases

### P4-B Scan / Dry-run Panel

- Add Build / Update Library page shell.
- Add path inputs and dry-run controls.
- Use existing scanner logic to count supported files.
- Derive conversion, library, and log folders from the output workspace.
- Estimate expected unique manifest targets with the runner-style slug/checksum collision convention.
- Count existing manifests in the conversion output folder when present.
- Show supported file count, selected target count, expected manifest count, existing manifest count, completion status, command previews, and path warnings.
- Do not convert files, build a library, create folders, or invoke the PowerShell runner in P4-B.

### P4-C Convert / Update Panel

- Add explicit Convert / Update action using the existing PowerShell runner.
- Show exact command, source path, derived conversion/log paths, mode, timeout minutes, max attempts, skip-existing status, render defaults, and no OCR/no AI notes before execution.
- Require a safety confirmation checkbox before execution.
- Capture stdout, stderr, exit code, log directory, final manifest count, and failed manifest count after the runner exits.
- Keep `--skip-existing` behavior through the existing runner.
- Preserve runner process-control behavior by invoking it rather than reimplementing it.
- Do not automatically run `build-library`.
- Do not automatically load a library.

### P4-D Build Library and Load Built Library

- Add Build Library action using existing library builder behavior.
- Show exact `python -m office2md.cli build-library` command before execution.
- Use derived `<workspace>\conversion` as input and `<workspace>\library` as output.
- Require a safety confirmation checkbox before execution.
- Capture stdout, stderr, exit code, and Library Output Folder summary after completion.
- Show whether `library.db`, `library_index.json`, `library_graph.json`, `_library.md`, and `_quality_report.md` exist.
- Display document, chunk, and entity counts when `library_report()` can load the built library.
- Add Load Built Library button to set the GUI library path to the built library folder.
- Warn clearly when the selected folder does not contain `library.db`, especially if the user selected the Conversion Output Folder instead of the Library Output Folder.
- Use a pending session-state key before rerun so Load Built Library does not modify a Streamlit widget key after instantiation.
- Do not automatically run conversion.
- Do not implement one-click full workflow.

### P4-E Polish / Evidence Package Integration

- Add optional report/export generation.
- Link with the existing evidence package workflow.
- Improve progress summaries and validation output.

## Decision Recommendation

Implement P4-B first: Scan / Dry-run Panel.

Reasoning:

- It is the safest first write-adjacent GUI step.
- It validates user paths, quoting, runner availability, and OneDrive/network warnings without converting files.
- It creates the command/log display pattern needed by later Convert / Update work.
- It does not change conversion behavior or runner process-control behavior.
