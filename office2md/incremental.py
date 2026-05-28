import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from office2md.detector import sha256_file
from office2md.scanner import is_supported_file
from office2md.utils import utc_now_iso


SOURCE_REGISTRY_SCHEMA_VERSION = "office2md.source_registry.v1"
CHANGE_PLAN_SCHEMA_VERSION = "office2md.change_plan.v1"
LIBRARY_STATUS_SCHEMA_VERSION = "office2md.library_status.v1"
LIBRARY_STATE_SCHEMA_VERSION = "office2md.library_state.v1"


def load_source_registry(library_path: Path, registry_path: Path | None = None) -> dict[str, Any]:
    path = _registry_path(library_path, registry_path)
    if not path.exists():
        return _empty_source_registry(library_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("schema_version", SOURCE_REGISTRY_SCHEMA_VERSION)
    data.setdefault("sources", [])
    return data


def write_source_registry(path: Path, registry: dict[str, Any]) -> None:
    _write_json(path, registry)


def save_source_registry(library_path: Path, output_path: Path | None = None) -> dict[str, Any]:
    registry = build_source_registry(library_path)
    target = output_path.expanduser().resolve() if output_path else default_source_registry_path(library_path)
    registry["registry_path"] = str(target)
    write_source_registry(target, registry)
    return registry


def build_source_registry(library_path: Path) -> dict[str, Any]:
    library_dir = _library_dir(library_path)
    db_path = _library_db_path(library_path)
    conversion_root = _library_conversion_root(library_dir)
    generated_at = utc_now_iso()
    sources: list[dict[str, Any]] = []
    warnings: list[str] = []

    if db_path.exists():
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT doc_id, source_file, source_path, checksum, converter, output_dir
                FROM documents
                ORDER BY source_file, doc_id
                """
            ).fetchall()
        for row in rows:
            sources.append(_registry_record_from_document(library_dir, conversion_root, row, generated_at))
    else:
        warnings.append(f"library.db not found: {db_path}")

    return {
        "schema_version": SOURCE_REGISTRY_SCHEMA_VERSION,
        "generated_at": generated_at,
        "library_path": str(library_dir),
        "registry_path": str(default_source_registry_path(library_path)),
        "sources": sources,
        "warnings": warnings,
    }


def scan_changes(
    source_path: Path,
    library_path: Path,
    *,
    registry_path: Path | None = None,
    export_json: Path | None = None,
    dry_run: bool = True,
    include_hidden: bool = False,
) -> dict[str, Any]:
    source_root = source_path.expanduser().resolve()
    if not source_root.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_root}")

    registry = load_source_registry(library_path, registry_path)
    if not registry.get("sources"):
        registry = build_source_registry(library_path)
    plan = build_change_plan(source_root, library_path, registry, include_hidden=include_hidden)
    plan["dry_run"] = dry_run
    if export_json and not dry_run:
        _write_json(export_json, plan)
    return plan


def build_change_plan(source_root: Path, library_path: Path, registry: dict[str, Any], *, include_hidden: bool = False) -> dict[str, Any]:
    generated_at = utc_now_iso()
    current_supported, unsupported = _collect_source_files(source_root, include_hidden=include_hidden)
    registry_records = [item for item in registry.get("sources", []) if isinstance(item, dict)]
    registry_by_path = {str(item.get("normalized_source_path")): item for item in registry_records if item.get("normalized_source_path")}
    registry_by_hash: dict[str, list[dict[str, Any]]] = {}
    for item in registry_records:
        checksum = item.get("sha256")
        if checksum:
            registry_by_hash.setdefault(str(checksum), []).append(item)

    changes: list[dict[str, Any]] = []
    seen_registry_paths: set[str] = set()
    for path in current_supported:
        current = _current_source_record(path, source_root)
        previous = registry_by_path.get(current["normalized_source_path"])
        if previous:
            seen_registry_paths.add(current["normalized_source_path"])
            status, reasons = _classify_existing_file(current, previous)
            changes.append(_change_record(status, path, current, previous, reasons))
            continue
        candidates = [item for item in registry_by_hash.get(current["sha256"], []) if item.get("normalized_source_path") not in seen_registry_paths]
        if candidates:
            previous = candidates[0]
            seen_registry_paths.add(str(previous.get("normalized_source_path")))
            changes.append(
                _change_record(
                    "moved_or_renamed_candidate",
                    path,
                    current,
                    previous,
                    ["checksum matches a registered source at a different path"],
                )
            )
        else:
            changes.append(_change_record("new", path, current, None, ["not present in source registry"]))

    current_paths = {item["normalized_source_path"] for item in (_current_source_record(path, source_root) for path in current_supported)}
    for previous in registry_records:
        normalized = str(previous.get("normalized_source_path") or "")
        if normalized and normalized not in current_paths and normalized not in seen_registry_paths:
            changes.append(
                {
                    "status": "deleted_missing",
                    "source_path": previous.get("source_path"),
                    "relative_path": previous.get("relative_path"),
                    "source_file": previous.get("source_file"),
                    "extension": previous.get("extension"),
                    "previous": _registry_change_projection(previous),
                    "current": None,
                    "reasons": ["registered source was not found in current scan"],
                }
            )

    for path in unsupported:
        changes.append(
            {
                "status": "unsupported",
                "source_path": str(path),
                "relative_path": _safe_relative_path(path, source_root),
                "source_file": path.name,
                "extension": path.suffix.lower(),
                "previous": None,
                "current": _file_metadata(path, source_root, compute_hash=False),
                "reasons": ["unsupported extension or temporary Office file"],
            }
        )

    counts = _change_counts(changes)
    return {
        "schema_version": CHANGE_PLAN_SCHEMA_VERSION,
        "generated_at": generated_at,
        "source_path": str(source_root),
        "library_path": str(_library_dir(library_path)),
        "registry_path": str(_registry_path(library_path, None)),
        "dry_run": True,
        "options": {"include_hidden": include_hidden},
        "counts": counts,
        "changes": sorted(changes, key=lambda item: (str(item.get("relative_path") or ""), str(item.get("status") or ""))),
        "warnings": _change_plan_warnings(counts),
        "limitations": [
            "scan-changes does not modify conversion output, library files, or source files",
            "moved/renamed detection is checksum-based and advisory",
            "agents must not assume new raw files are visible until scan/update workflow is run",
        ],
    }


def load_library_state(library_path: Path, state_path: Path | None = None) -> dict[str, Any]:
    path = _state_path(library_path, state_path)
    if not path.exists():
        return _empty_library_state(library_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("schema_version", LIBRARY_STATE_SCHEMA_VERSION)
    return data


def write_library_state(path: Path, state: dict[str, Any]) -> None:
    _write_json(path, state)


def build_library_state(
    library_path: Path,
    *,
    change_plan_path: Path | None = None,
    registry_path: Path | None = None,
    state_path: Path | None = None,
) -> dict[str, Any]:
    status = library_status(library_path, change_plan_path=change_plan_path, registry_path=registry_path, state_path=state_path)
    db_path = _library_db_path(library_path)
    return {
        "schema_version": LIBRARY_STATE_SCHEMA_VERSION,
        "generated_at": utc_now_iso(),
        "library_path": status["library_path"],
        "library_db": status["library_db"],
        "library_db_exists": status["library_db_exists"],
        "library_db_sha256": sha256_file(db_path) if db_path.exists() else None,
        "source_registry_path": status["source_registry_path"],
        "source_registry_exists": status["source_registry_exists"],
        "change_plan_path": str(change_plan_path.expanduser().resolve()) if change_plan_path else None,
        "change_plan_exists": bool(change_plan_path and change_plan_path.expanduser().resolve().exists()),
        "status": status["status"],
        "counts": status["counts"],
        "pending_changes": status["pending_changes"],
        "warnings": status["warnings"],
        "limitations": [
            "library_state.json is a status snapshot, not an update operation",
            "agents must refresh status/scan before relying on old state snapshots",
        ],
    }


def save_library_state(
    library_path: Path,
    *,
    output_path: Path | None = None,
    change_plan_path: Path | None = None,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    target = output_path.expanduser().resolve() if output_path else default_library_state_path(library_path)
    state = build_library_state(library_path, change_plan_path=change_plan_path, registry_path=registry_path, state_path=target)
    state["library_state_path"] = str(target)
    write_library_state(target, state)
    return state


def library_status(
    library_path: Path,
    *,
    change_plan_path: Path | None = None,
    registry_path: Path | None = None,
    state_path: Path | None = None,
) -> dict[str, Any]:
    library_dir = _library_dir(library_path)
    db_path = _library_db_path(library_path)
    registry_file = _registry_path(library_path, registry_path)
    state_file = _state_path(library_path, state_path)
    state_exists = state_file.exists()
    state = load_library_state(library_path, state_path) if state_exists else _empty_library_state(library_path)
    registry = load_source_registry(library_path, registry_path) if registry_file.exists() else build_source_registry(library_path)
    registry_exists = registry_file.exists()
    registry_records = [item for item in registry.get("sources", []) if isinstance(item, dict)]
    source_state = [_source_registry_status(item) for item in registry_records]
    stale_records = [item for item in source_state if item["status"] != "current"]
    status = "unknown"
    if registry_records:
        status = "current" if not stale_records else "stale"

    change_plan = None
    if change_plan_path:
        change_plan = json.loads(change_plan_path.expanduser().resolve().read_text(encoding="utf-8"))
        plan_counts = change_plan.get("counts", {})
        if any(int(plan_counts.get(key, 0) or 0) for key in ["new", "modified", "deleted_missing", "moved_or_renamed_candidate", "unsupported", "stale"]):
            status = "stale"
    elif status == "unknown" and state_exists and state.get("status") in {"current", "stale", "unknown"}:
        status = str(state.get("status"))

    return {
        "schema_version": LIBRARY_STATUS_SCHEMA_VERSION,
        "generated_at": utc_now_iso(),
        "library_path": str(library_dir),
        "library_db": str(db_path),
        "library_db_exists": db_path.exists(),
        "source_registry_path": str(registry_file),
        "source_registry_exists": registry_exists,
        "library_state_path": str(state_file),
        "library_state_exists": state_exists,
        "state_status": state.get("status") if state_exists else None,
        "status": status,
        "counts": {
            "registered_sources": len(registry_records),
            "current_sources": sum(1 for item in source_state if item["status"] == "current"),
            "stale_sources": len(stale_records),
            "missing_sources": sum(1 for item in source_state if item["status"] == "missing"),
        },
        "pending_changes": None if not change_plan else change_plan.get("counts", {}),
        "warnings": _library_status_warnings(status, db_path, registry_exists, stale_records, change_plan, state_exists),
        "limitations": [
            "library-status is read-only",
            "library status is unknown without a registry or library document source paths",
            "agents must not assume new raw files are visible until scan/update workflow is run",
        ],
    }


def default_source_registry_path(library_path: Path) -> Path:
    return _library_dir(library_path) / "source_registry.json"


def default_change_plan_path(library_path: Path) -> Path:
    return _library_dir(library_path) / "change_plan.json"


def default_library_state_path(library_path: Path) -> Path:
    return _library_dir(library_path) / "library_state.json"


def _registry_record_from_document(library_dir: Path, conversion_root: Path | None, row: sqlite3.Row, generated_at: str) -> dict[str, Any]:
    source_path = Path(str(row["source_path"] or row["source_file"] or "")).expanduser()
    source_exists = source_path.exists()
    output_dir = Path(str(row["output_dir"] or ""))
    if output_dir and not output_dir.is_absolute():
        output_dir = (conversion_root / output_dir) if conversion_root else (library_dir / output_dir)
    manifest_path = output_dir / "manifest.json" if output_dir else None
    stat = source_path.stat() if source_exists else None
    checksum = sha256_file(source_path) if source_exists else row["checksum"]
    return {
        "source_id": row["doc_id"],
        "normalized_source_path": _normalize_source_path(source_path) if source_path else "",
        "source_path": str(source_path) if source_path else "",
        "relative_path": source_path.name if source_path else str(row["source_file"] or ""),
        "source_file": row["source_file"] or source_path.name,
        "extension": source_path.suffix.lower() if source_path else Path(str(row["source_file"] or "")).suffix.lower(),
        "size": stat.st_size if stat else None,
        "mtime_ns": stat.st_mtime_ns if stat else None,
        "sha256": checksum,
        "converter": row["converter"],
        "converter_version": None,
        "profile": None,
        "knowledge_pack_path": str(output_dir) if output_dir else None,
        "manifest_path": str(manifest_path) if manifest_path else None,
        "status": "active" if source_exists else "missing",
        "registered_at": generated_at,
    }


def _collect_source_files(source_root: Path, *, include_hidden: bool) -> tuple[list[Path], list[Path]]:
    files = [source_root] if source_root.is_file() else sorted((item for item in source_root.rglob("*") if item.is_file()), key=lambda item: str(item).lower())
    supported = []
    unsupported = []
    for path in files:
        if not include_hidden and _has_hidden_part(path, source_root):
            continue
        if is_supported_file(path):
            supported.append(path.resolve())
        else:
            unsupported.append(path.resolve())
    return supported, unsupported


def _has_hidden_part(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    return any(part.startswith(".") for part in parts)


def _current_source_record(path: Path, root: Path) -> dict[str, Any]:
    return _file_metadata(path, root, compute_hash=True)


def _file_metadata(path: Path, root: Path, *, compute_hash: bool) -> dict[str, Any]:
    stat = path.stat()
    return {
        "normalized_source_path": _normalize_source_path(path),
        "source_path": str(path),
        "relative_path": _safe_relative_path(path, root),
        "source_file": path.name,
        "extension": path.suffix.lower(),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256_file(path) if compute_hash else None,
    }


def _classify_existing_file(current: dict[str, Any], previous: dict[str, Any]) -> tuple[str, list[str]]:
    reasons = []
    if previous.get("size") is not None and current["size"] != previous.get("size"):
        reasons.append("size changed")
    if previous.get("mtime_ns") is not None and current["mtime_ns"] != previous.get("mtime_ns"):
        reasons.append("mtime_ns changed")
    if previous.get("sha256") and current["sha256"] != previous.get("sha256"):
        reasons.append("sha256 changed")
    if reasons:
        return "modified", reasons
    manifest_path = previous.get("manifest_path")
    if manifest_path and not Path(str(manifest_path)).exists():
        return "stale", ["registered Knowledge Pack manifest is missing"]
    return "unchanged", []


def _change_record(status: str, path: Path, current: dict[str, Any], previous: dict[str, Any] | None, reasons: list[str]) -> dict[str, Any]:
    return {
        "status": status,
        "source_path": str(path),
        "relative_path": current.get("relative_path"),
        "source_file": current.get("source_file"),
        "extension": current.get("extension"),
        "previous": _registry_change_projection(previous) if previous else None,
        "current": current,
        "reasons": reasons,
    }


def _registry_change_projection(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not record:
        return None
    keys = [
        "source_id",
        "normalized_source_path",
        "source_path",
        "relative_path",
        "source_file",
        "extension",
        "size",
        "mtime_ns",
        "sha256",
        "converter",
        "converter_version",
        "profile",
        "knowledge_pack_path",
        "manifest_path",
        "status",
    ]
    return {key: record.get(key) for key in keys}


def _source_registry_status(record: dict[str, Any]) -> dict[str, Any]:
    source_path = Path(str(record.get("source_path") or ""))
    if not source_path.exists():
        return {"source_path": str(source_path), "status": "missing", "reasons": ["source file missing"]}
    current = _file_metadata(source_path.resolve(), source_path.parent.resolve(), compute_hash=True)
    status, reasons = _classify_existing_file(current, record)
    return {"source_path": str(source_path), "status": "current" if status == "unchanged" else status, "reasons": reasons}


def _change_counts(changes: list[dict[str, Any]]) -> dict[str, int]:
    statuses = ["new", "modified", "unchanged", "deleted_missing", "moved_or_renamed_candidate", "unsupported", "stale"]
    return {status: sum(1 for item in changes if item.get("status") == status) for status in statuses} | {"total": len(changes)}


def _change_plan_warnings(counts: dict[str, int]) -> list[str]:
    warnings = []
    if counts.get("new"):
        warnings.append("new raw files are not visible to agents until conversion/update workflow is run")
    if counts.get("modified") or counts.get("deleted_missing") or counts.get("stale"):
        warnings.append("library may be stale relative to source files")
    if counts.get("unsupported"):
        warnings.append("unsupported files were ignored for conversion planning")
    return warnings


def _library_status_warnings(
    status: str,
    db_path: Path,
    registry_exists: bool,
    stale_records: list[dict[str, Any]],
    change_plan: dict[str, Any] | None,
    state_exists: bool,
) -> list[str]:
    warnings = []
    if not db_path.exists():
        warnings.append(f"library.db not found: {db_path}")
    if not registry_exists:
        warnings.append("source_registry.json not found; status is derived from library documents where possible")
    if status == "stale":
        warnings.append("library may be stale relative to source files or change plan")
    if stale_records:
        warnings.append(f"{len(stale_records)} registered sources are stale or missing")
    if change_plan and change_plan.get("warnings"):
        warnings.extend(str(item) for item in change_plan.get("warnings", []))
    if state_exists:
        warnings.append("library_state.json is a snapshot; refresh status/scan before agent use")
    return _dedupe(warnings)


def _empty_source_registry(library_path: Path) -> dict[str, Any]:
    return {
        "schema_version": SOURCE_REGISTRY_SCHEMA_VERSION,
        "generated_at": None,
        "library_path": str(_library_dir(library_path)),
        "registry_path": str(default_source_registry_path(library_path)),
        "sources": [],
        "warnings": ["source_registry.json not found"],
    }


def _empty_library_state(library_path: Path) -> dict[str, Any]:
    return {
        "schema_version": LIBRARY_STATE_SCHEMA_VERSION,
        "generated_at": None,
        "library_path": str(_library_dir(library_path)),
        "library_state_path": str(default_library_state_path(library_path)),
        "status": "unknown",
        "warnings": ["library_state.json not found"],
    }


def _library_db_path(library_path: Path) -> Path:
    candidate = library_path.expanduser().resolve()
    return candidate if candidate.name == "library.db" else candidate / "library.db"


def _library_dir(library_path: Path) -> Path:
    candidate = library_path.expanduser().resolve()
    return candidate.parent if candidate.name == "library.db" else candidate


def _library_conversion_root(library_dir: Path) -> Path | None:
    manifest_path = library_dir / "library_manifest.json"
    if not manifest_path.exists():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    input_root = manifest.get("input_output_root")
    if not input_root:
        return None
    return Path(str(input_root)).expanduser().resolve()


def _registry_path(library_path: Path, registry_path: Path | None) -> Path:
    return registry_path.expanduser().resolve() if registry_path else default_source_registry_path(library_path)


def _state_path(library_path: Path, state_path: Path | None) -> Path:
    return state_path.expanduser().resolve() if state_path else default_library_state_path(library_path)


def _normalize_source_path(path: Path) -> str:
    return os.path.normcase(str(path.expanduser().resolve()))


def _safe_relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _write_json(path: Path, data: dict[str, Any]) -> None:
    target = path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _dedupe(values: list[str]) -> list[str]:
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
