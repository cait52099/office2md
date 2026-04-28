import importlib.metadata
import os
import platform
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Dict, Tuple


SAFE_ENV_VARS = [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "HF_HOME",
    "HUGGINGFACE_HUB_CACHE",
    "TRANSFORMERS_CACHE",
]


def diagnose_docling() -> Dict:
    result = {
        "python": f"{platform.python_version()} ({sys.executable})",
        "docling_import": "not checked",
        "docling_version": "unknown",
        "document_converter": "not checked",
        "fixture_conversion": "not checked",
        "environment": safe_environment(),
        "exception": None,
    }

    try:
        from docling.document_converter import DocumentConverter

        result["docling_import"] = "ok"
        result["docling_version"] = _package_version("docling")
    except Exception as exc:
        result["docling_import"] = "failed"
        result["exception"] = exception_summary(exc)
        return result

    try:
        converter = DocumentConverter()
        result["document_converter"] = "ok"
    except Exception as exc:
        result["document_converter"] = "failed"
        result["exception"] = exception_summary(exc)
        return result

    try:
        with tempfile.TemporaryDirectory(prefix="office2md_docling_") as temp_name:
            fixture = Path(temp_name) / "minimal.pdf"
            fixture.write_bytes(minimal_pdf_bytes())
            conversion = converter.convert(str(fixture))
            markdown = conversion.document.export_to_markdown()
            result["fixture_conversion"] = "ok"
            result["fixture_markdown_chars"] = len(markdown or "")
    except Exception as exc:
        result["fixture_conversion"] = "failed"
        result["exception"] = exception_summary(exc)
    return result


def warmup_docling() -> Tuple[bool, Dict]:
    result = diagnose_docling()
    ok = (
        result.get("docling_import") == "ok"
        and result.get("document_converter") == "ok"
        and result.get("fixture_conversion") == "ok"
    )
    return ok, result


def safe_environment() -> Dict[str, str]:
    values = {}
    for name in SAFE_ENV_VARS:
        value = os.environ.get(name)
        values[name] = value if value else ""
    return values


def exception_summary(exc: Exception) -> Dict[str, str]:
    tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    traceback_tail = "".join(tb_lines[-8:])
    return {
        "type": f"{exc.__class__.__module__}.{exc.__class__.__name__}",
        "message": str(exc),
        "traceback": traceback_tail,
    }


def minimal_pdf_bytes() -> bytes:
    return b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 44 >> stream
BT /F1 18 Tf 72 720 Td (Docling warmup) Tj ET
endstream endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000251 00000 n 
0000000345 00000 n 
trailer << /Root 1 0 R /Size 6 >>
startxref
415
%%EOF
"""


def _package_version(package: str) -> str:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"

