import json
import os
from pathlib import Path
import subprocess
import sys

from typer.testing import CliRunner

from office2md.cli import app
from office2md.incremental import (
    CHANGE_PLAN_SCHEMA_VERSION,
    LIBRARY_STATE_SCHEMA_VERSION,
    LIBRARY_STATUS_SCHEMA_VERSION,
    SOURCE_REGISTRY_SCHEMA_VERSION,
    build_source_registry,
    default_library_state_path,
    default_source_registry_path,
    library_status,
    load_library_state,
    load_source_registry,
    save_library_state,
    save_source_registry,
    scan_changes,
    write_library_state,
    write_source_registry,
    _normalize_path_key,
)
from office2md.library import build_library, open_chunk, search_library
from office2md.models import ConvertOptions
from office2md.update_library import UPDATE_RESULT_SCHEMA_VERSION, update_library


runner = CliRunner()


def test_source_registry_write_and_read(tmp_path):
    library = tmp_path / "library"
    library.mkdir()
    registry_path = library / "source_registry.json"
    registry = {
        "schema_version": SOURCE_REGISTRY_SCHEMA_VERSION,
        "generated_at": "now",
        "library_path": str(library),
        "sources": [{"source_file": "a.txt", "status": "active"}],
        "warnings": [],
    }

    write_source_registry(registry_path, registry)
    loaded = load_source_registry(library)

    assert loaded["schema_version"] == SOURCE_REGISTRY_SCHEMA_VERSION
    assert loaded["sources"][0]["source_file"] == "a.txt"


def test_save_source_registry_default_and_export_path(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("source text", encoding="utf-8")
    output_root = tmp_path / "output"
    library = tmp_path / "library"
    _write_doc(output_root / "doc", "doc-id", str(source), "generic_text", [_chunk("chunk-1", "source text")])
    build_library(output_root, library)
    export_path = tmp_path / "exports" / "source_registry.json"

    saved_default = save_source_registry(library)
    saved_export = save_source_registry(library, output_path=export_path)

    assert default_source_registry_path(library).exists()
    assert export_path.exists()
    assert saved_default["schema_version"] == SOURCE_REGISTRY_SCHEMA_VERSION
    assert saved_export["registry_path"] == str(export_path.resolve())


def test_source_registry_cli_export_json(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("source text", encoding="utf-8")
    output_root = tmp_path / "output"
    library = tmp_path / "library"
    _write_doc(output_root / "doc", "doc-id", str(source), "generic_text", [_chunk("chunk-1", "source text")])
    build_library(output_root, library)
    export_path = tmp_path / "exports" / "source_registry.json"

    result = runner.invoke(app, ["source-registry", str(library), "--export-json", str(export_path)])

    assert result.exit_code == 0
    loaded = json.loads(export_path.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == SOURCE_REGISTRY_SCHEMA_VERSION
    assert len(loaded["sources"]) == 1


def test_library_state_write_read_and_status_fallback(tmp_path):
    library = tmp_path / "library"
    library.mkdir()
    state_path = default_library_state_path(library)
    state = {
        "schema_version": LIBRARY_STATE_SCHEMA_VERSION,
        "generated_at": "now",
        "library_path": str(library),
        "library_state_path": str(state_path),
        "status": "stale",
        "counts": {"registered_sources": 0},
        "warnings": [],
    }

    write_library_state(state_path, state)
    loaded = load_library_state(library)
    status = library_status(library)

    assert loaded["schema_version"] == LIBRARY_STATE_SCHEMA_VERSION
    assert loaded["status"] == "stale"
    assert status["library_state_exists"] is True
    assert status["state_status"] == "stale"
    assert status["status"] == "stale"


def test_save_library_state_writes_default_state(tmp_path):
    library = tmp_path / "library"
    library.mkdir()

    state = save_library_state(library)
    loaded = load_library_state(library)

    assert default_library_state_path(library).exists()
    assert state["schema_version"] == LIBRARY_STATE_SCHEMA_VERSION
    assert loaded["schema_version"] == LIBRARY_STATE_SCHEMA_VERSION


def test_library_status_cli_write_state(tmp_path):
    library = tmp_path / "library"
    library.mkdir()
    state_path = tmp_path / "state" / "library_state.json"

    result = runner.invoke(app, ["library-status", str(library), "--write-state", "--state-output", str(state_path)])

    assert result.exit_code == 0
    assert state_path.exists()
    loaded = json.loads(state_path.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == LIBRARY_STATE_SCHEMA_VERSION


def test_scan_changes_classifies_new_modified_unchanged_deleted_and_unsupported(tmp_path):
    source = tmp_path / "source"
    library = tmp_path / "library"
    source.mkdir()
    library.mkdir()
    unchanged = source / "unchanged.txt"
    modified = source / "modified.txt"
    new_file = source / "new.txt"
    unsupported = source / "notes.tmp"
    deleted = source / "deleted.txt"
    unchanged.write_text("same", encoding="utf-8")
    modified.write_text("before", encoding="utf-8")
    new_file.write_text("new", encoding="utf-8")
    unsupported.write_text("unsupported", encoding="utf-8")
    deleted.write_text("gone", encoding="utf-8")

    registry = _registry(library, [_source_record(unchanged, source), _source_record(modified, source), _source_record(deleted, source)])
    modified.write_text("after", encoding="utf-8")
    deleted.unlink()

    plan = scan_changes(source, library, registry_path=_write_registry(library, registry), dry_run=True)

    assert plan["schema_version"] == CHANGE_PLAN_SCHEMA_VERSION
    assert plan["counts"]["unchanged"] == 1
    assert plan["counts"]["modified"] == 1
    assert plan["counts"]["new"] == 1
    assert plan["counts"]["deleted_missing"] == 1
    assert plan["counts"]["unsupported"] == 1


def test_macos_path_key_normalization_is_case_insensitive(monkeypatch):
    monkeypatch.setattr("office2md.incremental.sys.platform", "darwin")

    assert _normalize_path_key("/private/var/Folders/Example/Source.TXT") == _normalize_path_key("/private/var/folders/example/source.txt")


def test_scan_changes_detects_moved_or_renamed_candidate(tmp_path):
    source = tmp_path / "source"
    library = tmp_path / "library"
    source.mkdir()
    library.mkdir()
    old = source / "old.txt"
    old.write_text("same content", encoding="utf-8")
    registry = _registry(library, [_source_record(old, source)])
    old.unlink()
    renamed = source / "renamed.txt"
    renamed.write_text("same content", encoding="utf-8")

    plan = scan_changes(source, library, registry_path=_write_registry(library, registry), dry_run=True)

    assert plan["counts"]["moved_or_renamed_candidate"] == 1
    assert plan["counts"]["deleted_missing"] == 0


def test_scan_changes_export_json_writes_change_plan(tmp_path):
    source = tmp_path / "source"
    library = tmp_path / "library"
    source.mkdir()
    library.mkdir()
    (source / "new.txt").write_text("new", encoding="utf-8")
    export_path = tmp_path / "plans" / "change_plan.json"

    plan = scan_changes(source, library, export_json=export_path, dry_run=False)
    loaded = json.loads(export_path.read_text(encoding="utf-8"))

    assert loaded["schema_version"] == CHANGE_PLAN_SCHEMA_VERSION
    assert loaded["counts"] == plan["counts"]


def test_scan_changes_dry_run_does_not_write_change_plan(tmp_path):
    source = tmp_path / "source"
    library = tmp_path / "library"
    source.mkdir()
    library.mkdir()
    (source / "new.txt").write_text("new", encoding="utf-8")
    export_path = tmp_path / "change_plan.json"

    scan_changes(source, library, export_json=export_path, dry_run=True)

    assert not export_path.exists()


def test_library_status_reports_current_and_stale(tmp_path):
    source = tmp_path / "source"
    library = tmp_path / "library"
    source.mkdir()
    library.mkdir()
    file_path = source / "a.txt"
    file_path.write_text("same", encoding="utf-8")
    _write_registry(library, _registry(library, [_source_record(file_path, source)]))

    current = library_status(library)
    file_path.write_text("changed", encoding="utf-8")
    stale = library_status(library)

    assert current["schema_version"] == LIBRARY_STATUS_SCHEMA_VERSION
    assert current["status"] == "current"
    assert stale["status"] == "stale"
    assert stale["counts"]["stale_sources"] == 1


def test_library_status_summarizes_change_plan(tmp_path):
    source = tmp_path / "source"
    library = tmp_path / "library"
    source.mkdir()
    library.mkdir()
    (source / "new.txt").write_text("new", encoding="utf-8")
    export_path = tmp_path / "change_plan.json"
    scan_changes(source, library, export_json=export_path, dry_run=False)

    status = library_status(library, change_plan_path=export_path)

    assert status["status"] == "stale"
    assert status["pending_changes"]["new"] == 1
    assert status["next_steps"]
    assert any("update-library" in step for step in status["next_steps"])


def test_library_status_cli_json(tmp_path):
    library = tmp_path / "library"
    library.mkdir()

    result = runner.invoke(app, ["library-status", str(library), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == LIBRARY_STATUS_SCHEMA_VERSION
    assert payload["next_steps"]
    assert any("source registry" in step for step in payload["next_steps"])


def test_library_status_readable_output_shows_next_steps(tmp_path):
    library = tmp_path / "library"
    library.mkdir()

    result = runner.invoke(app, ["library-status", str(library)])

    assert result.exit_code == 0
    assert "next steps" in result.stdout


def test_scan_changes_cli_help_and_export(tmp_path):
    source = tmp_path / "source"
    library = tmp_path / "library"
    source.mkdir()
    library.mkdir()
    (source / "new.txt").write_text("new", encoding="utf-8")
    export_path = tmp_path / "change_plan.json"

    help_result = runner.invoke(app, ["scan-changes", "--help"])
    result = runner.invoke(app, ["scan-changes", str(source), str(library), "--export-json", str(export_path)])

    assert help_result.exit_code == 0
    assert result.exit_code == 0
    assert export_path.exists()
    assert json.loads(export_path.read_text(encoding="utf-8"))["counts"]["new"] == 1


def test_scan_changes_json_handles_non_ascii_under_strict_console_encoding(tmp_path):
    source = tmp_path / "source"
    library = tmp_path / "library"
    source.mkdir()
    library.mkdir()
    (source / "中文-évidence.txt").write_text("非 ASCII content", encoding="utf-8")
    env = {**os.environ, "PYTHONIOENCODING": "cp936:strict"}

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "office2md.cli",
            "scan-changes",
            str(source),
            str(library),
            "--dry-run",
            "--json",
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    payload = json.loads(result.stdout.decode("utf-8"))
    assert payload["schema_version"] == CHANGE_PLAN_SCHEMA_VERSION
    assert payload["counts"]["new"] == 1
    assert payload["changes"][0]["source_file"] == "中文-évidence.txt"


def test_scan_changes_export_json_remains_utf8_for_non_ascii(tmp_path):
    source = tmp_path / "source"
    library = tmp_path / "library"
    source.mkdir()
    library.mkdir()
    (source / "中文-évidence.txt").write_text("非 ASCII content", encoding="utf-8")
    export_path = tmp_path / "计划" / "change_plan.json"

    result = runner.invoke(app, ["scan-changes", str(source), str(library), "--export-json", str(export_path)])

    assert result.exit_code == 0
    loaded = json.loads(export_path.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == CHANGE_PLAN_SCHEMA_VERSION
    assert loaded["changes"][0]["source_file"] == "中文-évidence.txt"


def test_build_source_registry_from_library_documents(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("source text", encoding="utf-8")
    output_root = tmp_path / "output"
    library = tmp_path / "library"
    _write_doc(output_root / "doc", "doc-id", str(source), "generic_text", [_chunk("chunk-1", "source text")])
    build_library(output_root, library)

    registry = build_source_registry(library)

    assert registry["schema_version"] == SOURCE_REGISTRY_SCHEMA_VERSION
    assert registry["sources"][0]["source_file"] == str(source)
    assert registry["sources"][0]["knowledge_pack_path"]
    assert registry["sources"][0]["manifest_path"].endswith("manifest.json")


def test_existing_search_and_open_chunk_behavior_still_work(tmp_path):
    output_root = tmp_path / "output"
    library = tmp_path / "library"
    _write_doc(output_root / "doc", "doc-id", "Doc.txt", "generic_text", [_chunk("chunk-1", "pump fault evidence")])
    build_library(output_root, library)

    results = search_library(library / "library.db", "pump fault")
    opened = open_chunk(library, "chunk-1", context=0)

    assert results[0]["chunk_id"] == "chunk-1"
    assert opened["target_chunk"]["chunk_id"] == "chunk-1"


def test_update_library_dry_run_does_not_modify_outputs(tmp_path):
    source = tmp_path / "source"
    output_root = tmp_path / "output"
    library = tmp_path / "library"
    source.mkdir()
    doc = source / "doc.txt"
    doc.write_text("old pump evidence", encoding="utf-8")
    _write_doc(output_root / "doc", "doc-id", str(doc), "generic_text", [_chunk("chunk-1", "old pump evidence")])
    build_library(output_root, library)
    save_source_registry(library)
    before_output = sorted(path.relative_to(output_root).as_posix() for path in output_root.rglob("*"))
    before_library = sorted(path.relative_to(library).as_posix() for path in library.rglob("*"))
    doc.write_text("new pump evidence", encoding="utf-8")

    result = update_library(
        source,
        output_root,
        library,
        convert_file=_fake_convert_one,
        dry_run=True,
        review_report_path=tmp_path / "review" / "update_review.md",
        options=ConvertOptions(engine="markitdown"),
    )

    assert result["status"] == "dry_run"
    assert result["planned"]["convert"] == 1
    assert result["review_summary"]["status"] == "stale"
    assert result["review_summary"]["convert_total"] == 1
    assert result["next_steps"]
    assert (tmp_path / "review" / "update_review.md").exists()
    assert sorted(path.relative_to(output_root).as_posix() for path in output_root.rglob("*")) == before_output
    assert sorted(path.relative_to(library).as_posix() for path in library.rglob("*")) == before_library
    assert not (library / "update_result.json").exists()


def test_update_library_updates_new_modified_reuses_unchanged_and_records_deleted(tmp_path):
    source = tmp_path / "source"
    output_root = tmp_path / "output"
    library = tmp_path / "library"
    source.mkdir()
    unchanged = source / "unchanged.txt"
    modified = source / "modified.txt"
    deleted = source / "deleted.txt"
    unchanged.write_text("unchanged pump evidence", encoding="utf-8")
    modified.write_text("old valve evidence", encoding="utf-8")
    deleted.write_text("deleted motor evidence", encoding="utf-8")
    _write_doc(output_root / "unchanged", "unchanged-id", str(unchanged), "generic_text", [_chunk("unchanged-1", "unchanged pump evidence")])
    _write_doc(output_root / "modified", "modified-id", str(modified), "generic_text", [_chunk("modified-old", "old valve evidence")])
    _write_doc(output_root / "deleted", "deleted-id", str(deleted), "generic_text", [_chunk("deleted-1", "deleted motor evidence")])
    build_library(output_root, library)
    save_source_registry(library)
    modified.write_text("new valve evidence", encoding="utf-8")
    deleted.unlink()
    new_file = source / "new.txt"
    new_file.write_text("new gearbox evidence", encoding="utf-8")

    result = update_library(
        source,
        output_root,
        library,
        convert_file=_fake_convert_one,
        dry_run=False,
        options=ConvertOptions(engine="markitdown"),
    )
    update_result = json.loads((library / "update_result.json").read_text(encoding="utf-8"))
    state = load_library_state(library)

    assert result["status"] == "updated"
    assert update_result["schema_version"] == UPDATE_RESULT_SCHEMA_VERSION
    assert result["planned"]["convert"] == 2
    assert len(result["converted"]) == 2
    assert len(result["reused_packs"]) == 2
    assert result["missing_sources"][0]["source_file"].endswith("deleted.txt")
    assert (library / "library.db").exists()
    assert default_source_registry_path(library).exists()
    assert default_library_state_path(library).exists()
    assert state["schema_version"] == LIBRARY_STATE_SCHEMA_VERSION
    search_results = search_library(library / "library.db", "gearbox")
    opened = open_chunk(library, search_results[0]["chunk_id"], context=0)
    assert search_results[0]["source_file"].endswith("new.txt")
    assert "gearbox" in opened["target_chunk"]["text"]


def test_update_library_conversion_failure_writes_failed_manifest_and_stops_before_rebuild(tmp_path):
    source = tmp_path / "source"
    output_root = tmp_path / "output"
    library = tmp_path / "library"
    source.mkdir()
    doc = source / "doc.txt"
    doc.write_text("oldonly evidence", encoding="utf-8")
    _write_doc(output_root / "doc", "doc-id", str(doc), "generic_text", [_chunk("chunk-1", "oldonly evidence")])
    build_library(output_root, library)
    save_source_registry(library)
    doc.write_text("newonly evidence", encoding="utf-8")

    def fail_convert(source_path: Path, output_root: Path, options: ConvertOptions):
        raise RuntimeError("planned update failure")

    result = update_library(
        source,
        output_root,
        library,
        convert_file=fail_convert,
        dry_run=False,
        options=ConvertOptions(engine="markitdown"),
    )
    update_result = json.loads((library / "update_result.json").read_text(encoding="utf-8"))
    failure = result["conversion_failures"][0]
    manifest = json.loads(Path(failure["manifest_path"]).read_text(encoding="utf-8"))

    assert result["status"] == "failed"
    assert update_result["status"] == "failed"
    assert result["build_result"] is None
    assert result["reused_packs"] == []
    assert failure["status"] == "failed"
    assert failure["source_file"] == "doc.txt"
    assert "RuntimeError: planned update failure" == failure["error"]
    assert manifest["status"] == "failed"
    assert manifest["errors"] == ["planned update failure"]
    assert (output_root / "_index.json").exists()
    assert result["review_summary"]["converted_total"] == 0
    assert result["review_summary"]["conversion_failure_total"] == 1
    assert any("not rebuilt" in step for step in result["next_steps"])
    assert search_library(library / "library.db", "newonly") == []
    assert search_library(library / "library.db", "oldonly")


def test_update_library_cli_exits_nonzero_when_conversion_fails(tmp_path, monkeypatch):
    source = tmp_path / "source"
    output_root = tmp_path / "output"
    library = tmp_path / "library"
    source.mkdir()
    doc = source / "doc.txt"
    doc.write_text("oldonly evidence", encoding="utf-8")
    _write_doc(output_root / "doc", "doc-id", str(doc), "generic_text", [_chunk("chunk-1", "oldonly evidence")])
    build_library(output_root, library)
    save_source_registry(library)
    doc.write_text("newonly evidence", encoding="utf-8")

    def fail_convert(source_path: Path, output_root: Path, options: ConvertOptions):
        raise RuntimeError("planned cli update failure")

    monkeypatch.setattr("office2md.cli.convert_one", fail_convert)

    result = runner.invoke(app, ["update-library", str(source), str(output_root), str(library)])

    assert result.exit_code == 1
    assert "conversion_failures" in result.stdout
    assert "failed:" in result.stdout
    assert "RuntimeError: planned cli update failure" in result.stdout


def test_update_library_cli_help(tmp_path):
    result = runner.invoke(app, ["update-library", "--help"])

    assert result.exit_code == 0
    assert "--dry-run" in result.stdout
    assert "--change-plan" in result.stdout


def test_update_library_review_summary_flags_large_pending_plan(tmp_path):
    source = tmp_path / "source"
    library = tmp_path / "library"
    source.mkdir()
    library.mkdir()
    for index in range(101):
        (source / f"new-{index}.txt").write_text("new evidence", encoding="utf-8")

    result = update_library(
        source,
        tmp_path / "output",
        library,
        convert_file=_fake_convert_one,
        dry_run=True,
        options=ConvertOptions(engine="markitdown"),
    )

    assert result["review_summary"]["pending_total"] == 101
    assert result["review_summary"]["high_pending_changes"] is True
    assert result["large_folder_warnings"]


def _write_registry(library: Path, registry: dict) -> Path:
    path = library / "source_registry.json"
    write_source_registry(path, registry)
    return path


def _registry(library: Path, sources: list[dict]) -> dict:
    return {
        "schema_version": SOURCE_REGISTRY_SCHEMA_VERSION,
        "generated_at": "now",
        "library_path": str(library),
        "sources": sources,
        "warnings": [],
    }


def _source_record(path: Path, root: Path) -> dict:
    stat = path.stat()
    from office2md.detector import sha256_file

    return {
        "source_id": path.stem,
        "normalized_source_path": str(path.resolve()).lower(),
        "source_path": str(path.resolve()),
        "relative_path": path.relative_to(root).as_posix(),
        "source_file": path.name,
        "extension": path.suffix.lower(),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256_file(path),
        "converter": "markitdown",
        "converter_version": None,
        "profile": "kb",
        "knowledge_pack_path": str(root / "packs" / path.stem),
        "manifest_path": None,
        "status": "active",
    }


def _chunk(chunk_id: str, text: str) -> dict:
    return {
        "chunk_id": chunk_id,
        "evidence_type": "text",
        "heading_path": [],
        "title": "Doc",
        "text": text,
        "locator": "Line 1",
        "confidence": "high",
    }


def _write_doc(path: Path, doc_id: str, source_file: str, document_kind: str, chunks: list[dict]) -> None:
    path.mkdir(parents=True)
    manifest = {
        "status": "success",
        "source_file": source_file,
        "document_kind": document_kind,
        "checksum": "sha256:test",
        "converter": "markitdown",
    }
    knowledge = {"title": Path(source_file).name, "document_kind": document_kind}
    source_map = {chunk["chunk_id"]: {"locator": chunk.get("locator")} for chunk in chunks}
    (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (path / "knowledge.json").write_text(json.dumps(knowledge), encoding="utf-8")
    (path / "entities.json").write_text(json.dumps({}), encoding="utf-8")
    (path / "source_map.json").write_text(json.dumps(source_map), encoding="utf-8")
    with (path / "chunks.jsonl").open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk) + "\n")


def _fake_convert_one(source_path: Path, output_root: Path, options: ConvertOptions):
    from office2md.detector import sha256_file

    checksum = sha256_file(source_path).split(":", 1)[-1][:8]
    pack = output_root / f"{source_path.stem}-{checksum}"
    text = source_path.read_text(encoding="utf-8")
    _write_doc(pack, f"{source_path.stem}-{checksum}", str(source_path), "generic_text", [_chunk(f"{source_path.stem}-{checksum}-chunk", text)])
    return pack, "success"
