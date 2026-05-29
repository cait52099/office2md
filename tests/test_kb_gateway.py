import json
from pathlib import Path

from typer.testing import CliRunner

from office2md.cli import app
from office2md.kb_gateway import AGENT_CONTEXT_SCHEMA_VERSION, kb_context, kb_review
from office2md.library import build_library, open_chunk, search_library
from office2md.library_catalog import add_library_to_catalog
from office2md.incremental import save_source_registry


runner = CliRunner()


def test_kb_list_json_from_catalog(tmp_path):
    catalog, _, _ = _catalog_with_two_libraries(tmp_path)

    result = runner.invoke(app, ["kb-list", str(catalog), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "office2md.library_catalog.v1"
    assert payload["libraries_count"] == 2


def test_kb_context_one_library_includes_provenance(tmp_path):
    catalog, lib_a, _ = _catalog_with_two_libraries(tmp_path)

    payload = kb_context(catalog, "pump", library_ids=["lib-a"], limit=2, context=1)

    assert payload["schema_version"] == AGENT_CONTEXT_SCHEMA_VERSION
    assert payload["selected_libraries"][0]["library_id"] == "lib-a"
    assert payload["evidence"]
    item = payload["evidence"][0]
    assert item["library_id"] == "lib-a"
    assert item["library_name"] == "Library A"
    assert item["library_path"] == str(lib_a.resolve())
    assert item["source_file"].endswith("a.txt")
    assert item["chunk_id"]
    assert item["document_id"]


def test_kb_context_two_libraries_preserves_each_library(tmp_path):
    catalog, _, _ = _catalog_with_two_libraries(tmp_path)

    payload = kb_context(catalog, "pump", library_ids=["lib-a", "lib-b"], limit=2, context=0)

    library_ids = {item["library_id"] for item in payload["evidence"]}
    assert library_ids == {"lib-a", "lib-b"}


def test_kb_context_stale_library_returns_warning_and_next_steps(tmp_path):
    catalog, _, source_a = _catalog_with_two_libraries(tmp_path)
    (source_a / "a.txt").write_text("changed pump evidence", encoding="utf-8")

    payload = kb_context(catalog, "pump", library_ids=["lib-a"], limit=1, context=0)

    assert any("lib-a" in warning for warning in payload["warnings"])
    assert payload["next_steps"]
    assert payload["library_status"][0]["status"] == "stale"


def test_kb_context_unknown_library_id_fails_clearly(tmp_path):
    catalog, _, _ = _catalog_with_two_libraries(tmp_path)

    result = runner.invoke(app, ["kb-context", str(catalog), "pump", "--library", "missing"])

    assert result.exit_code != 0
    assert "Unknown library_id" in result.output


def test_kb_review_does_not_run_update(tmp_path):
    catalog, lib_a, source_a = _catalog_with_two_libraries(tmp_path)
    (source_a / "a.txt").write_text("changed pump evidence", encoding="utf-8")

    payload = kb_review(catalog, "lib-a")

    assert payload["schema_version"] == "office2md.kb_review.v1"
    assert payload["review_summary"]["status"] == "stale"
    assert not (lib_a / "update_result.json").exists()


def test_existing_search_open_chunk_still_work(tmp_path):
    catalog, lib_a, _ = _catalog_with_two_libraries(tmp_path)

    results = search_library(lib_a, "pump")
    opened = open_chunk(lib_a, results[0]["chunk_id"])

    assert catalog.exists()
    assert results[0]["chunk_id"] == "a-chunk"
    assert opened["target_chunk"]["chunk_id"] == "a-chunk"


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
    _write_doc(out_a / "doc-a", "doc-a", str(file_a), "a-chunk", "alpha pump evidence")
    _write_doc(out_b / "doc-b", "doc-b", str(file_b), "b-chunk", "beta pump evidence")
    build_library(out_a, lib_a)
    build_library(out_b, lib_b)
    save_source_registry(lib_a)
    save_source_registry(lib_b)
    add_library_to_catalog(catalog, library_path=lib_a, library_id="lib-a", library_name="Library A", source_root=source_a)
    add_library_to_catalog(catalog, library_path=lib_b, library_id="lib-b", library_name="Library B", source_root=source_b)
    return catalog, lib_a, source_a


def _write_doc(path: Path, doc_id: str, source_file: str, chunk_id: str, text: str) -> None:
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
