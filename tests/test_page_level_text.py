import json
from pathlib import Path

from office2md import cli
from office2md.models import ConvertOptions, ConvertResult
from office2md.postprocess.pdf_structure import enrich_page_semantics


class FakePdfConverter:
    name = "markitdown"

    def convert(self, path: Path, options: ConvertOptions) -> ConvertResult:
        return ConvertResult(
            markdown="Document-level cover sheet text.",
            raw_markdown="Document-level cover sheet text.",
            engine="markitdown",
            metadata={"source": str(path), "fallback": "docling_to_markitdown"},
        )


def test_page_level_text_semantic_titles_are_per_page():
    pages = [
        {"page_number": 1, "image_path": "assets/page_001.png", "text": "Cover Sheet"},
        {"page_number": 2, "image_path": "assets/page_002.png", "text": "Table of Contents"},
        {"page_number": 3, "image_path": "assets/page_003.png", "text": "Revision Overview"},
    ]

    enriched = enrich_page_semantics(pages)

    assert enriched[0]["semantic_title"] == "Cover Sheet"
    assert enriched[1]["semantic_title"] == "Table of Contents"
    assert enriched[2]["semantic_title"] == "Revision Overview"


def test_page_text_written_to_document_json_chunks_and_source_map(tmp_path, monkeypatch):
    source = tmp_path / "SY909735_ENG-186350_Wiring diagram.pdf"
    source.write_text("%PDF", encoding="utf-8")
    output = tmp_path / "out"
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakePdfConverter())
    monkeypatch.setattr(cli, "render_pdf_pages", lambda path, assets_dir, max_pages: _fake_pages(assets_dir))

    out_dir, status = cli.convert_one(
        source,
        output,
        ConvertOptions(engine="markitdown", render_pdf_pages=True, max_render_pages=3),
    )

    assert status == "success"
    document_json = json.loads((out_dir / "document.json").read_text(encoding="utf-8"))
    chunks = [json.loads(line) for line in (out_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    source_map = json.loads((out_dir / "source_map.json").read_text(encoding="utf-8"))
    knowledge = json.loads((out_dir / "knowledge.json").read_text(encoding="utf-8"))
    entities = json.loads((out_dir / "entities.json").read_text(encoding="utf-8"))
    document = (out_dir / "document.md").read_text(encoding="utf-8")

    assert document_json["pages"][1]["text"] == "Table of Contents"
    assert document_json["pages"][1]["text_char_count"] == len("Table of Contents")
    assert document_json["pages"][1]["semantic_title"] == "Table of Contents"
    assert "## Table of Contents" in document
    assert "Table of Contents" in chunks[1]["text"]
    assert chunks[1]["heading_path"] == ["Table of Contents"]
    assert chunks[0]["heading_path"] != ["Page 1"]
    assert chunks[0]["locator"] == "Page 1"
    assert source_map[chunks[1]["chunk_id"]]["semantic_title"] == "Table of Contents"
    assert source_map[chunks[1]["chunk_id"]]["locator"] == "Page 2"
    assert chunks[1]["evidence_type"] == "page"
    assert source_map[chunks[1]["chunk_id"]]["evidence_type"] == "page"
    assert knowledge["pages_count"] == 3
    assert knowledge["pages_with_text_count"] == 3
    assert knowledge["page_chunks_count"] == 3
    assert knowledge["image_chunks_count"] == 0
    assert knowledge["image_only_chunks_count"] == 0
    assert knowledge["searchable_page_chunks_count"] == 3
    assert entities["drawing_number"] == ["ENG-186350"]
    assert entities["project_number"] == ["SY909735"]
    assert entities["order_number"] == ["SY909735"]
    assert entities["commission_number"] == []


def test_extract_all_page_text_decouples_text_from_rendered_images(tmp_path, monkeypatch):
    source = tmp_path / "SY909735_Functional Description.pdf"
    source.write_text("%PDF", encoding="utf-8")
    output = tmp_path / "out"
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakePdfConverter())
    monkeypatch.setattr(cli, "render_pdf_pages", lambda path, assets_dir, max_pages: _fake_pages(assets_dir)[:2])
    monkeypatch.setattr(cli, "extract_pdf_text_pages", lambda path, max_pages=None: _fake_text_pages(4 if max_pages is None else max_pages))

    out_dir, status = cli.convert_one(
        source,
        output,
        ConvertOptions(engine="markitdown", render_pdf_pages=True, max_render_pages=2, extract_all_page_text=True),
    )

    assert status == "success"
    document_json = json.loads((out_dir / "document.json").read_text(encoding="utf-8"))
    knowledge = json.loads((out_dir / "knowledge.json").read_text(encoding="utf-8"))
    chunks = [json.loads(line) for line in (out_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    source_map = json.loads((out_dir / "source_map.json").read_text(encoding="utf-8"))

    assert document_json["pages_count"] == 4
    assert document_json["text_pages_count"] == 4
    assert document_json["rendered_pages_count"] == 2
    assert document_json["pages"][2]["image_path"] is None
    assert knowledge["text_pages_count"] == 4
    assert knowledge["rendered_pages_count"] == 2
    assert chunks[2]["evidence_type"] == "text_page"
    assert chunks[2]["page_number"] == 3
    assert source_map[chunks[2]["chunk_id"]]["evidence_type"] == "text_page"
    section_chunks = [chunk for chunk in chunks if chunk["evidence_type"] == "section"]
    assert any(chunk["section_number"] == "7" and chunk["source_page_start"] == 4 for chunk in section_chunks)


def test_wiring_max_text_pages_keeps_limited_page_count(tmp_path, monkeypatch):
    source = tmp_path / "SY909735_Wiring diagram.pdf"
    source.write_text("%PDF", encoding="utf-8")
    output = tmp_path / "out"
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakePdfConverter())
    monkeypatch.setattr(cli, "render_pdf_pages", lambda path, assets_dir, max_pages: _fake_pages(assets_dir)[:max_pages])
    monkeypatch.setattr(cli, "extract_pdf_text_pages", lambda path, max_pages=None: _fake_text_pages(max_pages or 9))

    out_dir, status = cli.convert_one(
        source,
        output,
        ConvertOptions(engine="markitdown", render_pdf_pages=True, max_render_pages=5, max_text_pages=5),
    )

    assert status == "success"
    knowledge = json.loads((out_dir / "knowledge.json").read_text(encoding="utf-8"))

    assert knowledge["pages_count"] == 5
    assert knowledge["text_pages_count"] == 5
    assert knowledge["rendered_pages_count"] == 3


def _fake_pages(assets_dir: Path):
    assets_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    texts = ["Cover Sheet\nMake Control Panel", "Table of Contents", "Revision Overview"]
    for index, text in enumerate(texts, start=1):
        image = assets_dir / f"page_{index:03d}.png"
        image.write_bytes(b"fake")
        pages.append(
            {
                "page_number": index,
                "source_page": index,
                "locator": f"Page {index}",
                "semantic_title": None,
                "image_path": f"assets/page_{index:03d}.png",
                "text": text,
                "text_char_count": len(text),
            }
        )
    return pages


def _fake_text_pages(count: int):
    base = [
        "Functional Description\nProduction Mixer System\nManufacturer:\nsymex GmbH & Co. KG\nSymex no.:\nSY909735",
        "Table of Contents\n1 Safety 1\n3 Operation 2\n7 Fault Messages 4",
        "3 Operation\nOperator text from unrendered section page.",
        "7 Fault Messages\nFault body from page beyond rendered images.",
    ]
    return [
        {
            "page_number": index,
            "source_page": index,
            "locator": f"Page {index}",
            "semantic_title": None,
            "image_path": None,
            "text": base[(index - 1) % len(base)],
            "text_char_count": len(base[(index - 1) % len(base)]),
        }
        for index in range(1, count + 1)
    ]
