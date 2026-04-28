from office2md.docling_diagnostics import SAFE_ENV_VARS, exception_summary, safe_environment


def test_safe_environment_only_reports_allowlisted_variables(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example")
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    monkeypatch.setenv("HF_TOKEN", "secret")

    values = safe_environment()

    assert set(values) == set(SAFE_ENV_VARS)
    assert values["HTTP_PROXY"] == "http://proxy.example"
    assert "OPENAI_API_KEY" not in values
    assert "HF_TOKEN" not in values


def test_exception_summary_contains_type_message_and_traceback():
    try:
        raise RuntimeError("network/model download failed")
    except RuntimeError as exc:
        summary = exception_summary(exc)

    assert summary["type"].endswith(".RuntimeError")
    assert summary["message"] == "network/model download failed"
    assert "RuntimeError" in summary["traceback"]
