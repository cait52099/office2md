import json
import gc
import shutil
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from office2md.detector import sha256_file
from office2md.incremental import (
    default_change_plan_path,
    default_library_state_path,
    default_source_registry_path,
    save_library_state,
    save_source_registry,
    scan_changes,
)
from office2md.library import build_library
from office2md.models import ConvertOptions, ConvertResult
from office2md.storage.index import rebuild_output_index
from office2md.storage.manifest import build_manifest
from office2md.storage.writer import write_document_output
from office2md.utils import utc_now_iso


UPDATE_RESULT_SCHEMA_VERSION = "office2md.update_result.v1"


ConvertCallback = Callable[[Path, Path, ConvertOptions], tuple[Path, str]]


def update_library(
    source_path: Path,
    conversion_output: Path,
    library_path: Path,
    *,
    convert_file: ConvertCallback,
    dry_run: bool = False,
    change_plan_path: Path | None = None,
    export_plan_path: Path | None = None,
    update_result_path: Path | None = None,
    review_report_path: Path | None = None,
    include_hidden: bool = False,
    options: ConvertOptions | None = None,
) -> dict[str, Any]:
    source_root = source_path.expanduser().resolve()
    output_root = conversion_output.expanduser().resolve()
    library_dir = _library_dir(library_path)
    convert_options = options or ConvertOptions()

    plan = _load_or_scan_plan(
        source_root,
        library_dir,
        change_plan_path=change_plan_path,
        export_plan_path=export_plan_path,
        include_hidden=include_hidden,
        dry_run=dry_run,
    )
    changes = [item for item in plan.get("changes", []) if isinstance(item, dict)]
    result = _base_update_result(source_root, output_root, library_dir, plan, dry_run, convert_options)

    planned_conversions = [item for item in changes if item.get("status") in {"new", "modified"}]
    reusable_changes = [item for item in changes if item.get("status") in {"unchanged", "deleted_missing", "moved_or_renamed_candidate"}]
    result["planned"] = {
        "convert": len(planned_conversions),
        "reuse": len(reusable_changes),
        "unsupported": sum(1 for item in changes if item.get("status") == "unsupported"),
    }
    result["missing_sources"] = [_missing_source_summary(item) for item in changes if item.get("status") == "deleted_missing"]
    result["stale_sources"] = [_source_summary(item) for item in changes if item.get("status") == "stale"]
    result["unsupported_sources"] = [_source_summary(item) for item in changes if item.get("status") == "unsupported"]
    result["review_summary"] = _build_review_summary(plan, result)
    result["large_folder_warnings"] = _large_folder_warnings(result["review_summary"])
    result["next_steps"] = _next_steps(result["review_summary"], dry_run=dry_run)
    if review_report_path:
        _write_review_report(review_report_path, result)
        result["written_files"]["review_report"] = str(review_report_path.expanduser().resolve())

    if dry_run:
        result["warnings"].append("dry-run: conversion output, library files, registry, state, and update_result.json were not written")
        result["status"] = "dry_run"
        return result

    output_root.mkdir(parents=True, exist_ok=True)
    converted_packs: list[Path] = []
    for change in planned_conversions:
        source = Path(str(change.get("source_path") or ""))
        try:
            pack_path, status = convert_file(source, output_root, convert_options)
            converted_packs.append(pack_path)
            result["converted"].append(
                {
                    "source_path": str(source),
                    "relative_path": change.get("relative_path"),
                    "status": status,
                    "knowledge_pack_path": str(pack_path),
                }
            )
        except Exception as exc:  # pragma: no cover - exercised through CLI/manual failures
            failed_pack = _write_failure_manifest(source, output_root, convert_options, exc)
            result["conversion_failures"].append(
                {
                    "source_path": str(source),
                    "relative_path": change.get("relative_path"),
                    "source_file": change.get("source_file"),
                    "status": "failed",
                    "knowledge_pack_path": str(failed_pack),
                    "manifest_path": str(failed_pack / "manifest.json"),
                    "error": f"{exc.__class__.__name__}: {exc}",
                }
            )

    if result["conversion_failures"]:
        rebuild_output_index(output_root, profile=convert_options.profile)
        result["status"] = "failed"
        _refresh_execution_review_fields(result)
        result["warnings"].append("one or more conversions failed; failed manifests were written and library rebuild was not run")
        result["next_steps"] = _failure_next_steps(result)
        result["written_files"].update({
            "output_index": str(output_root / "_index.json"),
            "update_result": str((update_result_path or library_dir / "update_result.json").expanduser().resolve()),
        })
        _write_update_result(update_result_path or library_dir / "update_result.json", result)
        return result

    reusable_packs, unsafe_reuse_packs = _classify_reusable_packs(reusable_changes)
    result["unsafe_reuse_packs"] = unsafe_reuse_packs
    result["reused_packs"] = [{"knowledge_pack_path": str(path)} for path in reusable_packs]
    if unsafe_reuse_packs:
        result["status"] = "failed"
        _refresh_execution_review_fields(result)
        result["warnings"].append("one or more planned reuse candidates were unsafe; library rebuild was not run")
        result["next_steps"] = _unsafe_reuse_next_steps(result)
        result["written_files"]["update_result"] = str((update_result_path or library_dir / "update_result.json").expanduser().resolve())
        _write_update_result(update_result_path or library_dir / "update_result.json", result)
        return result

    selected_packs = reusable_packs + converted_packs
    staging_root = _stage_valid_packs(selected_packs, library_dir)
    result["staging_root"] = str(staging_root)

    rebuild_output_index(staging_root, profile=convert_options.profile)
    build_result = _build_library_with_retry(staging_root, library_dir)
    result["build_result"] = build_result

    registry = save_source_registry(library_dir)
    state = save_library_state(library_dir, change_plan_path=export_plan_path or change_plan_path)
    result["written_files"].update({
        "source_registry": registry.get("registry_path") or str(default_source_registry_path(library_dir)),
        "library_state": state.get("library_state_path") or str(default_library_state_path(library_dir)),
        "update_result": str((update_result_path or library_dir / "update_result.json").expanduser().resolve()),
    })
    result["status"] = "updated"
    if result["missing_sources"]:
        result["warnings"].append("deleted/missing sources were recorded but no evidence was deleted")
    if result["stale_sources"]:
        result["warnings"].append("stale sources were recorded for review and not converted automatically")
    if any(item.get("status") == "moved_or_renamed_candidate" for item in changes):
        result["warnings"].append("moved/renamed candidates reused existing packs and require human review")

    _write_update_result(update_result_path or library_dir / "update_result.json", result)
    return result


def _load_or_scan_plan(
    source_root: Path,
    library_dir: Path,
    *,
    change_plan_path: Path | None,
    export_plan_path: Path | None,
    include_hidden: bool,
    dry_run: bool,
) -> dict[str, Any]:
    if change_plan_path:
        return json.loads(change_plan_path.expanduser().resolve().read_text(encoding="utf-8"))
    plan = scan_changes(
        source_root,
        library_dir,
        export_json=export_plan_path,
        dry_run=dry_run or export_plan_path is None,
        include_hidden=include_hidden,
    )
    if export_plan_path and not dry_run:
        plan["change_plan_path"] = str(export_plan_path.expanduser().resolve())
    return plan


def _base_update_result(
    source_root: Path,
    output_root: Path,
    library_dir: Path,
    plan: dict[str, Any],
    dry_run: bool,
    options: ConvertOptions,
) -> dict[str, Any]:
    return {
        "schema_version": UPDATE_RESULT_SCHEMA_VERSION,
        "generated_at": utc_now_iso(),
        "status": "planned",
        "dry_run": dry_run,
        "source_path": str(source_root),
        "conversion_output": str(output_root),
        "library_path": str(library_dir),
        "change_plan_schema": plan.get("schema_version"),
        "change_plan_path": plan.get("change_plan_path") or str(default_change_plan_path(library_dir)),
        "change_counts": plan.get("counts", {}),
        "options": {
            "engine": options.engine,
            "profile": options.profile,
            "include_hidden": bool(plan.get("options", {}).get("include_hidden", False)),
        },
        "planned": {},
        "converted": [],
        "conversion_failures": [],
        "reused_packs": [],
        "unsafe_reuse_packs": [],
        "missing_sources": [],
        "stale_sources": [],
        "unsupported_sources": [],
        "staging_root": None,
        "build_result": None,
        "written_files": {},
        "review_summary": {},
        "large_folder_warnings": [],
        "next_steps": [],
        "warnings": list(plan.get("warnings", [])),
        "limitations": [
            "update-library is explicit and never runs automatically",
            "source files are never modified",
            "deleted/missing evidence is marked but not deleted",
            "library rebuild uses existing build_library behavior rather than row-level SQLite updates",
        ],
    }


def _build_review_summary(plan: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    counts = dict(plan.get("counts", {}))
    pending_keys = ["new", "modified", "deleted_missing", "moved_or_renamed_candidate", "unsupported", "stale"]
    pending_total = sum(int(counts.get(key, 0) or 0) for key in pending_keys)
    convert_total = int(result.get("planned", {}).get("convert", 0) or 0)
    total = int(counts.get("total", 0) or 0)
    unchanged = int(counts.get("unchanged", 0) or 0)
    status = "current" if pending_total == 0 and total > 0 else "stale" if pending_total else "unknown"
    return {
        "status": status,
        "total_sources": total,
        "pending_total": pending_total,
        "convert_total": convert_total,
        "reuse_total": int(result.get("planned", {}).get("reuse", 0) or 0),
        "converted_total": len(result.get("converted", []) or []),
        "conversion_failure_total": len(result.get("conversion_failures", []) or []),
        "unsafe_reuse_total": len(result.get("unsafe_reuse_packs", []) or []),
        "unchanged_total": unchanged,
        "deleted_missing_total": int(counts.get("deleted_missing", 0) or 0),
        "stale_total": int(counts.get("stale", 0) or 0),
        "unsupported_total": int(counts.get("unsupported", 0) or 0),
        "moved_or_renamed_candidate_total": int(counts.get("moved_or_renamed_candidate", 0) or 0),
        "large_folder": total >= 500,
        "high_pending_changes": pending_total >= 100,
        "guidance": _review_guidance(status, convert_total, pending_total),
    }


def _review_guidance(status: str, convert_total: int, pending_total: int) -> str:
    if status == "current":
        return "Library appears current; no update run is needed."
    if status == "unknown":
        return "Library freshness is unknown; inspect registry and change plan before answering from this library."
    if convert_total:
        return f"Review {pending_total} pending changes; running update-library will convert {convert_total} new/modified files."
    return f"Review {pending_total} pending changes; no new/modified conversions are planned."


def _large_folder_warnings(summary: dict[str, Any]) -> list[str]:
    warnings = []
    if summary.get("large_folder"):
        warnings.append("large source set detected; review the change plan before running update-library")
    if summary.get("high_pending_changes"):
        warnings.append("high pending-change count detected; consider smaller batches or reviewing unsupported files first")
    return warnings


def _next_steps(summary: dict[str, Any], *, dry_run: bool) -> list[str]:
    if summary.get("status") == "current":
        return ["No update required; agents may answer from the current built library."]
    steps = ["Review change counts and unsupported/deleted/stale entries."]
    if dry_run and summary.get("convert_total"):
        steps.append("Run update-library without --dry-run to convert new/modified files and rebuild the library.")
    elif dry_run:
        steps.append("Resolve review items or refresh source_registry/library_state as needed.")
    else:
        steps.append("Run library-status and agent search/open-chunk checks against the rebuilt library.")
    return steps


def _refresh_execution_review_fields(result: dict[str, Any]) -> None:
    summary = result.get("review_summary")
    if not isinstance(summary, dict):
        return
    summary["converted_total"] = len(result.get("converted", []) or [])
    summary["conversion_failure_total"] = len(result.get("conversion_failures", []) or [])
    summary["unsafe_reuse_total"] = len(result.get("unsafe_reuse_packs", []) or [])


def _failure_next_steps(result: dict[str, Any]) -> list[str]:
    failures = result.get("conversion_failures") or []
    steps = [
        "Inspect conversion_failures and failed manifests before relying on this update result.",
        "Fix or exclude failed source files, then rerun update-library.",
        "Run library-status after a successful rerun before agent use.",
    ]
    if failures:
        steps.insert(1, "The library was not rebuilt, so previous library evidence remains unchanged.")
    return steps


def _unsafe_reuse_next_steps(result: dict[str, Any]) -> list[str]:
    steps = [
        "Inspect unsafe_reuse_packs before relying on this update result.",
        "Regenerate or remove failed, unreadable, or incomplete Knowledge Packs before rerunning update-library.",
        "Run scan-changes and update-library again after reuse candidates are repaired or reconverted.",
    ]
    if result.get("unsafe_reuse_packs"):
        steps.insert(1, "The library was not rebuilt because reuse safety could not be proven.")
    return steps


def _write_review_report(path: Path, result: dict[str, Any]) -> None:
    target = path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    summary = result.get("review_summary", {})
    counts = result.get("change_counts", {})
    lines = [
        "# office2md update-library review",
        "",
        f"- Status: {summary.get('status')}",
        f"- Total sources: {summary.get('total_sources', 0)}",
        f"- Pending changes: {summary.get('pending_total', 0)}",
        f"- Planned conversions: {summary.get('convert_total', 0)}",
        f"- Planned reuse: {summary.get('reuse_total', 0)}",
        "",
        "## Change Counts",
        "",
    ]
    for key in ["new", "modified", "unchanged", "deleted_missing", "moved_or_renamed_candidate", "unsupported", "stale", "total"]:
        lines.append(f"- {key}: {counts.get(key, 0)}")
    lines.extend(["", "## Guidance", "", str(summary.get("guidance") or "")])
    if result.get("large_folder_warnings"):
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in result["large_folder_warnings"])
    if result.get("next_steps"):
        lines.extend(["", "## Next Steps", ""])
        lines.extend(f"{index}. {item}" for index, item in enumerate(result["next_steps"], start=1))
    target.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def _write_failure_manifest(source_path: Path, output_root: Path, options: ConvertOptions, exc: Exception) -> Path:
    source = source_path.expanduser().resolve()
    checksum = sha256_file(source) if source.exists() else "sha256:"
    engine = _failure_engine(source, options)
    result = ConvertResult(markdown="", raw_markdown="", engine=engine, errors=[str(exc)])
    manifest = build_manifest(
        source_path=source,
        checksum=checksum,
        engine=engine,
        status="failed",
        warnings=[],
        errors=[str(exc)],
    )
    return write_document_output(source, output_root, result, "", [], manifest)


def _failure_engine(path: Path, options: ConvertOptions) -> str:
    if options.engine != "auto":
        return options.engine
    if path.suffix.lower() == ".pdf":
        return "docling"
    return "markitdown"


def _classify_reusable_packs(changes: list[dict[str, Any]]) -> tuple[list[Path], list[dict[str, Any]]]:
    paths: list[Path] = []
    unsafe: list[dict[str, Any]] = []
    for change in changes:
        previous = change.get("previous") if isinstance(change.get("previous"), dict) else {}
        pack = previous.get("knowledge_pack_path")
        manifest = previous.get("manifest_path")
        pack_path = Path(str(pack)).expanduser().resolve() if pack else None
        manifest_path = Path(str(manifest)).expanduser().resolve() if manifest else None
        if pack_path and not manifest_path:
            manifest_path = pack_path / "manifest.json"
        elif manifest_path and not pack_path:
            pack_path = manifest_path.parent

        reason = _reuse_safety_issue(pack_path, manifest_path)
        if reason:
            unsafe.append(_unsafe_reuse_record(change, pack_path, manifest_path, reason))
            continue
        if pack_path:
            paths.append(pack_path)
    return _dedupe_paths(paths), unsafe


def _reuse_safety_issue(pack_path: Path | None, manifest_path: Path | None) -> str | None:
    if not pack_path:
        return "missing Knowledge Pack path"
    if not pack_path.exists():
        return "Knowledge Pack path does not exist"
    if not manifest_path:
        return "missing manifest path"
    if not manifest_path.exists():
        return "Knowledge Pack manifest is missing"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "Knowledge Pack manifest is unreadable"
    if not isinstance(manifest, dict):
        return "Knowledge Pack manifest is not an object"
    status = manifest.get("status")
    if status != "success":
        return f"Knowledge Pack manifest status is {status or 'missing'}"
    return None


def _unsafe_reuse_record(change: dict[str, Any], pack_path: Path | None, manifest_path: Path | None, reason: str) -> dict[str, Any]:
    return {
        "source_path": change.get("source_path"),
        "relative_path": change.get("relative_path"),
        "source_file": change.get("source_file"),
        "change_status": change.get("status"),
        "knowledge_pack_path": None if pack_path is None else str(pack_path),
        "manifest_path": None if manifest_path is None else str(manifest_path),
        "reason": reason,
    }


def _stage_valid_packs(pack_paths: list[Path], library_dir: Path) -> Path:
    staging_root = library_dir / "_office2md_update_build" / _safe_timestamp(utc_now_iso())
    staging_root.mkdir(parents=True, exist_ok=True)
    used_names: set[str] = set()
    for pack_path in _dedupe_paths(pack_paths):
        if not (pack_path / "manifest.json").exists():
            continue
        name = _unique_name(pack_path.name or "pack", used_names)
        shutil.copytree(pack_path, staging_root / name)
    return staging_root


def _safe_timestamp(value: str) -> str:
    return value.replace(":", "").replace("-", "").replace(".", "").replace("+", "Z")


def _unique_name(name: str, used: set[str]) -> str:
    candidate = name
    index = 2
    while candidate in used:
        candidate = f"{name}-{index}"
        index += 1
    used.add(candidate)
    return candidate


def _source_summary(change: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_path": change.get("source_path"),
        "relative_path": change.get("relative_path"),
        "source_file": change.get("source_file"),
        "status": change.get("status"),
        "reasons": change.get("reasons", []),
    }


def _missing_source_summary(change: dict[str, Any]) -> dict[str, Any]:
    return _source_summary(change)


def _write_update_result(path: Path, result: dict[str, Any]) -> None:
    target = path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_library_with_retry(staging_root: Path, library_dir: Path) -> dict[str, Any]:
    last_error: PermissionError | None = None
    for _ in range(20):
        try:
            gc.collect()
            return build_library(staging_root, library_dir)
        except PermissionError as exc:
            last_error = exc
            time.sleep(0.25)
    if last_error:
        raise last_error
    return build_library(staging_root, library_dir)


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    seen = set()
    result = []
    for path in paths:
        key = str(path)
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def _library_dir(library_path: Path) -> Path:
    candidate = library_path.expanduser().resolve()
    return candidate.parent if candidate.name == "library.db" else candidate
