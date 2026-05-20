import json
import hashlib
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from office2md.detector import sha256_file
from office2md.library import library_report
from office2md.scanner import scan_input
from office2md.utils import utc_now_iso


WORKSPACE_SCHEMA_VERSION = "1"
WORKSPACE_DIRECTORIES = [
    "conversion",
    "library",
    "wiki",
    "wiki/Concepts",
    "wiki/Notes",
    "wiki/Corrections",
    "wiki/_suggestions",
    "outputs",
    "outputs/obsidian",
    "outputs/reports",
    "outputs/html",
    "outputs/_manifests",
    "logs",
    "versions",
]
WORKSPACE_MANIFEST_FILES = [
    "workspace_manifest.json",
    "source_manifest.json",
    "versions/library_versions.json",
    "versions/output_versions.json",
]


def init_workspace(workspace_path: Path, dry_run: bool = False, overwrite_manifests: bool = False) -> dict[str, Any]:
    workspace = workspace_path.expanduser().resolve()
    directories = [workspace / rel for rel in WORKSPACE_DIRECTORIES]
    manifest_paths = [workspace / rel for rel in WORKSPACE_MANIFEST_FILES]
    planned_directories = [str(path) for path in directories]
    planned_manifests = [str(path) for path in manifest_paths]
    now = utc_now_iso()

    if dry_run:
        return {
            "workspace_path": str(workspace),
            "dry_run": True,
            "directories": planned_directories,
            "manifest_files": planned_manifests,
            "created_directories": [],
            "written_manifests": [],
            "preserved_manifests": [],
        }

    created_directories = []
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_directories.append(str(directory))

    written_manifests = []
    preserved_manifests = []
    workspace_manifest_path = workspace / "workspace_manifest.json"
    existing_workspace_manifest = _read_json_if_possible(workspace_manifest_path)
    workspace_manifest = _workspace_manifest(workspace, now, existing_workspace_manifest)
    _write_json(workspace_manifest_path, workspace_manifest)
    written_manifests.append(str(workspace_manifest_path))

    initial_manifests = {
        workspace / "source_manifest.json": _source_manifest(now),
        workspace / "versions" / "library_versions.json": _library_versions_manifest(),
        workspace / "versions" / "output_versions.json": _output_versions_manifest(),
    }
    for path, data in initial_manifests.items():
        if path.exists() and not overwrite_manifests:
            preserved_manifests.append(str(path))
            continue
        _write_json(path, data)
        written_manifests.append(str(path))

    return {
        "workspace_path": str(workspace),
        "dry_run": False,
        "directories": planned_directories,
        "manifest_files": planned_manifests,
        "created_directories": created_directories,
        "written_manifests": written_manifests,
        "preserved_manifests": preserved_manifests,
    }


def detect_workspace(path: Path) -> bool:
    workspace = path.expanduser()
    return (
        workspace.is_dir()
        and (workspace / "workspace_manifest.json").exists()
        and (workspace / "source_manifest.json").exists()
        and (workspace / "conversion").is_dir()
        and (workspace / "library").is_dir()
        and (workspace / "wiki").is_dir()
        and (workspace / "outputs").is_dir()
        and (workspace / "versions").is_dir()
    )


def summarize_workspace(path: Path) -> dict[str, Any]:
    workspace = path.expanduser().resolve()
    manifest_path = workspace / "workspace_manifest.json"
    manifest = _read_json_if_possible(manifest_path)
    return {
        "workspace_path": str(workspace),
        "exists": workspace.exists(),
        "is_workspace": detect_workspace(workspace),
        "workspace_manifest_exists": manifest_path.exists(),
        "source_manifest_exists": (workspace / "source_manifest.json").exists(),
        "library_versions_exists": (workspace / "versions" / "library_versions.json").exists(),
        "output_versions_exists": (workspace / "versions" / "output_versions.json").exists(),
        "folders": {rel: (workspace / rel).exists() for rel in WORKSPACE_DIRECTORIES},
        "schema_version": manifest.get("schema_version") if manifest else None,
        "created_at": manifest.get("created_at") if manifest else None,
        "updated_at": manifest.get("updated_at") if manifest else None,
    }


def load_workspace_status(workspace_path: Path) -> dict[str, Any]:
    workspace = workspace_path.expanduser().resolve()
    return {
        "workspace_manifest": _read_json_if_possible(workspace / "workspace_manifest.json"),
        "source_manifest": _read_json_if_possible(workspace / "source_manifest.json"),
        "library_versions": _read_json_if_possible(workspace / "versions" / "library_versions.json"),
        "output_versions": _read_json_if_possible(workspace / "versions" / "output_versions.json"),
    }


def current_source_manifest_hash(workspace_path: Path) -> str | None:
    source_manifest_path = workspace_path.expanduser().resolve() / "source_manifest.json"
    if not source_manifest_path.exists():
        return None
    return compute_json_file_sha256(source_manifest_path)


def summarize_workspace_status(workspace_path: Path, *, show_history: bool = False, limit: int = 5) -> dict[str, Any]:
    workspace = workspace_path.expanduser().resolve()
    if not detect_workspace(workspace):
        raise ValueError(f"Not an office2md workspace: {workspace}. Run workspace-init first.")
    data = load_workspace_status(workspace)
    workspace_manifest = data["workspace_manifest"] or {}
    source_manifest = data["source_manifest"] or {}
    library_versions_manifest = data["library_versions"] or {}
    output_versions_manifest = data["output_versions"] or {}
    current_source_hash = current_source_manifest_hash(workspace)
    library_records = [item for item in library_versions_manifest.get("library_versions", []) if isinstance(item, dict)]
    output_records = [item for item in output_versions_manifest.get("output_versions", []) if isinstance(item, dict)]
    latest_library = _latest_version_record(library_records)
    latest_output = _latest_version_record(output_records)
    warnings = []
    errors = []
    missing_folders = [rel for rel in WORKSPACE_DIRECTORIES if not (workspace / rel).exists()]
    missing_manifests = [rel for rel in WORKSPACE_MANIFEST_FILES if not (workspace / rel).exists()]
    if missing_manifests:
        errors.append(f"missing expected manifest(s): {', '.join(missing_manifests)}")
    source_counts = _normalized_source_counts(source_manifest.get("counts", {}))
    warnings.extend(_dirty_source_warnings(source_counts))
    if latest_output and latest_output.get("library_version_id"):
        linked_library = next((item for item in library_records if item.get("library_version_id") == latest_output.get("library_version_id")), None)
        if linked_library is None:
            warning = f"latest output links to missing library_version_id: {latest_output.get('library_version_id')}"
            warnings.append(warning)
            errors.append(warning)
    if latest_library and latest_library.get("source_manifest_hash") and latest_library.get("source_manifest_hash") != current_source_hash:
        warnings.append("latest library source_manifest_hash differs from current source_manifest hash")
    if latest_output and latest_output.get("source_manifest_hash") and latest_output.get("source_manifest_hash") != current_source_hash:
        warnings.append("latest output source_manifest_hash differs from current source_manifest hash")
    return {
        "workspace": {
            "workspace_path": str(workspace),
            "office2md_version": workspace_manifest.get("office2md_version") or _office2md_version(),
            "schema_version": workspace_manifest.get("schema_version"),
            "created_at": workspace_manifest.get("created_at"),
            "updated_at": workspace_manifest.get("updated_at"),
            "folders": {rel: (workspace / rel).exists() for rel in WORKSPACE_DIRECTORIES},
            "missing_expected_folders": missing_folders,
            "missing_expected_manifests": missing_manifests,
        },
        "source_manifest": {
            **source_counts,
            "source_roots_count": len(source_manifest.get("source_roots", []) or []),
            "last_scan": source_manifest.get("last_scan"),
            "current_source_manifest_hash": current_source_hash,
            "warnings": _dirty_source_warnings(source_counts),
        },
        "library_versions": {
            "total_versions": len(library_records),
            "latest": _library_status_summary(latest_library),
            "history": [_library_status_summary(item) for item in _recent_version_records(library_records, limit)] if show_history else [],
        },
        "output_versions": {
            "total_versions": len(output_records),
            "latest": _output_status_summary(latest_output),
            "history": [_output_status_summary(item) for item in _recent_version_records(output_records, limit)] if show_history else [],
        },
        "traceability": build_traceability_summary(latest_library, latest_output, current_source_hash),
        "warnings": warnings,
        "errors": errors,
    }


def build_traceability_summary(latest_library: dict[str, Any] | None, latest_output: dict[str, Any] | None, current_source_hash: str | None) -> dict[str, Any]:
    source_hash = (latest_output or {}).get("source_manifest_hash") or (latest_library or {}).get("source_manifest_hash") or current_source_hash
    return {
        "source_manifest_hash": source_hash,
        "library_version_id": (latest_output or {}).get("library_version_id") or (latest_library or {}).get("library_version_id"),
        "output_version_id": (latest_output or {}).get("output_version_id"),
    }


def load_source_manifest(workspace_path: Path) -> dict[str, Any]:
    manifest_path = workspace_path.expanduser().resolve() / "source_manifest.json"
    return _read_json_if_possible(manifest_path) or _source_manifest(utc_now_iso())


def write_source_manifest(workspace_path: Path, manifest: dict[str, Any]) -> None:
    manifest_path = workspace_path.expanduser().resolve() / "source_manifest.json"
    _write_json(manifest_path, manifest)


def compute_file_sha256(path: Path) -> str:
    return sha256_file(path)


def load_library_versions(workspace_path: Path) -> dict[str, Any]:
    versions_path = workspace_path.expanduser().resolve() / "versions" / "library_versions.json"
    return _read_json_if_possible(versions_path) or _library_versions_manifest()


def write_library_versions(workspace_path: Path, manifest: dict[str, Any]) -> None:
    versions_path = workspace_path.expanduser().resolve() / "versions" / "library_versions.json"
    _write_json(versions_path, manifest)


def load_output_versions(workspace_path: Path) -> dict[str, Any]:
    versions_path = workspace_path.expanduser().resolve() / "versions" / "output_versions.json"
    return _read_json_if_possible(versions_path) or _output_versions_manifest()


def write_output_versions(workspace_path: Path, manifest: dict[str, Any]) -> None:
    versions_path = workspace_path.expanduser().resolve() / "versions" / "output_versions.json"
    _write_json(versions_path, manifest)


def compute_json_file_sha256(path: Path) -> str:
    return compute_file_sha256(path)


def compute_source_manifest_hash(workspace_path: Path) -> str:
    return compute_json_file_sha256(workspace_path.expanduser().resolve() / "source_manifest.json")


def register_library_version(
    workspace_path: Path,
    library_path: Path,
    *,
    dry_run: bool = False,
    label: str | None = None,
    notes: str | None = None,
    allow_dirty_source: bool = False,
    library_version_id: str | None = None,
) -> dict[str, Any]:
    workspace = workspace_path.expanduser().resolve()
    if not detect_workspace(workspace):
        raise ValueError(f"Not an office2md workspace: {workspace}. Run workspace-init first.")

    library_summary = summarize_library_for_version(library_path)
    source_manifest = load_source_manifest(workspace)
    library_versions = load_library_versions(workspace)
    registered_at = utc_now_iso()
    source_counts = _normalized_source_counts(source_manifest.get("counts", {}))
    warnings = _dirty_source_warnings(source_counts)
    if warnings and not allow_dirty_source:
        warnings.append("source_manifest has dirty source state; registration allowed with warning")

    source_hash = compute_source_manifest_hash(workspace)
    record = {
        "library_version_id": library_version_id
        or _library_version_id(registered_at, library_summary["library_path"], source_hash, library_summary["library_files"]),
        "registered_at": registered_at,
        "office2md_version": _office2md_version(),
        "workspace_path": str(workspace),
        "library_path": library_summary["library_path"],
        "label": label,
        "notes": notes,
        "source_manifest_hash": source_hash,
        "source_counts": source_counts,
        "source_dirty": bool(warnings),
        "library_files": library_summary["library_files"],
        "library_metrics": library_summary["library_metrics"],
        "warnings": warnings,
    }
    next_manifest = {
        "schema_version": str(library_versions.get("schema_version") or WORKSPACE_SCHEMA_VERSION),
        "library_versions": [*library_versions.get("library_versions", []), record],
    }
    if not dry_run:
        write_library_versions(workspace, next_manifest)
    return {
        "workspace_path": str(workspace),
        "library_path": library_summary["library_path"],
        "dry_run": dry_run,
        "record": record,
        "versions_count": len(next_manifest["library_versions"]),
        "warnings": warnings,
        "manifest": next_manifest,
    }


def summarize_library_for_version(library_path: Path) -> dict[str, Any]:
    library_dir, db_path = _resolve_library_paths(library_path)
    report = library_report(db_path)
    return {
        "library_path": str(library_dir),
        "library_files": {
            "library_db": _version_file_record(db_path),
            "library_index": _version_file_record(library_dir / "library_index.json"),
            "library_graph": _version_file_record(library_dir / "library_graph.json"),
        },
        "library_metrics": {
            "documents_count": int(report.get("documents_count") or 0),
            "chunks_count": int(report.get("chunks_count") or 0),
            "entities_count": int(report.get("entities_count") or 0),
            "chunks_without_locator": int(report.get("chunks_without_locator") or 0),
            "noisy_chunks_count": int(report.get("noisy_chunks_count") or 0),
            "low_quality_documents": len(report.get("low_quality_documents") or []),
            "page_level_pdf_documents": len(report.get("page_level_pdf_documents") or []),
        },
    }


def register_output_version(
    workspace_path: Path,
    output_path: Path,
    *,
    dry_run: bool = False,
    label: str | None = None,
    notes: str | None = None,
    output_type: str = "auto",
    library_version_id: str | None = None,
    output_version_id: str | None = None,
    allow_missing_library_version: bool = False,
) -> dict[str, Any]:
    workspace = workspace_path.expanduser().resolve()
    if not detect_workspace(workspace):
        raise ValueError(f"Not an office2md workspace: {workspace}. Run workspace-init first.")

    output = output_path.expanduser().resolve()
    if not output.exists():
        raise FileNotFoundError(f"Output path does not exist: {output}")

    library_versions = load_library_versions(workspace)
    selected_library, library_warnings = _resolve_library_version_for_output(
        library_versions.get("library_versions", []),
        library_version_id=library_version_id,
        allow_missing_library_version=allow_missing_library_version,
    )
    output_versions = load_output_versions(workspace)
    registered_at = utc_now_iso()
    output_summary = summarize_output_for_version(output, output_type=output_type)
    source_counts = _normalized_source_counts((selected_library or {}).get("source_counts", {}))
    source_manifest_hash = (selected_library or {}).get("source_manifest_hash")
    warnings = [*library_warnings, *output_summary["warnings"]]
    record = {
        "output_version_id": output_version_id
        or _output_version_id(registered_at, str(output), output_summary["output_files"], selected_library),
        "registered_at": registered_at,
        "office2md_version": _office2md_version(),
        "workspace_path": str(workspace),
        "output_path": str(output),
        "output_type": output_summary["output_type"],
        "label": label,
        "notes": notes,
        "library_version_id": (selected_library or {}).get("library_version_id"),
        "source_manifest_hash": source_manifest_hash,
        "source_counts": source_counts,
        "output_files": output_summary["output_files"],
        "export_manifest": output_summary["export_manifest"],
        "warnings": warnings,
    }
    next_manifest = {
        "schema_version": str(output_versions.get("schema_version") or WORKSPACE_SCHEMA_VERSION),
        "output_versions": [*output_versions.get("output_versions", []), record],
    }
    if not dry_run:
        write_output_versions(workspace, next_manifest)
    return {
        "workspace_path": str(workspace),
        "output_path": str(output),
        "dry_run": dry_run,
        "record": record,
        "versions_count": len(next_manifest["output_versions"]),
        "warnings": warnings,
        "manifest": next_manifest,
    }


def summarize_output_for_version(output_path: Path, *, output_type: str = "auto") -> dict[str, Any]:
    output = output_path.expanduser().resolve()
    detected_type = detect_output_type(output) if output_type == "auto" else output_type
    export_manifest = parse_obsidian_export_manifest(output) if output.is_dir() else None
    return {
        "output_type": detected_type,
        "output_files": _folder_output_record(output) if output.is_dir() else _file_output_record(output),
        "export_manifest": export_manifest,
        "warnings": [],
    }


def compute_folder_sha256(path: Path) -> str:
    folder = path.expanduser().resolve()
    digest = hashlib.sha256()
    for file_path in _folder_files(folder):
        relative = file_path.relative_to(folder).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(compute_file_sha256(file_path).encode("utf-8"))
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def detect_output_type(output_path: Path) -> str:
    output = output_path.expanduser().resolve()
    if output.is_dir() and (output / "00_Index.md").exists() and (output / "_office2md" / "export_manifest.json").exists():
        return "obsidian_vault"
    if output.is_file() and output.suffix.lower() in {".md", ".html", ".htm", ".pdf", ".docx"}:
        return "report"
    return "generic_output"


def parse_obsidian_export_manifest(output_path: Path) -> dict[str, Any] | None:
    manifest_path = output_path.expanduser().resolve() / "_office2md" / "export_manifest.json"
    data = _read_json_if_possible(manifest_path)
    if data is None:
        return None
    return {
        "path": str(manifest_path),
        "export_type": data.get("export_type"),
        "documents_exported": data.get("documents_exported"),
        "concepts_exported": data.get("concepts_exported"),
        "warnings": data.get("warnings") or [],
    }


def scan_workspace_sources(
    workspace_path: Path,
    source_path: Path,
    *,
    dry_run: bool = False,
    include_hidden: bool = False,
    hash_files: bool = True,
    max_files: int | None = None,
    relative_paths: bool = True,
) -> dict[str, Any]:
    workspace = workspace_path.expanduser().resolve()
    source_root = source_path.expanduser().resolve()
    if not detect_workspace(workspace):
        raise ValueError(f"Not an office2md workspace: {workspace}. Run workspace-init first.")
    if not source_root.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_root}")

    previous = load_source_manifest(workspace)
    discovered = scan_input(source_root, recursive=True)
    if not include_hidden:
        discovered = [path for path in discovered if not _has_hidden_relative_part(path, source_root)]
    selected = discovered[: max(0, max_files)] if max_files is not None else discovered
    scan_limited = max_files is not None and len(selected) < len(discovered)
    scanned_at = utc_now_iso()
    next_manifest = diff_source_manifest(
        previous,
        source_root,
        selected,
        scanned_at=scanned_at,
        include_hidden=include_hidden,
        hash_files=hash_files,
        relative_paths=relative_paths,
        scan_limited=scan_limited,
        max_files=max_files,
    )
    if not dry_run:
        write_source_manifest(workspace, next_manifest)
    return {
        "workspace_path": str(workspace),
        "source_path": str(source_root),
        "dry_run": dry_run,
        "include_hidden": include_hidden,
        "hash": hash_files,
        "relative_paths": relative_paths,
        "max_files": max_files,
        "scan_limited": scan_limited,
        "discovered_files": len(discovered),
        "scanned_files": len(selected),
        "counts": next_manifest["counts"],
        "manifest": next_manifest,
    }


def diff_source_manifest(
    previous: dict[str, Any],
    source_root: Path,
    files: list[Path],
    *,
    scanned_at: str,
    include_hidden: bool,
    hash_files: bool,
    relative_paths: bool,
    scan_limited: bool,
    max_files: int | None,
) -> dict[str, Any]:
    root_text = str(source_root)
    previous_sources = [dict(item) for item in previous.get("sources", []) if isinstance(item, dict)]
    previous_by_id = {str(item.get("source_id")): item for item in previous_sources if item.get("source_id")}
    updated_by_id = dict(previous_by_id)
    seen_ids: set[str] = set()

    for file_path in files:
        source_id = _source_id(source_root, file_path)
        previous_item = previous_by_id.get(source_id)
        next_item = _source_record(
            source_root,
            file_path,
            scanned_at=scanned_at,
            hash_files=hash_files,
            relative_paths=relative_paths,
        )
        if previous_item is None:
            next_item["status"] = "new"
            next_item["previous_status"] = None
            next_item["changed"] = False
        else:
            changed = _source_record_changed(previous_item, next_item)
            next_item["status"] = "changed" if changed else "active"
            next_item["previous_status"] = previous_item.get("status")
            next_item["changed"] = changed
        updated_by_id[source_id] = next_item
        seen_ids.add(source_id)

    if not scan_limited:
        for source_id, item in previous_by_id.items():
            if item.get("source_root") != root_text or source_id in seen_ids:
                continue
            missing_item = dict(item)
            missing_item["previous_status"] = item.get("status")
            missing_item["status"] = "missing"
            missing_item["changed"] = False
            missing_item["scanned_at"] = scanned_at
            updated_by_id[source_id] = missing_item

    sources = sorted(updated_by_id.values(), key=lambda item: (str(item.get("source_root", "")).lower(), str(item.get("relative_path", "")).lower()))
    source_roots = _update_source_roots(
        previous.get("source_roots", []),
        source_root,
        scanned_at=scanned_at,
        include_hidden=include_hidden,
        hash_files=hash_files,
        relative_paths=relative_paths,
        scan_limited=scan_limited,
        max_files=max_files,
    )
    counts = _source_counts(sources)
    return {
        "schema_version": str(previous.get("schema_version") or WORKSPACE_SCHEMA_VERSION),
        "generated_at": scanned_at,
        "source_roots": source_roots,
        "sources": sources,
        "counts": counts,
        "last_scan": {
            "source_root": root_text,
            "scanned_at": scanned_at,
            "include_hidden": include_hidden,
            "hash": hash_files,
            "relative_paths": relative_paths,
            "scan_limited": scan_limited,
            "max_files": max_files,
        },
    }


def _workspace_manifest(workspace: Path, now: str, existing: dict[str, Any] | None) -> dict[str, Any]:
    data = dict(existing or {})
    data.setdefault("schema_version", WORKSPACE_SCHEMA_VERSION)
    data.setdefault("office2md_version", _office2md_version())
    data.setdefault("workspace_path", str(workspace))
    data.setdefault("created_at", now)
    data["updated_at"] = now
    data.setdefault(
        "layers",
        {
            "ram": ["conversion", "library"],
            "wiki": ["wiki"],
            "output": ["outputs"],
            "versions": ["versions"],
        },
    )
    data.setdefault(
        "folders",
        {
            "conversion": "conversion",
            "library": "library",
            "wiki": "wiki",
            "outputs": "outputs",
            "logs": "logs",
            "versions": "versions",
        },
    )
    return data


def _source_manifest(now: str) -> dict[str, Any]:
    return {
        "schema_version": WORKSPACE_SCHEMA_VERSION,
        "source_roots": [],
        "sources": [],
        "counts": {
            "total_sources": 0,
            "active_sources": 0,
            "new_sources": 0,
            "changed_sources": 0,
            "missing_sources": 0,
        },
        "generated_at": now,
    }


def _library_versions_manifest() -> dict[str, Any]:
    return {
        "schema_version": WORKSPACE_SCHEMA_VERSION,
        "library_versions": [],
    }


def _output_versions_manifest() -> dict[str, Any]:
    return {
        "schema_version": WORKSPACE_SCHEMA_VERSION,
        "output_versions": [],
    }


def _office2md_version() -> str:
    try:
        return version("office2md")
    except PackageNotFoundError:
        return "unknown"


def _read_json_if_possible(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _has_hidden_relative_part(path: Path, source_root: Path) -> bool:
    try:
        relative_parts = path.relative_to(source_root).parts
    except ValueError:
        return False
    return any(part.startswith(".") for part in relative_parts)


def _source_record(source_root: Path, file_path: Path, *, scanned_at: str, hash_files: bool, relative_paths: bool) -> dict[str, Any]:
    stat = file_path.stat()
    return {
        "source_id": _source_id(source_root, file_path),
        "source_root": str(source_root),
        "absolute_path": str(file_path),
        "relative_path": file_path.relative_to(source_root).as_posix() if relative_paths else None,
        "file_name": file_path.name,
        "extension": file_path.suffix.lower(),
        "size_bytes": stat.st_size,
        "modified_time": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "sha256": compute_file_sha256(file_path) if hash_files else None,
        "status": "active",
        "scanned_at": scanned_at,
    }


def _source_id(source_root: Path, file_path: Path) -> str:
    identity = f"{source_root}|{file_path.relative_to(source_root).as_posix()}".lower()
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def _source_record_changed(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    return any(
        previous.get(key) != current.get(key)
        for key in ("size_bytes", "modified_time", "sha256")
    )


def _update_source_roots(
    existing_roots: list[Any],
    source_root: Path,
    *,
    scanned_at: str,
    include_hidden: bool,
    hash_files: bool,
    relative_paths: bool,
    scan_limited: bool,
    max_files: int | None,
) -> list[dict[str, Any]]:
    root_text = str(source_root)
    normalized: list[dict[str, Any]] = []
    replaced = False
    for item in existing_roots:
        if isinstance(item, str):
            item = {"path": item}
        if not isinstance(item, dict):
            continue
        if item.get("path") == root_text:
            normalized.append(
                {
                    **item,
                    "path": root_text,
                    "last_scanned_at": scanned_at,
                    "include_hidden": include_hidden,
                    "hash": hash_files,
                    "relative_paths": relative_paths,
                    "scan_limited": scan_limited,
                    "max_files": max_files,
                }
            )
            replaced = True
        else:
            normalized.append(dict(item))
    if not replaced:
        normalized.append(
            {
                "path": root_text,
                "last_scanned_at": scanned_at,
                "include_hidden": include_hidden,
                "hash": hash_files,
                "relative_paths": relative_paths,
                "scan_limited": scan_limited,
                "max_files": max_files,
            }
        )
    return sorted(normalized, key=lambda item: str(item.get("path", "")).lower())


def _source_counts(sources: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total_sources": len(sources),
        "active_sources": sum(1 for item in sources if item.get("status") != "missing"),
        "new_sources": sum(1 for item in sources if item.get("status") == "new"),
        "changed_sources": sum(1 for item in sources if item.get("status") == "changed"),
        "missing_sources": sum(1 for item in sources if item.get("status") == "missing"),
    }


def _resolve_library_paths(library_path: Path) -> tuple[Path, Path]:
    candidate = library_path.expanduser().resolve()
    db_path = candidate if candidate.name == "library.db" else candidate / "library.db"
    library_dir = db_path.parent
    if not db_path.exists():
        raise FileNotFoundError(f"Built library not found: {candidate}. Expected a library folder or library.db path.")
    return library_dir, db_path


def _version_file_record(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "sha256": compute_file_sha256(resolved),
    }


def _normalized_source_counts(counts: dict[str, Any]) -> dict[str, int]:
    return {
        "total_sources": int(counts.get("total_sources") or 0),
        "active_sources": int(counts.get("active_sources") or 0),
        "new_sources": int(counts.get("new_sources") or 0),
        "changed_sources": int(counts.get("changed_sources") or 0),
        "missing_sources": int(counts.get("missing_sources") or 0),
    }


def _dirty_source_warnings(source_counts: dict[str, int]) -> list[str]:
    warnings = []
    if source_counts["changed_sources"]:
        warnings.append(f"source_manifest has {source_counts['changed_sources']} changed source file(s)")
    if source_counts["missing_sources"]:
        warnings.append(f"source_manifest has {source_counts['missing_sources']} missing source file(s)")
    return warnings


def _library_version_id(registered_at: str, library_path: str, source_hash: str, library_files: dict[str, Any]) -> str:
    db_hash = (library_files.get("library_db") or {}).get("sha256") or ""
    identity = f"{registered_at}|{library_path}|{source_hash}|{db_hash}"
    return "lib_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]


def _resolve_library_version_for_output(
    library_versions: list[Any],
    *,
    library_version_id: str | None,
    allow_missing_library_version: bool,
) -> tuple[dict[str, Any] | None, list[str]]:
    records = [item for item in library_versions if isinstance(item, dict)]
    if library_version_id:
        for record in records:
            if record.get("library_version_id") == library_version_id:
                return record, []
        raise ValueError(f"Library version id not found: {library_version_id}")
    if len(records) == 1:
        return records[0], []
    if len(records) > 1:
        latest = sorted(records, key=lambda item: str(item.get("registered_at") or ""))[-1]
        return latest, [f"multiple library versions found; using latest registered version {latest.get('library_version_id')}"]
    if allow_missing_library_version:
        return None, ["no library version registered; output version recorded without library linkage"]
    raise ValueError("No library version registered. Run workspace-register-library first or use --allow-missing-library-version.")


def _file_output_record(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "kind": "file",
        "file_count": 1,
        "total_size_bytes": stat.st_size,
        "sha256": compute_file_sha256(path),
        "folder_sha256": None,
        "recognized_files": _recognized_output_files(path),
    }


def _folder_output_record(path: Path) -> dict[str, Any]:
    files = _folder_files(path)
    return {
        "kind": "folder",
        "file_count": len(files),
        "total_size_bytes": sum(file_path.stat().st_size for file_path in files),
        "sha256": None,
        "folder_sha256": compute_folder_sha256(path),
        "recognized_files": _recognized_output_files(path),
    }


def _folder_files(path: Path) -> list[Path]:
    folder = path.expanduser().resolve()
    return sorted((item for item in folder.rglob("*") if item.is_file()), key=lambda item: item.relative_to(folder).as_posix().lower())


def _recognized_output_files(path: Path) -> list[str]:
    output = path.expanduser().resolve()
    if output.is_file():
        return [output.name] if detect_output_type(output) == "report" else []
    recognized = []
    for relative in ["00_Index.md", "00_Library_Report.md", "_office2md/export_manifest.json"]:
        if (output / relative).exists():
            recognized.append(relative)
    return recognized


def _output_version_id(registered_at: str, output_path: str, output_files: dict[str, Any], library_version: dict[str, Any] | None) -> str:
    output_hash = output_files.get("folder_sha256") or output_files.get("sha256") or ""
    identity = f"{registered_at}|{output_path}|{output_hash}|{(library_version or {}).get('library_version_id', '')}"
    return "out_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]


def _latest_version_record(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not records:
        return None
    return sorted(records, key=lambda item: str(item.get("registered_at") or ""))[-1]


def _recent_version_records(records: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return list(reversed(sorted(records, key=lambda item: str(item.get("registered_at") or ""))))[: max(0, limit)]


def _library_status_summary(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not record:
        return None
    metrics = record.get("library_metrics") or {}
    return {
        "library_version_id": record.get("library_version_id"),
        "registered_at": record.get("registered_at"),
        "label": record.get("label"),
        "source_manifest_hash": record.get("source_manifest_hash"),
        "metrics": {
            "documents_count": metrics.get("documents_count"),
            "chunks_count": metrics.get("chunks_count"),
            "entities_count": metrics.get("entities_count"),
            "chunks_without_locator": metrics.get("chunks_without_locator"),
        },
        "warnings": record.get("warnings") or [],
    }


def _output_status_summary(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not record:
        return None
    output_files = record.get("output_files") or {}
    export_manifest = record.get("export_manifest") or None
    return {
        "output_version_id": record.get("output_version_id"),
        "registered_at": record.get("registered_at"),
        "output_type": record.get("output_type"),
        "label": record.get("label"),
        "library_version_id": record.get("library_version_id"),
        "source_manifest_hash": record.get("source_manifest_hash"),
        "output_files": {
            "file_count": output_files.get("file_count"),
            "total_size_bytes": output_files.get("total_size_bytes"),
        },
        "export_manifest": export_manifest,
        "warnings": record.get("warnings") or [],
    }
