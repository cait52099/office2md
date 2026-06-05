import shutil
import subprocess
from pathlib import Path


def convert_legacy_office(path: Path, temp_dir: Path, *, timeout_seconds: int = 60) -> Path:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice/soffice not found")

    target_format = {
        ".doc": "docx",
        ".ppt": "pptx",
        ".xls": "xlsx",
    }[path.suffix.lower()]

    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        completed = subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                target_format,
                "--outdir",
                str(temp_dir),
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"LibreOffice/soffice legacy conversion timed out after {timeout_seconds} seconds") from exc

    converted = temp_dir / f"{path.stem}.{target_format}"
    if not converted.exists():
        raise RuntimeError(
            f"Converted file not found: {converted}. stdout={completed.stdout} stderr={completed.stderr}"
        )
    return converted
