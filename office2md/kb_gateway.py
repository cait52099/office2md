from pathlib import Path
from typing import Any

from office2md.incremental import library_status
from office2md.library import open_chunk, search_library
from office2md.library_catalog import list_library_catalog, load_library_catalog
from office2md.models import ConvertOptions
from office2md.update_library import update_library
from office2md.utils import utc_now_iso


AGENT_CONTEXT_SCHEMA_VERSION = "office2md.agent_context.v1"


def kb_list(catalog_path: Path) -> dict[str, Any]:
    return list_library_catalog(catalog_path)


def kb_context(
    catalog_path: Path,
    query: str,
    *,
    library_ids: list[str] | None = None,
    limit: int = 5,
    context: int = 1,
) -> dict[str, Any]:
    catalog = load_library_catalog(catalog_path)
    selected = _select_libraries(catalog, library_ids)
    warnings: list[str] = []
    next_steps: list[str] = []
    statuses = []
    evidence = []
    supporting_chunks = []

    for library in selected:
        library_path = Path(str(library["library_path"]))
        status = library_status(library_path)
        status_packet = {
            "library_id": library["library_id"],
            "library_name": library.get("library_name"),
            "library_path": str(library_path),
            "status": status.get("status"),
            "warnings": status.get("warnings", []),
            "pending_changes": status.get("pending_changes"),
        }
        statuses.append(status_packet)
        if status.get("status") == "stale":
            warnings.append(f"library {library['library_id']} may be stale")
            next_steps.append(f"Run kb-review or library-status for {library['library_id']} before relying on new source changes.")
        elif status.get("status") == "unknown":
            warnings.append(f"library {library['library_id']} freshness is unknown")

        results = search_library(library_path, query, limit=limit, related=max(context, 0))
        for item in results:
            opened = open_chunk(library_path, item["chunk_id"], context=max(context, 0)) or {}
            target = opened.get("target_chunk") or {}
            evidence.append(_evidence_packet(library, item, target))
            for related in opened.get("context_chunks", []):
                supporting_chunks.append(_supporting_packet(library, item, related))

    if not evidence:
        warnings.append("no evidence found")
        next_steps.append("Try a different query or select additional libraries.")

    return {
        "schema_version": AGENT_CONTEXT_SCHEMA_VERSION,
        "generated_at": utc_now_iso(),
        "request": {
            "catalog_path": str(catalog_path.expanduser().resolve()),
            "query": query,
            "library_ids": [item["library_id"] for item in selected],
            "limit": limit,
            "context": context,
        },
        "selected_libraries": [_library_selection_packet(item) for item in selected],
        "library_status": statuses,
        "evidence": evidence,
        "supporting_chunks": supporting_chunks,
        "limitations": [
            "office2md provides evidence/context only, not AI-generated final answers",
            "multi-library ranking is grouped by selected library and preserves existing per-library search behavior",
            "stale libraries are reported but never auto-updated",
        ],
        "warnings": _dedupe(warnings),
        "next_steps": _dedupe(next_steps),
    }


def kb_review(catalog_path: Path, library_id: str) -> dict[str, Any]:
    catalog = load_library_catalog(catalog_path)
    library = _library_by_id(catalog, library_id)
    library_path = Path(str(library["library_path"]))
    source_root = library.get("source_root")
    status = library_status(library_path)
    review = None
    warnings = list(status.get("warnings", []))
    next_steps = []
    if source_root:
        source_path = Path(str(source_root))
        if source_path.exists():
            review = update_library(
                source_path,
                library_path,
                library_path,
                convert_file=_unreachable_convert,
                dry_run=True,
                options=ConvertOptions(),
            )
            next_steps.extend(review.get("next_steps", []))
        else:
            warnings.append(f"source_root does not exist: {source_path}")
    else:
        warnings.append("catalog record has no source_root; update review is limited to library-status")
        next_steps.append("Register source_root in the library catalog to enable scan-based review.")
    return {
        "schema_version": "office2md.kb_review.v1",
        "generated_at": utc_now_iso(),
        "request": {
            "catalog_path": str(catalog_path.expanduser().resolve()),
            "library_id": library_id,
        },
        "library": _library_selection_packet(library),
        "library_status": status,
        "review_summary": None if review is None else review.get("review_summary"),
        "change_counts": None if review is None else review.get("change_counts"),
        "large_folder_warnings": [] if review is None else review.get("large_folder_warnings", []),
        "warnings": _dedupe(warnings + ([] if review is None else review.get("warnings", []))),
        "next_steps": _dedupe(next_steps),
        "limitations": [
            "kb-review is read-only and never runs update-library execution",
            "review uses source_root from the library catalog when available",
        ],
    }


def _select_libraries(catalog: dict[str, Any], library_ids: list[str] | None) -> list[dict[str, Any]]:
    libraries = [item for item in catalog.get("libraries", []) if isinstance(item, dict)]
    if not library_ids:
        return libraries
    selected = []
    missing = []
    by_id = {str(item.get("library_id")): item for item in libraries}
    for library_id in library_ids:
        item = by_id.get(library_id)
        if item is None:
            missing.append(library_id)
        else:
            selected.append(item)
    if missing:
        raise ValueError(f"Unknown library_id: {', '.join(missing)}")
    return selected


def _library_by_id(catalog: dict[str, Any], library_id: str) -> dict[str, Any]:
    matches = _select_libraries(catalog, [library_id])
    return matches[0]


def _library_selection_packet(library: dict[str, Any]) -> dict[str, Any]:
    return {
        "library_id": library.get("library_id"),
        "library_name": library.get("library_name"),
        "library_path": library.get("library_path"),
        "source_root": library.get("source_root"),
    }


def _evidence_packet(library: dict[str, Any], search_item: dict[str, Any], chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "library_id": library.get("library_id"),
        "library_name": library.get("library_name"),
        "library_path": library.get("library_path"),
        "rank": search_item.get("rank"),
        "source_file": chunk.get("source_file") or search_item.get("source_file"),
        "locator": chunk.get("locator") or search_item.get("locator"),
        "chunk_id": chunk.get("chunk_id") or search_item.get("chunk_id"),
        "document_id": chunk.get("document_id"),
        "document_title": chunk.get("document_title") or search_item.get("document_title"),
        "document_kind": chunk.get("document_kind") or search_item.get("document_kind"),
        "evidence_type": chunk.get("evidence_type") or search_item.get("evidence_type"),
        "confidence": chunk.get("confidence"),
        "limitation": chunk.get("limitation"),
        "preview": chunk.get("preview") or search_item.get("preview"),
        "text": chunk.get("text"),
    }


def _supporting_packet(library: dict[str, Any], search_item: dict[str, Any], chunk: dict[str, Any]) -> dict[str, Any]:
    packet = _evidence_packet(library, search_item, chunk)
    packet.pop("text", None)
    packet["for_chunk_id"] = search_item.get("chunk_id")
    return packet


def _unreachable_convert(source_path: Path, output_root: Path, options: ConvertOptions) -> tuple[Path, str]:
    raise RuntimeError("kb-review must not execute conversion")


def _dedupe(values: list[str]) -> list[str]:
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
