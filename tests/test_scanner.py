from pathlib import Path

import pytest

from office2md.scanner import scan_input


def test_scan_input_filters_supported_files(tmp_path: Path):
    (tmp_path / "a.txt").write_text("ok", encoding="utf-8")
    (tmp_path / "b.exe").write_text("no", encoding="utf-8")
    (tmp_path / "~$temp.docx").write_text("no", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "c.pdf").write_text("ok", encoding="utf-8")

    files = scan_input(tmp_path, recursive=True)

    assert [path.name for path in files] == ["a.txt", "c.pdf"]


def test_scan_input_non_recursive(tmp_path: Path):
    (tmp_path / "a.txt").write_text("ok", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "c.pdf").write_text("ok", encoding="utf-8")

    files = scan_input(tmp_path, recursive=False)

    assert [path.name for path in files] == ["a.txt"]


def test_scan_input_missing_path(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        scan_input(tmp_path / "missing")

