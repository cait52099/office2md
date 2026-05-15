import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

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
