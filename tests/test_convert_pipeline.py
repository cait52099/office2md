import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from office2md import cli
from office2md.converters.libreoffice_converter import convert_legacy_office
from office2md.models import ConvertOptions, ConvertResult


class FakeConverter:
    def __init__(self, name, markdown="# Converted\n\nBody", error=None):
        self.name = name
        self.markdown = markdown
        self.error = error

    def convert(self, path: Path, options: ConvertOptions) -> ConvertResult:
        if self.error:
            raise self.error
        return ConvertResult(
            markdown=self.markdown,
            raw_markdown=self.markdown,
            engine=self.name,
            metadata={"source": str(path)},
        )


def test_auto_pdf_docling_failure_falls_back_to_markitdown(tmp_path, monkeypatch):
    source = tmp_path / "sample.pdf"
    source.write_text("%PDF sample", encoding="utf-8")
    output = tmp_path / "out"

    converters = {
        "docling": FakeConverter("docling", error=RuntimeError("docling unavailable")),
        "markitdown": FakeConverter("markitdown", "# PDF fallback\n\nText"),
    }
    monkeypatch.setattr(cli, "get_converter", lambda engine: converters[engine])

    out_dir, status = cli.convert_one(source, output, ConvertOptions(engine="auto"))

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert status == "success"
    assert manifest["engine"] == "markitdown"
    assert manifest["fallback_used"] is True
    assert manifest["errors"] == []
    assert any("docling failed; fell back to markitdown" in warning for warning in manifest["warnings"])


def test_batch_convert_continues_when_one_file_fails(tmp_path, monkeypatch):
    good = tmp_path / "good.txt"
    bad = tmp_path / "bad.txt"
    good_markdown = "# Good\n\n" + ("Body text. " * 8)
    good.write_text(good_markdown, encoding="utf-8")
    bad.write_text("# Bad\n\n" + ("Body text. " * 8), encoding="utf-8")
    output = tmp_path / "out"

    class SelectiveConverter:
        name = "markitdown"

        def convert(self, path: Path, options: ConvertOptions) -> ConvertResult:
            if path.name == "bad.txt":
                raise RuntimeError("planned failure")
            return ConvertResult(
                markdown=good_markdown,
                raw_markdown=good_markdown,
                engine="markitdown",
                metadata={"source": str(path)},
            )

    monkeypatch.setattr(cli, "get_converter", lambda engine: SelectiveConverter())
    runner = CliRunner()

    result = runner.invoke(cli.app, ["convert", str(tmp_path), str(output), "--recursive"])

    assert result.exit_code == 0
    assert "Success: 1" in result.output
    assert "Failed: 1" in result.output
    success_manifest = json.loads((output / "good" / "manifest.json").read_text(encoding="utf-8"))
    failed_manifest = json.loads((output / "bad" / "manifest.json").read_text(encoding="utf-8"))
    assert success_manifest["status"] == "success"
    assert success_manifest["fallback_used"] is False
    assert success_manifest["warnings"] == []
    assert success_manifest["errors"] == []
    assert failed_manifest["status"] == "failed"
    assert failed_manifest["fallback_used"] is False
    assert failed_manifest["warnings"] == []
    assert failed_manifest["errors"] == ["planned failure"]


def test_convert_file_failure_writes_manifest_and_exits_nonzero(tmp_path, monkeypatch):
    source = tmp_path / "bad.txt"
    source.write_text("# Bad\n\nBody text.", encoding="utf-8")
    output = tmp_path / "out"
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakeConverter("markitdown", error=RuntimeError("single failure")))
    runner = CliRunner()

    result = runner.invoke(cli.app, ["convert-file", str(source), str(output), "--engine", "markitdown"])

    assert result.exit_code == 1
    assert "failed:" in result.output
    manifest = json.loads((output / "bad" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "failed"
    assert manifest["errors"] == ["single failure"]
    assert (output / "_index.json").exists()


def test_legacy_office_preprocess_failure_uses_failure_manifest(tmp_path, monkeypatch):
    source = tmp_path / "legacy.doc"
    source.write_bytes(b"legacy office bytes")
    output = tmp_path / "out"
    monkeypatch.setattr(cli, "convert_legacy_office", lambda path, temp_dir: (_ for _ in ()).throw(RuntimeError("soffice unavailable")))
    monkeypatch.setattr(cli, "get_converter", lambda engine: (_ for _ in ()).throw(AssertionError("converter should not receive raw legacy file")))
    runner = CliRunner()

    result = runner.invoke(cli.app, ["convert-file", str(source), str(output), "--engine", "markitdown"])

    assert result.exit_code == 1
    assert "legacy Office preprocessing failed" in result.output
    manifest = json.loads((output / "legacy" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "failed"
    assert "legacy Office preprocessing failed" in manifest["errors"][0]
    assert "Convert the source to docx/pptx/xlsx" in manifest["errors"][0]


def test_legacy_office_preprocess_timeout_has_clear_error(tmp_path, monkeypatch):
    source = tmp_path / "legacy.doc"
    source.write_bytes(b"legacy office bytes")
    monkeypatch.setattr("office2md.converters.libreoffice_converter.shutil.which", lambda name: "/usr/bin/soffice")

    def timeout_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr("office2md.converters.libreoffice_converter.subprocess.run", timeout_run)

    try:
        convert_legacy_office(source, tmp_path / "temp", timeout_seconds=2)
    except RuntimeError as exc:
        assert "timed out after 2 seconds" in str(exc)
    else:
        raise AssertionError("expected legacy conversion timeout")


def test_skip_existing_reuses_successful_same_checksum_output(tmp_path, monkeypatch):
    source = tmp_path / "repeat.txt"
    source.write_text("# Repeat\n\nBody", encoding="utf-8")
    output = tmp_path / "out"
    converter = FakeConverter("markitdown", "# Repeat\n\nBody")
    monkeypatch.setattr(cli, "get_converter", lambda engine: converter)

    first_dir, first_status = cli.convert_one(source, output, ConvertOptions(engine="markitdown"))
    marker = first_dir / "keep.txt"
    marker.write_text("do not remove", encoding="utf-8")
    second_dir, second_status = cli.convert_one(
        source,
        output,
        ConvertOptions(engine="markitdown", skip_existing=True),
    )

    assert first_status == "success"
    assert second_status == "skipped"
    assert first_dir == second_dir
    assert marker.read_text(encoding="utf-8") == "do not remove"


def test_same_name_different_files_use_checksum_directory(tmp_path, monkeypatch):
    input_a = tmp_path / "a"
    input_b = tmp_path / "b"
    input_a.mkdir()
    input_b.mkdir()
    first = input_a / "same.txt"
    second = input_b / "same.txt"
    first.write_text("# First\n\nBody", encoding="utf-8")
    second.write_text("# Second\n\nBody", encoding="utf-8")
    output = tmp_path / "out"
    converter = FakeConverter("markitdown")
    monkeypatch.setattr(cli, "get_converter", lambda engine: converter)

    first_dir, _ = cli.convert_one(first, output, ConvertOptions(engine="markitdown"))
    second_dir, _ = cli.convert_one(second, output, ConvertOptions(engine="markitdown"))

    assert first_dir.name == "same"
    assert second_dir.name.startswith("same-")
    assert first_dir != second_dir
