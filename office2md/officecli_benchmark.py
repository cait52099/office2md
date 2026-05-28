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


@dataclass(frozen=True)
class OfficeCliCommandSpec:
    name: str
    arguments: tuple[str, ...]
    artifact: str | None
    parse_json: bool = False


def benchmark_command_specs(*, skip_html: bool = False) -> list[OfficeCliCommandSpec]:
    specs = [
        OfficeCliCommandSpec("outline", ("view", "{file}", "outline"), "outline.txt"),
        OfficeCliCommandSpec("text", ("view", "{file}", "text", "--max-lines", "200"), "text.txt"),
        OfficeCliCommandSpec("structure", ("get", "{file}", "/", "--depth", "2", "--json"), "structure.json", parse_json=True),
        OfficeCliCommandSpec("validate", ("validate", "{file}"), "validate.txt"),
        OfficeCliCommandSpec("issues", ("view", "{file}", "issues", "--limit", "50"), "issues.txt"),
    ]
    if not skip_html:
        specs.insert(2, OfficeCliCommandSpec("html", ("view", "{file}", "html"), "preview.html"))
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
    dry_run: bool = False,
) -> dict[str, Any]:
    selected_files = collect_office_files(input_path, formats=formats, include_hidden=include_hidden, max_files=max_files)
    specs = benchmark_command_specs(skip_html=skip_html)
    resolved_officecli = None if dry_run else find_officecli(officecli_path)
    version_result = None if dry_run else run_officecli_command(resolved_officecli, ["--version"], timeout_seconds=timeout_seconds)
    officecli_version = None if version_result is None else (version_result["stdout"].strip() or version_result["stderr"].strip())

    options = {
        "max_files": max_files,
        "include_hidden": include_hidden,
        "formats": list(formats),
        "timeout_seconds": timeout_seconds,
        "skip_html": skip_html,
        "dry_run": dry_run,
    }
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
    }
    if dry_run:
        summary["files"] = [_dry_run_file_record(path, input_path, specs) for path in selected_files]
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
        commands.append(result_for_record)
        if result["succeeded"] and spec.artifact is not None:
            artifact_path = file_dir / spec.artifact
            artifact_path.write_text(result["stdout"], encoding="utf-8", errors="replace")
            artifacts[spec.artifact] = str(artifact_path)
            if spec.parse_json:
                try:
                    json.loads(result["stdout"])
                    json_parse_success = True
                except json.JSONDecodeError as exc:
                    warnings.append(f"structure JSON did not parse: {exc}")
        elif not result["succeeded"]:
            errors.append(f"{spec.name} failed")

    sha_after = compute_sha256(source)
    checksum_unchanged = sha_before == sha_after
    if not checksum_unchanged:
        errors.append("critical: source checksum changed during OfficeCLI benchmark")
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
        "",
        "## Per-Format Summary",
        "",
    ]
    for extension, count in _format_counts(summary["files"]).items():
        lines.append(f"- `{extension}`: {count}")
    if not summary["files"]:
        lines.append("- No supported Office files selected.")
    lines.extend(
        [
            "",
            "## Failures",
            "",
            f"- Files failed: {counts['files_failed']}",
            f"- JSON parse successes: {counts['json_parse_success']}",
            f"- HTML generated: {counts['html_generated']}",
            "",
            "## Checksum Safety Result",
            "",
            f"- Files with changed checksum: {counts['checksum_changed']}",
            "",
            "## Recommendation Placeholder",
            "",
            "- not evaluated",
            "- diagnostic only",
            "- sidecar candidate",
            "- engine candidate",
            "",
        ]
    )
    (output_dir / "officecli_benchmark_report.md").write_text("\n".join(lines), encoding="utf-8")


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
