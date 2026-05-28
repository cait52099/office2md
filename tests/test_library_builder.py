import json
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from office2md.cli import (
    _locate_document_export_json_payload,
    _open_chunk_json_payload,
    _report_context_json_payload,
    _search_diagnostics_json_payload,
    _write_library_report_export_json,
    _write_locate_document_export_json,
    _write_open_chunk_export_json,
    _write_report_context_export_json,
    _write_search_export_json,
    app,
)
from office2md.gui.helpers import (
    build_obsidian_export_command_preview,
    build_library_command_preview,
    build_runner_command_preview,
    build_workspace_init_command_hint,
    build_workspace_next_step_hints,
    classify_workspace_path_hint,
    count_existing_manifests,
    derive_workspace_paths,
    graph_layout_options,
    graph_node_types,
    graph_summary,
    graph_view_html,
    is_conversion_output_path,
    is_valid_library_path,
    load_workspace_status_for_gui,
    load_library_graph,
    load_curated_concept_index,
    prepare_curated_knowledge_graph,
    prepare_document_concept_graph,
    prepare_graph_view,
    prepare_raw_provenance_graph,
    run_build_library_command,
    run_convert_update_command,
    run_library_search,
    run_obsidian_export_for_gui,
    scan_source_folder_for_gui,
    search_result_table_rows,
    suggest_workspace_path,
    summarize_library_output,
    summarize_obsidian_export_output,
    summarize_conversion_output,
    validate_workspace_paths,
    workspace_status_json_for_download,
    workspace_traceability_display,
)
from office2md.library import build_library, library_report, locate_document, open_chunk, search_library, search_library_diagnostics, search_library_facets
from office2md.workspace import init_workspace, register_library_version, register_output_version, scan_workspace_sources


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


def test_open_chunk_returns_existing_chunk_by_exact_id(tmp_path):
    library_dir = _open_chunk_library(tmp_path)

    result = open_chunk(library_dir, "target_chunk", context=0)

    assert result is not None
    assert result["context_chunks"] == []
    target = result["target_chunk"]
    assert target["chunk_id"] == "target_chunk"
    assert target["document_id"] == "open-doc"
    assert target["document_title"] == "Open Manual"
    assert target["source_file"] == "Open Manual.pdf"
    assert target["document_kind"] == "manual_pdf"
    assert target["evidence_type"] == "page"
    assert target["locator"] == "Page 2"
    assert target["confidence"] == "high"
    assert target["limitation"] is None
    assert target["text"] == "Target pump fault evidence"


def test_open_chunk_context_zero_returns_no_context(tmp_path):
    library_dir = _open_chunk_library(tmp_path)

    result = open_chunk(library_dir / "library.db", "target_chunk", context=0)

    assert result is not None
    assert result["context_chunks"] == []


def test_open_chunk_context_returns_same_document_context(tmp_path):
    library_dir = _open_chunk_library(tmp_path)

    result = open_chunk(library_dir, "target_chunk", context=2)

    assert result is not None
    context_ids = [item["chunk_id"] for item in result["context_chunks"]]
    assert context_ids == ["neighbor_page", "intro_chunk"]
    assert all(item["document_id"] == "open-doc" for item in result["context_chunks"])
    assert all("text" not in item for item in result["context_chunks"])
    assert result["context_chunks"][0]["locator"] == "Page 2"


def test_open_chunk_export_json_creates_parent_and_uses_contract(tmp_path):
    library_dir = _open_chunk_library(tmp_path)
    result = open_chunk(library_dir, "target_chunk", context=1)
    export_path = tmp_path / "nested" / "agent" / "open_chunk.json"

    payload = _open_chunk_json_payload(library_dir, "target_chunk", 1, result)
    _write_open_chunk_export_json(export_path, payload)
    parsed = json.loads(export_path.read_text(encoding="utf-8"))

    assert parsed["schema_version"] == "office2md.open_chunk.v1"
    assert parsed["request"]["chunk_id"] == "target_chunk"
    assert parsed["target_chunk"]["chunk_id"] == "target_chunk"
    assert parsed["context_chunks"][0]["chunk_id"] == "neighbor_page"
    assert parsed["evidence"] == {
        "source_file": "Open Manual.pdf",
        "locator": "Page 2",
        "chunk_id": "target_chunk",
        "document_id": "open-doc",
        "document_title": "Open Manual",
        "document_kind": "manual_pdf",
        "evidence_type": "page",
        "confidence": "high",
        "limitation": None,
    }
    assert parsed["limitations"] == []
    assert parsed["warnings"] == []


def test_open_chunk_missing_chunk_cli_fails_clearly(tmp_path):
    library_dir = _open_chunk_library(tmp_path)
    runner = CliRunner()

    result = runner.invoke(app, ["open-chunk", str(library_dir), "missing_chunk"])

    assert result.exit_code != 0
    assert "chunk_id not found: missing_chunk" in result.output


def test_open_chunk_cli_export_json_smoke(tmp_path):
    library_dir = _open_chunk_library(tmp_path)
    export_path = tmp_path / "nested" / "open" / "chunk.json"
    runner = CliRunner()

    result = runner.invoke(app, ["open-chunk", str(library_dir), "target_chunk", "--context", "1", "--export-json", str(export_path)])

    assert result.exit_code == 0
    assert "export_json:" in result.stdout
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert payload["target_chunk"]["chunk_id"] == "target_chunk"
    assert len(payload["context_chunks"]) == 1


def test_open_chunk_does_not_change_existing_search_behavior(tmp_path):
    library_dir = _open_chunk_library(tmp_path)
    before = search_library(library_dir, "pump fault", limit=3)

    assert open_chunk(library_dir, "target_chunk", context=2) is not None

    after = search_library(library_dir, "pump fault", limit=3)
    assert [item["chunk_id"] for item in after] == [item["chunk_id"] for item in before]
    assert [item["rank"] for item in after] == [item["rank"] for item in before]


def test_locate_document_export_json_writes_valid_contract(tmp_path):
    library_dir = _open_chunk_library(tmp_path)
    results = locate_document(library_dir, "Open", limit=5)
    export_path = tmp_path / "nested" / "locate" / "documents.json"

    payload = _locate_document_export_json_payload(library_dir, "Open", 5, results)
    _write_locate_document_export_json(export_path, payload)
    parsed = json.loads(export_path.read_text(encoding="utf-8"))

    assert parsed["schema_version"] == "office2md.locate_document.v1"
    assert parsed["request"]["query"] == "Open"
    assert parsed["matches"] == [
        {
            "document_id": "open-doc",
            "document_title": "Open Manual",
            "source_file": "Open Manual.pdf",
            "document_kind": "manual_pdf",
            "output_dir": "manual",
            "source_path": "C:/src/Open Manual.pdf",
            "chunks_count": 3,
        }
    ]
    assert parsed["warnings"] == []
    assert parsed["limitations"] == []


def test_locate_document_cli_default_output_and_export_json(tmp_path):
    library_dir = _open_chunk_library(tmp_path)
    export_path = tmp_path / "nested" / "locate" / "documents.json"
    runner = CliRunner()

    result = runner.invoke(app, ["locate-document", str(library_dir), "Open", "--export-json", str(export_path)])

    assert result.exit_code == 0
    assert "locate-document: Open" in result.stdout
    assert "export_json:" in result.stdout
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "office2md.locate_document.v1"
    assert payload["matches"][0]["document_id"] == "open-doc"


def test_build_report_context_export_json_includes_evidence_fields(tmp_path):
    library_dir = _open_chunk_library(tmp_path)
    results = search_library(library_dir, "pump fault", limit=3, related=1)
    diagnostics = search_library_diagnostics("pump fault", results)
    export_path = tmp_path / "nested" / "reports" / "context.json"

    payload = _report_context_json_payload(library_dir, "pump fault", 3, 1, {"kind": [], "evidence": [], "document": None, "output_dir": None, "entity": [], "exclude_doc": [], "has_locator": False}, results, diagnostics)
    _write_report_context_export_json(export_path, payload)
    parsed = json.loads(export_path.read_text(encoding="utf-8"))

    assert parsed["schema_version"] == "office2md.report_context.v1"
    assert parsed["request"]["query"] == "pump fault"
    assert parsed["matches"]["shown_count"] == len(results)
    first = parsed["selected_evidence"][0]
    assert first["chunk_id"] == results[0]["chunk_id"]
    assert first["source_file"] == "Open Manual.pdf"
    assert first["locator"]
    assert first["document_title"] == "Open Manual"
    assert first["document_kind"] == "manual_pdf"
    assert first["evidence_type"]
    assert "confidence" in first
    assert "limitation" in first
    assert parsed["supporting_chunks"]
    assert parsed["coverage"]["selected_evidence_count"] == len(results)


def test_build_report_context_cli_export_json_and_preserves_search_order(tmp_path):
    library_dir = _open_chunk_library(tmp_path)
    before = search_library(library_dir, "pump fault", limit=3, related=1)
    export_path = tmp_path / "nested" / "reports" / "context.json"
    runner = CliRunner()

    result = runner.invoke(app, ["build-report-context", str(library_dir), "pump fault", "--limit", "3", "--context", "1", "--export-json", str(export_path)])

    assert result.exit_code == 0
    assert "build-report-context" in result.stdout
    assert "export_json:" in result.stdout
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert [item["chunk_id"] for item in payload["selected_evidence"]] == [item["chunk_id"] for item in before]
    after = search_library(library_dir, "pump fault", limit=3, related=1)
    assert [item["chunk_id"] for item in after] == [item["chunk_id"] for item in before]


def test_build_report_context_no_results_records_warning(tmp_path):
    library_dir = _open_chunk_library(tmp_path)
    runner = CliRunner()
    export_path = tmp_path / "nested" / "reports" / "empty.json"

    result = runner.invoke(app, ["build-report-context", str(library_dir), "no-such-query", "--export-json", str(export_path)])

    assert result.exit_code == 0
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert payload["selected_evidence"] == []
    assert payload["supporting_chunks"] == []
    assert payload["warnings"] == ["no results found"]
    assert payload["diagnostics"]["hints"] == ["no results found; try an identifier, known alias, or shorter terms"]


def test_gui_search_helpers_reuse_existing_search_results(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
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
                "HMI screen group PLC speed",
                "Sheet: User Texts / Row: 2",
                sheet_name="User Texts",
                group_path="C1 Contr_1 / Einsaugungen",
                row_number=2,
            ),
        ],
        {"project_number": ["SY909735"], "equipment": ["PLC", "HMI"]},
    )
    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)

    gui_data = run_library_search(
        library_dir,
        "PLC",
        limit=5,
        diagnostics=True,
        facets=True,
        context=1,
        output_dir="hmi",
        entity="HMI",
    )
    direct_results = search_library(library_dir, "PLC", limit=5, output_dir="hmi", entities=["HMI"], related=1)

    assert [item["chunk_id"] for item in gui_data["results"]] == [item["chunk_id"] for item in direct_results]
    assert gui_data["rows"] == search_result_table_rows(direct_results)
    assert gui_data["diagnostics"]["result_count"] == direct_results[0]["total_hits"]
    assert gui_data["facets"]["document_kind"] == [{"value": "hmi_translation_xlsx", "count": 2}]

    export_payload = json.loads(gui_data["export_json"])
    assert export_payload["query"]["original_query"] == "PLC"
    assert export_payload["query"]["filters"]["output_dir"] == "hmi"
    assert export_payload["query"]["filters"]["entity"] == ["HMI"]
    assert export_payload["results"][0]["preview"]


def test_gui_graph_helpers_load_and_bound_existing_graph_export(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_doc(
        output_root / "manual",
        "manual-doc",
        "Operation manual.pdf",
        "manual_pdf",
        [
            _chunk("manual_page", "page", ["Title Page"], "SY909735 operation manual maintenance cooling water vacuum pump alarm fault", "Page 1", page_number=1),
            _chunk("manual_section", "section", ["3 Operation"], "Operation section maintenance procedure for cooling water", "Page 12", page_number=12),
        ],
        {"symex_number": ["SY909735"], "document_type": ["operating manual"]},
    )
    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)

    graph = load_library_graph(library_dir)
    summary = graph_summary(graph)
    raw_view = prepare_raw_provenance_graph(graph, max_nodes=3, node_type="document", keyword="manual", show_isolated=True)
    concept_index = load_curated_concept_index(library_dir)
    knowledge_view = prepare_curated_knowledge_graph(concept_index, max_nodes=30)
    maintenance_view = prepare_curated_knowledge_graph(concept_index, max_nodes=30, keyword="maintenance")
    document_concept_view = prepare_document_concept_graph(concept_index, max_nodes=30)

    assert summary["node_count"] == len(graph["nodes"])
    assert summary["edge_count"] == len(graph["edges"])
    assert "document" in graph_node_types(graph)
    assert len(raw_view["nodes"]) <= 3
    assert any(node["type"] == "document" for node in raw_view["nodes"])
    assert any(row["label"] == "Operation manual" for row in raw_view["node_rows"])
    assert prepare_graph_view(graph, max_nodes=3, node_type="document", keyword="manual") == raw_view

    assert knowledge_view["nodes"]
    assert all(node["type"] == "concept" for node in knowledge_view["nodes"])
    assert all(node["label"] not in {"min", "en-GB", "zh-CN", "User Texts", "2019"} for node in knowledge_view["nodes"])
    assert all(node["type"] not in {"chunk", "asset", "source_page"} for node in knowledge_view["nodes"])
    assert all(edge["relation_type"] not in {"document_has_chunk", "document_has_asset", "chunk_has_source_locator"} for edge in knowledge_view["edges"])
    assert {edge["relation_type"] for edge in knowledge_view["edges"]} <= {"co_mentions", "co_occurs"}
    knowledge_labels = {node["label"].casefold() for node in knowledge_view["nodes"]}
    assert {"cooling water", "vacuum pump", "alarm", "fault", "operation manual", "maintenance"}.issubset(knowledge_labels)
    assert "maintenance" in {node["label"].casefold() for node in maintenance_view["nodes"]}
    hidden_label_html = graph_view_html(knowledge_view)
    visible_label_html = graph_view_html(knowledge_view, show_edge_labels=True)
    assert '"label": ""' in hidden_label_html
    assert '"label": "co_mentions"' not in hidden_label_html
    assert "co_mentions" in hidden_label_html
    assert '"label": "co_mentions"' in visible_label_html
    layout_options = json.loads(graph_layout_options())
    assert layout_options["layout"]["randomSeed"] == 42
    assert layout_options["physics"]["stabilization"]["enabled"] is True

    assert document_concept_view["nodes"]
    assert {node["type"] for node in document_concept_view["nodes"]} <= {"document", "concept"}
    assert {edge["relation_type"] for edge in document_concept_view["edges"]} <= {"document_mentions_concept"}


def test_gui_library_native_graph_does_not_force_equipment_vocabulary(tmp_path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_doc(
        output_root / "resume",
        "resume-doc",
        "Interview Resume.txt",
        "document",
        [
            _chunk(
                "resume_intro",
                "text",
                ["Interview Preparation"],
                "Interview resume portfolio. Participated in HPLC analytical method validation and stakeholder collaboration.",
                None,
            ),
            _chunk(
                "resume_project",
                "text",
                ["Project Experience"],
                "Built regulatory submission tracker, analytics dashboard, and cross functional project documentation.",
                None,
            ),
        ],
        {"candidate_topic": ["interview preparation"], "skill": ["regulatory submission", "HPLC"]},
    )
    _write_doc(
        output_root / "assessment",
        "assessment-doc",
        "Assessment Form.xlsx",
        "document",
        [
            _chunk(
                "assessment_cover",
                "text",
                ["Cover Sheet"],
                "Private confidential. Liang private candidate contact details and caner sheet fragment.",
                None,
            ),
            _chunk(
                "assessment_case",
                "table",
                ["Assessment for Case Study"],
                "Assessment for Case Study leadership logical thinking technical background risk level quality risk.",
                None,
            ),
            _chunk(
                "assessment_business",
                "table",
                ["Packaging Selection"],
                "Food Science drug discovery packaging selection new tooling cosmetic procedures quality risk.",
                None,
            ),
        ],
        {"assessment_topic": ["Assessment for Case Study"], "competency": ["Leadership", "Logical Thinking", "Technical Background"]},
    )
    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)

    concept_index = load_curated_concept_index(library_dir)
    knowledge_view = prepare_curated_knowledge_graph(concept_index, max_nodes=80)
    document_concept_view = prepare_document_concept_graph(concept_index, max_nodes=80)
    labels = {node["label"].casefold() for node in knowledge_view["nodes"]}

    assert "interview preparation" in labels
    assert "regulatory submission" in labels
    assert "assessment for case study" in labels
    assert "leadership" in labels
    assert "logical thinking" in labels
    assert "technical background" in labels
    assert "food science" in labels
    assert "drug discovery" in labels
    assert "quality risk" in labels
    assert "packaging selection" in labels
    assert "risk level" in labels
    assert any("hplc" in label for label in labels)
    assert "plc" not in labels
    assert "cip" not in labels
    assert "vfd" not in labels
    assert "vacuum pump" not in labels
    assert "untitled source page" not in labels
    assert "cover" not in labels
    assert "sheet" not in labels
    assert "cover sheet" not in labels
    assert "private confidential" not in labels
    assert "liang private" not in labels
    assert "selection new" not in labels
    assert "caner sheet" not in labels
    assert all(node["type"] == "concept" for node in knowledge_view["nodes"])
    assert all(node["type"] in {"document", "concept"} for node in document_concept_view["nodes"])
    assert all(edge["relation_type"] == "document_mentions_concept" for edge in document_concept_view["edges"])


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


def test_gui_build_update_dry_run_helpers_scan_and_preview_commands(tmp_path):
    source = tmp_path / "source files"
    source.mkdir()
    workspace = tmp_path / "source files-office2md-output"
    paths = derive_workspace_paths(workspace)
    conversion_output = paths["conversion_output_folder"]
    library_output = paths["library_output_folder"]
    log_folder = paths["log_folder"]
    (source / "Manual One.pdf").write_text("manual", encoding="utf-8")
    (source / "Notes.txt").write_text("notes", encoding="utf-8")
    (source / "ignore.tmp").write_text("ignore", encoding="utf-8")
    (source / "~$lock.docx").write_text("lock", encoding="utf-8")
    completed_folder = conversion_output / "manual-one"
    completed_folder.mkdir(parents=True)
    (completed_folder / "manifest.json").write_text(json.dumps({"status": "success"}), encoding="utf-8")
    failed_folder = conversion_output / "failed"
    failed_folder.mkdir()
    (failed_folder / "manifest.json").write_text(json.dumps({"status": "failed"}), encoding="utf-8")

    dry_run = scan_source_folder_for_gui(source, conversion_output, max_files=1)

    assert dry_run["supported_files_count"] == 2
    assert dry_run["selected_files_count"] == 1
    assert dry_run["expected_unique_manifest_count"] == 1
    assert dry_run["existing_manifest_count"] == 2
    assert dry_run["completed_expected_manifest_count"] == 1
    assert dry_run["failed_manifest_count"] == 1
    assert dry_run["target_reached"] is True
    assert count_existing_manifests(conversion_output)["failed_manifest_count"] == 1
    assert not library_output.exists()
    assert not log_folder.exists()
    assert suggest_workspace_path(source) == workspace
    assert paths["workspace_folder"] == workspace
    assert paths["conversion_output_folder"] == workspace / "conversion"
    assert paths["library_output_folder"] == workspace / "library"
    assert paths["log_folder"] == workspace / "logs"
    assert len({paths["conversion_output_folder"], paths["library_output_folder"], paths["log_folder"]}) == 3
    validate_workspace_paths(source, workspace)
    assert is_conversion_output_path(conversion_output)
    assert not is_valid_library_path(conversion_output)

    full_dry_run = scan_source_folder_for_gui(source, conversion_output, full_directory=True)
    assert full_dry_run["selected_files_count"] == 2
    assert full_dry_run["expected_unique_manifest_count"] == 2

    runner_command = build_runner_command_preview(source, conversion_output, log_folder, max_files=1, timeout_minutes=7, max_attempts=2)
    full_runner_command = build_runner_command_preview(source, conversion_output, log_folder, full_directory=True)
    build_command = build_library_command_preview(conversion_output, library_output)
    summary = summarize_conversion_output(conversion_output)

    assert '-InputPath "' in runner_command
    assert "-MaxFiles 1" in runner_command
    assert "-TimeoutMinutes 7" in runner_command
    assert "-MaxAttempts 2" in runner_command
    assert "-DryRun" not in runner_command
    assert "-FullDirectory" in full_runner_command
    assert "-MaxFiles" not in full_runner_command
    assert "build-library" in build_command
    assert f'"{conversion_output}"' in build_command
    assert f'"{library_output}"' in build_command
    assert summary["final_manifest_count"] == 2
    assert summary["failed_manifest_count"] == 1

    try:
        validate_workspace_paths(source, source)
    except ValueError as exc:
        assert "must not be the same" in str(exc)
    else:
        raise AssertionError("Expected workspace validation to reject source folder reuse.")


def test_gui_convert_update_helper_validates_before_runner_execution(tmp_path):
    missing_source = tmp_path / "missing source"
    conversion_output = tmp_path / "conversion output"
    log_folder = tmp_path / "dryrun logs"

    try:
        run_convert_update_command(
            missing_source,
            conversion_output,
            log_folder,
            max_files=1,
            runner_script=tmp_path / "missing-runner.ps1",
            cwd=tmp_path,
        )
    except FileNotFoundError as exc:
        assert "Source folder does not exist" in str(exc)
    else:
        raise AssertionError("Expected missing source validation to fail before runner execution.")

    assert not conversion_output.exists()
    assert not log_folder.exists()


def test_gui_build_library_helpers_build_and_summarize_tiny_library(tmp_path):
    conversion_output = tmp_path / "conversion output"
    library_output = tmp_path / "library output"
    _write_doc(
        conversion_output / "sample",
        "sample-doc",
        "sample.txt",
        "document",
        [_chunk("sample_text", "text", [], "Sample text for GUI build library", None)],
        {"topic": ["sample"]},
    )

    assert not is_valid_library_path(conversion_output)
    command = build_library_command_preview(conversion_output, library_output)
    assert "build-library" in command
    assert f'"{conversion_output}"' in command
    assert f'"{library_output}"' in command

    before_summary = summarize_library_output(library_output)
    assert before_summary["is_valid_library"] is False
    assert before_summary["library_db_exists"] is False

    result = run_build_library_command(conversion_output, library_output, cwd=Path.cwd(), subprocess_timeout_seconds=120)

    assert result["exit_code"] == 0
    assert result["summary"]["is_valid_library"] is True
    assert result["summary"]["library_db_exists"] is True
    assert result["summary"]["library_index_exists"] is True
    assert result["summary"]["library_graph_exists"] is True
    assert result["summary"]["library_markdown_exists"] is True
    assert result["summary"]["quality_report_exists"] is True
    assert result["summary"]["documents_count"] == 1
    assert result["summary"]["chunks_count"] == 1
    assert is_valid_library_path(library_output)


def test_gui_obsidian_export_helpers_preview_dry_run_and_summary(tmp_path):
    library_dir = _tiny_gui_export_library(tmp_path)
    vault = tmp_path / "vault"

    command = build_obsidian_export_command_preview(
        library_dir,
        vault,
        overwrite=True,
        dry_run=True,
        max_concepts=20,
        max_evidence_per_concept=3,
    )
    assert "export-obsidian" in command
    assert "--overwrite" in command
    assert "--dry-run" in command
    assert "--max-concepts 20" in command
    assert "--max-evidence-per-concept 3" in command

    preview = run_obsidian_export_for_gui(library_dir, vault, dry_run=True, max_concepts=20)
    assert preview["documents_exported"] == 1
    assert not vault.exists()

    result = run_obsidian_export_for_gui(library_dir, vault, max_concepts=20)
    summary = summarize_obsidian_export_output(vault)
    assert result["documents_exported"] == 1
    assert summary["manifest_exists"] is True
    assert summary["manifest"]["export_type"] == "obsidian"
    assert summary["documents_exported"] == 1
    assert summary["index_exists"] is True


def test_gui_obsidian_export_helper_validates_library_and_overwrite(tmp_path):
    library_dir = _tiny_gui_export_library(tmp_path)
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "existing.md").write_text("keep", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="Built library folder"):
        run_obsidian_export_for_gui(tmp_path / "missing-library", tmp_path / "missing-vault")
    with pytest.raises(RuntimeError, match="non-empty"):
        run_obsidian_export_for_gui(library_dir, vault)


def test_gui_workspace_status_helper_loads_init_only_workspace(tmp_path):
    workspace = tmp_path / "project.office2md"
    init_workspace(workspace)

    status = load_workspace_status_for_gui(workspace)
    payload = json.loads(workspace_status_json_for_download(status))
    hint = classify_workspace_path_hint(workspace)
    next_steps = build_workspace_next_step_hints(status)
    traceability = workspace_traceability_display(status)

    assert status["workspace"]["workspace_path"] == str(workspace.resolve())
    assert status["source_manifest"]["total_sources"] == 0
    assert status["library_versions"]["total_versions"] == 0
    assert status["output_versions"]["total_versions"] == 0
    assert payload["traceability"]["source_manifest_hash"].startswith("sha256:")
    assert hint["is_workspace"] is True
    assert hint["kind"] == "workspace_root"
    assert len(next_steps) == 3
    assert "workspace-scan" in next_steps[0]
    assert traceability["complete"] is False
    assert traceability["text"] == ""
    assert traceability["next_required_step"] == "Register a library version."


def test_gui_workspace_status_helper_handles_invalid_workspace_path(tmp_path):
    with pytest.raises(ValueError, match="workspace-init"):
        load_workspace_status_for_gui(tmp_path / "missing.office2md")


def test_gui_workspace_path_hint_identifies_built_library_folder(tmp_path):
    library_dir = _tiny_gui_export_library(tmp_path)

    hint = classify_workspace_path_hint(library_dir)

    assert hint["is_workspace"] is False
    assert hint["kind"] == "built_library"
    assert "Library folder" in hint["message"]


def test_gui_workspace_path_hint_identifies_obsidian_export_folder(tmp_path):
    vault = _write_tiny_gui_obsidian_vault(tmp_path / "vault")

    hint = classify_workspace_path_hint(vault)

    assert hint["is_workspace"] is False
    assert hint["kind"] == "obsidian_export"
    assert "Obsidian export" in hint["message"]


def test_gui_workspace_path_hint_identifies_conversion_output_folder(tmp_path):
    conversion_output = tmp_path / "interview-office2md-output"
    _write_doc(
        conversion_output / "sample",
        "sample-doc",
        "sample.txt",
        "document",
        [_chunk("sample", "text", ["Sample"], "sample text", "Line 1")],
        {},
    )

    hint = classify_workspace_path_hint(conversion_output)
    command = build_workspace_init_command_hint(conversion_output)

    assert hint["is_workspace"] is False
    assert hint["kind"] == "conversion_output"
    assert "Knowledge Pack" in hint["message"]
    assert str(tmp_path / "interview.office2md") in command
    assert "workspace-init" in command


def test_gui_workspace_path_hint_identifies_output_workspace_suffix(tmp_path):
    output_workspace = tmp_path / "interview-office2md-output"
    output_workspace.mkdir()

    hint = classify_workspace_path_hint(output_workspace)

    assert hint["is_workspace"] is False
    assert hint["kind"] == "output_workspace"
    assert "not a workspace root" in hint["message"]
    assert str(tmp_path / "interview.office2md") in hint["workspace_init_command"]


def test_gui_workspace_status_helper_loads_full_traceability_workspace(tmp_path):
    workspace = tmp_path / "project.office2md"
    source = tmp_path / "sources"
    source.mkdir()
    (source / "sample.txt").write_text("sample", encoding="utf-8")
    init_workspace(workspace)
    scan_workspace_sources(workspace, source)
    library_dir = _tiny_gui_export_library(tmp_path)
    library_record = register_library_version(workspace, library_dir, label="tiny-library")["record"]
    vault = _write_tiny_gui_obsidian_vault(tmp_path / "vault")
    output_record = register_output_version(workspace, vault, label="tiny-output")["record"]

    status = load_workspace_status_for_gui(workspace, show_history=True, limit=1)
    payload = json.loads(workspace_status_json_for_download(status))

    assert status["source_manifest"]["total_sources"] == 1
    assert status["library_versions"]["latest"]["library_version_id"] == library_record["library_version_id"]
    assert status["output_versions"]["latest"]["output_version_id"] == output_record["output_version_id"]
    assert status["traceability"]["library_version_id"] == library_record["library_version_id"]
    assert status["traceability"]["output_version_id"] == output_record["output_version_id"]
    traceability = workspace_traceability_display(status)
    assert status["output_versions"]["latest"]["export_manifest"]["export_type"] == "obsidian"
    assert traceability["complete"] is True
    assert library_record["library_version_id"] in traceability["text"]
    assert output_record["output_version_id"] in traceability["text"]
    assert len(status["library_versions"]["history"]) == 1
    assert len(status["output_versions"]["history"]) == 1
    assert payload["workspace"]["workspace_path"] == str(workspace.resolve())


def _tiny_gui_export_library(tmp_path: Path) -> Path:
    conversion_output = tmp_path / "conversion"
    _write_doc(
        conversion_output / "sample",
        "sample-doc",
        "sample.txt",
        "document",
        [
            _chunk("sample_overview", "text", ["Overview"], "Knowledge Retrieval overview.", "Section: Overview"),
            _chunk("sample_evidence", "text", ["Evidence"], "Knowledge Retrieval evidence.", "Section: Evidence"),
        ],
        {"topic": ["Knowledge Retrieval"]},
    )
    library_dir = tmp_path / "library"
    build_library(conversion_output, library_dir)
    return library_dir


def _write_tiny_gui_obsidian_vault(path: Path) -> Path:
    path.mkdir(parents=True)
    (path / "00_Index.md").write_text("# Index\n", encoding="utf-8")
    (path / "00_Library_Report.md").write_text("# Report\n", encoding="utf-8")
    (path / "Documents").mkdir()
    (path / "Concepts").mkdir()
    manifest_dir = path / "_office2md"
    manifest_dir.mkdir()
    (manifest_dir / "export_manifest.json").write_text(
        json.dumps(
            {
                "export_type": "obsidian",
                "documents_exported": 1,
                "concepts_exported": 1,
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    return path


def _open_chunk_library(tmp_path: Path) -> Path:
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_doc(
        output_root / "manual",
        "open-doc",
        "Open Manual.pdf",
        "manual_pdf",
        [
            _chunk("intro_chunk", "section", ["Intro"], "Intro context", "Page 1", page_number=1),
            _chunk("target_chunk", "page", ["Faults"], "Target pump fault evidence", "Page 2", page_number=2, confidence="high"),
            _chunk("neighbor_page", "page", ["Faults"], "Neighbor pump fault context", "Page 2", page_number=2),
        ],
        {"equipment": ["pump"]},
    )
    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)
    return library_dir


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
