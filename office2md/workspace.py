import json
import hashlib
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from office2md.detector import sha256_file
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


def load_source_manifest(workspace_path: Path) -> dict[str, Any]:
    manifest_path = workspace_path.expanduser().resolve() / "source_manifest.json"
    return _read_json_if_possible(manifest_path) or _source_manifest(utc_now_iso())


def write_source_manifest(workspace_path: Path, manifest: dict[str, Any]) -> None:
    manifest_path = workspace_path.expanduser().resolve() / "source_manifest.json"
    _write_json(manifest_path, manifest)


def compute_file_sha256(path: Path) -> str:
    return sha256_file(path)


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
