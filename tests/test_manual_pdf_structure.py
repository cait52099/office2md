import json
from pathlib import Path

from office2md import cli
from office2md.models import ConvertOptions, ConvertResult
from office2md.postprocess.knowledge_pack import extract_section_outline
from office2md.postprocess.manual_structure import extract_toc_entries_from_pages
from office2md.postprocess.pdf_structure import classify_document_kind, enrich_page_semantics


class FakeFunctionalConverter:
    name = "markitdown"

    def convert(self, path: Path, options: ConvertOptions) -> ConvertResult:
        text = "\n".join(
            [
                "Functional Description",
                "Production Mixer System",
                "Manufacturer Symex",
                "Customer",
                "Year built 2018",
                "1 Safety 5",
                "3 Operation 17",
                "3.3 Siemens touch panel 24",
                "7 Fault messages 70",
            ]
        )
        return ConvertResult(markdown=text, raw_markdown=text, engine="markitdown", metadata={"source": str(path)})


def test_functional_description_pdf_classification(tmp_path):
    path = tmp_path / "Functional Description CML125.pdf"

    assert classify_document_kind(path, "Functional Description Production Mixer System") == "functional_description_pdf"


def test_operating_manual_pdf_classification(tmp_path):
    path = tmp_path / "Operating Manual.pdf"

    assert classify_document_kind(path, "Operation manual for equipment") == "manual_pdf"


def test_operation_manual_en_pdf_classification(tmp_path):
    path = tmp_path / "Operation manual EN.pdf"

    assert classify_document_kind(path, "piping and instrumentation diagram appears in content") == "manual_pdf"


def test_functional_description_filename_priority_examples(tmp_path):
    first = tmp_path / "SY909735_Functional Description_08_02_19_AH.pdf"
    second = tmp_path / "SY909735_Functional Description_23_07_19_AH.pdf"

    assert classify_document_kind(first, "wiring diagram mentioned later") == "functional_description_pdf"
    assert classify_document_kind(second, "piping and instrumentation diagram mentioned later") == "functional_description_pdf"


def test_fault_catalog_pdf_classification(tmp_path):
    path = tmp_path / "Faults and measures catalog.pdf"

    assert classify_document_kind(path, "fault messages and measures catalog") == "fault_catalog_pdf"


def test_faults_and_measures_catalog_filename_priority(tmp_path):
    path = tmp_path / "Faults and measures catalog_SY909735_AH.pdf"

    assert classify_document_kind(path, "wiring diagram mentioned later") == "fault_catalog_pdf"


def test_wiring_diagram_file_classification(tmp_path):
    path = tmp_path / "SY909735 Wiring diagram.pdf"

    assert classify_document_kind(path, "") == "technical_drawing_pdf"


def test_unclear_file_under_piping_folder_is_technical_drawing(tmp_path):
    path = tmp_path / "Piping and instrumentation diagram" / "SY909735.pdf"

    assert classify_document_kind(path, "") == "technical_drawing_pdf"


def test_manual_file_under_unrelated_folder_is_not_technical_drawing(tmp_path):
    path = tmp_path / "Manuals" / "Operating Manual.pdf"

    assert classify_document_kind(path, "") == "manual_pdf"


def test_filename_classification_cannot_be_overridden_by_technical_content(tmp_path):
    manual = tmp_path / "Operating Manual.pdf"
    functional = tmp_path / "SY909735_Functional Description_08_02_19_AH.pdf"
    fault = tmp_path / "Faults and measures catalog_SY909735_AH.pdf"
    technical_content = "wiring diagram schematic p&id piping and instrumentation diagram"

    assert classify_document_kind(manual, technical_content) == "manual_pdf"
    assert classify_document_kind(functional, technical_content) == "functional_description_pdf"
    assert classify_document_kind(fault, technical_content) == "fault_catalog_pdf"


def test_title_page_not_misclassified_as_revision_overview():
    pages = [
        {
            "page_number": 1,
            "image_path": "assets/page_001.png",
            "text": "Functional Description\nProduction Mixer System\nManufacturer\nCustomer\nYear built\nRevision B",
        }
    ]

    enriched = enrich_page_semantics(pages)

    assert enriched[0]["semantic_title"] == "Title Page"


def test_functional_description_outputs_outline_and_page_provenance(tmp_path, monkeypatch):
    source = tmp_path / "Functional Description CML125.pdf"
    source.write_text("%PDF", encoding="utf-8")
    output = tmp_path / "out"
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakeFunctionalConverter())
    monkeypatch.setattr(cli, "render_pdf_pages", lambda path, assets_dir, max_pages: _fake_manual_pages(assets_dir))
    monkeypatch.setattr(cli, "extract_pdf_text_pages", lambda path, max_pages=None: _fake_manual_text_pages())

    out_dir, status = cli.convert_one(
        source,
        output,
        ConvertOptions(engine="markitdown", render_pdf_pages=True, max_render_pages=2),
    )

    assert status == "success"
    document = (out_dir / "document.md").read_text(encoding="utf-8")
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    knowledge = json.loads((out_dir / "knowledge.json").read_text(encoding="utf-8"))
    index_md = (output / "_index.md")
    chunks = [json.loads(line) for line in (out_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    source_map = json.loads((out_dir / "source_map.json").read_text(encoding="utf-8"))
    entities = json.loads((out_dir / "entities.json").read_text(encoding="utf-8"))

    assert manifest["document_kind"] == "functional_description_pdf"
    assert knowledge["document_kind"] == "functional_description_pdf"
    assert knowledge["key_metadata"]["manufacturer"] == "symex GmbH & Co. KG"
    assert knowledge["key_metadata"]["equipment_name"] == "Production Mixer System CML 125"
    assert knowledge["key_metadata"]["symex_number"] == "SY909735"
    assert entities["manufacturer"] == ["symex GmbH & Co. KG"]
    assert entities["equipment_name"] == ["Production Mixer System CML 125"]
    assert "## Section Outline" in document
    assert "- 1 Safety" in document
    assert "- 3 Operation" in document
    assert "- 7 Fault Messages" in document
    assert "## 1 Safety" in document
    assert "## 3 Operation" in document
    assert "### 3.3 Siemens Touch Panel" in document
    assert "Source page: 2" in document
    section_chunks = [chunk for chunk in chunks if chunk["evidence_type"] == "section"]
    assert section_chunks
    assert section_chunks[0]["provenance_status"] == "section_from_page_text"
    assert section_chunks[0]["source_page_start"] == 3
    assert source_map[section_chunks[0]["chunk_id"]]["evidence_type"] == "section"
    assert source_map[section_chunks[0]["chunk_id"]]["source_page_start"] == 3
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["locator"] == "Page 1"
    assert chunks[0]["provenance_status"] == "page_text"
    assert source_map[chunks[0]["chunk_id"]]["page_number"] == 1
    assert source_map[chunks[0]["chunk_id"]]["locator"] == "Page 1"
    assert source_map[chunks[0]["chunk_id"]]["evidence_type"] == "page"
    assert knowledge["section_chunks_count"] >= 1
    cli.rebuild_output_index(output, profile="kb")
    assert "functional_description_pdf" in index_md.read_text(encoding="utf-8")


def test_section_outline_extracts_manual_topics():
    text = "\n".join(["1 Safety 5", "3 Operation 17", "7 Fault messages 70"])

    outline = extract_section_outline(text)

    assert "1 Safety" in outline
    assert "3 Operation" in outline
    assert "7 Fault messages" in outline


def test_toc_entries_extract_requested_functional_sections():
    pages = [
        {
            "page_number": 5,
            "text": "\n".join(
                [
                    "Table of contents",
                    "1",
                    "Safety ............................................................................................................................. 1",
                    "3",
                    "Operation ....................................................................................................................... 2",
                    "5.4",
                    "Electrical Tempering ...............................................................................................20",
                    "7",
                    "Fault messages .........................................................................................................61",
                ]
            ),
        }
    ]

    entries = extract_toc_entries_from_pages(pages)
    labels = [f"{entry['section_number']} {entry['title']}" for entry in entries]

    assert "1 Safety" in labels
    assert "3 Operation" in labels
    assert "5.4 Electrical Tempering" in labels
    assert "7 Fault Messages" in labels


def _fake_manual_pages(assets_dir: Path):
    assets_dir.mkdir(parents=True, exist_ok=True)
    texts = [
        "\n".join(
            [
                "Functional Description",
                "Production Mixer System",
                "CML 125",
                "Manufacturer:",
                "symex GmbH & Co. KG",
                "Name:",
                "CML 125",
                "Symex no.:",
                "SY909735",
                "Customer:",
                "Esteé Lauder China",
                "Year built:",
                "2019",
                "Issue:",
                "2/8/2019",
                "Revision:",
                "Rev. 1.1",
            ]
        ),
        "Table of Contents\n1 Safety 5\n3 Operation 17\n3.3 Siemens touch panel 24\n7 Fault messages 70\n1 Safety\n3 Operation\n3.3 Siemens touch panel",
    ]
    pages = []
    for index, text in enumerate(texts, start=1):
        (assets_dir / f"page_{index:03d}.png").write_bytes(b"fake")
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


def _fake_manual_text_pages():
    texts = [
        "\n".join(
            [
                "Functional Description",
                "Production Mixer System",
                "CML 125",
                "Manufacturer:",
                "symex GmbH & Co. KG",
                "Name:",
                "CML 125",
                "Symex no.:",
                "SY909735",
                "Customer:",
                "Esteé Lauder China",
                "Year built:",
                "2019",
                "Issue:",
                "2/8/2019",
                "Revision:",
                "Rev. 1.1",
            ]
        ),
        "Table of Contents\n1 Safety 5\n3 Operation 17\n3.3 Siemens touch panel 24\n7 Fault messages 70",
        "1 Safety\nSafety body text.",
        "3 Operation\n3.3 Siemens touch panel\nOperation body text.",
    ]
    return [
        {
            "page_number": index,
            "source_page": index,
            "locator": f"Page {index}",
            "semantic_title": None,
            "image_path": None,
            "text": text,
            "text_char_count": len(text),
        }
        for index, text in enumerate(texts, start=1)
    ]
