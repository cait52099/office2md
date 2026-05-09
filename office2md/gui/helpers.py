import json
from pathlib import Path
from typing import Any

from office2md.cli import _search_export_json_payload
from office2md.library import library_report
from office2md.library import search_library, search_library_diagnostics, search_library_facets


def normalize_library_path(value: str) -> Path | None:
    text = (value or "").strip().strip('"')
    return Path(text).expanduser() if text else None


def is_valid_library_path(path: Path | None) -> bool:
    if path is None:
        return False
    if path.is_dir():
        return (path / "library.db").exists()
    return path.name == "library.db" and path.exists()


def load_library_report(path: Path) -> dict[str, Any]:
    return library_report(path)


def load_library_overview(path: Path) -> dict[str, Any]:
    return load_library_report(path)


def overview_metrics(report: dict[str, Any]) -> dict[str, int]:
    return {
        "documents_count": int(report.get("documents_count") or 0),
        "chunks_count": int(report.get("chunks_count") or 0),
        "entities_count": int(report.get("entities_count") or 0),
        "noisy_chunks_count": int(report.get("noisy_chunks_count") or 0),
        "chunks_without_locator": int(report.get("chunks_without_locator") or 0),
        "page_level_pdf_documents": len(report.get("page_level_pdf_documents") or []),
    }


def run_library_search(
    library_path: Path,
    query: str,
    limit: int = 5,
    diagnostics: bool = False,
    facets: bool = False,
    context: int = 0,
    output_dir: str | None = None,
    entity: str | None = None,
) -> dict[str, Any]:
    cleaned_query = query.strip()
    cleaned_output_dir = _clean_optional_text(output_dir)
    entities = [_clean_optional_text(entity)] if _clean_optional_text(entity) else []
    results = search_library(
        library_path,
        cleaned_query,
        limit=max(1, int(limit)),
        output_dir=cleaned_output_dir,
        entities=entities,
        related=max(0, int(context)),
    )
    diagnostic_data = search_library_diagnostics(
        cleaned_query,
        results,
        output_dir=cleaned_output_dir,
        entities=entities,
    )
    facet_data = (
        search_library_facets(
            library_path,
            cleaned_query,
            output_dir=cleaned_output_dir,
            entities=entities,
        )
        if facets
        else {}
    )
    return {
        "results": results,
        "rows": search_result_table_rows(results),
        "diagnostics": diagnostic_data if diagnostics else None,
        "facets": facet_data,
        "export_json": search_export_download_json(diagnostic_data, results),
    }


def search_result_table_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rank": item.get("rank"),
            "document_title": item.get("document_title"),
            "source_file": item.get("source_file"),
            "document_kind": item.get("document_kind"),
            "evidence_type": item.get("evidence_type"),
            "locator": item.get("locator"),
            "output_dir": item.get("output_dir"),
            "preview": item.get("preview"),
        }
        for item in results
    ]


def search_export_download_json(diagnostics: dict[str, Any], results: list[dict[str, Any]]) -> str:
    return json.dumps(_search_export_json_payload(diagnostics, results), ensure_ascii=False, indent=2) + "\n"


def _clean_optional_text(value: str | None) -> str | None:
    text = (value or "").strip()
    return text or None
