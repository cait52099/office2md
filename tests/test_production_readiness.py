from pathlib import Path

from typer.testing import CliRunner

from office2md import cli
from office2md.ai.doctor import run_ai_checks
from office2md.models import ConvertOptions, ConvertResult


class FakeConverter:
    name = "markitdown"

    def convert(self, path: Path, options: ConvertOptions) -> ConvertResult:
        return ConvertResult(
            markdown=f"# {path.stem}\n\nBody",
            raw_markdown=f"# {path.stem}\n\nBody",
            engine="markitdown",
            metadata={"source": str(path)},
        )


def test_doctor_ai_missing_mmx_is_non_failing(monkeypatch):
    monkeypatch.setattr("office2md.ai.doctor.shutil.which", lambda name: None)

    checks = run_ai_checks()

    assert checks["ai_backend"] == "disabled by default"
    assert checks["mmx_cli"] == "optional, not found"
    assert checks["mmx_auth_status"] == "optional integration not installed"


def test_dry_run_does_not_generate_document_output(tmp_path):
    input_dir = tmp_path / "input"
    output = tmp_path / "output"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text("hello", encoding="utf-8")
    runner = CliRunner()

    result = runner.invoke(cli.app, ["convert", str(input_dir), str(output), "--recursive", "--dry-run"])

    assert result.exit_code == 0
    assert "Dry run" in result.output
    assert not list(output.rglob("document.md"))


def test_max_files_limits_actual_processing(tmp_path, monkeypatch):
    input_dir = tmp_path / "input"
    output = tmp_path / "output"
    input_dir.mkdir()
    for name in ["a.txt", "b.txt", "c.txt"]:
        (input_dir / name).write_text("# title\n\nbody", encoding="utf-8")
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakeConverter())
    runner = CliRunner()

    result = runner.invoke(cli.app, ["convert", str(input_dir), str(output), "--recursive", "--max-files", "2"])

    assert result.exit_code == 0
    assert len(list(output.rglob("document.md"))) == 2


def test_include_exclude_filters_files(tmp_path, monkeypatch):
    input_dir = tmp_path / "input"
    output = tmp_path / "output"
    input_dir.mkdir()
    (input_dir / "keep.pdf").write_text("pdf", encoding="utf-8")
    (input_dir / "backup.pdf").write_text("pdf", encoding="utf-8")
    (input_dir / "note.txt").write_text("txt", encoding="utf-8")
    monkeypatch.setattr(cli, "get_converter", lambda engine: FakeConverter())
    runner = CliRunner()

    result = runner.invoke(
        cli.app,
        [
            "convert",
            str(input_dir),
            str(output),
            "--recursive",
            "--include",
            "*.pdf",
            "--exclude",
            "*backup*",
        ],
    )

    assert result.exit_code == 0
    manifests = list(output.rglob("manifest.json"))
    assert len(manifests) == 1
    assert "keep" in manifests[0].read_text(encoding="utf-8")


def test_docs_state_ai_is_optional():
    readme = Path("README.md").read_text(encoding="utf-8")
    checklist = Path("RELEASE_CHECKLIST.md").read_text(encoding="utf-8")

    assert "AI enrichment is opt-in" in readme
    assert "MiniMax CLI is not required" in readme
    assert "AI is disabled by default" in checklist
    assert "Missing MiniMax/mmx CLI does not block conversion" in checklist

