import json

from typer.testing import CliRunner

from office2md.cli import app
from office2md.library_catalog import LIBRARY_CATALOG_SCHEMA_VERSION, add_library_to_catalog, list_library_catalog


runner = CliRunner()


def test_library_catalog_add_and_list_json(tmp_path):
    catalog_path = tmp_path / "catalogs" / "libraries.json"
    library = tmp_path / "library-a"
    source = tmp_path / "source-a"
    library.mkdir()
    source.mkdir()

    add_library_to_catalog(
        catalog_path,
        library_path=library,
        library_id="lib-a",
        library_name="Library A",
        source_root=source,
    )
    listed = list_library_catalog(catalog_path)

    assert listed["schema_version"] == LIBRARY_CATALOG_SCHEMA_VERSION
    assert listed["libraries_count"] == 1
    assert listed["libraries"][0]["library_id"] == "lib-a"
    assert listed["libraries"][0]["library_name"] == "Library A"
    assert listed["libraries"][0]["library_path"].endswith("library-a")
    assert "library_id" in listed["libraries"][0]["metadata"]["agent_evidence_fields"]


def test_library_catalog_cli_add_and_json(tmp_path):
    catalog_path = tmp_path / "libraries.json"
    library = tmp_path / "library-b"
    source = tmp_path / "source-b"
    library.mkdir()
    source.mkdir()

    add_result = runner.invoke(
        app,
        [
            "library-catalog",
            str(catalog_path),
            "--add-library",
            str(library),
            "--library-id",
            "lib-b",
            "--library-name",
            "Library B",
            "--source-root",
            str(source),
        ],
    )
    list_result = runner.invoke(app, ["library-catalog", str(catalog_path), "--json"])

    assert add_result.exit_code == 0
    assert list_result.exit_code == 0
    payload = json.loads(list_result.stdout)
    assert payload["schema_version"] == LIBRARY_CATALOG_SCHEMA_VERSION
    assert payload["libraries"][0]["library_id"] == "lib-b"


def test_library_catalog_cli_requires_id_for_add(tmp_path):
    library = tmp_path / "library"
    library.mkdir()

    result = runner.invoke(app, ["library-catalog", str(tmp_path / "libraries.json"), "--add-library", str(library)])

    assert result.exit_code != 0
    assert "--library-id is required" in result.output
