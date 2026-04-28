import json
from pathlib import Path

from office2md import cli
from office2md.models import ConvertOptions, ConvertResult


class FakeDrawingConverter:
    name = "markitdown"

    def convert(self, path: Path, options: ConvertOptions) -> ConvertResult:
        return ConvertResult(
            markdown="",
            raw_markdown="",
            engine="markitdown",
            metadata={"source": str(path)},
        )


def test_image_only_technical_drawing_metadata_and_entities(tmp_path, monkeypatch):
    source = tmp_path / "Piping and instrumentation diagram" / "ENG-179298 flowsheet rev d.pdf"
    source.parent.mkdir()
    source.write_text("%PDF", encoding="utf-8")
    output = tmp_path / "out"
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakeDrawingConverter())
    monkeypatch.setattr(cli, "render_pdf_pages", lambda path, assets_dir, max_pages: _image_only_pages(assets_dir))

    out_dir, status = cli.convert_one(
        source,
        output,
        ConvertOptions(engine="markitdown", render_pdf_pages=True, max_render_pages=1),
    )

    assert status == "success"
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    document_json = json.loads((out_dir / "document.json").read_text(encoding="utf-8"))
    knowledge = json.loads((out_dir / "knowledge.json").read_text(encoding="utf-8"))
    entities = json.loads((out_dir / "entities.json").read_text(encoding="utf-8"))
    chunk = json.loads((out_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()[0])
    source_map = json.loads((out_dir / "source_map.json").read_text(encoding="utf-8"))
    document = (out_dir / "document.md").read_text(encoding="utf-8")

    assert manifest["document_kind"] == "technical_drawing_pdf"
    assert manifest["extraction_status"] == "image_only"
    assert manifest["quality_status"] == "visual_only"
    assert manifest["requires_ocr_or_vision"] is True
    assert document_json["extraction_status"] == "image_only"
    assert knowledge["extraction_status"] == "image_only"
    assert knowledge["requires_ocr_or_vision"] is True
    assert "flowsheet" in knowledge["tags"]
    assert "piping-instrumentation-diagram" in knowledge["tags"]
    assert "mechanical-design" in knowledge["tags"]
    assert "visual-only" in knowledge["tags"]
    assert entities["drawing_number"] == ["ENG-179298"]
    assert chunk["evidence_type"] == "image"
    assert chunk["provenance_status"] == "page_image_only"
    assert knowledge["page_chunks_count"] == 1
    assert knowledge["image_only_chunks_count"] == 1
    assert knowledge["searchable_page_chunks_count"] == 0
    assert source_map[chunk["chunk_id"]]["evidence_type"] == "image"
    assert source_map[chunk["chunk_id"]]["provenance_status"] == "page_image_only"
    assert "- extraction_status: image_only" in document
    assert "- requires_ocr_or_vision: true" in document
    assert "- note: No text was extracted; page image preserved for visual review." in document


def _image_only_pages(assets_dir: Path):
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "page_001.png").write_bytes(b"fake")
    return [
        {
            "page_number": 1,
            "source_page": 1,
            "locator": "Page 1",
            "semantic_title": None,
            "image_path": "assets/page_001.png",
            "text": "",
            "text_char_count": 0,
        }
    ]
