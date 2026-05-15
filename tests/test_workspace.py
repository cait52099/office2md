import json

from typer.testing import CliRunner

from office2md.cli import app
from office2md.workspace import detect_workspace, init_workspace, summarize_workspace


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
