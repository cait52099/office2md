from pathlib import Path
from typing import Any

from office2md.library import library_report


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
