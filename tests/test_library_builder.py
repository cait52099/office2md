import json
import sqlite3
from pathlib import Path

from office2md.library import build_library, locate_document, search_library


def test_build_library_database_graph_exports_search_and_warnings(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_doc(
        output_root / "pptx",
        "ppt-doc",
        "Deck.pptx",
        "process_development_presentation",
        [
            _chunk("ppt_slide", "slide", ["General info"], "M4E viscosity overview", "Slide 1", slide_number=1, topic_label="Project Overview"),
            _chunk("ppt_topic", "topic", ["M4E Study"], "M4E viscosity topic", "Slides 1-2", topic_label="M4E Study", slide_numbers=[1, 2]),
            _chunk("ppt_batch", "batch_study", ["VL324017"], "VL324017 success evidence", "Slide 20", batch_id="VL324017", confidence="high", slide_number=20),
        ],
        {"technology": ["M4E"], "batch_ids": ["VL324017"], "project_number": ["77563"]},
    )
    _write_doc(
        output_root / "xlsx",
        "xlsx-doc",
        "MPDP.xlsx",
        "mpdp_table_xlsx",
        [
            _chunk("xlsx_table", "table", ["MPDP-OWL"], "MPDP table", "Sheet: MPDP-OWL / Table 1", sheet_name="MPDP-OWL", table_name="MPDP-OWL / Table 1"),
            _chunk("xlsx_phase", "table_section", ["Pilot"], "Pilot 50kg stability", "Sheet: MPDP-OWL / Phase: Pilot", sheet_name="MPDP-OWL", topic_label="Pilot"),
        ],
        {"scaleup_phase": ["Pilot"], "batch_type": ["PPPB"]},
    )
    _write_doc(
        output_root / "manual",
        "manual-doc",
        "Operation manual EN.pdf",
        "manual_pdf",
        [
            _chunk("manual_page", "page", ["Title Page"], "SY909735 operation manual", "Page 1", page_number=1),
            _chunk("manual_section", "section", ["3 Operation"], "Operation section", "Page 12", page_number=12, section_number="3", section_title="Operation"),
        ],
        {"symex_number": ["SY909735"], "document_type": ["operating manual"]},
    )
    _write_doc(
        output_root / "drawing",
        "drawing-doc",
        "SY909735_Wiring diagram.pdf",
        "technical_drawing_pdf",
        [
            _chunk("drawing_page", "page", ["Cover Sheet"], "SY909735 wiring cover", "Page 1", page_number=1),
            _chunk("drawing_index", "drawing_index", ["Drawing Index", "Table of contents"], "Terminal diagram topic", "Table of Contents / Page 2"),
        ],
        {"project_number": ["SY909735"], "document_type": ["wiring diagram"]},
    )
    _write_doc(
        output_root / "docx",
        "docx-doc",
        "Release rationale.docx",
        "release_rationale_docx",
        [_chunk("docx_text", "text", ["Executive Summary"], "Release rationale for M4E process", None)],
        {"mass_code": ["43DS-00-M01U"]},
    )
    _write_doc(
        output_root / "hmi",
        "hmi-doc",
        "Copy of SY909735_Translation_Chinese ver.1.xlsx",
        "hmi_translation_xlsx",
        [
            _chunk(
                "hmi_table",
                "hmi_translation_table",
                ["User Texts"],
                "HMI translation table SY909735 PLC HMI",
                "Sheet: User Texts",
                sheet_name="User Texts",
            ),
            _chunk(
                "hmi_row",
                "hmi_translation_row",
                ["C1 Contr_1 / Einsaugungen", "Textfeld_84"],
                "HMI screen group: C1 Contr_1 / Einsaugungen\nField: Textfeld_84\nen-GB: PLC speed\nzh-CN: PLC speed\nUnit: %",
                "Sheet: User Texts / Row: 2",
                sheet_name="User Texts",
                group_path="C1 Contr_1 / Einsaugungen",
                row_number=2,
            ),
        ],
        {"project_number": ["SY909735"], "order_number": ["SY909735"], "equipment": ["PLC", "HMI"], "document_type": ["hmi translation"]},
    )
    _write_doc(
        output_root / "noisy",
        "noisy-doc",
        "Noisy.xlsx",
        "document",
        [
            _chunk(
                "noisy_raw",
                "text",
                ["User Texts"],
                ("NaN | " * 30) + "C:/Users/example/SY909735_PLC+HMI_V15/SY909735/Bilder/C1/Textfeld " + ("USb22NXN1iivCY2FKzp8v7Sq2hPlEwHfLKjBbqfgJyfmaQ4JYrVkKmbeLAeBIqMWurSKbtWwEE6MNYEwFuyxV4wHu3AALNDcU6t5qketBTsGWG80byDKlAobccs4g " * 2),
                None,
            )
        ],
        {"project_number": ["SY909735"]},
    )
    _write_failed_doc(output_root / "failed")
    _write_missing_entities_doc(output_root / "missing")
    before = sorted(path.relative_to(output_root).as_posix() for path in output_root.rglob("*"))

    library_dir = tmp_path / "library"
    result = build_library(output_root, library_dir)

    after = sorted(path.relative_to(output_root).as_posix() for path in output_root.rglob("*"))
    assert before == after
    assert result["documents_count"] == 8
    assert result["warnings"]
    assert (library_dir / "library.db").exists()
    assert (library_dir / "library_manifest.json").exists()
    assert (library_dir / "library_index.json").exists()
    assert (library_dir / "library_graph.json").exists()
    assert (library_dir / "_library.md").exists()
    assert (library_dir / "_entities.md").exists()
    assert (library_dir / "_quality_report.md").exists()
    for name in [
        "llamaindex_documents.jsonl",
        "haystack_documents.jsonl",
        "txtai_rows.jsonl",
        "graphrag_input.jsonl",
    ]:
        assert (library_dir / "exports" / name).exists()
    manifest = json.loads((library_dir / "library_manifest.json").read_text(encoding="utf-8"))
    index_json = json.loads((library_dir / "library_index.json").read_text(encoding="utf-8"))
    library_md = (library_dir / "_library.md").read_text(encoding="utf-8")
    assert manifest["schema_version"] == "1"
    assert manifest["documents_count"] == 8
    assert manifest["exports_count"] == 4
    assert manifest["release_label"] == "v0.2.0-rc1"

    with sqlite3.connect(library_dir / "library.db") as conn:
        kinds = {row[0] for row in conn.execute("SELECT document_kind FROM documents")}
        evidence = {row[0] for row in conn.execute("SELECT evidence_type FROM chunks")}
        entities_count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        locator = conn.execute("SELECT locator FROM chunks WHERE chunk_id = 'ppt_batch'").fetchone()[0]

    assert {
        "process_development_presentation",
        "mpdp_table_xlsx",
        "manual_pdf",
        "technical_drawing_pdf",
        "release_rationale_docx",
        "hmi_translation_xlsx",
    }.issubset(kinds)
    assert {
        "slide",
        "table",
        "table_section",
        "page",
        "section",
        "drawing_index",
        "batch_study",
        "topic",
        "hmi_translation_table",
        "hmi_translation_row",
    }.issubset(evidence)
    assert entities_count == len(_entity_rows(library_dir / "library.db"))
    assert locator == "Slide 20"
    sy_entities = [item for item in index_json["top_entities"] if item["normalized_text"] == "sy909735"]
    assert len(sy_entities) == 1
    assert {"project_number", "order_number"}.issubset(set(sy_entities[0]["entity_types"]))
    key_entities = library_md.split("## Key Entities", 1)[1].split("## Key Topics", 1)[0]
    assert key_entities.count("SY909735") == 1

    graph = json.loads((library_dir / "library_graph.json").read_text(encoding="utf-8"))
    node_types = {node["type"] for node in graph["nodes"]}
    assert {"document", "entity", "chunk"}.issubset(node_types)

    assert search_library(library_dir / "library.db", "M4E")
    assert search_library(library_dir / "library.db", "SY909735")
    assert search_library(library_dir / "library.db", "VL324017")
    assert search_library(library_dir / "library.db", "PLC", limit=1)[0]["output_dir"]
    assert search_library(library_dir / "library.db", "PLC", kinds=["hmi_translation_xlsx"])[0]["document_kind"] == "hmi_translation_xlsx"
    assert search_library(library_dir / "library.db", "PLC", evidences=["hmi_translation_row"])[0]["evidence_type"] == "hmi_translation_row"
    assert all("Translation" not in item["source_file"] for item in search_library(library_dir / "library.db", "PLC", exclude_docs=["Translation"]))
    assert all(item["locator"] for item in search_library(library_dir / "library.db", "SY909735", has_locator=True))
    noisy = search_library(library_dir / "library.db", "Textfeld", document="Noisy", limit=5)
    assert noisy[0]["is_noisy"]
    assert "NaN | NaN" not in noisy[0]["preview"]
    assert "[base64]" in noisy[0]["preview"]
    located = locate_document(library_dir, "Translation")
    assert located[0]["document_kind"] == "hmi_translation_xlsx"
    assert located[0]["output_dir"]
    located_from_db = locate_document(library_dir / "library.db", "Translation")
    assert located_from_db[0]["document_kind"] == "hmi_translation_xlsx"


def test_build_library_handles_duplicate_document_and_chunk_ids(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    chunks = [_chunk("duplicate_chunk", "page", ["Page"], "Duplicate terminal data", "Page 1", page_number=1)]
    _write_doc(output_root / "copy-a", "same-checksum", "Part.pdf", "generic_pdf", [dict(chunks[0])], {"equipment": ["terminal"]})
    _write_doc(output_root / "copy-b", "same-checksum", "Part.pdf", "generic_pdf", [dict(chunks[0])], {"equipment": ["terminal"]})

    library_dir = tmp_path / "library"
    result = build_library(output_root, library_dir)

    assert result["documents_count"] == 2
    with sqlite3.connect(library_dir / "library.db") as conn:
        doc_ids = [row[0] for row in conn.execute("SELECT doc_id FROM documents ORDER BY output_dir")]
        chunk_ids = [row[0] for row in conn.execute("SELECT chunk_id FROM chunks ORDER BY chunk_id")]

    assert len(doc_ids) == len(set(doc_ids)) == 2
    assert len(chunk_ids) == len(set(chunk_ids)) == 2
    assert any(doc_id.startswith("same-checksum-") for doc_id in doc_ids)


def _write_doc(path: Path, doc_id: str, source_file: str, document_kind: str, chunks: list[dict], entities: dict):
    path.mkdir(parents=True)
    manifest = {
        "source_file": source_file,
        "source_path": f"C:/src/{source_file}",
        "checksum": f"sha256:{doc_id}",
        "engine": "markitdown",
        "status": "success",
        "document_kind": document_kind,
        "quality_status": "ok",
        "extraction_status": "text",
    }
    knowledge = {
        "title": Path(source_file).stem,
        "document_kind": document_kind,
        "quality_status": "ok",
        "extraction_status": "text",
        "key_metadata": {"source_path": manifest["source_path"], "checksum": manifest["checksum"], "converter": "markitdown"},
        "tags": [document_kind],
    }
    for chunk in chunks:
        chunk["doc_id"] = doc_id
        chunk["source_file"] = source_file
        chunk["source_path"] = manifest["source_path"]
        chunk["document_kind"] = document_kind
        chunk["quality_status"] = "ok"
    source_map = {
        chunk["chunk_id"]: {
            "heading_path": chunk.get("heading_path", []),
            "locator": chunk.get("locator"),
            "evidence_type": chunk.get("evidence_type"),
            "slide_number": chunk.get("slide_number"),
            "topic_label": chunk.get("topic_label"),
            "batch_id": chunk.get("batch_id"),
            "confidence": chunk.get("confidence"),
        }
        for chunk in chunks
    }
    (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (path / "knowledge.json").write_text(json.dumps(knowledge), encoding="utf-8")
    (path / "entities.json").write_text(json.dumps(entities), encoding="utf-8")
    (path / "source_map.json").write_text(json.dumps(source_map), encoding="utf-8")
    with (path / "chunks.jsonl").open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk) + "\n")
    (path / "document.md").write_text("# Document\n", encoding="utf-8")


def _write_failed_doc(path: Path):
    path.mkdir(parents=True)
    (path / "manifest.json").write_text(json.dumps({"status": "failed", "source_file": "bad.pdf"}), encoding="utf-8")


def _write_missing_entities_doc(path: Path):
    path.mkdir(parents=True)
    (path / "manifest.json").write_text(
        json.dumps({"status": "success", "source_file": "Missing.pdf", "document_kind": "generic_pdf", "quality_status": "ok"}),
        encoding="utf-8",
    )
    (path / "knowledge.json").write_text(json.dumps({"title": "Missing", "document_kind": "generic_pdf"}), encoding="utf-8")
    (path / "chunks.jsonl").write_text("", encoding="utf-8")
    (path / "document.md").write_text("# Missing\n", encoding="utf-8")


def _chunk(
    chunk_id: str,
    evidence_type: str,
    heading_path: list[str],
    text: str,
    locator: str | None,
    **extra,
) -> dict:
    chunk = {
        "chunk_id": chunk_id,
        "evidence_type": evidence_type,
        "heading_path": heading_path,
        "text": text,
        "char_count": len(text),
        "locator": locator,
        "provenance_status": f"{evidence_type}_test",
    }
    chunk.update(extra)
    return chunk


def _entity_rows(db_path: Path):
    with sqlite3.connect(db_path) as conn:
        return conn.execute("SELECT entity_type, normalized_text FROM entities").fetchall()
