import json

from typer.testing import CliRunner

from office2md.cli import app
from office2md.workspace import detect_workspace, init_workspace, scan_workspace_sources, summarize_workspace


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
