import json
import sys
from pathlib import Path

from typer.testing import CliRunner

from office2md import cli
from office2md.ai.cli_adapter import CliAIAdapter
from office2md.models import ConvertOptions, ConvertResult


class FakePdfConverter:
    name = "markitdown"

    def convert(self, path: Path, options: ConvertOptions) -> ConvertResult:
        return ConvertResult(
            markdown="Symex CML125 wiring diagram with PLC terminal valve motor pump control panel.",
            raw_markdown="Symex CML125 wiring diagram with PLC terminal valve motor pump control panel.",
            engine="markitdown",
            metadata={"source": str(path), "fallback": "docling_to_markitdown"},
        )


def test_profile_kb_uses_standard_markdown_image_link(tmp_path, monkeypatch):
    out_dir = _convert_wiring_pdf(tmp_path, monkeypatch, profile="kb")
    document = (out_dir / "document.md").read_text(encoding="utf-8")

    assert "![Page 1](assets/page_001.png)" in document
    assert "![[assets/page_001.png]]" not in document
    assert "## Source Traceability" in document


def test_profile_obsidian_uses_wiki_image_link(tmp_path, monkeypatch):
    out_dir = _convert_wiring_pdf(tmp_path, monkeypatch, profile="obsidian")
    document = (out_dir / "document.md").read_text(encoding="utf-8")

    assert "![[assets/page_001.png]]" in document


def test_knowledge_source_map_chunks_and_entities_are_generated(tmp_path, monkeypatch):
    out_dir = _convert_wiring_pdf(tmp_path, monkeypatch)

    knowledge = json.loads((out_dir / "knowledge.json").read_text(encoding="utf-8"))
    source_map = json.loads((out_dir / "source_map.json").read_text(encoding="utf-8"))
    entities = json.loads((out_dir / "entities.json").read_text(encoding="utf-8"))
    chunk = json.loads((out_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()[0])

    assert knowledge["document_kind"] == "technical_drawing_pdf"
    assert knowledge["assets_count"] == 1
    assert source_map[chunk["chunk_id"]]["image_path"] == "assets/page_001.png"
    assert chunk["doc_id"]
    assert chunk["page_number"] == 1
    assert chunk["image_path"] == "assets/page_001.png"
    assert chunk["evidence_type"] == "page"
    assert chunk["locator"] == "Page 1"
    assert chunk["heading_path"] != ["Page 1"]
    assert chunk["heading_path"] == [chunk["semantic_title"]]
    assert "cml125" in chunk["tags"]
    assert entities["organization"] == ["Symex"]
    assert entities["line"] == ["CML125"]
    assert entities["document_type"] == ["wiring diagram"]
    assert "terminal" in entities["equipment"]
    assert source_map[chunk["chunk_id"]]["locator"] == "Page 1"
    assert source_map[chunk["chunk_id"]]["heading_path"] == [chunk["semantic_title"]]


def test_convert_file_generates_root_index(tmp_path, monkeypatch):
    source = tmp_path / "Symex_CML125_wiring_diagram.pdf"
    source.write_text("%PDF", encoding="utf-8")
    output = tmp_path / "out"
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakePdfConverter())
    monkeypatch.setattr(cli, "render_pdf_pages", lambda path, assets_dir, max_pages: _fake_render_pages(assets_dir))
    runner = CliRunner()

    result = runner.invoke(
        cli.app,
        [
            "convert-file",
            str(source),
            str(output),
            "--engine",
            "markitdown",
            "--render-pdf-pages",
            "--max-render-pages",
            "1",
        ],
    )

    assert result.exit_code == 0
    assert (output / "_index.md").exists()
    index_json = json.loads((output / "_index.json").read_text(encoding="utf-8"))
    assert index_json["documents"][0]["document_kind"] == "technical_drawing_pdf"


def test_use_ai_default_off_does_not_create_ai_notes(tmp_path, monkeypatch):
    out_dir = _convert_wiring_pdf(tmp_path, monkeypatch)

    assert not (out_dir / "ai_notes.md").exists()
    knowledge = json.loads((out_dir / "knowledge.json").read_text(encoding="utf-8"))
    assert "ai" not in knowledge


def test_ai_adapter_failure_does_not_block_and_writes_warning(tmp_path, monkeypatch):
    out_dir = _convert_wiring_pdf(
        tmp_path,
        monkeypatch,
        options=ConvertOptions(
            engine="markitdown",
            render_pdf_pages=True,
            use_ai=True,
            ai_backend="http",
        ),
    )

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "success"
    assert manifest["ai_used"] is False
    assert any("http ai adapter" in warning for warning in manifest["warnings"])


def test_ai_cli_success_writes_ai_outputs_and_manifest_flag(tmp_path, monkeypatch):
    command = f'"{sys.executable}" "{Path("examples/ai_cli_echo.py").resolve()}"'
    out_dir = _convert_wiring_pdf(
        tmp_path,
        monkeypatch,
        options=ConvertOptions(
            engine="markitdown",
            render_pdf_pages=True,
            use_ai=True,
            ai_backend="cli",
            ai_command=command,
        ),
    )

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    knowledge = json.loads((out_dir / "knowledge.json").read_text(encoding="utf-8"))
    document = (out_dir / "document.md").read_text(encoding="utf-8")

    assert manifest["ai_used"] is True
    assert (out_dir / "ai_notes.md").exists()
    assert "## AI Notes" in document
    assert "## AI Summary" in document
    assert "ai" in knowledge


def test_cli_adapter_reads_stdout():
    command = f'"{sys.executable}" -c "import sys; data=sys.stdin.read(); print(\'ok:\' + data[:5])"'
    adapter = CliAIAdapter(command)

    response = adapter.complete(type("Req", (), {"prompt": "abcdef", "model": None})())

    assert response.warnings == []
    assert response.text == "ok:abcde"


def _convert_wiring_pdf(tmp_path, monkeypatch, profile="kb", options=None):
    source = tmp_path / "Symex_CML125_wiring_diagram.pdf"
    source.write_text("%PDF", encoding="utf-8")
    output = tmp_path / f"out_{profile}"
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakePdfConverter())
    monkeypatch.setattr(cli, "render_pdf_pages", lambda path, assets_dir, max_pages: _fake_render_pages(assets_dir))
    convert_options = options or ConvertOptions(engine="markitdown", profile=profile, render_pdf_pages=True)
    out_dir, status = cli.convert_one(source, output, convert_options)
    assert status == "success"
    return out_dir


def _fake_render_pages(assets_dir: Path):
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "page_001.png").write_bytes(b"fake")
    return [{"page_number": 1, "image_path": "assets/page_001.png", "width": 100, "height": 100}]
