import json
from pathlib import Path

from typer.testing import CliRunner

from office2md.cli import app
from office2md.library import build_library
from office2md.workspace import (
    detect_workspace,
    init_workspace,
    register_library_version,
    register_output_version,
    scan_workspace_sources,
    summarize_workspace,
    summarize_workspace_status,
)


def test_workspace_init_creates_expected_folders_and_manifests(tmp_path):
    workspace = tmp_path / "project.office2md"

    result = init_workspace(workspace)

    assert result["dry_run"] is False
    for rel in [
        "conversion",
        "library",
        "wiki/Concepts",
        "wiki/Notes",
        "wiki/Corrections",
        "wiki/_suggestions",
        "outputs/obsidian",
        "outputs/reports",
        "outputs/html",
        "outputs/_manifests",
        "logs",
        "versions",
    ]:
        assert (workspace / rel).is_dir()
    for rel in [
        "workspace_manifest.json",
        "source_manifest.json",
        "versions/library_versions.json",
        "versions/output_versions.json",
    ]:
        assert (workspace / rel).exists()


def test_workspace_manifest_shapes(tmp_path):
    workspace = tmp_path / "project.office2md"
    init_workspace(workspace)

    workspace_manifest = json.loads((workspace / "workspace_manifest.json").read_text(encoding="utf-8"))
    source_manifest = json.loads((workspace / "source_manifest.json").read_text(encoding="utf-8"))
    library_versions = json.loads((workspace / "versions" / "library_versions.json").read_text(encoding="utf-8"))
    output_versions = json.loads((workspace / "versions" / "output_versions.json").read_text(encoding="utf-8"))

    assert workspace_manifest["schema_version"] == "1"
    assert workspace_manifest["layers"] == {
        "ram": ["conversion", "library"],
        "wiki": ["wiki"],
        "output": ["outputs"],
        "versions": ["versions"],
    }
    assert workspace_manifest["folders"]["conversion"] == "conversion"
    assert source_manifest == {
        "schema_version": "1",
        "source_roots": [],
        "sources": [],
        "counts": {
            "total_sources": 0,
            "active_sources": 0,
            "new_sources": 0,
            "changed_sources": 0,
            "missing_sources": 0,
        },
        "generated_at": source_manifest["generated_at"],
    }
    assert library_versions == {"schema_version": "1", "library_versions": []}
    assert output_versions == {"schema_version": "1", "output_versions": []}


def test_workspace_init_dry_run_writes_nothing(tmp_path):
    workspace = tmp_path / "dryrun.office2md"

    result = init_workspace(workspace, dry_run=True)

    assert result["dry_run"] is True
    assert len(result["directories"]) == 14
    assert len(result["manifest_files"]) == 4
    assert not workspace.exists()


def test_workspace_init_is_idempotent_and_preserves_existing_manifests(tmp_path):
    workspace = tmp_path / "project.office2md"
    init_workspace(workspace)
    first_workspace_manifest = json.loads((workspace / "workspace_manifest.json").read_text(encoding="utf-8"))
    custom_source = {"schema_version": "custom", "source_roots": ["C:/sources"], "sources": [{"path": "a.pdf"}]}
    custom_library = {"schema_version": "custom", "library_versions": [{"id": "lib-1"}]}
    custom_output = {"schema_version": "custom", "output_versions": [{"id": "out-1"}]}
    (workspace / "source_manifest.json").write_text(json.dumps(custom_source), encoding="utf-8")
    (workspace / "versions" / "library_versions.json").write_text(json.dumps(custom_library), encoding="utf-8")
    (workspace / "versions" / "output_versions.json").write_text(json.dumps(custom_output), encoding="utf-8")
    keep_file = workspace / "wiki" / "Notes" / "keep.md"
    keep_file.write_text("keep", encoding="utf-8")

    second = init_workspace(workspace)
    second_workspace_manifest = json.loads((workspace / "workspace_manifest.json").read_text(encoding="utf-8"))

    assert keep_file.exists()
    assert json.loads((workspace / "source_manifest.json").read_text(encoding="utf-8")) == custom_source
    assert json.loads((workspace / "versions" / "library_versions.json").read_text(encoding="utf-8")) == custom_library
    assert json.loads((workspace / "versions" / "output_versions.json").read_text(encoding="utf-8")) == custom_output
    assert second["preserved_manifests"]
    assert second_workspace_manifest["created_at"] == first_workspace_manifest["created_at"]
    assert second_workspace_manifest["updated_at"] >= first_workspace_manifest["updated_at"]


def test_workspace_init_overwrite_manifests_replaces_existing_version_files(tmp_path):
    workspace = tmp_path / "project.office2md"
    init_workspace(workspace)
    (workspace / "source_manifest.json").write_text('{"schema_version": "custom"}', encoding="utf-8")

    init_workspace(workspace, overwrite_manifests=True)

    source_manifest = json.loads((workspace / "source_manifest.json").read_text(encoding="utf-8"))
    assert source_manifest["schema_version"] == "1"
    assert source_manifest["source_roots"] == []


def test_detect_and_summarize_workspace(tmp_path):
    workspace = tmp_path / "project.office2md"
    assert detect_workspace(workspace) is False

    init_workspace(workspace)
    summary = summarize_workspace(workspace)

    assert detect_workspace(workspace) is True
    assert summary["is_workspace"] is True
    assert summary["workspace_manifest_exists"] is True
    assert summary["library_versions_exists"] is True
    assert summary["folders"]["wiki/Concepts"] is True


def test_workspace_init_cli_help_and_dry_run(tmp_path):
    runner = CliRunner()
    help_result = runner.invoke(app, ["workspace-init", "--help"])
    workspace = tmp_path / "dryrun.office2md"
    dry_run_result = runner.invoke(app, ["workspace-init", str(workspace), "--dry-run"])

    assert help_result.exit_code == 0
    assert "--overwrite-manifests" in help_result.stdout
    assert dry_run_result.exit_code == 0
    assert "planned_directories:" in dry_run_result.stdout
    assert not workspace.exists()


def test_workspace_scan_requires_existing_workspace(tmp_path):
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    (source_dir / "sample.txt").write_text("sample", encoding="utf-8")

    try:
        scan_workspace_sources(tmp_path / "missing.office2md", source_dir)
    except ValueError as exc:
        assert "workspace-init" in str(exc)
    else:
        raise AssertionError("workspace scan should reject non-workspace paths")


def test_workspace_scan_populates_source_manifest_with_file_metadata(tmp_path):
    workspace = tmp_path / "project.office2md"
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    source_file = source_dir / "sample.txt"
    source_file.write_text("sample", encoding="utf-8")
    init_workspace(workspace)

    result = scan_workspace_sources(workspace, source_dir)
    manifest = json.loads((workspace / "source_manifest.json").read_text(encoding="utf-8"))
    source = manifest["sources"][0]

    assert result["counts"]["total_sources"] == 1
    assert manifest["source_roots"][0]["path"] == str(source_dir.resolve())
    assert source["absolute_path"] == str(source_file.resolve())
    assert source["relative_path"] == "sample.txt"
    assert source["file_name"] == "sample.txt"
    assert source["extension"] == ".txt"
    assert source["size_bytes"] == 6
    assert source["modified_time"]
    assert source["sha256"].startswith("sha256:")
    assert source["status"] == "new"


def test_workspace_scan_dry_run_writes_nothing(tmp_path):
    workspace = tmp_path / "project.office2md"
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    (source_dir / "sample.txt").write_text("sample", encoding="utf-8")
    init_workspace(workspace)
    before = (workspace / "source_manifest.json").read_text(encoding="utf-8")

    result = scan_workspace_sources(workspace, source_dir, dry_run=True)

    assert result["dry_run"] is True
    assert result["counts"]["total_sources"] == 1
    assert (workspace / "source_manifest.json").read_text(encoding="utf-8") == before


def test_workspace_scan_detects_changed_and_missing_files(tmp_path):
    workspace = tmp_path / "project.office2md"
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    changed_file = source_dir / "changed.txt"
    missing_file = source_dir / "missing.txt"
    changed_file.write_text("first", encoding="utf-8")
    missing_file.write_text("keep", encoding="utf-8")
    init_workspace(workspace)
    scan_workspace_sources(workspace, source_dir)

    changed_file.write_text("second version", encoding="utf-8")
    missing_file.unlink()
    result = scan_workspace_sources(workspace, source_dir)
    manifest = result["manifest"]
    by_name = {item["file_name"]: item for item in manifest["sources"]}

    assert by_name["changed.txt"]["status"] == "changed"
    assert by_name["changed.txt"]["changed"] is True
    assert by_name["missing.txt"]["status"] == "missing"
    assert result["counts"]["changed_sources"] == 1
    assert result["counts"]["missing_sources"] == 1


def test_workspace_scan_max_files_limits_scan_without_marking_unscanned_missing(tmp_path):
    workspace = tmp_path / "project.office2md"
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    for name in ["a.txt", "b.txt", "c.txt"]:
        (source_dir / name).write_text(name, encoding="utf-8")
    init_workspace(workspace)
    scan_workspace_sources(workspace, source_dir)

    result = scan_workspace_sources(workspace, source_dir, max_files=1)

    assert result["scan_limited"] is True
    assert result["scanned_files"] == 1
    assert result["manifest"]["last_scan"]["scan_limited"] is True
    assert result["counts"]["missing_sources"] == 0


def test_workspace_scan_hidden_files_are_optional(tmp_path):
    workspace = tmp_path / "project.office2md"
    source_dir = tmp_path / "sources"
    hidden_dir = source_dir / ".hidden"
    hidden_dir.mkdir(parents=True)
    (source_dir / "visible.txt").write_text("visible", encoding="utf-8")
    (hidden_dir / "inside.txt").write_text("hidden", encoding="utf-8")
    init_workspace(workspace)

    default_result = scan_workspace_sources(workspace, source_dir)
    included_result = scan_workspace_sources(workspace, source_dir, include_hidden=True)

    assert default_result["counts"]["total_sources"] == 1
    assert included_result["counts"]["total_sources"] == 2


def test_workspace_scan_cli_help(tmp_path):
    runner = CliRunner()
    help_result = runner.invoke(app, ["workspace-scan", "--help"])
    invalid_result = runner.invoke(app, ["workspace-scan", str(tmp_path / "missing.office2md"), str(tmp_path)])

    assert help_result.exit_code == 0
    assert "--include-hidden" in help_result.stdout
    assert "--max-files" in help_result.stdout
    assert invalid_result.exit_code != 0
    assert "workspace-init" in invalid_result.stderr


def test_workspace_register_library_requires_existing_workspace(tmp_path):
    library_dir = _build_tiny_library(tmp_path)

    try:
        register_library_version(tmp_path / "missing.office2md", library_dir)
    except ValueError as exc:
        assert "workspace-init" in str(exc)
    else:
        raise AssertionError("library registration should reject non-workspace paths")


def test_workspace_register_library_requires_valid_built_library(tmp_path):
    workspace = tmp_path / "project.office2md"
    init_workspace(workspace)

    try:
        register_library_version(workspace, tmp_path / "not-a-library")
    except FileNotFoundError as exc:
        assert "Built library not found" in str(exc)
    else:
        raise AssertionError("library registration should reject invalid library paths")


def test_workspace_register_library_appends_record_and_preserves_history(tmp_path):
    workspace = tmp_path / "project.office2md"
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    (source_dir / "sample.txt").write_text("sample", encoding="utf-8")
    init_workspace(workspace)
    scan_workspace_sources(workspace, source_dir)
    library_dir = _build_tiny_library(tmp_path)
    existing = {
        "schema_version": "1",
        "library_versions": [{"library_version_id": "existing", "label": "before"}],
    }
    (workspace / "versions" / "library_versions.json").write_text(json.dumps(existing), encoding="utf-8")

    result = register_library_version(workspace, library_dir, label="first", notes="notes")
    manifest = json.loads((workspace / "versions" / "library_versions.json").read_text(encoding="utf-8"))
    record = manifest["library_versions"][1]

    assert result["versions_count"] == 2
    assert manifest["library_versions"][0] == existing["library_versions"][0]
    assert record["label"] == "first"
    assert record["notes"] == "notes"
    assert record["workspace_path"] == str(workspace.resolve())
    assert record["library_path"] == str(library_dir.resolve())
    assert record["library_version_id"].startswith("lib_")


def test_workspace_register_library_dry_run_writes_nothing(tmp_path):
    workspace = tmp_path / "project.office2md"
    init_workspace(workspace)
    library_dir = _build_tiny_library(tmp_path)
    before = (workspace / "versions" / "library_versions.json").read_text(encoding="utf-8")

    result = register_library_version(workspace, library_dir, dry_run=True)

    assert result["dry_run"] is True
    assert result["versions_count"] == 1
    assert (workspace / "versions" / "library_versions.json").read_text(encoding="utf-8") == before


def test_workspace_register_library_records_hashes_metrics_and_source_counts(tmp_path):
    workspace = tmp_path / "project.office2md"
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    (source_dir / "sample.txt").write_text("sample", encoding="utf-8")
    init_workspace(workspace)
    scan_workspace_sources(workspace, source_dir)
    library_dir = _build_tiny_library(tmp_path)

    result = register_library_version(workspace, library_dir / "library.db", library_version_id="manual-lib")
    record = result["record"]

    assert record["library_version_id"] == "manual-lib"
    assert record["source_manifest_hash"].startswith("sha256:")
    assert record["library_files"]["library_db"]["sha256"].startswith("sha256:")
    assert record["library_files"]["library_index"]["sha256"].startswith("sha256:")
    assert record["library_files"]["library_graph"]["sha256"].startswith("sha256:")
    assert record["library_metrics"]["documents_count"] == 1
    assert record["library_metrics"]["chunks_count"] == 1
    assert record["library_metrics"]["entities_count"] == 1
    assert record["source_counts"]["total_sources"] == 1
    assert record["source_counts"]["active_sources"] == 1


def test_workspace_register_library_records_dirty_source_warnings(tmp_path):
    workspace = tmp_path / "project.office2md"
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    changed_file = source_dir / "changed.txt"
    missing_file = source_dir / "missing.txt"
    changed_file.write_text("first", encoding="utf-8")
    missing_file.write_text("missing", encoding="utf-8")
    init_workspace(workspace)
    scan_workspace_sources(workspace, source_dir)
    changed_file.write_text("changed", encoding="utf-8")
    missing_file.unlink()
    scan_workspace_sources(workspace, source_dir)
    library_dir = _build_tiny_library(tmp_path)

    result = register_library_version(workspace, library_dir)
    warnings = result["record"]["warnings"]

    assert result["record"]["source_dirty"] is True
    assert any("changed source" in warning for warning in warnings)
    assert any("missing source" in warning for warning in warnings)


def test_workspace_register_library_cli_help_and_dry_run(tmp_path):
    runner = CliRunner()
    workspace = tmp_path / "project.office2md"
    init_workspace(workspace)
    library_dir = _build_tiny_library(tmp_path)
    before = (workspace / "versions" / "library_versions.json").read_text(encoding="utf-8")

    help_result = runner.invoke(app, ["workspace-register-library", "--help"])
    dry_run_result = runner.invoke(app, ["workspace-register-library", str(workspace), str(library_dir), "--dry-run"])

    assert help_result.exit_code == 0
    assert "--allow-dirty-source" in help_result.stdout
    assert "--library-version-id" in help_result.stdout
    assert dry_run_result.exit_code == 0
    assert "library_versions.json was not written" in dry_run_result.stdout
    assert (workspace / "versions" / "library_versions.json").read_text(encoding="utf-8") == before


def test_workspace_register_output_requires_existing_workspace(tmp_path):
    output = tmp_path / "report.md"
    output.write_text("# Report\n", encoding="utf-8")

    try:
        register_output_version(tmp_path / "missing.office2md", output, allow_missing_library_version=True)
    except ValueError as exc:
        assert "workspace-init" in str(exc)
    else:
        raise AssertionError("output registration should reject non-workspace paths")


def test_workspace_register_output_requires_existing_output_path(tmp_path):
    workspace = tmp_path / "project.office2md"
    init_workspace(workspace)

    try:
        register_output_version(workspace, tmp_path / "missing-output", allow_missing_library_version=True)
    except FileNotFoundError as exc:
        assert "Output path does not exist" in str(exc)
    else:
        raise AssertionError("output registration should reject missing output paths")


def test_workspace_register_output_appends_record_and_preserves_history(tmp_path):
    workspace, library_record = _workspace_with_registered_library(tmp_path)
    output = tmp_path / "report.md"
    output.write_text("# Report\n", encoding="utf-8")
    existing = {
        "schema_version": "1",
        "output_versions": [{"output_version_id": "existing", "label": "before"}],
    }
    (workspace / "versions" / "output_versions.json").write_text(json.dumps(existing), encoding="utf-8")

    result = register_output_version(workspace, output, label="first", notes="notes")
    manifest = json.loads((workspace / "versions" / "output_versions.json").read_text(encoding="utf-8"))
    record = manifest["output_versions"][1]

    assert result["versions_count"] == 2
    assert manifest["output_versions"][0] == existing["output_versions"][0]
    assert record["label"] == "first"
    assert record["notes"] == "notes"
    assert record["library_version_id"] == library_record["library_version_id"]
    assert record["output_version_id"].startswith("out_")


def test_workspace_register_output_dry_run_writes_nothing(tmp_path):
    workspace, _library_record = _workspace_with_registered_library(tmp_path)
    output = tmp_path / "report.md"
    output.write_text("# Report\n", encoding="utf-8")
    before = (workspace / "versions" / "output_versions.json").read_text(encoding="utf-8")

    result = register_output_version(workspace, output, dry_run=True)

    assert result["dry_run"] is True
    assert result["versions_count"] == 1
    assert (workspace / "versions" / "output_versions.json").read_text(encoding="utf-8") == before


def test_workspace_register_output_records_file_hash_for_file_output(tmp_path):
    workspace, _library_record = _workspace_with_registered_library(tmp_path)
    output = tmp_path / "report.md"
    output.write_text("# Report\n", encoding="utf-8")

    result = register_output_version(workspace, output, output_version_id="manual-output")
    record = result["record"]

    assert record["output_version_id"] == "manual-output"
    assert record["output_type"] == "report"
    assert record["output_files"]["kind"] == "file"
    assert record["output_files"]["file_count"] == 1
    assert record["output_files"]["sha256"].startswith("sha256:")
    assert record["output_files"]["folder_sha256"] is None


def test_workspace_register_output_records_folder_summary_and_hash(tmp_path):
    workspace, _library_record = _workspace_with_registered_library(tmp_path)
    output_dir = tmp_path / "folder-output"
    output_dir.mkdir()
    (output_dir / "a.md").write_text("a", encoding="utf-8")
    (output_dir / "nested").mkdir()
    (output_dir / "nested" / "b.md").write_text("bb", encoding="utf-8")

    result = register_output_version(workspace, output_dir)
    files = result["record"]["output_files"]

    assert result["record"]["output_type"] == "generic_output"
    assert files["kind"] == "folder"
    assert files["file_count"] == 2
    assert files["total_size_bytes"] == 3
    assert files["folder_sha256"].startswith("sha256:")


def test_workspace_register_output_detects_obsidian_vault_and_parses_manifest(tmp_path):
    workspace, library_record = _workspace_with_registered_library(tmp_path)
    vault = _write_tiny_obsidian_vault(tmp_path / "vault")

    result = register_output_version(workspace, vault)
    record = result["record"]

    assert record["output_type"] == "obsidian_vault"
    assert record["library_version_id"] == library_record["library_version_id"]
    assert record["source_manifest_hash"] == library_record["source_manifest_hash"]
    assert record["source_counts"] == library_record["source_counts"]
    assert "00_Index.md" in record["output_files"]["recognized_files"]
    assert "_office2md/export_manifest.json" in record["output_files"]["recognized_files"]
    assert record["export_manifest"]["export_type"] == "obsidian"
    assert record["export_manifest"]["documents_exported"] == 1
    assert record["export_manifest"]["concepts_exported"] == 1
    assert record["export_manifest"]["warnings"] == ["assets not copied"]


def test_workspace_register_output_uses_latest_library_version_when_multiple_exist(tmp_path):
    workspace, library_record = _workspace_with_registered_library(tmp_path)
    second = register_library_version(workspace, Path(library_record["library_path"]), label="second")["record"]
    output = tmp_path / "report.md"
    output.write_text("# Report\n", encoding="utf-8")

    result = register_output_version(workspace, output)

    assert result["record"]["library_version_id"] == second["library_version_id"]
    assert any("multiple library versions" in warning for warning in result["warnings"])


def test_workspace_register_output_missing_library_version_blocks_by_default(tmp_path):
    workspace = tmp_path / "project.office2md"
    init_workspace(workspace)
    output = tmp_path / "report.md"
    output.write_text("# Report\n", encoding="utf-8")

    try:
        register_output_version(workspace, output)
    except ValueError as exc:
        assert "workspace-register-library" in str(exc)
    else:
        raise AssertionError("output registration should require a library version by default")


def test_workspace_register_output_allow_missing_library_version_records_warning(tmp_path):
    workspace = tmp_path / "project.office2md"
    init_workspace(workspace)
    output = tmp_path / "report.md"
    output.write_text("# Report\n", encoding="utf-8")

    result = register_output_version(workspace, output, allow_missing_library_version=True)
    record = result["record"]

    assert record["library_version_id"] is None
    assert record["source_manifest_hash"] is None
    assert any("without library linkage" in warning for warning in record["warnings"])


def test_workspace_register_output_cli_help_and_dry_run(tmp_path):
    runner = CliRunner()
    workspace, _library_record = _workspace_with_registered_library(tmp_path)
    output = tmp_path / "report.md"
    output.write_text("# Report\n", encoding="utf-8")
    before = (workspace / "versions" / "output_versions.json").read_text(encoding="utf-8")

    help_result = runner.invoke(app, ["workspace-register-output", "--help"])
    dry_run_result = runner.invoke(app, ["workspace-register-output", str(workspace), str(output), "--dry-run"])

    assert help_result.exit_code == 0
    assert "--allow-missing-library-version" in help_result.stdout
    assert "--output-version-id" in help_result.stdout
    assert dry_run_result.exit_code == 0
    assert "output_versions.json was not written" in dry_run_result.stdout
    assert (workspace / "versions" / "output_versions.json").read_text(encoding="utf-8") == before


def test_workspace_status_requires_existing_workspace(tmp_path):
    try:
        summarize_workspace_status(tmp_path / "missing.office2md")
    except ValueError as exc:
        assert "workspace-init" in str(exc)
    else:
        raise AssertionError("workspace-status should reject non-workspace paths")


def test_workspace_status_with_init_only_manifests(tmp_path):
    workspace = tmp_path / "project.office2md"
    init_workspace(workspace)

    status = summarize_workspace_status(workspace)

    assert status["workspace"]["workspace_path"] == str(workspace.resolve())
    assert status["workspace"]["missing_expected_manifests"] == []
    assert status["source_manifest"]["total_sources"] == 0
    assert status["library_versions"]["total_versions"] == 0
    assert status["output_versions"]["total_versions"] == 0
    assert status["traceability"]["source_manifest_hash"].startswith("sha256:")


def test_workspace_status_summarizes_source_counts_after_scan(tmp_path):
    workspace = tmp_path / "project.office2md"
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    (source_dir / "sample.txt").write_text("sample", encoding="utf-8")
    init_workspace(workspace)
    scan_workspace_sources(workspace, source_dir)

    status = summarize_workspace_status(workspace)

    assert status["source_manifest"]["total_sources"] == 1
    assert status["source_manifest"]["active_sources"] == 1
    assert status["source_manifest"]["source_roots_count"] == 1
    assert status["source_manifest"]["last_scan"]["source_root"] == str(source_dir.resolve())


def test_workspace_status_summarizes_library_version(tmp_path):
    workspace, library_record = _workspace_with_registered_library(tmp_path)

    status = summarize_workspace_status(workspace)
    latest = status["library_versions"]["latest"]

    assert status["library_versions"]["total_versions"] == 1
    assert latest["library_version_id"] == library_record["library_version_id"]
    assert latest["label"] == "tiny-library"
    assert latest["metrics"]["documents_count"] == 1
    assert latest["metrics"]["chunks_count"] == 1
    assert latest["metrics"]["entities_count"] == 1


def test_workspace_status_summarizes_output_version_and_traceability_chain(tmp_path):
    workspace, library_record = _workspace_with_registered_library(tmp_path)
    vault = _write_tiny_obsidian_vault(tmp_path / "vault")
    output_record = register_output_version(workspace, vault, label="tiny-obsidian-export")["record"]

    status = summarize_workspace_status(workspace)
    latest_output = status["output_versions"]["latest"]
    traceability = status["traceability"]

    assert status["output_versions"]["total_versions"] == 1
    assert latest_output["output_version_id"] == output_record["output_version_id"]
    assert latest_output["output_type"] == "obsidian_vault"
    assert latest_output["label"] == "tiny-obsidian-export"
    assert latest_output["library_version_id"] == library_record["library_version_id"]
    assert latest_output["export_manifest"]["export_type"] == "obsidian"
    assert traceability["source_manifest_hash"] == library_record["source_manifest_hash"]
    assert traceability["library_version_id"] == library_record["library_version_id"]
    assert traceability["output_version_id"] == output_record["output_version_id"]


def test_workspace_status_warns_when_output_links_to_missing_library_version(tmp_path):
    workspace = tmp_path / "project.office2md"
    init_workspace(workspace)
    output_versions = {
        "schema_version": "1",
        "output_versions": [
            {
                "output_version_id": "out_missing",
                "registered_at": "2026-01-01T00:00:00Z",
                "library_version_id": "lib_missing",
                "source_manifest_hash": "sha256:old",
                "output_files": {"file_count": 1, "total_size_bytes": 1},
            }
        ],
    }
    (workspace / "versions" / "output_versions.json").write_text(json.dumps(output_versions), encoding="utf-8")

    status = summarize_workspace_status(workspace)

    assert any("missing library_version_id" in warning for warning in status["warnings"])
    assert status["errors"]


def test_workspace_status_warns_when_current_source_hash_differs_from_latest_library(tmp_path):
    workspace, _library_record = _workspace_with_registered_library(tmp_path)
    source_manifest = json.loads((workspace / "source_manifest.json").read_text(encoding="utf-8"))
    source_manifest["manual_change"] = True
    (workspace / "source_manifest.json").write_text(json.dumps(source_manifest), encoding="utf-8")

    status = summarize_workspace_status(workspace)

    assert any("latest library source_manifest_hash differs" in warning for warning in status["warnings"])


def test_workspace_status_json_outputs_parseable_json_only(tmp_path):
    runner = CliRunner()
    workspace, _library_record = _workspace_with_registered_library(tmp_path)

    result = runner.invoke(app, ["workspace-status", str(workspace), "--json"])
    payload = json.loads(result.stdout)

    assert result.exit_code == 0
    assert payload["workspace"]["workspace_path"] == str(workspace.resolve())
    assert "office2md workspace-status" not in result.stdout


def test_workspace_status_show_history_respects_limit(tmp_path):
    workspace, library_record = _workspace_with_registered_library(tmp_path)
    register_library_version(workspace, Path(library_record["library_path"]), label="second")
    vault = _write_tiny_obsidian_vault(tmp_path / "vault")
    register_output_version(workspace, vault, label="first-output")
    register_output_version(workspace, vault, label="second-output")

    status = summarize_workspace_status(workspace, show_history=True, limit=1)

    assert len(status["library_versions"]["history"]) == 1
    assert len(status["output_versions"]["history"]) == 1
    assert status["library_versions"]["history"][0]["label"] == "second"
    assert status["output_versions"]["history"][0]["label"] == "second-output"


def test_workspace_status_strict_fails_for_missing_required_manifest(tmp_path):
    runner = CliRunner()
    workspace = tmp_path / "project.office2md"
    init_workspace(workspace)
    (workspace / "versions" / "output_versions.json").unlink()

    result = runner.invoke(app, ["workspace-status", str(workspace), "--strict"])

    assert result.exit_code != 0
    assert "missing expected manifest" in result.stdout


def test_workspace_status_cli_help(tmp_path):
    runner = CliRunner()
    result = runner.invoke(app, ["workspace-status", "--help"])

    assert result.exit_code == 0
    assert "--show-history" in result.stdout
    assert "--strict" in result.stdout


def _build_tiny_library(tmp_path):
    output_root = tmp_path / "output"
    doc_dir = output_root / "doc"
    doc_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source_file": "sample.txt",
        "source_path": str(tmp_path / "sources" / "sample.txt"),
        "checksum": "sha256:sample",
        "engine": "markitdown",
        "status": "success",
        "document_kind": "document",
        "quality_status": "ok",
        "extraction_status": "text",
    }
    knowledge = {
        "title": "sample",
        "document_kind": "document",
        "quality_status": "ok",
        "extraction_status": "text",
        "key_metadata": {"source_path": manifest["source_path"], "checksum": manifest["checksum"]},
        "tags": ["document"],
    }
    chunk = {
        "chunk_id": "sample_chunk",
        "doc_id": "sample",
        "source_file": "sample.txt",
        "source_path": manifest["source_path"],
        "document_kind": "document",
        "quality_status": "ok",
        "evidence_type": "text",
        "heading_path": ["Sample"],
        "text": "sample text",
        "char_count": 11,
        "locator": "Line 1",
        "provenance_status": "text",
    }
    source_map = {"sample_chunk": {"heading_path": ["Sample"], "locator": "Line 1", "evidence_type": "text"}}
    entities = {"project": ["sample project"]}
    (doc_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (doc_dir / "knowledge.json").write_text(json.dumps(knowledge), encoding="utf-8")
    (doc_dir / "entities.json").write_text(json.dumps(entities), encoding="utf-8")
    (doc_dir / "source_map.json").write_text(json.dumps(source_map), encoding="utf-8")
    (doc_dir / "chunks.jsonl").write_text(json.dumps(chunk) + "\n", encoding="utf-8")
    (doc_dir / "document.md").write_text("# Sample\n", encoding="utf-8")
    library_dir = tmp_path / "library"
    build_library(output_root, library_dir)
    return library_dir


def _workspace_with_registered_library(tmp_path):
    workspace = tmp_path / "project.office2md"
    source_dir = tmp_path / "sources"
    source_dir.mkdir(exist_ok=True)
    (source_dir / "sample.txt").write_text("sample", encoding="utf-8")
    init_workspace(workspace)
    scan_workspace_sources(workspace, source_dir)
    library_dir = _build_tiny_library(tmp_path)
    record = register_library_version(workspace, library_dir, label="tiny-library")["record"]
    return workspace, record


def _write_tiny_obsidian_vault(path):
    path.mkdir(parents=True)
    (path / "00_Index.md").write_text("# Index\n", encoding="utf-8")
    (path / "00_Library_Report.md").write_text("# Library Report\n", encoding="utf-8")
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
                "warnings": ["assets not copied"],
            }
        ),
        encoding="utf-8",
    )
    return path
