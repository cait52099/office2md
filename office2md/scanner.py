from pathlib import Path
from typing import List


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".pptx",
    ".ppt",
    ".xlsx",
    ".xls",
    ".html",
    ".htm",
    ".txt",
    ".csv",
    ".json",
    ".md",
}


def is_supported_file(path: Path) -> bool:
    name = path.name
    if name.startswith(".") or name.startswith("~$"):
        return False
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def scan_input(input_path: Path, recursive: bool = True) -> List[Path]:
    path = input_path.expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Input path does not exist: {path}")

    if path.is_file():
        return [path] if is_supported_file(path) else []

    iterator = path.rglob("*") if recursive else path.iterdir()
    files = [item.resolve() for item in iterator if is_supported_file(item)]
    return sorted(files, key=lambda p: str(p).lower())

