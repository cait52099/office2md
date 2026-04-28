import importlib.util
import platform
import shutil
import sys
from pathlib import Path
from typing import Dict


def run_checks(output_dir: Path = None) -> Dict[str, str]:
    checks = {
        "python": f"{platform.python_version()} ({sys.executable})",
        "docling": _module_status("docling"),
        "markitdown": _module_status("markitdown"),
        "marker": _module_status("marker"),
        "soffice": shutil.which("soffice") or shutil.which("libreoffice") or "not found",
        "poppler": shutil.which("pdftotext") or "not found",
        "tesseract": shutil.which("tesseract") or "not found",
    }
    if output_dir is not None:
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            probe = output_dir / ".office2md_write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            checks["output_writable"] = "ok"
        except OSError as exc:
            checks["output_writable"] = f"failed: {exc}"
    return checks


def _module_status(name: str) -> str:
    return "installed" if importlib.util.find_spec(name) else "not installed"

