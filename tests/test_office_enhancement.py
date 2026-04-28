import json
from pathlib import Path

from office2md import cli
from office2md.models import ConvertOptions, ConvertResult
from office2md.postprocess.drawing_index import extract_drawing_index
from office2md.postprocess.pdf_structure import enrich_page_semantics


class FakeConverter:
    def __init__(self, markdown: str):
        self.markdown = markdown

    def convert(self, path: Path, options: ConvertOptions) -> ConvertResult:
        return ConvertResult(markdown=self.markdown, raw_markdown=self.markdown, engine="markitdown")


def test_wiring_drawing_index_parses_expected_entries():
    pages = [
        {
            "page_number": 2,
            "locator": "Page 2",
            "text": "\n".join(
                [
                    "Table of contents",
                    "Page",
                    "+N02/1",
                    "Wohlers",
                    "Power supply",
                    "Schematic multi-line",
                    "21.08.2018",
                    "+N01/25",
                    "Wohlers",
                    "Emergency stop",
                    "Schematic multi-line",
                    "21.08.2018",
                    "+N02/101",
                    "Wohlers",
                    "CML Co-Twister pump rotor",
                    "Schematic multi-line",
                    "21.08.2018",
                    "+N03/1",
                    "Wohlers",
                    "PLC",
                    "Schematic multi-line",
                    "21.08.2018",
                    "+N04/1",
                    "Wohlers",
                    "Terminal diagram",
                    "Terminal diagram",
                    "21.08.2018",
                ]
            ),
        }
    ]

    entries = extract_drawing_index(pages)
    descriptions = [entry["page_description"] for entry in entries]

    assert "Power supply" in descriptions
    assert "Emergency stop" in descriptions
    assert "CML Co-Twister pump rotor" in descriptions
    assert "PLC" in descriptions
    assert "Terminal diagram" in descriptions


def test_operation_manual_title_page_and_document_type(tmp_path, monkeypatch):
    source = tmp_path / "Operation manual EN.pdf"
    source.write_text("%PDF", encoding="utf-8")
    pages = [
        {
            "page_number": 1,
            "source_page": 1,
            "locator": "Page 1",
            "image_path": "assets/page_001.png",
            "text": "symex GmbH & Co. KG\nRev. 1.1\nOperating Manual\nProduction Mixer System\nCML 125\nMachine No./Order no.\nSY909735\n2019",
            "text_char_count": 120,
        }
    ]
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakeConverter("Operating Manual"))
    monkeypatch.setattr(cli, "render_pdf_pages", lambda path, assets_dir, max_pages: pages)
    monkeypatch.setattr(cli, "extract_pdf_text_pages", lambda path, max_pages=None: pages)

    out_dir, status = cli.convert_one(source, tmp_path / "out", ConvertOptions(engine="markitdown", render_pdf_pages=True))

    assert status == "success"
    document_json = json.loads((out_dir / "document.json").read_text(encoding="utf-8"))
    entities = json.loads((out_dir / "entities.json").read_text(encoding="utf-8"))
    knowledge = json.loads((out_dir / "knowledge.json").read_text(encoding="utf-8"))

    assert enrich_page_semantics(pages)[0]["semantic_title"] == "Title Page"
    assert document_json["pages"][0]["semantic_title"] == "Title Page"
    assert entities["document_type"] == ["operating manual"]
    assert "wiring diagram" not in entities["document_type"]
    assert knowledge["key_metadata"]["manufacturer"] == "symex GmbH & Co. KG"
    assert knowledge["key_metadata"]["symex_number"] == "SY909735"
    assert knowledge["key_metadata"]["year_built"] == "2019"
    assert knowledge["key_metadata"]["revision"] == "Rev. 1.1"


def test_xlsx_table_provenance_and_entities(tmp_path, monkeypatch):
    markdown = "\n".join(
        [
            "## MPDP-OWL",
            "| Scaleup Phase | Batches | Size kg | Tasks |",
            "| --- | --- | --- | --- |",
            "| PFA | Lab bench | 2.3kg | Stability |",
            "| Pilot | Pilot 1 | 50kg | Stability & approval |",
            "| Practice | PPPB 1 | 100kg | Test Fill |",
            "| Pre-Production | PPB 1 | 180kg | Approval |",
            "| Production | FPB | 180kg | Approval |",
            "| Before Practice Release | | | |",
        ]
    )
    source = tmp_path / "43DS MPDP.xlsx"
    source.write_text("fake", encoding="utf-8")
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakeConverter(markdown))

    out_dir, status = cli.convert_one(source, tmp_path / "out", ConvertOptions(engine="markitdown"))

    chunks = [json.loads(line) for line in (out_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    source_map = json.loads((out_dir / "source_map.json").read_text(encoding="utf-8"))
    entities = json.loads((out_dir / "entities.json").read_text(encoding="utf-8"))
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))

    assert status == "success"
    assert manifest["document_kind"] == "mpdp_table_xlsx"
    assert chunks[0]["evidence_type"] == "table"
    assert any(chunk["evidence_type"] == "table_section" for chunk in chunks)
    assert any(item["evidence_type"] == "table_section" for item in source_map.values())
    assert source_map[chunks[0]["chunk_id"]]["sheet_name"] == "MPDP-OWL"
    assert entities["scaleup_phase"]
    assert "PPPB" in entities["batch_type"]


def test_pptx_slide_chunks_and_entities(tmp_path, monkeypatch):
    markdown = "<!-- Slide number: 1 -->\nProject number: PN77563\nProject name: LS Daily Rescue Eye Serum\nFormula structure: W/O\nTechnology: M4E\nVL322673\n![](Picture13.jpg)"
    source = tmp_path / "43DS-LS Daily Rescue Eye Serum 20260417.pptx"
    source.write_text("fake", encoding="utf-8")
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakeConverter(markdown))

    out_dir, status = cli.convert_one(source, tmp_path / "out", ConvertOptions(engine="markitdown"))

    chunks = [json.loads(line) for line in (out_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    entities = json.loads((out_dir / "entities.json").read_text(encoding="utf-8"))
    knowledge = json.loads((out_dir / "knowledge.json").read_text(encoding="utf-8"))
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))

    assert status == "success"
    assert manifest["document_kind"] == "process_development_presentation"
    assert chunks[0]["evidence_type"] == "slide"
    assert chunks[0]["locator"] == "Slide 1"
    assert entities["project_number"] == ["77563"]
    assert entities["formula_structure"] == ["W/O"]
    assert entities["technology"] == ["M4E"]
    assert "VL322673" in entities["batch_ids"]
    assert knowledge["slide_chunks_count"] == 1
    assert knowledge["missing_assets_count"] == 1


def test_pptx_process_development_markdown_reconstruction(tmp_path, monkeypatch):
    markdown = _process_development_pptx_markdown()
    source = tmp_path / "43DS-LS Daily Rescue Eye Serum 20260417.pptx"
    source.write_text("fake", encoding="utf-8")
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakeConverter(markdown))

    out_dir, status = cli.convert_one(source, tmp_path / "out", ConvertOptions(engine="markitdown"))

    assert status == "success"
    document = (out_dir / "document.md").read_text(encoding="utf-8")
    knowledge = json.loads((out_dir / "knowledge.json").read_text(encoding="utf-8"))
    source_map = json.loads((out_dir / "source_map.json").read_text(encoding="utf-8"))
    chunks = [json.loads(line) for line in (out_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]

    for heading in [
        "## Presentation Summary",
        "## Slide Index",
        "## Topic Outline",
        "## Process Development Narrative",
        "## Batch Study Summary",
    ]:
        assert heading in document
    assert "### Slide 10 - General info" not in document
    assert "### Submission sensory tracking" in document
    assert "### Timeline" in document
    assert "### Lab Formula Study" in document
    assert "### Process flowchart" in document
    assert "### General info" in document
    assert "Source: Slide 10" in document
    assert "| 10 | General info |" in document

    slide_titles = {item["slide_number"]: item["slide_title"] for item in knowledge["slide_index"]}
    assert slide_titles[3] == "Submission sensory tracking"
    assert slide_titles[4] == "Timeline"
    assert slide_titles[5] == "Lab Formula Study"
    assert slide_titles[8] == "Process flowchart"
    assert "LS Daily Rescue Eye Serum" not in {slide_titles[3], slide_titles[4], slide_titles[5], slide_titles[8]}

    assert knowledge["topic_outline"]
    assert knowledge["batch_study_summary"]
    assert knowledge["topic_chunks_count"] > 0
    assert knowledge["batch_study_chunks_count"] >= 11
    assert knowledge["visual_heavy_slides_count"] >= 2
    assert any(item["evidence_type"] == "topic" for item in source_map.values())
    assert any(item["evidence_type"] == "batch_study" for item in source_map.values())
    assert any(chunk["evidence_type"] == "slide" and chunk["visual_evidence_needed"] for chunk in chunks)
    slide10_chunk = next(chunk for chunk in chunks if chunk.get("evidence_type") == "slide" and chunk.get("slide_number") == 10)
    assert source_map[slide10_chunk["chunk_id"]]["heading_path"] == ["General info"]
    assert source_map[slide10_chunk["chunk_id"]]["locator"] == "Slide 10"
    assert source_map[slide10_chunk["chunk_id"]]["slide_title"] == "General info"
    assert source_map[slide10_chunk["chunk_id"]]["topic_label"] == "Project Overview"
    batch_chunk = next(chunk for chunk in chunks if chunk.get("evidence_type") == "batch_study")
    assert "Slide" not in " ".join(batch_chunk["heading_path"])
    assert batch_chunk["heading_path"] == [batch_chunk["batch_id"]]
    batch_rows = {row["batch_id"]: row for row in knowledge["batch_study_summary"]}
    assert batch_rows["VL322673"]["result_status"] != "Pass"
    assert "fail" in batch_rows["VL322673"]["result_status"].lower()
    assert 20 in batch_rows["VL324017"]["evidence_slides"]
    assert batch_rows["VL325458"]["result_status"] == "Fail"
    assert "fail" in batch_rows["VL325459"]["result_status"].lower()
    assert batch_rows["VL326528"]["batch_size"] == "100kg"
    assert "Symex" in batch_rows["VL326528"]["equipment_process_route"]
    assert "25L/min" in batch_rows["VL326528"]["m4e_parameter"]
    assert batch_rows["VL324017"]["confidence"] in {"high", "medium", "low"}
    assert batch_rows["VL324017"]["evidence_snippet"]
    slide14 = next(slide for slide in knowledge["slide_index"] if slide["slide_number"] == 14)
    assert slide14["topic_label"] != "Micro / Risk Assessment"


def test_docx_release_rationale_metadata_tags_and_embedded_warning(tmp_path, monkeypatch):
    markdown = "\n".join(
        [
            "# Executive Summary",
            "The product has an annual production volume of 200 kilograms and is produced at Oevel.",
            "M4E Venturi 35L/min for 5mins, viscosity was adjusted up from 33% to 37%",
            "I recommend proceeding to PPPB.",
            "![x](data:image/png;base64...)",
            "| Product Name | ANTI-FATIGUE + YTH RNFR FST PWRFL EYE SERUM |",
            "| Pathfinder Mass Code (if applicable) | 43DS-00-M01U |",
            "| Manufacturing Location(s) Oevel, Agincourt, Whitman, Melville, or others (specify) | OEVEL |",
            "| Product Formula System O/W, W/O, W/Si, Aqueous, Anhydrous, or others (specify) | W/Si |",
            "| Specialty Equipment (if applicable) | M4E |",
        ]
    )
    source = tmp_path / "43DS-00-M01U PPPBC release rational.docx"
    source.write_text("fake", encoding="utf-8")
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakeConverter(markdown))

    out_dir, status = cli.convert_one(source, tmp_path / "out", ConvertOptions(engine="markitdown"))

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    knowledge = json.loads((out_dir / "knowledge.json").read_text(encoding="utf-8"))
    entities = json.loads((out_dir / "entities.json").read_text(encoding="utf-8"))
    document = (out_dir / "document.md").read_text(encoding="utf-8")

    assert status == "success"
    assert manifest["document_kind"] == "release_rationale_docx"
    assert knowledge["key_metadata"]["product_name"] == "ANTI-FATIGUE + YTH RNFR FST PWRFL EYE SERUM"
    assert knowledge["key_metadata"]["pathfinder_mass_code"] == "43DS-00-M01U"
    assert knowledge["key_metadata"]["formula_system"] == "W/Si"
    assert "release-rationale" in knowledge["tags"]
    assert "pppbc" in knowledge["tags"]
    assert "m4e" in knowledge["tags"]
    assert "viscosity" in knowledge["tags"]
    assert entities["document_type"] == ["release rationale"]
    assert entities["mass_code"] == ["43DS-00-M01U"]
    assert knowledge["embedded_image_detected"] is True
    assert "## Release Summary" in document
    assert "## Key Release Metadata" in document
    assert "## Key Process Parameters" in document
    assert "## Recommendation" in document


def test_operation_manual_source_map_removes_wiring_semantic_noise(tmp_path, monkeypatch):
    source = tmp_path / "Operation manual EN.pdf"
    source.write_text("%PDF", encoding="utf-8")
    pages = [
        {
            "page_number": 1,
            "source_page": 1,
            "locator": "Page 1",
            "image_path": "assets/page_001.png",
            "text": "Operating Manual\nProduction Mixer System\nCML 125\nMachine No./Order no.\nSY909735",
            "text_char_count": 90,
        },
        {
            "page_number": 2,
            "source_page": 2,
            "locator": "Page 2",
            "image_path": "assets/page_002.png",
            "text": "Cable Overview\nPower Supply\nCover Sheet\nProcess operation notes",
            "text_char_count": 70,
        },
        {
            "page_number": 3,
            "source_page": 3,
            "locator": "Page 3",
            "image_path": "assets/page_003.png",
            "text": "Table of Contents\n1 Safety ................................ 99\n2 Operation ............................. 2\n3 Cleaning .............................. 3",
            "text_char_count": 120,
        },
    ]
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakeConverter("Operating Manual"))
    monkeypatch.setattr(cli, "render_pdf_pages", lambda path, assets_dir, max_pages: pages)
    monkeypatch.setattr(cli, "extract_pdf_text_pages", lambda path, max_pages=None: pages)

    out_dir, status = cli.convert_one(source, tmp_path / "out", ConvertOptions(engine="markitdown", render_pdf_pages=True))

    assert status == "success"
    source_map = json.loads((out_dir / "source_map.json").read_text(encoding="utf-8"))
    knowledge = json.loads((out_dir / "knowledge.json").read_text(encoding="utf-8"))
    semantic_titles = {item.get("semantic_title") for item in source_map.values()}

    assert "Cable Overview" not in semantic_titles
    assert "Power Supply" not in semantic_titles
    assert "Cover Sheet" not in semantic_titles
    assert all(entry["page_hint"] <= knowledge["pages_count"] for entry in knowledge.get("section_outline", []))


def _process_development_pptx_markdown() -> str:
    return "\n".join(
        [
            "<!-- Slide number: 1 -->",
            "LS Daily Rescue Eye Serum",
            "General info",
            "Project number: PN77563",
            "Project name: LS Daily Rescue Eye Serum",
            "Annual Volume (kg): 200",
            "Production size: 100kg",
            "Formula structure: W/O high internal water phase",
            "Technology: M4E",
            "Manloc: Oevel",
            "Package type: airless pump",
            "<!-- Slide number: 2 -->",
            "CONFIDENTIAL",
            "Prototype history information collection",
            "W/O active system and PD sensory feedback.",
            "<!-- Slide number: 3 -->",
            "LS Daily Rescue Eye Serum",
            "Submission sensory tracking",
            "Sensory feedback shows viscosity and particle size sensitivity.",
            "<!-- Slide number: 4 -->",
            "LS Daily Rescue Eye Serum",
            "Timeline",
            "Milestones for lab, pilot and recommendation.",
            "<!-- Slide number: 5 -->",
            "LS Daily Rescue Eye Serum",
            "Lab Formula Study",
            "Viscosity linked to particle size, homo speed, time, M4E Venturi speed 35L/min and timer 5mins.",
            "<!-- Slide number: 6 -->",
            "Batch",
            "| Batch | 1st 50kg(SC061) VL322673 | 2nd 50kg(M4E) VL322674 | 3rd 50kg(M4E) VL324017 | 4th 50kg(M4E) VL324568 | 6th 50kg(M4E) VL324869 | 7th 50kg(M4E) TC324870 | 8th 50kg(M4E) VL325458 | 9th 100kg(Symex+M4E) VL326528 |",
            "| Batch purpose | First pilot batch on symex | Second pilot batch to study M4E feasibility | Formula update | Study M4E Ventri speed parameter/timer linkage | Sensitivity study on ventri speed: Fix M4E venri speed 30L/MIN | Sensitivity study on ventri speed: Fix M4E venri speed 35L/MIN | Sensitivity study on ventri speed: Fix M4E venri speed 75L/MIN | Check if symex kettle could be connect to M4E |",
            "| Results | Shake stability fail | Shake stability pass while viscosity above 27%, but F/TH fail | Pass shake & F/TH stability Micro issue pool3 fail | Stability ok | Stability ok | Stability ok | Stability fail | Stability fail |",
            "<!-- Slide number: 7 -->",
            "Pilot Summary",
            "Lee Trimix + M4E route appears feasible",
            "<!-- Slide number: 8 -->",
            "LS Daily Rescue Eye Serum",
            "Process flowchart",
            "Process flowchart includes M4E connection and recirculation path.",
            "![flow](Picture13.jpg)",
            "<!-- Slide number: 9 -->",
            "M4E Study",
            "VL325890 M4E Venturi speed 30L/min feasible",
            "VL326103 M4E timer 3mins challenge",
            "<!-- Slide number: 10 -->",
            "Daily Rescue Eye Serum",
            "General info",
            "Project overview notes.",
            "<!-- Slide number: 11 -->",
            "Formula Technical Risk Assessment",
            "Risk assessment: process parameters need control because viscosity/spec is sensitive.",
            "<!-- Slide number: 12 -->",
            "Spec",
            "Spec CPP-CQA includes viscosity.",
            "<!-- Slide number: 13 -->",
            "Recommendation",
            "Recommendation: Lee Trimix + M4E / Oevel route.",
            "<!-- Slide number: 14 -->",
            "Feasibility study for Pilot Scale-up",
            "VL322673-50kg microscopy and shaker review.",
            "<!-- Slide number: 20 -->",
            "M4E pilot scale up",
            "VL324017- 50kg",
            "50kg pilot scale up: Success",
            "Results: achieve the spec and pass Fth 4cyc & Shaker",
            "<!-- Slide number: 29 -->",
            "M4E pilot scale up",
            "-VL325458 Fail",
            "| 3 | ->M4E venturi, 3min, 35L/min | 41% |",
            "<!-- Slide number: 33 -->",
            "M4E pilot scale up",
            "-VL325459 50kg symex 32.4kg discharge using Symex",
            "F/TH fail",
            "| 1 | ->M4E venturi, 10min, 25L/min | 18% |",
            "VL326528 100kg symex",
            "| 2 | ->M4E venturi, 10min, 25L/min | 23% |",
        ]
    )
