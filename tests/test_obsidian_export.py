import json
from pathlib import Path

import pytest

from office2md.exports.obsidian import ObsidianExportError, export_obsidian, safe_note_name, unique_note_name
from office2md.library import build_library


def test_safe_filename_generation():
    assert safe_note_name('Bad:/\\Name*?"<>|.md') == "Bad Name .md"
    assert safe_note_name("   ...   ", fallback="document") == "document"


def test_duplicate_filename_suffix_is_stable():
    used = set()
    first = unique_note_name("Same Name", used, "doc-a")
    second = unique_note_name("Same Name", used, "doc-b")
    assert first == "Same Name"
    assert second.startswith("Same Name ")
    assert second == unique_note_name("Same Name", {"same name"}, "doc-b")


def test_dry_run_writes_no_files(tmp_path):
    library_dir = _tiny_library(tmp_path)
    vault = tmp_path / "vault"

    result = export_obsidian(library_dir, vault, dry_run=True)

    assert result["documents_exported"] == 2
    assert result["concepts_exported"] >= 1
    assert not vault.exists()


def test_non_empty_output_without_overwrite_fails(tmp_path):
    library_dir = _tiny_library(tmp_path)
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "existing.md").write_text("keep", encoding="utf-8")

    with pytest.raises(ObsidianExportError, match="non-empty"):
        export_obsidian(library_dir, vault)


def test_export_creates_expected_vault_structure(tmp_path):
    library_dir = _tiny_library(tmp_path)
    vault = tmp_path / "vault"

    export_obsidian(library_dir, vault)

    assert (vault / "00_Index.md").exists()
    assert (vault / "00_Library_Report.md").exists()
    assert (vault / "Documents").is_dir()
    assert (vault / "Concepts").is_dir()
    assert (vault / "_office2md" / "export_manifest.json").exists()


def test_export_accepts_library_db_path(tmp_path):
    library_dir = _tiny_library(tmp_path)
    vault = tmp_path / "vault"

    result = export_obsidian(library_dir / "library.db", vault)

    assert result["documents_exported"] == 2
    assert (vault / "_office2md" / "export_manifest.json").exists()


def test_document_note_has_frontmatter_and_related_concepts(tmp_path):
    library_dir = _tiny_library(tmp_path)
    vault = tmp_path / "vault"

    export_obsidian(library_dir, vault)

    notes = list((vault / "Documents").glob("*.md"))
    assert notes
    text = notes[0].read_text(encoding="utf-8")
    assert "office2md_type: document" in text
    assert "created_by: office2md" in text
    assert "## Related Concepts" in text
    assert "[[" in text


def test_concept_note_has_frontmatter_and_related_documents(tmp_path):
    library_dir = _tiny_library(tmp_path)
    vault = tmp_path / "vault"

    export_obsidian(library_dir, vault)

    notes = list((vault / "Concepts").glob("*.md"))
    assert notes
    text = notes[0].read_text(encoding="utf-8")
    assert "office2md_type: concept" in text
    assert "match_count:" in text
    assert "document_count:" in text
    assert "## Related Documents" in text
    assert "[[" in text


def test_export_manifest_counts_documents_and_concepts(tmp_path):
    library_dir = _tiny_library(tmp_path)
    vault = tmp_path / "vault"

    result = export_obsidian(library_dir, vault, max_concepts=10)
    manifest = json.loads((vault / "_office2md" / "export_manifest.json").read_text(encoding="utf-8"))

    assert manifest["documents_exported"] == result["documents_exported"] == 2
    assert manifest["concepts_exported"] == result["concepts_exported"]
    assert manifest["options"]["max_concepts"] == 10


def test_export_manifest_warns_when_assets_are_not_copied(tmp_path):
    library_dir = _tiny_library(tmp_path, with_assets=True)
    vault = tmp_path / "vault"

    result = export_obsidian(library_dir, vault)
    manifest = json.loads((vault / "_office2md" / "export_manifest.json").read_text(encoding="utf-8"))

    assert result["warnings"]
    assert "assets were not copied" in manifest["warnings"][0]


def test_no_fixed_equipment_vocabulary_is_used(tmp_path):
    library_dir = _tiny_library(tmp_path, entities={"custom_research_theme": ["Orchid Fermentation"], "project": ["PX-101"]})
    vault = tmp_path / "vault"

    export_obsidian(library_dir, vault, max_concepts=20)

    concept_text = "\n".join(path.read_text(encoding="utf-8") for path in (vault / "Concepts").glob("*.md"))
    assert "Orchid Fermentation" in concept_text


def test_tiny_library_end_to_end_export_smoke(tmp_path):
    library_dir = _tiny_library(tmp_path)
    vault = tmp_path / "vault"

    result = export_obsidian(library_dir, vault, max_concepts=5, max_evidence_per_concept=2)

    assert result["documents_exported"] == len(list((vault / "Documents").glob("*.md")))
    assert result["concepts_exported"] == len(list((vault / "Concepts").glob("*.md")))
    assert result["concepts_exported"] > 0


def _tiny_library(tmp_path: Path, entities: dict | None = None, with_assets: bool = False) -> Path:
    output_root = tmp_path / "output"
    output_root.mkdir()
    shared_entities = entities or {"project": ["SY909735"], "technology": ["Knowledge Retrieval"]}
    _write_doc(
        output_root / "alpha",
        "doc-alpha",
        "Alpha.txt",
        "text",
        [
            _chunk("alpha-1", "Knowledge Retrieval overview for SY909735.", "Overview"),
            _chunk("alpha-2", "Knowledge Retrieval appears again with field validation evidence.", "Evidence"),
        ],
        shared_entities,
        with_assets=with_assets,
    )
    _write_doc(
        output_root / "beta",
        "doc-beta",
        "Beta.txt",
        "text",
        [
            _chunk("beta-1", "SY909735 library export validates Knowledge Retrieval.", "Export"),
        ],
        shared_entities,
    )
    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)
    return library_dir


def _write_doc(path: Path, doc_id: str, source_file: str, document_kind: str, chunks: list[dict], entities: dict, with_assets: bool = False) -> None:
    path.mkdir(parents=True)
    manifest = {
        "source_file": source_file,
        "source_path": str(path / source_file),
        "checksum": f"sha256:{doc_id}",
        "engine": "test",
        "status": "success",
        "warnings": [],
        "errors": [],
        "document_kind": document_kind,
        "quality_status": "ok",
    }
    knowledge = {
        "title": Path(source_file).stem,
        "source_file": source_file,
        "document_kind": document_kind,
        "quality_status": "ok",
        "tags": ["test"],
        "key_metadata": {"source_path": str(path / source_file), "checksum": f"sha256:{doc_id}"},
    }
    (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (path / "knowledge.json").write_text(json.dumps(knowledge), encoding="utf-8")
    (path / "entities.json").write_text(json.dumps(entities), encoding="utf-8")
    (path / "source_map.json").write_text(json.dumps({chunk["chunk_id"]: {"locator": chunk["locator"]} for chunk in chunks}), encoding="utf-8")
    (path / "document.md").write_text("\n\n".join(chunk["text"] for chunk in chunks), encoding="utf-8")
    (path / "document.raw.md").write_text("\n\n".join(chunk["text"] for chunk in chunks), encoding="utf-8")
    (path / "document.json").write_text(json.dumps({"source_file": source_file}), encoding="utf-8")
    with (path / "chunks.jsonl").open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk) + "\n")
    if with_assets:
        assets = path / "assets"
        assets.mkdir()
        (assets / "page_001.png").write_bytes(b"not-a-real-image")


def _chunk(chunk_id: str, text: str, title: str) -> dict:
    return {
        "chunk_id": chunk_id,
        "source_file": "fixture.txt",
        "evidence_type": "text",
        "heading_path": [title],
        "title": title,
        "text": text,
        "locator": f"Section: {title}",
        "tags": ["test"],
    }
