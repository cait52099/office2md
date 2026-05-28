import json
import sys

from typer.testing import CliRunner

from office2md.cli import app
from office2md.officecli_benchmark import (
    benchmark_command_specs,
    classify_file_failure,
    collect_office_files,
    compute_sha256,
    recommend_benchmark,
    run_officecli_benchmark,
    run_officecli_command,
    safe_file_id,
)


def test_officecli_benchmark_help_exists():
    result = CliRunner().invoke(app, ["officecli-benchmark", "--help"])

    assert result.exit_code == 0
    assert "officecli-benchmark" in result.output
    assert "--officecli-path" in result.output


def test_missing_officecli_path_gives_clear_error(tmp_path):
    source = tmp_path / "sample.docx"
    source.write_text("content", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["officecli-benchmark", str(source), str(tmp_path / "out"), "--officecli-path", str(tmp_path / "missing.exe")],
    )

    assert result.exit_code != 0
    assert "OfficeCLI executable was not found" in result.output


def test_dry_run_writes_no_artifacts(tmp_path):
    source = tmp_path / "sample.docx"
    source.write_text("content", encoding="utf-8")
    output = tmp_path / "benchmark"

    summary = run_officecli_benchmark(source, output, dry_run=True)

    assert summary["dry_run"] is True
    assert summary["counts"]["files_selected"] == 1
    assert not output.exists()


def test_file_collection_selects_only_supported_office_files(tmp_path):
    for name in ["a.docx", "b.xlsx", "c.pptx", "d.doc", "e.txt"]:
        (tmp_path / name).write_text("content", encoding="utf-8")

    files = collect_office_files(tmp_path)

    assert [item.name for item in files] == ["a.docx", "b.xlsx", "c.pptx"]


def test_temporary_office_files_are_ignored(tmp_path):
    (tmp_path / "~$draft.docx").write_text("temp", encoding="utf-8")
    (tmp_path / "draft.docx").write_text("real", encoding="utf-8")

    files = collect_office_files(tmp_path)

    assert [item.name for item in files] == ["draft.docx"]


def test_safe_file_id_is_stable_and_filesystem_safe(tmp_path):
    source = tmp_path / "Bad Name (Final).docx"
    source.write_text("content", encoding="utf-8")

    first = safe_file_id(source)
    second = safe_file_id(source)

    assert first == second
    assert " " not in first
    assert "(" not in first
    assert first.endswith(first.split("-")[-1])


def test_command_result_capture_handles_success():
    result = run_officecli_command(
        sys.executable,
        ["-c", "print('ok')"],
        timeout_seconds=10,
    )

    assert result["succeeded"] is True
    assert result["exit_code"] == 0
    assert result["stdout"].strip() == "ok"


def test_command_result_capture_handles_failure():
    result = run_officecli_command(
        sys.executable,
        ["-c", "import sys; print('bad', file=sys.stderr); raise SystemExit(2)"],
        timeout_seconds=10,
    )

    assert result["succeeded"] is False
    assert result["exit_code"] == 2
    assert "bad" in result["stderr"]


def test_summary_json_and_markdown_report_are_written(tmp_path, monkeypatch):
    source = tmp_path / "sample.docx"
    source.write_text("content", encoding="utf-8")
    output = tmp_path / "benchmark"
    officecli = tmp_path / "officecli.exe"
    officecli.write_text("fake", encoding="utf-8")
    monkeypatch.setattr("office2md.officecli_benchmark.find_officecli", lambda path=None: officecli)
    monkeypatch.setattr("office2md.officecli_benchmark.run_officecli_command", _fake_officecli_success)

    summary = run_officecli_benchmark(source, output, officecli_path=officecli)

    summary_path = output / "officecli_benchmark_summary.json"
    report_path = output / "officecli_benchmark_report.md"
    assert summary_path.exists()
    assert report_path.exists()
    parsed = json.loads(summary_path.read_text(encoding="utf-8"))
    assert parsed["schema_version"] == "1"
    assert parsed["counts"]["files_selected"] == 1
    assert summary["counts"]["files_succeeded"] == 1


def test_checksum_unchanged_is_recorded(tmp_path, monkeypatch):
    source = tmp_path / "sample.docx"
    source.write_text("content", encoding="utf-8")
    before = compute_sha256(source)
    output = tmp_path / "benchmark"
    officecli = tmp_path / "officecli.exe"
    officecli.write_text("fake", encoding="utf-8")
    monkeypatch.setattr("office2md.officecli_benchmark.find_officecli", lambda path=None: officecli)
    monkeypatch.setattr("office2md.officecli_benchmark.run_officecli_command", _fake_officecli_success)

    summary = run_officecli_benchmark(source, output, officecli_path=officecli)

    record = summary["files"][0]
    assert record["sha256_before"] == before
    assert record["sha256_after"] == before
    assert record["checksum_unchanged"] is True


def test_mocked_officecli_run_does_not_modify_source(tmp_path, monkeypatch):
    source = tmp_path / "sample.docx"
    source.write_text("content", encoding="utf-8")
    before_text = source.read_text(encoding="utf-8")
    output = tmp_path / "benchmark"
    officecli = tmp_path / "officecli.exe"
    officecli.write_text("fake", encoding="utf-8")
    monkeypatch.setattr("office2md.officecli_benchmark.find_officecli", lambda path=None: officecli)
    monkeypatch.setattr("office2md.officecli_benchmark.run_officecli_command", _fake_officecli_success)

    run_officecli_benchmark(source, output, officecli_path=officecli)

    assert source.read_text(encoding="utf-8") == before_text


def test_no_mutating_commands_appear_in_planned_command_list():
    planned_tokens = {token for spec in benchmark_command_specs() for token in spec.arguments}

    assert not (planned_tokens & {"create", "add", "set", "remove", "open", "close"})


def test_command_result_capture_handles_per_file_failure(tmp_path, monkeypatch):
    source = tmp_path / "sample.docx"
    source.write_text("content", encoding="utf-8")
    output = tmp_path / "benchmark"
    officecli = tmp_path / "officecli.exe"
    officecli.write_text("fake", encoding="utf-8")
    monkeypatch.setattr("office2md.officecli_benchmark.find_officecli", lambda path=None: officecli)
    monkeypatch.setattr("office2md.officecli_benchmark.run_officecli_command", _fake_officecli_failure)

    summary = run_officecli_benchmark(source, output, officecli_path=officecli)

    assert summary["counts"]["files_failed"] == 1
    assert (output / "files").is_dir()
    assert summary["files"][0]["errors"]
    assert summary["files"][0]["failure_category"] == "command_failed"
    assert summary["files"][0]["failed_commands"]
    assert summary["recommendation"] == "diagnostic_only"


def test_failure_classification_for_timeout():
    category = classify_file_failure(
        checksum_unchanged=True,
        failed_commands=["outline"],
        timed_out_commands=["outline"],
        json_parse_success=False,
        html_generated=False,
        skip_html=False,
        selected=True,
    )

    assert category == "command_timeout"


def test_failure_classification_for_json_parse_failure():
    category = classify_file_failure(
        checksum_unchanged=True,
        failed_commands=[],
        timed_out_commands=[],
        json_parse_success=False,
        html_generated=True,
        skip_html=False,
        selected=True,
    )

    assert category == "json_parse_failed"


def test_report_includes_diagnostics_sections(tmp_path, monkeypatch):
    source = tmp_path / "sample.docx"
    source.write_text("content", encoding="utf-8")
    output = tmp_path / "benchmark"
    officecli = tmp_path / "officecli.exe"
    officecli.write_text("fake", encoding="utf-8")
    monkeypatch.setattr("office2md.officecli_benchmark.find_officecli", lambda path=None: officecli)
    monkeypatch.setattr("office2md.officecli_benchmark.run_officecli_command", _fake_officecli_failure)

    run_officecli_benchmark(source, output, officecli_path=officecli)

    report = (output / "officecli_benchmark_report.md").read_text(encoding="utf-8")
    assert "## Failed Files" in report
    assert "## Per-Command Results" in report
    assert "## Checksum Safety Result" in report
    assert "Failure category" in report


def test_recommendation_sidecar_candidate_when_safe_readable_conditions_pass():
    summary = {
        "dry_run": False,
        "counts": {"files_selected": 3, "files_failed": 0, "checksum_changed": 0, "json_parse_success": 2, "html_generated": 1},
        "files": [
            {"artifacts": {"text.txt": "a"}},
            {"artifacts": {"outline.txt": "b"}},
            {"artifacts": {}},
        ],
    }

    recommendation, reasons = recommend_benchmark(summary)

    assert recommendation == "sidecar_candidate"
    assert reasons


def test_recommendation_diagnostic_only_when_partial_failures_exist():
    summary = {
        "dry_run": False,
        "counts": {"files_selected": 2, "files_failed": 1, "checksum_changed": 0, "json_parse_success": 1, "html_generated": 1},
        "files": [{"artifacts": {"text.txt": "a"}}, {"artifacts": {}}],
    }

    recommendation, reasons = recommend_benchmark(summary)

    assert recommendation == "diagnostic_only"
    assert "failure" in reasons[0] or "timeout" in reasons[0]


def test_summary_json_contains_additive_diagnostics_fields(tmp_path, monkeypatch):
    source = tmp_path / "sample.docx"
    source.write_text("content", encoding="utf-8")
    output = tmp_path / "benchmark"
    officecli = tmp_path / "officecli.exe"
    officecli.write_text("fake", encoding="utf-8")
    monkeypatch.setattr("office2md.officecli_benchmark.find_officecli", lambda path=None: officecli)
    monkeypatch.setattr("office2md.officecli_benchmark.run_officecli_command", _fake_officecli_success)

    run_officecli_benchmark(source, output, officecli_path=officecli)

    data = json.loads((output / "officecli_benchmark_summary.json").read_text(encoding="utf-8"))
    record = data["files"][0]
    assert data["recommendation"] in {"engine_candidate", "sidecar_candidate"}
    assert "recommendation_reasons" in data
    assert "failure_category" in record
    assert "failed_commands" in record
    assert "timed_out_commands" in record
    assert "html_generated" in record


def _fake_officecli_success(officecli_path, arguments, *, timeout_seconds=60):
    stdout = "OfficeCLI 1.0.100"
    if "--version" not in arguments:
        stdout = "{}" if "--json" in arguments else "ok"
    return {
        "command": [str(officecli_path), *arguments],
        "exit_code": 0,
        "runtime_seconds": 0.001,
        "timed_out": False,
        "stdout": stdout,
        "stderr": "",
        "succeeded": True,
    }


def _fake_officecli_failure(officecli_path, arguments, *, timeout_seconds=60):
    return {
        "command": [str(officecli_path), *arguments],
        "exit_code": 2,
        "runtime_seconds": 0.001,
        "timed_out": False,
        "stdout": "",
        "stderr": "failed",
        "succeeded": False,
    }
