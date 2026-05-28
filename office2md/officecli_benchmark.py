import hashlib
import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from slugify import slugify

from office2md import __version__
from office2md.utils import ensure_directory, utc_now_iso


SCHEMA_VERSION = "1"
DEFAULT_FORMATS = ("docx", "xlsx", "pptx")
FORBIDDEN_COMMAND_TOKENS = {"create", "add", "set", "remove", "open", "close"}
TEXT_ARTIFACTS = {"outline.txt", "text.txt", "validate.txt", "issues.txt"}


@dataclass(frozen=True)
class OfficeCliCommandSpec:
    name: str
    arguments: tuple[str, ...]
    artifact: str | None
    parse_json: bool = False


def benchmark_command_specs(
    *,
    skip_html: bool = False,
    skip_structure_json: bool = False,
    skip_validate: bool = False,
    skip_issues: bool = False,
) -> list[OfficeCliCommandSpec]:
    specs = [
        OfficeCliCommandSpec("outline", ("view", "{file}", "outline"), "outline.txt"),
        OfficeCliCommandSpec("text", ("view", "{file}", "text", "--max-lines", "200"), "text.txt"),
    ]
    if not skip_html:
        specs.append(OfficeCliCommandSpec("html", ("view", "{file}", "html"), "preview.html"))
    if not skip_structure_json:
        specs.append(OfficeCliCommandSpec("structure", ("get", "{file}", "/", "--depth", "2", "--json"), "structure.json", parse_json=True))
    if not skip_validate:
        specs.append(OfficeCliCommandSpec("validate", ("validate", "{file}"), "validate.txt"))
    if not skip_issues:
        specs.append(OfficeCliCommandSpec("issues", ("view", "{file}", "issues", "--limit", "50"), "issues.txt"))
    _assert_no_mutating_commands(specs)
    return specs


def find_officecli(officecli_path: Path | None = None) -> Path:
    if officecli_path is not None:
        candidate = officecli_path.expanduser()
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
        raise FileNotFoundError(f"OfficeCLI executable was not found: {candidate}")
    found = shutil.which("officecli")
    if found:
        return Path(found).resolve()
    raise FileNotFoundError("OfficeCLI executable was not found. Pass --officecli-path or add officecli to PATH.")


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def collect_office_files(
    input_path: Path,
    *,
    formats: tuple[str, ...] = DEFAULT_FORMATS,
    include_hidden: bool = False,
    max_files: int | None = None,
) -> list[Path]:
    source = input_path.expanduser()
    if not source.exists():
        raise FileNotFoundError(f"Input path does not exist: {source}")
    allowed = {f".{item.lower().lstrip('.')}" for item in formats}
    if source.is_file():
        files = [source] if _is_supported_office_file(source, allowed, include_hidden=include_hidden) else []
    else:
        files = [
            item
            for item in sorted(source.rglob("*"), key=lambda path: str(path).lower())
            if item.is_file() and _is_supported_office_file(item, allowed, include_hidden=include_hidden)
        ]
    if max_files is not None:
        files = files[: max(0, max_files)]
    return [item.resolve() for item in files]


def safe_file_id(path: Path) -> str:
    resolved = path.expanduser().resolve()
    digest = hashlib.sha256(str(resolved).encode("utf-8", errors="replace")).hexdigest()[:12]
    stem = slugify(resolved.stem, lowercase=False) or "office-file"
    suffix = resolved.suffix.lower().lstrip(".") or "file"
    return f"{stem}-{suffix}-{digest}"


def run_officecli_command(
    officecli_path: Path,
    arguments: list[str],
    *,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    started = time.perf_counter()
    command = [str(officecli_path), *arguments]
    try:
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            shell=False,
            errors="replace",
        )
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        exit_code = None
        stdout = _decode_timeout_output(exc.stdout)
        stderr = _decode_timeout_output(exc.stderr) or f"Command timed out after {timeout_seconds} seconds."
        timed_out = True
    runtime = time.perf_counter() - started
    return {
        "command": command,
        "exit_code": exit_code,
        "runtime_seconds": round(runtime, 6),
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
        "succeeded": exit_code == 0 and not timed_out,
    }


def run_officecli_benchmark(
    input_path: Path,
    output_dir: Path,
    *,
    officecli_path: Path | None = None,
    max_files: int | None = None,
    include_hidden: bool = False,
    formats: tuple[str, ...] = DEFAULT_FORMATS,
    timeout_seconds: int = 60,
    skip_html: bool = False,
    skip_structure_json: bool = False,
    skip_validate: bool = False,
    skip_issues: bool = False,
    large_file_size_mb: int | None = 25,
    dry_run: bool = False,
) -> dict[str, Any]:
    selected_files = collect_office_files(input_path, formats=formats, include_hidden=include_hidden, max_files=max_files)
    specs = benchmark_command_specs(
        skip_html=skip_html,
        skip_structure_json=skip_structure_json,
        skip_validate=skip_validate,
        skip_issues=skip_issues,
    )
    resolved_officecli = None if dry_run else find_officecli(officecli_path)
    version_result = None if dry_run else run_officecli_command(resolved_officecli, ["--version"], timeout_seconds=timeout_seconds)
    officecli_version = None if version_result is None else (version_result["stdout"].strip() or version_result["stderr"].strip())

    options = {
        "max_files": max_files,
        "include_hidden": include_hidden,
        "formats": list(formats),
        "timeout_seconds": timeout_seconds,
        "skip_html": skip_html,
        "skip_structure_json": skip_structure_json,
        "skip_validate": skip_validate,
        "skip_issues": skip_issues,
        "large_file_size_mb": large_file_size_mb,
        "dry_run": dry_run,
    }
    skipped_commands = _skipped_commands(
        skip_html=skip_html,
        skip_structure_json=skip_structure_json,
        skip_validate=skip_validate,
        skip_issues=skip_issues,
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now_iso(),
        "office2md_version": __version__,
        "officecli_path": str(resolved_officecli or officecli_path or "officecli"),
        "officecli_version": officecli_version,
        "input_path": str(input_path.expanduser().resolve()),
        "output_dir": str(output_dir.expanduser().resolve()),
        "options": options,
        "counts": {
            "files_selected": len(selected_files),
            "files_succeeded": 0,
            "files_failed": 0,
            "checksum_changed": 0,
            "json_parse_success": 0,
            "html_generated": 0,
        },
        "files": [],
        "warnings": [],
        "errors": [],
        "dry_run": dry_run,
        "planned_commands": [_planned_command(spec) for spec in specs],
        "skipped_commands": skipped_commands,
        "timeout_summary": [],
        "suggested_rerun_options": [],
        "large_file_warnings": _large_file_warnings(selected_files, large_file_size_mb),
    }
    if dry_run:
        summary["files"] = [_dry_run_file_record(path, input_path, specs) for path in selected_files]
        _finalize_diagnostics(summary)
        summary["recommendation"], summary["recommendation_reasons"] = recommend_benchmark(summary)
        return summary

    ensure_directory(output_dir)
    files_dir = output_dir / "files"
    ensure_directory(files_dir)
    for file_path in selected_files:
        record = _run_file_benchmark(file_path, input_path, files_dir, resolved_officecli, specs, timeout_seconds=timeout_seconds)
        summary["files"].append(record)
        if record["checksum_unchanged"] is False:
            summary["counts"]["checksum_changed"] += 1
        if record["errors"]:
            summary["counts"]["files_failed"] += 1
        else:
            summary["counts"]["files_succeeded"] += 1
        if record.get("json_parse_success"):
            summary["counts"]["json_parse_success"] += 1
        if "preview.html" in record["artifacts"]:
            summary["counts"]["html_generated"] += 1
    _finalize_diagnostics(summary)
    summary["recommendation"], summary["recommendation_reasons"] = recommend_benchmark(summary)
    _write_summary(output_dir, summary)
    _write_report(output_dir, summary)
    return summary


def write_benchmark_artifacts(output_dir: Path, summary: dict[str, Any]) -> None:
    ensure_directory(output_dir)
    _write_summary(output_dir, summary)
    _write_report(output_dir, summary)


def _run_file_benchmark(
    file_path: Path,
    input_path: Path,
    files_dir: Path,
    officecli_path: Path,
    specs: list[OfficeCliCommandSpec],
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    source = file_path.resolve()
    file_dir = files_dir / safe_file_id(source)
    ensure_directory(file_dir)
    sha_before = compute_sha256(source)
    commands = []
    artifacts: dict[str, str] = {}
    warnings: list[str] = []
    errors: list[str] = []
    json_parse_success = False

    for spec in specs:
        arguments = [str(source) if item == "{file}" else item for item in spec.arguments]
        result = run_officecli_command(officecli_path, arguments, timeout_seconds=timeout_seconds)
        result_for_record = _command_result_for_record(spec.name, result)
        if result["succeeded"] and spec.artifact is not None:
            artifact_path = file_dir / spec.artifact
            artifact_path.write_text(result["stdout"], encoding="utf-8", errors="replace")
            artifacts[spec.artifact] = str(artifact_path)
            result_for_record["artifact_path"] = str(artifact_path)
            if spec.parse_json:
                try:
                    json.loads(result["stdout"])
                    json_parse_success = True
                except json.JSONDecodeError as exc:
                    warnings.append(f"structure JSON did not parse: {exc}")
        elif not result["succeeded"]:
            errors.append(f"{spec.name} failed")
        commands.append(result_for_record)

    sha_after = compute_sha256(source)
    checksum_unchanged = sha_before == sha_after
    if not checksum_unchanged:
        errors.append("critical: source checksum changed during OfficeCLI benchmark")
    failed_commands = [command["name"] for command in commands if not command["succeeded"]]
    timed_out_commands = [command["name"] for command in commands if command["timed_out"]]
    html_generated = "preview.html" in artifacts
    failure_category = classify_file_failure(
        checksum_unchanged=checksum_unchanged,
        failed_commands=failed_commands,
        timed_out_commands=timed_out_commands,
        json_parse_success=json_parse_success,
        html_generated=html_generated,
        skip_html=not any(spec.name == "html" for spec in specs),
        skip_structure_json=not any(spec.name == "structure" for spec in specs),
        selected=True,
    )
    record = {
        "source_path": str(source),
        "relative_path": _relative_path(source, input_path),
        "extension": source.suffix.lower(),
        "size_bytes": source.stat().st_size,
        "sha256_before": sha_before,
        "sha256_after": sha_after,
        "checksum_unchanged": checksum_unchanged,
        "commands": commands,
        "artifacts": artifacts,
        "warnings": warnings,
        "errors": errors,
        "json_parse_success": json_parse_success,
        "html_generated": html_generated,
        "failed_commands": failed_commands,
        "timed_out_commands": timed_out_commands,
        "failure_category": failure_category,
    }
    (file_dir / "metadata.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    (file_dir / "command_results.json").write_text(json.dumps(commands, ensure_ascii=False, indent=2), encoding="utf-8")
    artifacts["metadata.json"] = str(file_dir / "metadata.json")
    artifacts["command_results.json"] = str(file_dir / "command_results.json")
    return record


def _write_summary(output_dir: Path, summary: dict[str, Any]) -> None:
    (output_dir / "officecli_benchmark_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_report(output_dir: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    recommendation = summary.get("recommendation") or "not_evaluated"
    recommendation_reasons = summary.get("recommendation_reasons") or []
    lines = [
        "# OfficeCLI Benchmark Report",
        "",
        "## Benchmark Overview",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Input path: `{summary['input_path']}`",
        f"- Output dir: `{summary['output_dir']}`",
        f"- OfficeCLI path: `{summary['officecli_path']}`",
        f"- OfficeCLI version: `{summary.get('officecli_version') or 'unknown'}`",
        f"- Selected files: {counts['files_selected']}",
        f"- Recommendation: `{recommendation}`",
        f"- Per-command timeout seconds: {summary.get('options', {}).get('timeout_seconds')}",
        "",
        "## Option Summary",
        "",
        f"- Skipped commands: {', '.join(summary.get('skipped_commands') or []) or 'None'}",
        f"- Large-file warning threshold: {summary.get('options', {}).get('large_file_size_mb')} MB",
        "",
        "## Per-Format Summary",
        "",
        "| Format | Files | Succeeded | Failed | JSON parsed | HTML generated | Checksum changed |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for extension, row in _format_summary(summary["files"]).items():
        lines.append(
            f"| `{extension}` | {row['files']} | {row['succeeded']} | {row['failed']} | "
            f"{row['json_parse_success']} | {row['html_generated']} | {row['checksum_changed']} |"
        )
    if not summary["files"]:
        lines.append("| none | 0 | 0 | 0 | 0 | 0 | 0 |")
    lines.extend(
        [
            "",
            "## Per-File Results",
            "",
            "| File | Format | Size bytes | Status | Failure category | Failed commands | Timed out commands | JSON parsed | HTML generated | Checksum unchanged |",
            "|---|---|---:|---|---|---|---|---|---|---|",
        ]
    )
    for item in summary["files"]:
        status = "failed" if item.get("errors") else "succeeded"
        lines.append(
            f"| `{_md_escape(item.get('relative_path') or item.get('source_path') or '')}` | `{item.get('extension') or ''}` | "
            f"{item.get('size_bytes') or 0} | "
            f"{status} | `{item.get('failure_category') or 'none'}` | "
            f"{', '.join(item.get('failed_commands') or []) or '-'} | "
            f"{', '.join(item.get('timed_out_commands') or []) or '-'} | "
            f"{bool(item.get('json_parse_success'))} | {bool(item.get('html_generated'))} | {bool(item.get('checksum_unchanged'))} |"
        )
    lines.extend(
        [
            "",
            "## Per-Command Results",
            "",
            "| File | Command | Exit code | Timed out | Succeeded | Runtime seconds | Artifact |",
            "|---|---|---:|---|---|---:|---|",
        ]
    )
    for item in summary["files"]:
        file_label = _md_escape(item.get("relative_path") or item.get("source_path") or "")
        for command in item.get("commands") or []:
            exit_code = command.get("exit_code")
            lines.append(
                f"| `{file_label}` | `{command.get('name')}` | {exit_code if exit_code is not None else ''} | "
                f"{bool(command.get('timed_out'))} | {bool(command.get('succeeded'))} | "
                f"{command.get('runtime_seconds') or 0} | `{_md_escape(command.get('artifact_path') or '')}` |"
            )
    lines.extend(
        [
            "",
            "## Failed Files",
            "",
            f"- Files failed: {counts['files_failed']}",
            "",
        ]
    )
    failed_files = [item for item in summary["files"] if item.get("errors")]
    if not failed_files:
        lines.append("No failed files recorded.")
    for item in failed_files:
        lines.extend(_failed_file_report_lines(item))
    lines.extend(
        [
            "",
            "## Command Timeout Summary",
            "",
        ]
    )
    timeout_summary = summary.get("timeout_summary") or []
    if not timeout_summary:
        lines.append("No command timeouts recorded.")
    else:
        lines.extend(
            [
                "| Command | Timeouts | Affected files |",
                "|---|---:|---|",
            ]
        )
        for item in timeout_summary:
            affected = ", ".join(f"`{_md_escape(path)}`" for path in item.get("affected_files", []))
            lines.append(f"| `{item.get('command')}` | {item.get('timeouts')} | {affected} |")
    lines.extend(
        [
            "",
            "## Timeout Rerun Suggestions",
            "",
        ]
    )
    suggestions = summary.get("suggested_rerun_options") or []
    if not suggestions:
        lines.append("No timeout-focused rerun suggestions.")
    for suggestion in suggestions:
        lines.append(f"- `{suggestion}`")
    lines.extend(
        [
            "",
            "## Expensive Command Hints",
            "",
            "- HTML preview may be slow for large Office files.",
            "- Structure JSON may be slow for complex workbooks or presentations.",
            "- For timeout-heavy folders, benchmark smaller batches with lower `--max-files`.",
            "",
            "## Large File Warnings",
            "",
        ]
    )
    large_warnings = summary.get("large_file_warnings") or []
    if not large_warnings:
        lines.append("No large-file warnings recorded.")
    for warning in large_warnings:
        lines.append(f"- `{_md_escape(warning.get('relative_path') or warning.get('source_path') or '')}`: {warning.get('size_mb')} MB")
    lines.extend(
        [
            "",
            "## JSON Parseability",
            "",
            f"- JSON parse successes: {counts['json_parse_success']} / {counts['files_selected']}",
            "",
            "## HTML Generation",
            "",
            f"- HTML generated: {counts['html_generated']} / {counts['files_selected']}",
            "",
            "## Checksum Safety Result",
            "",
            f"- Files with changed checksum: {counts['checksum_changed']}",
            f"- All source checksums unchanged: {counts['checksum_changed'] == 0}",
            "",
            "## Recommendation",
            "",
            f"`{recommendation}`",
            "",
        ]
    )
    for reason in recommendation_reasons:
        lines.append(f"- {reason}")
    (output_dir / "officecli_benchmark_report.md").write_text("\n".join(lines), encoding="utf-8")


def classify_file_failure(
    *,
    checksum_unchanged: bool | None,
    failed_commands: list[str],
    timed_out_commands: list[str],
    json_parse_success: bool,
    html_generated: bool,
    skip_html: bool,
    skip_structure_json: bool = False,
    selected: bool,
) -> str | None:
    if not selected:
        return "unsupported_file"
    if checksum_unchanged is False:
        return "checksum_changed"
    if timed_out_commands:
        return "command_timeout"
    if failed_commands:
        return "command_failed"
    if not skip_structure_json and not json_parse_success:
        return "json_parse_failed"
    if not skip_html and not html_generated:
        return "html_not_generated"
    return None


def recommend_benchmark(summary: dict[str, Any]) -> tuple[str, list[str]]:
    if summary.get("dry_run"):
        return "not_evaluated", ["Dry-run did not execute OfficeCLI commands."]
    counts = summary.get("counts") or {}
    files = summary.get("files") or []
    selected = int(counts.get("files_selected") or 0)
    if selected == 0:
        return "not_evaluated", ["No Office files were processed."]
    if int(counts.get("checksum_changed") or 0) > 0:
        return "diagnostic_only", ["At least one source checksum changed; do not use for sidecar or engine work."]
    failed = int(counts.get("files_failed") or 0)
    if failed:
        reasons = [f"{failed} file(s) had command failures or timeouts."]
        reasons.extend(f"Consider rerun option: {item}" for item in summary.get("suggested_rerun_options", [])[:4])
        return "diagnostic_only", reasons
    json_success = int(counts.get("json_parse_success") or 0)
    html_generated = int(counts.get("html_generated") or 0)
    text_like = sum(1 for item in files if _has_text_artifact(item))
    if json_success == selected and html_generated == selected and text_like == selected:
        return "engine_candidate", ["All files succeeded with JSON, HTML, and text-like artifacts."]
    if json_success >= max(1, selected * 2 // 3) and (html_generated > 0 or text_like > 0):
        return "sidecar_candidate", ["Most files produced parseable JSON and usable artifacts with unchanged checksums."]
    return "diagnostic_only", ["Read-only commands completed without checksum changes, but artifact coverage is limited."]


def _finalize_diagnostics(summary: dict[str, Any]) -> None:
    summary["timeout_summary"] = _timeout_summary(summary.get("files") or [])
    summary["suggested_rerun_options"] = _suggested_rerun_options(summary)


def _timeout_summary(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_command: dict[str, set[str]] = {}
    for item in files:
        file_label = item.get("relative_path") or item.get("source_path") or ""
        for command in item.get("commands") or []:
            if command.get("timed_out"):
                by_command.setdefault(str(command.get("name") or "unknown"), set()).add(file_label)
    return [
        {"command": command, "timeouts": len(paths), "affected_files": sorted(paths)}
        for command, paths in sorted(by_command.items())
    ]


def _suggested_rerun_options(summary: dict[str, Any]) -> list[str]:
    if not summary.get("timeout_summary"):
        return []
    suggestions = ["--max-files 1", "--timeout-seconds 120"]
    timed_out_commands = {item.get("command") for item in summary["timeout_summary"]}
    skipped = set(summary.get("skipped_commands") or [])
    if "html" in timed_out_commands and "html" not in skipped:
        suggestions.insert(0, "--skip-html")
    if "structure" in timed_out_commands and "structure" not in skipped:
        suggestions.insert(0, "--skip-structure-json")
    if "issues" in timed_out_commands and "issues" not in skipped:
        suggestions.append("--skip-issues")
    if "validate" in timed_out_commands and "validate" not in skipped:
        suggestions.append("--skip-validate")
    suggestions.append("benchmark smaller batches")
    return _dedupe(suggestions)


def _skipped_commands(*, skip_html: bool, skip_structure_json: bool, skip_validate: bool, skip_issues: bool) -> list[str]:
    skipped = []
    if skip_html:
        skipped.append("html")
    if skip_structure_json:
        skipped.append("structure")
    if skip_validate:
        skipped.append("validate")
    if skip_issues:
        skipped.append("issues")
    return skipped


def _large_file_warnings(files: list[Path], threshold_mb: int | None) -> list[dict[str, Any]]:
    if threshold_mb is None or threshold_mb <= 0:
        return []
    threshold_bytes = threshold_mb * 1024 * 1024
    warnings = []
    for path in files:
        size = path.stat().st_size
        if size >= threshold_bytes:
            warnings.append(
                {
                    "source_path": str(path),
                    "relative_path": path.name,
                    "size_bytes": size,
                    "size_mb": round(size / (1024 * 1024), 3),
                    "threshold_mb": threshold_mb,
                }
            )
    return warnings


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _failed_file_report_lines(item: dict[str, Any]) -> list[str]:
    lines = [
        "",
        f"### `{_md_escape(item.get('relative_path') or item.get('source_path') or '')}`",
        "",
        f"- Failure category: `{item.get('failure_category') or 'unknown'}`",
        f"- Errors: {'; '.join(item.get('errors') or [])}",
        "",
        "| Command | Exit code | Timed out | Stderr excerpt | Stdout excerpt | Artifact |",
        "|---|---:|---|---|---|---|",
    ]
    artifacts = item.get("artifacts") or {}
    for command in item.get("commands") or []:
        if command.get("succeeded"):
            continue
        artifact_path = command.get("artifact_path") or _artifact_for_command(command.get("name"), artifacts)
        exit_code = command.get("exit_code")
        lines.append(
            f"| `{command.get('name')}` | {exit_code if exit_code is not None else ''} | {bool(command.get('timed_out'))} | "
            f"{_excerpt(command.get('stderr') or '')} | {_excerpt(command.get('stdout') or '')} | `{_md_escape(artifact_path or '')}` |"
        )
    return lines


def _format_summary(files: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    for item in files:
        extension = item.get("extension") or "(none)"
        row = summary.setdefault(
            extension,
            {"files": 0, "succeeded": 0, "failed": 0, "json_parse_success": 0, "html_generated": 0, "checksum_changed": 0},
        )
        row["files"] += 1
        if item.get("errors"):
            row["failed"] += 1
        else:
            row["succeeded"] += 1
        if item.get("json_parse_success"):
            row["json_parse_success"] += 1
        if item.get("html_generated"):
            row["html_generated"] += 1
        if item.get("checksum_unchanged") is False:
            row["checksum_changed"] += 1
    return dict(sorted(summary.items()))


def _has_text_artifact(item: dict[str, Any]) -> bool:
    artifacts = item.get("artifacts") or {}
    return any(name in artifacts for name in TEXT_ARTIFACTS)


def _artifact_for_command(name: str | None, artifacts: dict[str, str]) -> str:
    mapping = {
        "outline": "outline.txt",
        "text": "text.txt",
        "html": "preview.html",
        "structure": "structure.json",
        "validate": "validate.txt",
        "issues": "issues.txt",
    }
    artifact_name = mapping.get(str(name or ""))
    return artifacts.get(artifact_name, "") if artifact_name else ""


def _excerpt(value: str, limit: int = 120) -> str:
    text = " ".join(str(value or "").split())
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return _md_escape(text)


def _md_escape(value: str) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def _is_supported_office_file(path: Path, allowed: set[str], *, include_hidden: bool) -> bool:
    if path.name.startswith("~$"):
        return False
    if path.suffix.lower() not in allowed:
        return False
    if not include_hidden and any(part.startswith(".") for part in path.parts):
        return False
    return True


def _assert_no_mutating_commands(specs: list[OfficeCliCommandSpec]) -> None:
    for spec in specs:
        tokens = {item.lower() for item in spec.arguments if item != "{file}"}
        forbidden = sorted(tokens & FORBIDDEN_COMMAND_TOKENS)
        if forbidden:
            raise ValueError(f"Forbidden OfficeCLI command token in benchmark plan: {forbidden}")


def _planned_command(spec: OfficeCliCommandSpec) -> list[str]:
    return list(spec.arguments)


def _dry_run_file_record(path: Path, input_path: Path, specs: list[OfficeCliCommandSpec]) -> dict[str, Any]:
    source = path.resolve()
    return {
        "source_path": str(source),
        "relative_path": _relative_path(source, input_path),
        "extension": source.suffix.lower(),
        "size_bytes": source.stat().st_size,
        "sha256_before": None,
        "sha256_after": None,
        "checksum_unchanged": None,
        "commands": [{"name": spec.name, "planned_arguments": list(spec.arguments), "artifact": spec.artifact} for spec in specs],
        "artifacts": {},
        "warnings": ["dry-run only: OfficeCLI was not executed"],
        "errors": [],
        "json_parse_success": False,
        "html_generated": False,
        "failed_commands": [],
        "timed_out_commands": [],
        "failure_category": None,
    }


def _command_result_for_record(name: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "command": result["command"],
        "exit_code": result["exit_code"],
        "runtime_seconds": result["runtime_seconds"],
        "timed_out": result["timed_out"],
        "succeeded": result["succeeded"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "artifact_path": None,
    }


def _relative_path(path: Path, input_path: Path) -> str:
    base = input_path.expanduser().resolve()
    try:
        if base.is_file():
            return path.name
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.name


def _format_counts(files: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in files:
        extension = item.get("extension") or "(none)"
        counts[extension] = counts.get(extension, 0) + 1
    return dict(sorted(counts.items()))


def _decode_timeout_output(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
