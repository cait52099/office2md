from pathlib import Path
from typing import Dict, List

from office2md.detector import detect_file_type
from office2md.utils import utc_now_iso


def build_manifest(
    source_path: Path,
    checksum: str,
    engine: str,
    status: str,
    warnings: List[str],
    errors: List[str],
    fallback_used: bool = False,
    ocr_used: bool = False,
    quality_status: str = "ok",
    document_kind: str = "document",
    asset_count: int = 0,
    ai_used: bool = False,
    extraction_status: str = "text",
    requires_ocr_or_vision: bool = False,
    converted_at: str = "",
) -> Dict:
    return {
        "source_file": source_path.name,
        "source_path": str(source_path.resolve()),
        "checksum": checksum,
        "file_type": detect_file_type(source_path),
        "engine": engine,
        "fallback_used": fallback_used,
        "ocr_used": ocr_used,
        "quality_status": quality_status,
        "document_kind": document_kind,
        "asset_count": asset_count,
        "ai_used": ai_used,
        "extraction_status": extraction_status,
        "requires_ocr_or_vision": requires_ocr_or_vision,
        "converted_at": converted_at or utc_now_iso(),
        "status": status,
        "warnings": warnings,
        "errors": errors,
    }
