import json
from pathlib import Path
from typing import Any

from office2md.utils import utc_now_iso


LIBRARY_CATALOG_SCHEMA_VERSION = "office2md.library_catalog.v1"


def load_library_catalog(catalog_path: Path) -> dict[str, Any]:
    path = catalog_path.expanduser().resolve()
    if not path.exists():
        return _empty_catalog(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("schema_version", LIBRARY_CATALOG_SCHEMA_VERSION)
    data.setdefault("libraries", [])
    return data


def write_library_catalog(catalog_path: Path, catalog: dict[str, Any]) -> None:
    target = catalog_path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def add_library_to_catalog(
    catalog_path: Path,
    *,
    library_path: Path,
    library_id: str,
    library_name: str | None = None,
    source_root: Path | None = None,
) -> dict[str, Any]:
    catalog = load_library_catalog(catalog_path)
    now = utc_now_iso()
    record = {
        "library_id": library_id,
        "library_name": library_name or library_id,
        "library_path": str(library_path.expanduser().resolve()),
        "source_root": str(source_root.expanduser().resolve()) if source_root else None,
        "registered_at": now,
        "metadata": {
            "agent_evidence_fields": [
                "library_id",
                "library_name",
                "library_path",
                "source_file",
                "locator",
                "chunk_id",
                "document_id",
            ]
        },
    }
    libraries = [item for item in catalog.get("libraries", []) if item.get("library_id") != library_id]
    libraries.append(record)
    catalog["schema_version"] = LIBRARY_CATALOG_SCHEMA_VERSION
    catalog["updated_at"] = now
    catalog["catalog_path"] = str(catalog_path.expanduser().resolve())
    catalog["libraries"] = sorted(libraries, key=lambda item: str(item.get("library_id") or ""))
    write_library_catalog(catalog_path, catalog)
    return catalog


def list_library_catalog(catalog_path: Path) -> dict[str, Any]:
    catalog = load_library_catalog(catalog_path)
    return {
        "schema_version": catalog.get("schema_version", LIBRARY_CATALOG_SCHEMA_VERSION),
        "generated_at": utc_now_iso(),
        "catalog_path": str(catalog_path.expanduser().resolve()),
        "libraries_count": len(catalog.get("libraries", [])),
        "libraries": catalog.get("libraries", []),
        "limitations": [
            "library catalog is an additive registry for agent routing",
            "multi-library search/report execution is a future feature",
            "future MCP adapters should wrap these read-only contracts and must not expose unrestricted SQL",
        ],
    }


def _empty_catalog(path: Path) -> dict[str, Any]:
    return {
        "schema_version": LIBRARY_CATALOG_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "updated_at": None,
        "catalog_path": str(path),
        "libraries": [],
    }
