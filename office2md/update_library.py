import json
import gc
import shutil
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from office2md.incremental import (
    default_change_plan_path,
    default_library_state_path,
    default_source_registry_path,
    save_library_state,
    save_source_registry,
    scan_changes,
)
from office2md.library import build_library
from office2md.models import ConvertOptions
from office2md.storage.index import rebuild_output_index
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
            result["conversion_failures"].append(
                {
                    "source_path": str(source),
                    "relative_path": change.get("relative_path"),
                    "error": f"{exc.__class__.__name__}: {exc}",
                }
            )

    if result["conversion_failures"]:
        result["status"] = "failed"
        result["warnings"].append("one or more conversions failed; library rebuild was not run")
        _write_update_result(update_result_path or library_dir / "update_result.json", result)
        return result

    reusable_packs = _reusable_pack_paths(reusable_changes)
    result["reused_packs"] = [{"knowledge_pack_path": str(path)} for path in reusable_packs]
    selected_packs = reusable_packs + converted_packs
    staging_root = _stage_valid_packs(selected_packs, library_dir)
    result["staging_root"] = str(staging_root)

    rebuild_output_index(staging_root, profile=convert_options.profile)
    build_result = _build_library_with_retry(staging_root, library_dir)
    result["build_result"] = build_result

    registry = save_source_registry(library_dir)
    state = save_library_state(library_dir, change_plan_path=export_plan_path or change_plan_path)
    result["written_files"] = {
        "source_registry": registry.get("registry_path") or str(default_source_registry_path(library_dir)),
        "library_state": state.get("library_state_path") or str(default_library_state_path(library_dir)),
        "update_result": str((update_result_path or library_dir / "update_result.json").expanduser().resolve()),
    }
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
        "missing_sources": [],
        "stale_sources": [],
        "unsupported_sources": [],
        "staging_root": None,
        "build_result": None,
        "written_files": {},
        "warnings": list(plan.get("warnings", [])),
        "limitations": [
            "update-library is explicit and never runs automatically",
            "source files are never modified",
            "deleted/missing evidence is marked but not deleted",
            "library rebuild uses existing build_library behavior rather than row-level SQLite updates",
        ],
    }


def _reusable_pack_paths(changes: list[dict[str, Any]]) -> list[Path]:
    paths: list[Path] = []
    for change in changes:
        previous = change.get("previous") if isinstance(change.get("previous"), dict) else {}
        pack = previous.get("knowledge_pack_path")
        manifest = previous.get("manifest_path")
        if pack and Path(str(pack)).exists():
            paths.append(Path(str(pack)).expanduser().resolve())
        elif manifest and Path(str(manifest)).exists():
            paths.append(Path(str(manifest)).expanduser().resolve().parent)
    return _dedupe_paths(paths)


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
