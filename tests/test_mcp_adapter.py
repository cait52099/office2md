import json
from pathlib import Path

from office2md import mcp_adapter
from office2md.library import build_library
from office2md.library_catalog import add_library_to_catalog
from office2md.incremental import save_source_registry


def test_mcp_kb_list_wrapper(tmp_path):
    catalog, _, _ = _catalog_with_two_libraries(tmp_path)

    payload = mcp_adapter.kb_list(str(catalog))

    assert payload["schema_version"] == "office2md.library_catalog.v1"
    assert payload["libraries_count"] == 2


def test_mcp_kb_context_wrapper_one_library(tmp_path):
    catalog, lib_a, _ = _catalog_with_two_libraries(tmp_path)

    payload = mcp_adapter.kb_context(str(catalog), "pump", library_id="lib-a", limit=2, context=1)

    assert payload["schema_version"] == "office2md.agent_context.v1"
    assert payload["evidence"]
    evidence = payload["evidence"][0]
    assert evidence["library_id"] == "lib-a"
    assert evidence["library_name"] == "Library A"
    assert evidence["library_path"] == str(lib_a.resolve())
    assert evidence["source_file"]
    assert evidence["locator"]
    assert evidence["chunk_id"]
    assert evidence["document_id"]


def test_mcp_kb_context_wrapper_two_libraries(tmp_path):
    catalog, _, _ = _catalog_with_two_libraries(tmp_path)

    payload = mcp_adapter.kb_context(str(catalog), "pump", libraries="lib-a,lib-b", limit=2, context=0)

    assert payload["schema_version"] == "office2md.agent_context.v1"
    assert {item["library_id"] for item in payload["evidence"]} == {"lib-a", "lib-b"}


def test_mcp_kb_review_wrapper_remains_read_only(tmp_path):
    catalog, lib_a, source_a = _catalog_with_two_libraries(tmp_path)
    (source_a / "a.txt").write_text("changed pump evidence", encoding="utf-8")

    payload = mcp_adapter.kb_review(str(catalog), "lib-a")

    assert payload["schema_version"] == "office2md.kb_review.v1"
    assert payload["review_summary"]["status"] == "stale"
    assert not (lib_a / "update_result.json").exists()


def test_mcp_unknown_library_returns_clear_error(tmp_path):
    catalog, _, _ = _catalog_with_two_libraries(tmp_path)

    payload = mcp_adapter.kb_context(str(catalog), "pump", library_id="missing")

    assert payload["schema_version"] == "office2md.mcp_error.v1"
    assert "Unknown library_id" in payload["error"]["message"]
    assert payload["warnings"]


def _catalog_with_two_libraries(tmp_path):
    catalog = tmp_path / "libraries.json"
    source_a = tmp_path / "source-a"
    source_b = tmp_path / "source-b"
    out_a = tmp_path / "out-a"
    out_b = tmp_path / "out-b"
    lib_a = tmp_path / "lib-a"
    lib_b = tmp_path / "lib-b"
    source_a.mkdir()
    source_b.mkdir()
    file_a = source_a / "a.txt"
    file_b = source_b / "b.txt"
    file_a.write_text("alpha pump evidence", encoding="utf-8")
    file_b.write_text("beta pump evidence", encoding="utf-8")
    _write_doc(out_a / "doc-a", str(file_a), "a-chunk", "alpha pump evidence")
    _write_doc(out_b / "doc-b", str(file_b), "b-chunk", "beta pump evidence")
    build_library(out_a, lib_a)
    build_library(out_b, lib_b)
    save_source_registry(lib_a)
    save_source_registry(lib_b)
    add_library_to_catalog(catalog, library_path=lib_a, library_id="lib-a", library_name="Library A", source_root=source_a)
    add_library_to_catalog(catalog, library_path=lib_b, library_id="lib-b", library_name="Library B", source_root=source_b)
    return catalog, lib_a, source_a


def _write_doc(path: Path, source_file: str, chunk_id: str, text: str) -> None:
    path.mkdir(parents=True)
    manifest = {
        "status": "success",
        "source_file": Path(source_file).name,
        "source_path": source_file,
        "document_kind": "generic_text",
        "checksum": "sha256:test",
        "converter": "test",
    }
    chunk = {
        "chunk_id": chunk_id,
        "evidence_type": "text",
        "heading_path": [],
        "title": Path(source_file).stem,
        "text": text,
        "locator": "Line 1",
        "confidence": "high",
    }
    (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (path / "knowledge.json").write_text(json.dumps({"title": Path(source_file).stem, "document_kind": "generic_text"}), encoding="utf-8")
    (path / "entities.json").write_text("{}", encoding="utf-8")
    (path / "source_map.json").write_text(json.dumps({chunk_id: {"locator": "Line 1"}}), encoding="utf-8")
    (path / "document.md").write_text(text, encoding="utf-8")
    (path / "chunks.jsonl").write_text(json.dumps(chunk) + "\n", encoding="utf-8")
