import json
from pathlib import Path

from office2md import cli
from office2md.models import ConvertOptions, ConvertResult
from office2md.postprocess.pdf_structure import classify_document_kind, determine_quality_status


class FakePdfConverter:
    name = "markitdown"

    def convert(self, path: Path, options: ConvertOptions) -> ConvertResult:
        return ConvertResult(
            markdown="wire labels and terminal references",
            raw_markdown="wire labels and terminal references",
            engine="markitdown",
            metadata={"source": str(path), "fallback": "docling_to_markitdown"},
        )


def test_classify_technical_drawing_pdf_by_filename(tmp_path):
    path = tmp_path / "wiring_diagram.pdf"
    path.write_text("pdf", encoding="utf-8")

    assert classify_document_kind(path, "plain text") == "technical_drawing_pdf"


def test_pdf_fallback_without_headings_is_low_structure(tmp_path):
    path = tmp_path / "manual.pdf"
    path.write_text("pdf", encoding="utf-8")

    assert determine_quality_status(path, "plain text", True, {"pages": [], "elements": []}) == "low_structure"


def test_technical_drawing_pdf_writes_page_assets_json_and_page_chunks(tmp_path, monkeypatch):
    source = tmp_path / "wiring_diagram.pdf"
    source.write_text("%PDF sample", encoding="utf-8")
    output = tmp_path / "out"

    monkeypatch.setattr(cli, "get_converter", lambda engine: FakePdfConverter())
    monkeypatch.setattr(
        cli,
        "render_pdf_pages",
        lambda path, assets_dir, max_pages: _fake_render_pages(assets_dir),
    )

    out_dir, status = cli.convert_one(
        source,
        output,
        ConvertOptions(engine="markitdown", render_pdf_pages=True, max_render_pages=1),
    )

    assert status == "success"
    document = (out_dir / "document.md").read_text(encoding="utf-8")
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    document_json = json.loads((out_dir / "document.json").read_text(encoding="utf-8"))
    chunks = (out_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()

    assert "# wiring_diagram" in document
    assert "## Document Classification" in document
    assert "## Page Index" in document
    assert "## Terminal Diagram" in document
    assert "Source page: 1" in document
    assert "![Page 1](assets/page_001.png)" in document
    assert "### Extracted Text" in document
    assert manifest["document_kind"] == "technical_drawing_pdf"
    assert manifest["quality_status"] == "visual_only"
    assert manifest["fallback_used"] is True
    assert document_json["pages"][0]["image_path"] == "assets/page_001.png"
    assert json.loads(chunks[0])["image_path"] == "assets/page_001.png"
    assert json.loads(chunks[0])["heading_path"] == ["Terminal Diagram"]
    assert json.loads(chunks[0])["locator"] == "Page 1"
    assert json.loads(chunks[0])["semantic_title"] == "Terminal Diagram"


def _fake_render_pages(assets_dir: Path):
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "page_001.png").write_bytes(b"fake")
    return [{"page_number": 1, "image_path": "assets/page_001.png", "width": 100, "height": 100}]
