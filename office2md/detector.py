import hashlib
from pathlib import Path


LEGACY_OFFICE_EXTENSIONS = {".doc", ".ppt", ".xls"}


def detect_file_type(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "unknown"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def is_legacy_office(path: Path) -> bool:
    return path.suffix.lower() in LEGACY_OFFICE_EXTENSIONS


def is_probably_scanned_pdf(path: Path) -> bool:
    return False

