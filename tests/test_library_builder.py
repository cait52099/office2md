import json
import sqlite3
from pathlib import Path

from office2md.cli import _search_diagnostics_json_payload, _write_library_report_export_json, _write_search_export_json
from office2md.library import build_library, library_report, locate_document, search_library, search_library_diagnostics, search_library_facets


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
    assert search_library(library_dir / "library.db", "SY909735")[0]["mode"] == "fts"
    assert search_library(library_dir / "library.db", "PLC", limit=1)[0]["output_dir"]
    assert search_library(library_dir / "library.db", "PLC", kinds=["hmi_translation_xlsx"])[0]["document_kind"] == "hmi_translation_xlsx"
    assert search_library(library_dir / "library.db", "PLC", evidences=["hmi_translation_row"])[0]["evidence_type"] == "hmi_translation_row"
    assert all("Translation" not in item["source_file"] for item in search_library(library_dir / "library.db", "PLC", exclude_docs=["Translation"]))
    assert all(item["locator"] for item in search_library(library_dir / "library.db", "SY909735", has_locator=True))
    assert search_library(library_dir / "library.db", "PLC", output_dir="hmi")[0]["output_dir"] == "hmi"
    assert search_library(library_dir / "library.db", "PLC", entities=["HMI"])[0]["document_kind"] == "hmi_translation_xlsx"
    facets = search_library_facets(library_dir / "library.db", "PLC")
    assert {"document_kind", "evidence_type", "source_file", "output_dir", "has_locator", "entity"}.issubset(facets)
    assert {"value": "hmi_translation_xlsx", "count": 2} in facets["document_kind"]
    assert facets["has_locator"][0]["value"] == "yes"
    related = search_library(library_dir / "library.db", "PLC", evidences=["hmi_translation_row"], related=1)
    assert related[0]["related_chunks"]
    assert related[0]["related_chunks"][0]["chunk_id"] == "hmi_table"
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


def test_build_library_refines_pdf_subtypes_and_page_level_quality(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_doc(
        output_root / "datasheet",
        "datasheet-doc",
        "Pump_data.pdf",
        "generic_pdf",
        [_chunk("datasheet_page", "page", ["Data"], "Technical data for pump", "Page 1", page_number=1, image_path="assets/page_001.png")],
        {"equipment": ["pump"]},
        quality_status="low_structure",
    )

    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)

    quality_report = (library_dir / "_quality_report.md").read_text(encoding="utf-8")
    with sqlite3.connect(library_dir / "library.db") as conn:
        kind = conn.execute("SELECT document_kind FROM documents").fetchone()[0]

    assert kind == "datasheet_pdf"
    assert "## Page-Level Searchable PDFs" in quality_report
    assert "- page_level_pdf_count: 1" in quality_report
    assert "## Low Structure\n\n_None._" in quality_report
    assert "- No noisy chunks detected." in quality_report


def test_search_library_falls_back_for_zero_hit_multi_term_query(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_doc(
        output_root / "equipment",
        "equipment-doc",
        "Equipment list.pdf",
        "generic_pdf",
        [
            _chunk("homogenizer_chunk", "page", ["Parts"], "Homogenizer motor 2M2001", "Page 1"),
            _chunk("cooling_chunk", "page", ["Parts"], "Cooling valve 1V2005", "Page 2"),
        ],
        {"equipment": ["homogenizer", "valve"]},
    )

    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)
    results = search_library(library_dir, "homogenizer cooling", limit=5)

    assert results
    assert results[0]["fallback_used"] is True
    assert results[0]["mode"] == "token_fallback"
    assert {item["chunk_id"] for item in results} == {"homogenizer_chunk", "cooling_chunk"}


def test_token_fallback_uses_bounded_pool_independent_of_display_limit(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    noisy_partial_chunks = [
        _chunk(f"pump_only_{index}", "hmi_translation_row", ["HMI"], f"External pump row {index}", f"Sheet: User Texts / Row: {index}")
        for index in range(30)
    ]
    noisy_partial_chunks.extend(
        _chunk(
            f"vacuum_only_{index}",
            "hmi_translation_row",
            ["HMI"],
            f"Pressure vacuum row {index}",
            f"Sheet: User Texts / Row: {index + 100}",
        )
        for index in range(30)
    )
    noisy_partial_chunks.extend(
        _chunk(f"fault_only_{index}", "hmi_translation_row", ["HMI"], f"Faults row {index}", f"Sheet: User Texts / Row: {index + 200}")
        for index in range(30)
    )
    _write_doc(
        output_root / "hmi",
        "hmi-partials",
        "Translation.xlsx",
        "hmi_translation_xlsx",
        noisy_partial_chunks,
        {"equipment": ["HMI"]},
    )
    _write_doc(
        output_root / "faults",
        "fault-catalog",
        "Faults and measures catalog.pdf",
        "fault_catalog_pdf",
        [
            _chunk(
                "vacuum_pump_fault",
                "page",
                ["Faults"],
                "Fault 00200: Vacuum pump motor protection switch tripped.",
                "Page 3",
                page_number=3,
            )
        ],
        {"equipment": ["vacuum pump"]},
    )

    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)
    results = search_library(library_dir, "vacuum pump fault missingterm", limit=1)

    assert results[0]["chunk_id"] == "vacuum_pump_fault"
    assert results[0]["mode"] == "token_fallback"
    assert results[0]["matched_tokens"] == ["fault", "pump", "vacuum"]


def test_token_fallback_prefers_chunks_matching_more_query_terms(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_doc(
        output_root / "search",
        "search-doc",
        "Search.pdf",
        "generic_pdf",
        [
            _chunk("single_a", "hmi_translation_row", ["HMI"], "Alpha only", "Sheet: User Texts / Row: 1"),
            _chunk("single_b", "hmi_translation_row", ["HMI"], "Beta only", "Sheet: User Texts / Row: 2"),
            _chunk("double_match", "page", ["Manual"], "Alpha beta combined evidence", "Page 5", page_number=5),
        ],
        {"equipment": ["alpha", "beta"]},
    )

    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)
    results = search_library(library_dir, "alpha beta missingterm", limit=3)

    assert results[0]["chunk_id"] == "double_match"
    assert results[0]["matched_tokens"] == ["alpha", "beta"]


def test_token_fallback_prefers_fault_catalog_for_failure_intent_ties(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_doc(
        output_root / "hmi",
        "hmi-search",
        "Translation.xlsx",
        "hmi_translation_xlsx",
        [
            _chunk(
                "hmi_agitator_temperature",
                "hmi_translation_group",
                ["HMI"],
                "Agitator cooling water temperature display",
                "Sheet: User Texts / Group: Trends",
            )
        ],
        {"equipment": ["HMI"]},
    )
    _write_doc(
        output_root / "faults",
        "fault-search",
        "Faults and measures catalog.pdf",
        "fault_catalog_pdf",
        [
            _chunk(
                "fault_agitator_temperature",
                "text_page",
                ["Faults"],
                "CML Central agitator VFD fault. Probe fault: agitator cooling water temperature.",
                "Page 5",
                page_number=5,
            )
        ],
        {"equipment": ["agitator"]},
    )

    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)
    results = search_library(library_dir, "agitator temperature problem missingterm", limit=2)

    assert results[0]["chunk_id"] == "fault_agitator_temperature"
    assert results[0]["document_kind"] == "fault_catalog_pdf"
    assert results[0]["matched_tokens"] == ["agitator", "temperature"]


def test_search_library_keeps_exact_part_numbers_and_prefers_locator_chunks(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_doc(
        output_root / "parts",
        "parts-doc",
        "Parts.pdf",
        "generic_pdf",
        [
            _chunk("raw_part", "text", ["Raw"], "1V2005 spare valve raw text", None),
            _chunk("located_part", "page", ["Parts"], "1V2005 spare valve page", "Page 4", page_number=4),
            _chunk("motor_part", "hmi_translation_row", ["Motor"], "2M2001 homogenizer motor", "Sheet: User Texts / Row: 9"),
        ],
        {"equipment": ["1V2005", "2M2001"]},
    )

    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)

    valve_results = search_library(library_dir, "1V2005", limit=5)
    motor_results = search_library(library_dir, "2M2001", limit=5)

    assert {item["chunk_id"] for item in valve_results} == {"raw_part", "located_part"}
    assert valve_results[0]["chunk_id"] == "located_part"
    assert valve_results[0]["alias_used"] is None
    assert valve_results[0]["normalized_used"] is False
    assert motor_results[0]["chunk_id"] == "motor_part"


def test_search_library_uses_conservative_aliases_and_identifier_normalization(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_doc(
        output_root / "hmi",
        "hmi-alias-doc",
        "Translation.xlsx",
        "hmi_translation_xlsx",
        [
            _chunk("cooling_water", "hmi_translation_row", ["Cooling"], "Cooling water pump 1M2098", "Sheet: User Texts / Row: 1"),
            _chunk("alarm_history", "hmi_translation_row", ["Alarms"], "Alarm history active faults", "Sheet: User Texts / Row: 2"),
            _chunk("sealing_liquid", "hmi_translation_row", ["Seal"], "Sealing liquid pump 1M2509", "Sheet: User Texts / Row: 3"),
            _chunk("operation_manual", "page", ["Manual"], "Operation manual safety instructions", "Page 4", page_number=4),
            _chunk("identifier", "hmi_translation_row", ["Probe"], "Sealing liquid temperature 1THS2506", "Sheet: User Texts / Row: 5"),
        ],
        {"equipment": ["HMI", "1THS2506"]},
    )

    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)

    cooling = search_library(library_dir, "\u51b7\u5374\u6c34", limit=3)
    alarm = search_library(library_dir, "\u62a5\u8b66\u5386\u53f2", limit=3)
    sealing = search_library(library_dir, "\u5bc6\u5c01\u6db2", limit=3)
    manual = search_library(library_dir, "\u64cd\u4f5c\u624b\u518c", limit=3)
    identifier = search_library(library_dir, "1THLS200", limit=3)

    assert cooling[0]["chunk_id"] == "cooling_water"
    assert cooling[0]["alias_used"] == "\u51b7\u5374\u6c34 -> cooling water"
    assert alarm[0]["chunk_id"] == "alarm_history"
    assert sealing[0]["chunk_id"] == "sealing_liquid"
    assert manual[0]["chunk_id"] == "operation_manual"
    assert identifier[0]["chunk_id"] == "identifier"
    assert identifier[0]["normalized_used"] is True
    assert identifier[0]["query_used"].endswith("*")


def test_search_library_diagnostics_explain_query_handling_without_changing_results(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_doc(
        output_root / "hmi",
        "diagnostics-doc",
        "Translation.xlsx",
        "hmi_translation_xlsx",
        [
            _chunk("cooling_water", "hmi_translation_row", ["Cooling"], "Cooling water pump 1M2098", "Sheet: User Texts / Row: 1"),
            _chunk("alarm_history", "hmi_translation_row", ["Alarms"], "Alarm history active faults", "Sheet: User Texts / Row: 2"),
        ],
        {"equipment": ["HMI"]},
    )

    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)

    default_results = search_library(library_dir, "alarm history", limit=5)
    fallback_results = search_library(library_dir, "alarm history missingterm", limit=5)
    alias_results = search_library(library_dir, "\u51b7\u5374\u6c34", limit=5)

    default_diagnostics = search_library_diagnostics("alarm history", default_results)
    fallback_diagnostics = search_library_diagnostics("alarm history missingterm", fallback_results)
    alias_diagnostics = search_library_diagnostics("\u51b7\u5374\u6c34", alias_results, kinds=["hmi_translation_xlsx"], has_locator=True)

    assert [item["chunk_id"] for item in default_results] == ["alarm_history"]
    assert default_diagnostics["mode"] == "fts"
    assert default_diagnostics["hints"] == ["exact query matched"]
    assert fallback_diagnostics["token_fallback_used"] is True
    assert fallback_diagnostics["fallback_tokens"] == ["alarm", "history", "missingterm"]
    assert "broad terms may be causing wider results" not in fallback_diagnostics["hints"]
    assert alias_diagnostics["alias_used"] == "\u51b7\u5374\u6c34 -> cooling water"
    assert alias_diagnostics["filters"]["kind"] == ["hmi_translation_xlsx"]
    assert alias_diagnostics["filters"]["has_locator"] is True
    assert alias_diagnostics["top_evidence_types"][0] == {"value": "hmi_translation_row", "count": 1}


def test_search_library_diagnostics_json_payload_is_stable_and_compact(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_doc(
        output_root / "hmi",
        "diagnostics-json-doc",
        "Translation.xlsx",
        "hmi_translation_xlsx",
        [
            _chunk("cooling_water", "hmi_translation_row", ["Cooling"], "Cooling water pump 1M2098", "Sheet: User Texts / Row: 1"),
            _chunk("alarm_history", "hmi_translation_row", ["Alarms"], "Alarm history active faults", "Sheet: User Texts / Row: 2"),
        ],
        {"equipment": ["HMI"]},
    )

    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)
    results = search_library(library_dir, "\u51b7\u5374\u6c34", limit=5, kinds=["hmi_translation_xlsx"], has_locator=True)
    diagnostics = search_library_diagnostics("\u51b7\u5374\u6c34", results, kinds=["hmi_translation_xlsx"], has_locator=True)
    payload = _search_diagnostics_json_payload(diagnostics, results)

    assert list(payload) == [
        "original_query",
        "effective_query",
        "mode",
        "alias_used",
        "normalized_query",
        "token_fallback_used",
        "fallback_tokens",
        "filters",
        "result_count",
        "shown_count",
        "top_evidence_types",
        "top_document_kinds",
        "locator_coverage",
        "hints",
        "results",
    ]
    assert payload["original_query"] == "\u51b7\u5374\u6c34"
    assert payload["effective_query"] == "cooling water"
    assert payload["alias_used"] == "\u51b7\u5374\u6c34 -> cooling water"
    assert payload["filters"]["kind"] == ["hmi_translation_xlsx"]
    assert payload["locator_coverage"] == {"shown_with_locator": 1, "shown_count": 1}
    assert payload["results"] == [
        {
            "rank": 1,
            "chunk_id": "cooling_water",
            "document_title": "Translation",
            "source_file": "Translation.xlsx",
            "document_kind": "hmi_translation_xlsx",
            "evidence_type": "hmi_translation_row",
            "locator": "Sheet: User Texts / Row: 1",
            "output_dir": "hmi",
        }
    ]


def test_search_library_export_json_file_is_stable_and_creates_parent(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_doc(
        output_root / "hmi",
        "export-json-doc",
        "Translation.xlsx",
        "hmi_translation_xlsx",
        [
            _chunk("cooling_water", "hmi_translation_row", ["Cooling"], "Cooling water pump 1M2098", "Sheet: User Texts / Row: 1"),
            _chunk("alarm_history", "hmi_translation_row", ["Alarms"], "Alarm history active faults", "Sheet: User Texts / Row: 2"),
        ],
        {"equipment": ["HMI"]},
    )

    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)
    results = search_library(library_dir, "alarm history", limit=5, kinds=["hmi_translation_xlsx"], has_locator=True)
    diagnostics = search_library_diagnostics("alarm history", results, kinds=["hmi_translation_xlsx"], has_locator=True)
    export_path = tmp_path / "nested" / "search" / "results.json"

    _write_search_export_json(export_path, diagnostics, results)
    payload = json.loads(export_path.read_text(encoding="utf-8"))

    assert payload["query"] == {
        "original_query": "alarm history",
        "effective_query": "alarm history",
        "mode": "fts",
        "alias_used": None,
        "normalized_query": None,
        "token_fallback_used": False,
        "fallback_tokens": [],
        "filters": {
            "kind": ["hmi_translation_xlsx"],
            "evidence": [],
            "document": None,
            "output_dir": None,
            "entity": [],
            "has_locator": True,
            "exclude_doc": [],
        },
    }
    assert payload["result_count"] == 1
    assert payload["shown_count"] == 1
    assert payload["diagnostics"]["locator_coverage"] == {"shown_with_locator": 1, "shown_count": 1}
    assert payload["results"] == [
        {
            "rank": 1,
            "chunk_id": "alarm_history",
            "document_title": "Translation",
            "source_file": "Translation.xlsx",
            "document_kind": "hmi_translation_xlsx",
            "evidence_type": "hmi_translation_row",
            "locator": "Sheet: User Texts / Row: 2",
            "output_dir": "hmi",
            "preview": "Alarm history active faults",
        }
    ]


def test_library_report_export_json_file_uses_report_data_and_creates_parent(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_doc(
        output_root / "manual",
        "report-export-doc",
        "Operation manual.pdf",
        "manual_pdf",
        [_chunk("manual_page", "page", ["Manual"], "SY909735 operation manual", "Page 1", page_number=1)],
        {"symex_number": ["SY909735"]},
    )

    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)
    report = library_report(library_dir)
    export_path = tmp_path / "nested" / "reports" / "library_report.json"

    _write_library_report_export_json(export_path, report)
    payload = json.loads(export_path.read_text(encoding="utf-8"))

    assert payload["documents_count"] == report["documents_count"] == 1
    assert payload["chunks_count"] == report["chunks_count"] == 1
    assert payload["entities_count"] == report["entities_count"] == 1
    assert payload["document_kind_distribution"] == report["document_kind_distribution"]
    assert payload["evidence_type_distribution"] == report["evidence_type_distribution"]
    assert payload["top_entities"] == report["top_entities"]
    assert payload["top_batches"] == report["top_batches"]
    assert payload["missing_assets_summary"] == report["missing_assets_summary"]
    assert payload["low_quality_documents"] == report["low_quality_documents"]
    assert payload["page_level_pdf_documents"] == report["page_level_pdf_documents"]
    assert payload["noisy_chunks_count"] == report["noisy_chunks_count"] == 0
    assert payload["chunks_without_locator"] == report["chunks_without_locator"] == 0
    assert payload["chunks_without_locator_by_document_kind"] == report["chunks_without_locator_by_document_kind"] == {}
    assert payload["chunks_without_locator_by_evidence_type"] == report["chunks_without_locator_by_evidence_type"] == {}
    assert payload["chunks_without_locator_by_extension"] == report["chunks_without_locator_by_extension"] == {}
    assert payload["chunks_without_locator_top_sources"] == report["chunks_without_locator_top_sources"] == []
    assert payload["noisy_documents"] == report["noisy_documents"]
    assert payload["hmi_translation_documents"] == report["hmi_translation_documents"]
    assert payload["export_files_generated"] == report["export_files_generated"]


def test_library_report_and_quality_report_include_missing_locator_detail(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_doc(
        output_root / "agreement",
        "agreement-doc",
        "Purchase Agreement.docx",
        "document",
        [
            _chunk("agreement_text_1", "text", [], "Agreement clause 1", None, provenance_status="raw_markdown"),
            _chunk("agreement_text_2", "text", [], "Agreement clause 2", None, provenance_status="raw_markdown"),
        ],
        {"document_type": ["agreement"]},
    )
    _write_doc(
        output_root / "schedule",
        "schedule-doc",
        "CML125 Project.xlsx",
        "document",
        [_chunk("schedule_text", "text", ["2017-10-23"], "Project schedule", None, provenance_status="raw_markdown")],
        {"project_number": ["CML125"]},
    )
    _write_doc(
        output_root / "manual",
        "manual-doc",
        "Manual.pdf",
        "manual_pdf",
        [_chunk("manual_page", "page", ["Manual"], "Manual page", "Page 1", page_number=1)],
        {"document_type": ["manual"]},
    )

    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)
    report = library_report(library_dir)
    quality_report = (library_dir / "_quality_report.md").read_text(encoding="utf-8")

    assert report["chunks_without_locator"] == 3
    assert report["chunks_without_locator_by_document_kind"] == {"document": 3}
    assert report["chunks_without_locator_by_evidence_type"] == {"text": 3}
    assert report["chunks_without_locator_by_extension"] == {"docx": 2, "xlsx": 1}
    assert report["office_raw_markdown_missing_locator_summary"] == {
        "chunks_without_locator": 3,
        "by_extension": {"docx": 2, "xlsx": 1},
        "note": "Missing locator data is already absent in source_map/chunks for raw_markdown Office chunks; the library builder preserves the available data.",
    }
    assert report["chunks_without_locator_top_sources"][0]["source_file"] == "Purchase Agreement.docx"
    assert report["chunks_without_locator_top_sources"][0]["chunks_without_locator"] == 2
    assert report["chunks_without_locator_top_sources"][0]["raw_markdown_chunks"] == 2

    assert "- chunks_without_locator: 3" in quality_report
    assert "### By Document Kind" in quality_report
    assert "- document: 3" in quality_report
    assert "### By Evidence Type" in quality_report
    assert "- text: 3" in quality_report
    assert "### By Source Extension" in quality_report
    assert "- .docx: 2" in quality_report
    assert "- .xlsx: 1" in quality_report
    assert "### Top Source Files Without Locators" in quality_report
    assert "- Purchase Agreement.docx: 2 chunks" in quality_report
    assert "### Office Raw Markdown Missing Locator Summary" in quality_report
    assert "- office_raw_markdown_chunks_without_locator: 3" in quality_report
    assert "the library builder preserves available locator data" in quality_report


def _write_doc(path: Path, doc_id: str, source_file: str, document_kind: str, chunks: list[dict], entities: dict, quality_status: str = "ok"):
    path.mkdir(parents=True)
    manifest = {
        "source_file": source_file,
        "source_path": f"C:/src/{source_file}",
        "checksum": f"sha256:{doc_id}",
        "engine": "markitdown",
        "status": "success",
        "document_kind": document_kind,
        "quality_status": quality_status,
        "extraction_status": "text",
    }
    knowledge = {
        "title": Path(source_file).stem,
        "document_kind": document_kind,
        "quality_status": quality_status,
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
