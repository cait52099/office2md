import itertools
import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from slugify import slugify

from office2md.cli import _search_export_json_payload
from office2md.detector import sha256_file
from office2md.exports.obsidian import ObsidianExportError, export_obsidian
from office2md.library import library_report
from office2md.library import search_library, search_library_diagnostics, search_library_facets
from office2md.scanner import scan_input
from office2md.workspace import detect_workspace, summarize_workspace_status


DEFAULT_RUNNER_PYTHON = r".\.venv\Scripts\python.exe"
CONCEPT_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "system",
    "user texts",
    "page",
    "pages",
    "document",
    "documents",
    "file",
    "source",
    "asset",
    "assets",
    "image",
    "images",
    "locator",
    "locators",
    "extracted",
    "form",
    "group",
    "summary",
    "untitled",
    "png",
    "jpg",
    "jpeg",
    "table",
    "section",
    "text",
    "chapter",
    "title",
    "untitled source page",
}
NOISY_CONCEPT_PHRASES = {
    "cover sheet",
    "private confidential",
    "liang private",
    "selection new",
    "caner sheet",
}
CONCEPT_SOURCE_WEIGHTS = {
    "structured_header": 7.0,
    "entity": 6.0,
    "document_title": 4.0,
    "heading": 4.0,
    "text_phrase": 2.0,
    "weak_page_title": 0.5,
}


def normalize_library_path(value: str) -> Path | None:
    text = (value or "").strip().strip('"')
    return Path(text).expanduser() if text else None


def is_valid_library_path(path: Path | None) -> bool:
    if path is None:
        return False
    if path.is_dir():
        return (path / "library.db").exists()
    return path.name == "library.db" and path.exists()


def is_conversion_output_path(path: Path | None) -> bool:
    if path is None or not path.is_dir() or is_valid_library_path(path):
        return False
    return any(path.rglob("manifest.json"))


def suggest_workspace_path(source_folder: Path | None) -> Path | None:
    if source_folder is None:
        return None
    source = source_folder.expanduser()
    name = source.name or "office2md"
    return source.parent / f"{name}-office2md-output"


def derive_workspace_paths(workspace_folder: Path) -> dict[str, Path]:
    workspace = workspace_folder.expanduser()
    return {
        "workspace_folder": workspace,
        "conversion_output_folder": workspace / "conversion",
        "library_output_folder": workspace / "library",
        "log_folder": workspace / "logs",
    }


def validate_workspace_paths(source_folder: Path, workspace_folder: Path) -> None:
    source = source_folder.expanduser().resolve()
    workspace = workspace_folder.expanduser().resolve()
    if source == workspace:
        raise ValueError("Output Workspace Folder must not be the same as Source Folder.")
    paths = derive_workspace_paths(workspace)
    derived = [
        paths["conversion_output_folder"].resolve(),
        paths["library_output_folder"].resolve(),
        paths["log_folder"].resolve(),
    ]
    if len(set(derived)) != len(derived):
        raise ValueError("Derived conversion, library, and log folders must be distinct.")


def workspace_warnings(workspace_folder: Path) -> list[str]:
    workspace = workspace_folder.expanduser()
    if workspace.exists() and any(workspace.iterdir()):
        return [
            "Output Workspace Folder already exists and is not empty.",
            "Reusing an old workspace can include old conversion manifests in the next Build Library step.",
            "Use a new empty workspace for each source collection when possible. Nothing is deleted automatically.",
        ]
    return []


def load_library_report(path: Path) -> dict[str, Any]:
    return library_report(path)


def load_library_overview(path: Path) -> dict[str, Any]:
    return load_library_report(path)


def overview_metrics(report: dict[str, Any]) -> dict[str, int]:
    return {
        "documents_count": int(report.get("documents_count") or 0),
        "chunks_count": int(report.get("chunks_count") or 0),
        "entities_count": int(report.get("entities_count") or 0),
        "noisy_chunks_count": int(report.get("noisy_chunks_count") or 0),
        "chunks_without_locator": int(report.get("chunks_without_locator") or 0),
        "page_level_pdf_documents": len(report.get("page_level_pdf_documents") or []),
    }


def run_library_search(
    library_path: Path,
    query: str,
    limit: int = 5,
    diagnostics: bool = False,
    facets: bool = False,
    context: int = 0,
    output_dir: str | None = None,
    entity: str | None = None,
) -> dict[str, Any]:
    cleaned_query = query.strip()
    cleaned_output_dir = _clean_optional_text(output_dir)
    entities = [_clean_optional_text(entity)] if _clean_optional_text(entity) else []
    results = search_library(
        library_path,
        cleaned_query,
        limit=max(1, int(limit)),
        output_dir=cleaned_output_dir,
        entities=entities,
        related=max(0, int(context)),
    )
    diagnostic_data = search_library_diagnostics(
        cleaned_query,
        results,
        output_dir=cleaned_output_dir,
        entities=entities,
    )
    facet_data = (
        search_library_facets(
            library_path,
            cleaned_query,
            output_dir=cleaned_output_dir,
            entities=entities,
        )
        if facets
        else {}
    )
    return {
        "results": results,
        "rows": search_result_table_rows(results),
        "diagnostics": diagnostic_data if diagnostics else None,
        "facets": facet_data,
        "export_json": search_export_download_json(diagnostic_data, results),
    }


def search_result_table_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rank": item.get("rank"),
            "document_title": item.get("document_title"),
            "source_file": item.get("source_file"),
            "document_kind": item.get("document_kind"),
            "evidence_type": item.get("evidence_type"),
            "locator": item.get("locator"),
            "output_dir": item.get("output_dir"),
            "preview": item.get("preview"),
        }
        for item in results
    ]


def search_export_download_json(diagnostics: dict[str, Any], results: list[dict[str, Any]]) -> str:
    return json.dumps(_search_export_json_payload(diagnostics, results), ensure_ascii=False, indent=2) + "\n"


def scan_source_folder_for_gui(
    source_folder: Path,
    conversion_output_folder: Path,
    max_files: int | None = None,
    full_directory: bool = False,
) -> dict[str, Any]:
    source = source_folder.expanduser()
    output = conversion_output_folder.expanduser()
    if not source.exists():
        raise FileNotFoundError(f"Source folder does not exist: {source}")
    if not source.is_dir():
        raise NotADirectoryError(f"Source path is not a folder: {source}")

    files = scan_input(source, recursive=True)
    selected_files = files if full_directory or max_files is None else files[: max(0, int(max_files))]
    expected_names = _expected_manifest_names(selected_files, output)
    manifest_counts = count_existing_manifests(output, expected_names)
    warnings = dry_run_path_warnings(source, output)
    return {
        "source_folder": str(source),
        "conversion_output_folder": str(output),
        "supported_files_count": len(files),
        "selected_files_count": len(selected_files),
        "expected_unique_manifest_count": len(expected_names),
        "expected_manifest_names": expected_names,
        "existing_manifest_count": manifest_counts["existing_manifest_count"],
        "completed_expected_manifest_count": manifest_counts["completed_expected_manifest_count"],
        "failed_manifest_count": manifest_counts["failed_manifest_count"],
        "target_reached": manifest_counts["completed_expected_manifest_count"] >= len(expected_names) if expected_names else False,
        "warnings": warnings,
    }


def count_existing_manifests(output_folder: Path, expected_names: list[str] | None = None) -> dict[str, int]:
    output = output_folder.expanduser()
    if not output.exists():
        return {
            "existing_manifest_count": 0,
            "completed_expected_manifest_count": 0,
            "failed_manifest_count": 0,
        }
    manifests = list(output.rglob("manifest.json"))
    failed = 0
    for manifest_path in manifests:
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("status") == "failed":
            failed += 1
    expected = expected_names or []
    completed_expected = sum(1 for name in expected if (output / name / "manifest.json").exists())
    return {
        "existing_manifest_count": len(manifests),
        "completed_expected_manifest_count": completed_expected,
        "failed_manifest_count": failed,
    }


def build_runner_command_preview(
    source_folder: Path,
    conversion_output_folder: Path,
    log_folder: Path,
    max_files: int | None = None,
    full_directory: bool = False,
    timeout_minutes: int = 45,
    max_attempts: int = 20,
    python_path: str = DEFAULT_RUNNER_PYTHON,
    runner_script: Path | str = r".\scripts\Invoke-Office2MdChunkedConvert.ps1",
) -> str:
    return _powershell_command(
        build_runner_script_arguments(
            source_folder,
            conversion_output_folder,
            log_folder,
            max_files=max_files,
            full_directory=full_directory,
            timeout_minutes=timeout_minutes,
            max_attempts=max_attempts,
            python_path=python_path,
            runner_script=runner_script,
        )
    )


def build_runner_script_arguments(
    source_folder: Path,
    conversion_output_folder: Path,
    log_folder: Path,
    max_files: int | None = None,
    full_directory: bool = False,
    timeout_minutes: int = 45,
    max_attempts: int = 20,
    python_path: str = DEFAULT_RUNNER_PYTHON,
    runner_script: Path | str = r".\scripts\Invoke-Office2MdChunkedConvert.ps1",
) -> list[str]:
    parts = [
        str(runner_script),
        "-InputPath",
        str(source_folder),
        "-OutputPath",
        str(conversion_output_folder),
        "-LogDirectory",
        str(log_folder),
        "-TimeoutMinutes",
        str(int(timeout_minutes)),
        "-MaxAttempts",
        str(int(max_attempts)),
    ]
    if full_directory:
        parts.append("-FullDirectory")
    elif max_files:
        parts.extend(["-MaxFiles", str(max_files)])
    parts.extend(["-Python", python_path])
    return parts


def run_convert_update_command(
    source_folder: Path,
    conversion_output_folder: Path,
    log_folder: Path,
    max_files: int | None = None,
    full_directory: bool = False,
    timeout_minutes: int = 45,
    max_attempts: int = 20,
    python_path: str = DEFAULT_RUNNER_PYTHON,
    runner_script: Path | str = r".\scripts\Invoke-Office2MdChunkedConvert.ps1",
    cwd: Path | None = None,
    subprocess_timeout_seconds: int | None = None,
) -> dict[str, Any]:
    source = source_folder.expanduser()
    output = conversion_output_folder.expanduser()
    logs = log_folder.expanduser()
    runner = Path(runner_script)
    working_dir = cwd or Path.cwd()
    runner_path = runner if runner.is_absolute() else working_dir / runner
    if not source.exists():
        raise FileNotFoundError(f"Source folder does not exist: {source}")
    if not source.is_dir():
        raise NotADirectoryError(f"Source path is not a folder: {source}")
    if not runner_path.exists():
        raise FileNotFoundError(f"Runner script does not exist: {runner_path}")
    powershell = _find_powershell()
    if powershell is None:
        raise FileNotFoundError("PowerShell was not found on PATH.")

    script_args = build_runner_script_arguments(
        source,
        output,
        logs,
        max_files=max_files,
        full_directory=full_directory,
        timeout_minutes=timeout_minutes,
        max_attempts=max_attempts,
        python_path=python_path,
        runner_script=runner_path,
    )
    command = [
        powershell,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        *script_args,
    ]
    completed = subprocess.run(
        command,
        cwd=working_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=subprocess_timeout_seconds,
        check=False,
    )
    summary = summarize_conversion_output(output)
    return {
        "command": _powershell_command(script_args),
        "argv": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "log_folder": str(logs),
        "summary": summary,
    }


def summarize_conversion_output(conversion_output_folder: Path) -> dict[str, int | bool | str]:
    output = conversion_output_folder.expanduser()
    counts = count_existing_manifests(output)
    return {
        "conversion_output_folder": str(output),
        "output_exists": output.exists(),
        "final_manifest_count": counts["existing_manifest_count"],
        "failed_manifest_count": counts["failed_manifest_count"],
    }


def build_library_command_preview(
    conversion_output_folder: Path,
    library_output_folder: Path,
    python_path: str = DEFAULT_RUNNER_PYTHON,
) -> str:
    return _powershell_command(
        [
            python_path,
            "-m",
            "office2md.cli",
            "build-library",
            str(conversion_output_folder),
            str(library_output_folder),
        ]
    )


def run_build_library_command(
    conversion_output_folder: Path,
    library_output_folder: Path,
    python_path: str | None = None,
    cwd: Path | None = None,
    subprocess_timeout_seconds: int | None = None,
) -> dict[str, Any]:
    conversion_output = conversion_output_folder.expanduser()
    library_output = library_output_folder.expanduser()
    if not conversion_output.exists():
        raise FileNotFoundError(f"Conversion output folder does not exist: {conversion_output}")
    if not conversion_output.is_dir():
        raise NotADirectoryError(f"Conversion output path is not a folder: {conversion_output}")
    executable = python_path or sys.executable
    command = [
        executable,
        "-m",
        "office2md.cli",
        "build-library",
        str(conversion_output),
        str(library_output),
    ]
    completed = subprocess.run(
        command,
        cwd=cwd or Path.cwd(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=subprocess_timeout_seconds,
        check=False,
    )
    return {
        "command": _powershell_command(command),
        "argv": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "summary": summarize_library_output(library_output),
    }


def summarize_library_output(library_output_folder: Path) -> dict[str, Any]:
    library_output = library_output_folder.expanduser()
    summary: dict[str, Any] = {
        "library_output_folder": str(library_output),
        "output_exists": library_output.exists(),
        "library_db_exists": (library_output / "library.db").exists(),
        "library_index_exists": (library_output / "library_index.json").exists(),
        "library_graph_exists": (library_output / "library_graph.json").exists(),
        "library_markdown_exists": (library_output / "_library.md").exists(),
        "quality_report_exists": (library_output / "_quality_report.md").exists(),
        "is_valid_library": is_valid_library_path(library_output),
    }
    if summary["is_valid_library"]:
        try:
            report = library_report(library_output)
        except Exception as exc:  # pragma: no cover - defensive summary only.
            summary["library_report_error"] = str(exc)
        else:
            summary["documents_count"] = report.get("documents_count")
            summary["chunks_count"] = report.get("chunks_count")
            summary["entities_count"] = report.get("entities_count")
    return summary


def build_obsidian_export_command_preview(
    library_path: Path,
    vault_output_folder: Path,
    overwrite: bool = False,
    dry_run: bool = False,
    max_concepts: int = 100,
    max_evidence_per_concept: int = 5,
    python_path: str = DEFAULT_RUNNER_PYTHON,
) -> str:
    parts = [
        python_path,
        "-m",
        "office2md.cli",
        "export-obsidian",
        str(library_path),
        str(vault_output_folder),
        "--max-concepts",
        str(int(max_concepts)),
        "--max-evidence-per-concept",
        str(int(max_evidence_per_concept)),
    ]
    if overwrite:
        parts.append("--overwrite")
    if dry_run:
        parts.append("--dry-run")
    return _powershell_command(parts)


def run_obsidian_export_for_gui(
    library_path: Path,
    vault_output_folder: Path,
    overwrite: bool = False,
    dry_run: bool = False,
    max_concepts: int = 100,
    max_evidence_per_concept: int = 5,
) -> dict[str, Any]:
    library = library_path.expanduser()
    if not is_valid_library_path(library):
        raise FileNotFoundError(f"Built library folder or library.db was not found: {library}")
    try:
        return export_obsidian(
            library,
            vault_output_folder.expanduser(),
            overwrite=overwrite,
            dry_run=dry_run,
            max_concepts=max_concepts,
            max_evidence_per_concept=max_evidence_per_concept,
        )
    except ObsidianExportError:
        raise


def summarize_obsidian_export_output(vault_output_folder: Path) -> dict[str, Any]:
    vault = vault_output_folder.expanduser()
    manifest_path = vault / "_office2md" / "export_manifest.json"
    summary: dict[str, Any] = {
        "vault_output_folder": str(vault),
        "output_exists": vault.exists(),
        "index_exists": (vault / "00_Index.md").exists(),
        "library_report_exists": (vault / "00_Library_Report.md").exists(),
        "documents_dir_exists": (vault / "Documents").is_dir(),
        "concepts_dir_exists": (vault / "Concepts").is_dir(),
        "manifest_exists": manifest_path.exists(),
    }
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            summary["manifest_error"] = str(exc)
        else:
            summary["manifest"] = manifest
            summary["documents_exported"] = manifest.get("documents_exported")
            summary["concepts_exported"] = manifest.get("concepts_exported")
            summary["warnings"] = manifest.get("warnings") or []
    return summary


def load_workspace_status_for_gui(workspace_path: Path, show_history: bool = False, limit: int = 5) -> dict[str, Any]:
    workspace = workspace_path.expanduser()
    return summarize_workspace_status(workspace, show_history=show_history, limit=max(0, int(limit)))


def workspace_status_json_for_download(status: dict[str, Any]) -> str:
    return json.dumps(status, ensure_ascii=False, indent=2) + "\n"


def classify_workspace_path_hint(path: Path) -> dict[str, Any]:
    candidate = path.expanduser()
    expected_markers = [
        "workspace_manifest.json",
        "source_manifest.json",
        "versions/library_versions.json",
        "versions/output_versions.json",
    ]
    hint: dict[str, Any] = {
        "path": str(candidate),
        "exists": candidate.exists(),
        "is_workspace": detect_workspace(candidate),
        "kind": "workspace_root" if detect_workspace(candidate) else "unknown",
        "message": "",
        "expected_markers": expected_markers,
        "suggested_workspace_path": str(_suggest_workspace_root_from_path(candidate)),
        "workspace_init_command": build_workspace_init_command_hint(candidate),
    }
    if hint["is_workspace"]:
        hint["message"] = "This looks like an office2md workspace root."
        return hint
    if candidate.is_dir() and ((candidate / "library.db").exists() or (candidate / "library_index.json").exists()):
        hint["kind"] = "built_library"
        hint["message"] = "This looks like a built Library folder. Use it in Library Overview, Search, or Graph View, not as the Workspace Root Path."
        return hint
    if candidate.is_dir() and (candidate / "00_Index.md").exists() and (candidate / "_office2md" / "export_manifest.json").exists():
        hint["kind"] = "obsidian_export"
        hint["message"] = "This looks like an Obsidian export folder. It is an output artifact, not a workspace root."
        return hint
    if candidate.is_dir() and _looks_like_conversion_output(candidate):
        hint["kind"] = "conversion_output"
        hint["message"] = "This looks like a conversion output or Knowledge Pack folder. It is not a workspace root."
        return hint
    if candidate.name.endswith("-office2md-output") or candidate.name.endswith("_office2md_output"):
        hint["kind"] = "output_workspace"
        hint["message"] = "This looks like an office2md output workspace folder. It may contain conversion, library, or export outputs, but it is not a workspace root unless workspace-init was run there."
        return hint
    if not candidate.exists():
        hint["kind"] = "missing_path"
        hint["message"] = "This path does not exist yet. Create a workspace root with workspace-init before loading it here."
    else:
        hint["message"] = "This folder is not recognized as an office2md workspace root."
    return hint


def build_workspace_init_command_hint(path: Path) -> str:
    suggested = _suggest_workspace_root_from_path(path.expanduser())
    return _powershell_command(["python", "-m", "office2md.cli", "workspace-init", str(suggested)])


def build_workspace_next_step_hints(status: dict[str, Any]) -> list[str]:
    workspace_path = status.get("workspace", {}).get("workspace_path") or "WORKSPACE_PATH"
    source_total = int(status.get("source_manifest", {}).get("total_sources") or 0)
    library_total = int(status.get("library_versions", {}).get("total_versions") or 0)
    output_total = int(status.get("output_versions", {}).get("total_versions") or 0)
    if source_total or library_total or output_total:
        return []
    return [
        _powershell_command(["python", "-m", "office2md.cli", "workspace-scan", workspace_path, "SOURCE_PATH"]),
        _powershell_command(["python", "-m", "office2md.cli", "workspace-register-library", workspace_path, "LIBRARY_PATH"]),
        _powershell_command(["python", "-m", "office2md.cli", "workspace-register-output", workspace_path, "OUTPUT_PATH"]),
    ]


def dry_run_path_warnings(source_folder: Path, conversion_output_folder: Path) -> list[str]:
    warnings = ["Dry-run only: no files will be converted and no library will be built."]
    source_text = str(source_folder)
    if re.search(r"onedrive|teams", source_text, flags=re.IGNORECASE):
        warnings.append("OneDrive/Teams source detected: ensure files are available offline before conversion.")
    if source_text.startswith(r"\\"):
        warnings.append("Network/UNC source detected: paths can be slow, unavailable, or locked.")
    if conversion_output_folder.exists():
        warnings.append("Conversion output folder already exists; existing manifests will be counted but not modified.")
    warnings.append("Legacy .doc files remain unsupported/fragile in the validated workflow.")
    warnings.append("OCR and AI are disabled by default.")
    return warnings


def _find_powershell() -> str | None:
    return shutil.which("powershell.exe") or shutil.which("powershell") or shutil.which("pwsh")


def _suggest_workspace_root_from_path(path: Path) -> Path:
    candidate = path.expanduser()
    name = candidate.name
    if name.endswith("-office2md-output"):
        return candidate.with_name(name[: -len("-office2md-output")] + ".office2md")
    if name.endswith("_office2md_output"):
        return candidate.with_name(name[: -len("_office2md_output")] + ".office2md")
    if candidate.suffix == ".office2md":
        return candidate
    return candidate.with_suffix(".office2md") if candidate.suffix else candidate.with_name(f"{name}.office2md")


def _looks_like_conversion_output(path: Path) -> bool:
    direct_markers = {"manifest.json", "chunks.jsonl", "source_map.json", "knowledge.json"}
    if any((path / marker).exists() for marker in direct_markers):
        return True
    marker_count = 0
    for child in path.iterdir():
        if not child.is_dir():
            continue
        if any((child / marker).exists() for marker in direct_markers):
            marker_count += 1
        if marker_count >= 1:
            return True
    return False


def _expected_manifest_names(files: list[Path], output_root: Path) -> list[str]:
    seen: dict[Path, tuple[str, str]] = {}
    targets = []
    for source in files:
        checksum = sha256_file(source)
        slug = slugify(source.stem) or "document"
        base_target = output_root / slug
        source_key = (str(source.resolve()), checksum)
        if base_target not in seen:
            target = base_target
        elif seen[base_target] == source_key:
            target = base_target
        else:
            short_hash = checksum.split(":", 1)[-1][:8]
            target = output_root / f"{slug}-{short_hash}"
        seen[target] = source_key
        targets.append(target)
    return sorted({target.name for target in targets})


def _powershell_command(parts: list[str]) -> str:
    return " ".join(_quote_powershell_arg(part) for part in parts)


def _quote_powershell_arg(value: str) -> str:
    text = str(value)
    if not text:
        return '""'
    if re.search(r'[\s"]', text):
        return '"' + text.replace('"', r'\"') + '"'
    return text


def graph_json_path(library_path: Path) -> Path:
    base = library_path if library_path.is_dir() else library_path.parent
    return base / "library_graph.json"


def load_library_graph(library_path: Path) -> dict[str, Any]:
    path = graph_json_path(library_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "nodes": data.get("nodes", []) or [],
        "edges": data.get("edges", []) or [],
        "path": str(path),
    }


def load_curated_concept_index(library_path: Path) -> dict[str, Any]:
    db_path = _library_db_path(library_path)
    concept_data: dict[str, dict[str, Any]] = {}
    doc_labels: dict[str, str] = {}
    hidden_noisy = 0

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT c.chunk_id, c.doc_id, c.title AS chunk_title, c.text, c.heading_path_json,
                   d.title AS document_title, d.source_file, d.document_kind
            FROM chunks c
            JOIN documents d ON d.doc_id = c.doc_id
            """
        ).fetchall()
        entity_rows = conn.execute(
            """
            SELECT e.entity_text, e.entity_type, e.normalized_text, m.doc_id, m.chunk_id
            FROM entities e
            JOIN entity_mentions m ON m.entity_id = e.entity_id
            """
        ).fetchall()

    for row in rows:
        doc_id = row["doc_id"]
        doc_labels[doc_id] = row["document_title"] or row["source_file"] or doc_id
        context = " ".join(str(value or "") for value in [row["document_title"], row["chunk_title"], row["text"]])
        candidates = []
        title_candidate = _direct_concept_candidate(row["document_title"] or "")
        if title_candidate:
            candidates.append((title_candidate, "document_title"))
        candidates.extend((label, "document_title") for label in _concept_candidates_from_text(row["document_title"] or "", max_terms=12))
        candidates.extend((label, "heading") for label in _heading_concept_candidates(row["heading_path_json"], row["chunk_title"]))
        candidates.extend((label, "text_phrase") for label in _concept_candidates_from_text(row["text"] or "", max_terms=24))
        for label, base_source_type in candidates:
            normalized = normalize_concept_label(label)
            if _is_short_ascii_acronym(normalized) and _looks_like_page_header_only(row["text"] or "", normalized):
                hidden_noisy += 1
                continue
            if base_source_type in {"document_title", "heading"} and _is_short_ascii_acronym(normalized) and not _contains_standalone_term(row["text"] or "", normalized):
                hidden_noisy += 1
                continue
            if is_noisy_concept_label(normalized):
                hidden_noisy += 1
                continue
            source_type = _concept_source_type(label, base_source_type, row)
            _add_library_native_concept(
                concept_data,
                normalized,
                label,
                source_type,
                doc_id,
                row["chunk_id"],
                row["document_title"] or row["source_file"] or doc_id,
                context,
            )

    doc_title_by_id = {row["doc_id"]: doc_labels[row["doc_id"]] for row in rows}
    chunk_context_by_id = {
        row["chunk_id"]: " ".join(str(value or "") for value in [row["document_title"], row["chunk_title"], row["text"]])
        for row in rows
    }
    for entity in entity_rows:
        label = entity["entity_text"] or entity["normalized_text"]
        normalized = normalize_concept_label(label)
        if is_noisy_concept_label(normalized):
            hidden_noisy += 1
            continue
        doc_id = entity["doc_id"]
        chunk_id = entity["chunk_id"]
        _add_library_native_concept(
            concept_data,
            normalized,
            label,
            "entity",
            doc_id,
            chunk_id,
            doc_title_by_id.get(doc_id, doc_id),
            chunk_context_by_id.get(chunk_id or "", doc_title_by_id.get(doc_id, "")),
        )

    concepts = {}
    for label, data in concept_data.items():
        if not (data["chunk_ids"] or data["doc_ids"]):
            continue
        score = _concept_quality_score(data)
        if not _passes_concept_quality(label, data, score):
            hidden_noisy += 1
            continue
        concepts[label] = {
            **data,
            "chunk_ids": data["chunk_ids"],
            "doc_ids": data["doc_ids"],
            "doc_counts": dict(data["doc_counts"]),
            "contexts": data["contexts"],
            "source_types": sorted(data["source_types"]),
            "source_counts": dict(data["source_counts"]),
            "match_count": sum(data["source_counts"].values()),
            "quality_score": round(score, 2),
            "weight": round(score + len(data["chunk_ids"]) + len(data["doc_ids"]), 2),
        }
    return {
        "concepts": concepts,
        "doc_labels": doc_labels,
        "hidden_noisy_concepts_count": hidden_noisy,
    }


def _library_db_path(library_path: Path) -> Path:
    return library_path / "library.db" if library_path.is_dir() else library_path


def normalize_concept_label(label: str) -> str:
    return " ".join((label or "").strip().casefold().split())


def is_noisy_concept_label(label: str) -> bool:
    text = normalize_concept_label(label)
    if not text:
        return True
    if text in CONCEPT_STOPWORDS:
        return True
    if text in NOISY_CONCEPT_PHRASES:
        return True
    if "private" in text or "confidential" in text:
        return True
    if text.endswith(" sheet") and text.split(" ", 1)[0] not in {"data", "assessment", "score", "risk"}:
        return True
    if re.search(r"\d", text) and (" form " in f" {text} " or "group" in text):
        return True
    if "pm-group" in text:
        return True
    if len(text) < 3 and not re.search(r"[\u4e00-\u9fff]", text):
        return True
    if re.fullmatch(r"\d{4}|\d+(\.\d+)?", text):
        return True
    if re.fullmatch(r"[a-z]{2}-[a-z]{2}", text):
        return True
    if text in {"min", "°c", "℃", "%", "bar", "rpm"}:
        return True
    if text.startswith("assets/") or re.search(r"\.(png|jpg|jpeg|gif|bmp|tiff)$", text):
        return True
    if re.search(r"\.(pdf|docx?|xlsx?|pptx?|txt|md|html)$", text):
        return True
    if re.fullmatch(r"eng-\d+", text):
        return True
    if text in {"document_has_chunk", "document_has_asset", "chunk_has_source_locator"}:
        return True
    return False


def _add_library_native_concept(
    concepts: dict[str, dict[str, Any]],
    normalized: str,
    label: str,
    source_type: str,
    doc_id: str,
    chunk_id: str | None,
    document_title: str,
    context: str,
) -> None:
    item = concepts.setdefault(
        normalized,
        {
            "label": _display_concept_label(label),
            "aliases": set(),
            "chunk_ids": set(),
            "doc_ids": set(),
            "doc_counts": Counter(),
            "contexts": set(),
            "source_types": set(),
            "source_counts": Counter(),
            "sample_document_title": document_title,
        },
    )
    item["aliases"].add(label)
    item["source_types"].add(source_type)
    item["source_counts"][source_type] += 1
    item["doc_ids"].add(doc_id)
    item["doc_counts"][doc_id] += 1
    if chunk_id:
        item["chunk_ids"].add(chunk_id)
    if context:
        item["contexts"].add(_short_label(context, 240))


def _display_concept_label(label: str) -> str:
    text = " ".join(str(label or "").strip().split())
    return text[:1].upper() + text[1:] if text.islower() else text


def _heading_concept_candidates(heading_path_json: str | None, chunk_title: str | None) -> list[str]:
    values = []
    if heading_path_json:
        try:
            loaded = json.loads(heading_path_json)
        except json.JSONDecodeError:
            loaded = []
        if isinstance(loaded, list):
            values.extend(str(item) for item in loaded)
    if chunk_title:
        values.append(chunk_title)
    candidates = []
    for value in values:
        direct = _direct_concept_candidate(value)
        if direct:
            candidates.append(direct)
        candidates.extend(_concept_candidates_from_text(value, max_terms=10))
    return candidates


def _direct_concept_candidate(text: str) -> str | None:
    clean = re.sub(r"\s+", " ", (text or "").strip(" .:-|"))
    if not clean or len(clean) > 80:
        return None
    normalized = normalize_concept_label(clean)
    if is_noisy_concept_label(normalized):
        return None
    words = re.findall(r"[A-Za-z][A-Za-z0-9+.-]*|[\u4e00-\u9fff]{2,}", clean)
    if not (1 <= len(words) <= 8):
        return None
    if len(words) == 1 and not re.search(r"[\u4e00-\u9fff]", clean) and len(words[0]) < 5:
        return None
    return clean


def _concept_source_type(label: str, base_source_type: str, row: sqlite3.Row) -> str:
    if base_source_type in {"heading", "text_phrase"} and _looks_structured_header_label(label):
        return "structured_header"
    if base_source_type == "heading" and _is_weak_page_title_source(row):
        return "weak_page_title"
    return base_source_type


def _looks_structured_header_label(label: str) -> bool:
    text = normalize_concept_label(label)
    if is_noisy_concept_label(text):
        return False
    words = text.split()
    if 2 <= len(words) <= 6 and any(word in words for word in {"assessment", "leadership", "thinking", "background", "experience", "risk", "study"}):
        return True
    return text in {
        "leadership",
        "communication",
        "collaboration",
        "resilience",
        "english",
        "result",
        "case study",
        "logical thinking",
        "strategic thinking",
        "technical background",
        "learning agility",
        "background information",
    }


def _is_weak_page_title_source(row: sqlite3.Row) -> bool:
    document_kind = normalize_concept_label(row["document_kind"] or "")
    chunk_title = normalize_concept_label(row["chunk_title"] or "")
    if document_kind in {"generic_pdf", "low_structure_pdf"}:
        return True
    return chunk_title in {"cover", "cover sheet", "summary", "sheet", "untitled source page"}


def _concept_candidates_from_text(text: str, max_terms: int) -> list[str]:
    clean = re.sub(r"https?://\S+|[\w.+-]+@[\w.-]+\.\w+|\+?\d[\d\s().-]{7,}\d|[\\/_]+", " ", text or "")
    chinese_terms = re.findall(r"[\u4e00-\u9fff]{2,8}", clean)
    tokens = [
        token.strip(".-+").casefold()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9+.-]*", clean)
        if not is_noisy_concept_label(token.strip(".-+"))
    ]
    counts = Counter(tokens)
    phrases = Counter()
    for left, right in zip(tokens, tokens[1:]):
        if left not in CONCEPT_STOPWORDS and right not in CONCEPT_STOPWORDS:
            phrases[f"{left} {right}"] += 1
    selected = [label for label, _count in phrases.most_common(max_terms)]
    selected.extend(label for label, _count in counts.most_common(max_terms) if label not in selected)
    selected.extend(term for term in chinese_terms[:max_terms] if term not in selected)
    return [label for label in selected[:max_terms] if not is_noisy_concept_label(label)]


def _concept_quality_score(data: dict[str, Any]) -> float:
    source_counts = data.get("source_counts") or {}
    source_score = max((CONCEPT_SOURCE_WEIGHTS.get(source_type, 1.0) for source_type in source_counts), default=0.0)
    match_count = sum(source_counts.values())
    document_count = len(data.get("doc_ids") or [])
    repeated_bonus = min(match_count, 8) * 0.45
    document_bonus = min(document_count, 5) * 0.8
    if source_counts.get("weak_page_title") and len(source_counts) == 1:
        source_score = min(source_score, 0.5)
    return source_score + repeated_bonus + document_bonus


def _passes_concept_quality(label: str, data: dict[str, Any], score: float) -> bool:
    normalized = normalize_concept_label(label)
    if is_noisy_concept_label(normalized):
        return False
    source_counts = data.get("source_counts") or {}
    if source_counts.get("weak_page_title") and len(source_counts) == 1:
        return False
    if set(source_counts) == {"document_title"} and sum(source_counts.values()) == 1:
        return False
    if source_counts.get("text_phrase") and len(source_counts) == 1 and len(data.get("doc_ids") or []) == 1 and score < 3.0:
        return False
    return score >= 3.0


def _is_short_ascii_acronym(label: str) -> bool:
    return bool(re.fullmatch(r"[a-z]{2,3}", normalize_concept_label(label)))


def _contains_standalone_term(text: str, term: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", text or "", flags=re.IGNORECASE) is not None


def _looks_like_page_header_only(text: str, term: str) -> bool:
    value = text or ""
    if not re.match(rf"^\s*{re.escape(term)}\s*(\r?\n|$)", value, flags=re.IGNORECASE):
        return False
    marker = "Extracted text:"
    if marker not in value:
        return False
    extracted = value.split(marker, 1)[1]
    return not _contains_standalone_term(extracted, term)


def _contains_concept_alias(text: str, alias: str) -> bool:
    if re.search(r"[\u4e00-\u9fff]", alias):
        return alias in text
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])", text, flags=re.IGNORECASE) is not None


def graph_summary(graph: dict[str, Any]) -> dict[str, Any]:
    nodes = graph.get("nodes", []) or []
    edges = graph.get("edges", []) or []
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_type_distribution": dict(Counter(node.get("type") or "" for node in nodes).most_common()),
        "edge_type_distribution": dict(Counter(edge.get("relation_type") or "" for edge in edges).most_common()),
    }


def graph_node_types(graph: dict[str, Any]) -> list[str]:
    return sorted({node.get("type") for node in graph.get("nodes", []) if node.get("type")})


def prepare_curated_knowledge_graph(
    concept_index: dict[str, Any],
    max_nodes: int = 150,
    keyword: str | None = None,
    show_isolated: bool = True,
) -> dict[str, Any]:
    keyword = _clean_optional_text(keyword)
    node_limit = max(1, int(max_nodes))
    edge_limit = _graph_edge_limit(node_limit)
    concepts = concept_index.get("concepts", {})
    pair_counts = _concept_pair_counts(concepts, "chunk_ids")
    node_scores: Counter = Counter({label: data.get("weight", 0) for label, data in concepts.items()})
    for (left_label, right_label), weight in pair_counts.items():
        node_scores[left_label] += weight
        node_scores[right_label] += weight

    candidates = [
        label
        for label, _score in node_scores.most_common()
        if label in concepts and _concept_matches(concepts[label], keyword)
    ]
    selected_labels = set(candidates[:node_limit])
    edges = [
        {
            "source_id": _concept_id(left_label),
            "source_type": "concept",
            "target_id": _concept_id(right_label),
            "target_type": "concept",
            "relation_type": "co_mentions",
            "weight": weight,
            "evidence": f"{weight} shared chunks",
            "locator": None,
        }
        for (left_label, right_label), weight in pair_counts.most_common()
        if left_label in selected_labels and right_label in selected_labels
    ][:edge_limit]
    if not show_isolated:
        connected_ids = {edge["source_id"] for edge in edges} | {edge["target_id"] for edge in edges}
        selected_labels = {label for label in selected_labels if _concept_id(label) in connected_ids}
    nodes = [_concept_node(concepts[label], node_scores[label]) for label in candidates if label in selected_labels]
    return _graph_view_payload(nodes, edges)


def prepare_knowledge_graph(
    graph: dict[str, Any],
    max_nodes: int = 150,
    keyword: str | None = None,
    show_isolated: bool = True,
) -> dict[str, Any]:
    return _prepare_entity_cooccurrence_graph(graph, max_nodes=max_nodes, keyword=keyword, show_isolated=show_isolated)


def prepare_document_concept_graph(
    concept_index: dict[str, Any],
    max_nodes: int = 150,
    keyword: str | None = None,
    show_isolated: bool = True,
) -> dict[str, Any]:
    keyword = _clean_optional_text(keyword)
    node_limit = max(1, int(max_nodes))
    edge_limit = _graph_edge_limit(node_limit)
    concepts = concept_index.get("concepts", {})
    doc_labels = concept_index.get("doc_labels", {})
    all_edges = []
    for label, concept in concepts.items():
        if not _concept_matches(concept, keyword) and keyword and not any(keyword.casefold() in doc_labels.get(doc_id, "").casefold() for doc_id in concept["doc_ids"]):
            continue
        for doc_id in sorted(concept["doc_ids"]):
            all_edges.append(
                {
                    "source_id": doc_id,
                    "source_type": "document",
                    "target_id": _concept_id(label),
                    "target_type": "concept",
                    "relation_type": "document_mentions_concept",
                    "weight": concept.get("doc_counts", {}).get(doc_id, 1),
                    "evidence": label,
                    "locator": None,
                }
            )
    selected_ids: set[str] = set()
    selected_edges = []
    for edge in all_edges:
        edge_ids = {edge["source_id"], edge["target_id"]}
        if len(selected_ids | edge_ids) > node_limit:
            continue
        selected_ids |= edge_ids
        selected_edges.append(edge)
        if len(selected_edges) >= edge_limit:
            break
        if len(selected_ids) >= node_limit:
            break
    if not show_isolated:
        connected_ids = {edge["source_id"] for edge in selected_edges} | {edge["target_id"] for edge in selected_edges}
        selected_ids &= connected_ids
    nodes = []
    for doc_id, label in doc_labels.items():
        if doc_id in selected_ids:
            nodes.append({"id": doc_id, "type": "document", "label": label})
    for label, concept in concepts.items():
        node = _concept_node(concept, concept.get("weight", 0))
        if node["id"] in selected_ids:
            nodes.append(node)
    return _graph_view_payload(nodes, selected_edges)


def prepare_document_entity_graph(
    graph: dict[str, Any],
    max_nodes: int = 150,
    keyword: str | None = None,
    show_isolated: bool = True,
) -> dict[str, Any]:
    return _prepare_document_entity_graph(graph, max_nodes=max_nodes, keyword=keyword, show_isolated=show_isolated)


def prepare_raw_provenance_graph(
    graph: dict[str, Any],
    max_nodes: int = 150,
    node_type: str | None = None,
    keyword: str | None = None,
    show_isolated: bool = True,
) -> dict[str, Any]:
    node_type = _clean_optional_text(node_type)
    keyword = _clean_optional_text(keyword)
    node_limit = max(1, int(max_nodes))
    all_nodes = {node.get("id"): node for node in graph.get("nodes", []) if node.get("id")}
    seed_nodes = [
        node
        for node in graph.get("nodes", [])
        if _graph_node_matches(node, node_type=node_type, keyword=keyword)
    ]
    selected_ids: set[str] = set()
    for node in seed_nodes:
        if len(selected_ids) >= node_limit:
            break
        node_id = node.get("id")
        if node_id:
            selected_ids.add(node_id)
        for edge in graph.get("edges", []):
            if len(selected_ids) >= node_limit:
                break
            if edge.get("source_id") == node_id and edge.get("target_id") in all_nodes:
                selected_ids.add(edge["target_id"])
            elif edge.get("target_id") == node_id and edge.get("source_id") in all_nodes:
                selected_ids.add(edge["source_id"])
    nodes = [node for node in graph.get("nodes", []) if node.get("id") in selected_ids]
    node_ids = {node.get("id") for node in nodes}
    edges = [
        edge
        for edge in graph.get("edges", [])
        if edge.get("source_id") in node_ids and edge.get("target_id") in node_ids
    ]
    if not show_isolated:
        connected_ids = {edge.get("source_id") for edge in edges} | {edge.get("target_id") for edge in edges}
        nodes = [node for node in nodes if node.get("id") in connected_ids]
        node_ids = {node.get("id") for node in nodes}
        edges = [
            edge
            for edge in edges
            if edge.get("source_id") in node_ids and edge.get("target_id") in node_ids
        ]
    return _graph_view_payload(nodes, edges)


def prepare_graph_view(
    graph: dict[str, Any],
    max_nodes: int = 150,
    node_type: str | None = None,
    keyword: str | None = None,
    show_isolated: bool = True,
) -> dict[str, Any]:
    return prepare_raw_provenance_graph(
        graph,
        max_nodes=max_nodes,
        node_type=node_type,
        keyword=keyword,
        show_isolated=show_isolated,
    )


def graph_view_html(
    graph_view: dict[str, Any],
    show_edge_labels: bool = False,
    stabilize: bool = True,
    random_seed: int = 42,
) -> str:
    from pyvis.network import Network

    network = Network(height="640px", width="100%", bgcolor="#ffffff", font_color="#222222", directed=False)
    network.set_options(graph_layout_options(stabilize=stabilize, random_seed=random_seed))
    for node in graph_view.get("nodes", []):
        node_id = node.get("id")
        if not node_id:
            continue
        network.add_node(
            node_id,
            label=_short_label(node.get("label") or node_id, 28),
            title=_graph_node_title(node),
            group=node.get("type") or "unknown",
            value=_node_size_value(node),
        )
    for edge in graph_view.get("edges", []):
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")
        if source_id and target_id:
            network.add_edge(
                source_id,
                target_id,
                title=_graph_edge_title(edge),
                label=_short_label(edge.get("relation_type") or "", 24) if show_edge_labels else "",
                value=edge.get("weight"),
                width=_edge_width(edge),
            )
    return network.generate_html(notebook=False)


def graph_layout_options(stabilize: bool = True, random_seed: int = 42) -> str:
    return json.dumps(
        {
            "layout": {"randomSeed": random_seed, "improvedLayout": True},
            "nodes": {
                "shape": "dot",
                "scaling": {"min": 12, "max": 28},
                "font": {"size": 15, "face": "Inter, Arial", "strokeWidth": 3, "strokeColor": "#ffffff"},
            },
            "edges": {
                "color": {"color": "#9aa4b2", "highlight": "#4f6f8f"},
                "smooth": {"enabled": True, "type": "dynamic", "roundness": 0.25},
                "font": {"size": 10, "align": "middle", "strokeWidth": 3, "strokeColor": "#ffffff"},
            },
            "physics": {
                "enabled": True,
                "solver": "forceAtlas2Based",
                "forceAtlas2Based": {
                    "gravitationalConstant": -90,
                    "centralGravity": 0.006,
                    "springLength": 180,
                    "springConstant": 0.04,
                    "damping": 0.65,
                    "avoidOverlap": 0.8,
                },
                "stabilization": {"enabled": stabilize, "iterations": 250, "updateInterval": 25, "fit": True},
                "minVelocity": 0.75,
                "timestep": 0.35,
            },
            "interaction": {"hover": True, "tooltipDelay": 120, "hideEdgesOnDrag": True},
        }
    )


def _node_size_value(node: dict[str, Any]) -> int:
    weight = int(node.get("weight") or node.get("chunks_count") or 1)
    return max(1, min(40, weight))


def _edge_width(edge: dict[str, Any]) -> float:
    weight = float(edge.get("weight") or 1)
    return max(1.0, min(5.0, 1.0 + weight ** 0.35))


def _concept_pair_counts(concepts: dict[str, dict[str, Any]], key: str) -> Counter:
    chunk_concepts: dict[str, set[str]] = defaultdict(set)
    for label, concept in concepts.items():
        for item_id in concept.get(key, set()):
            chunk_concepts[item_id].add(label)
    return _cooccurrence_pairs(chunk_concepts.values())


def _concept_matches(concept: dict[str, Any], keyword: str | None) -> bool:
    if not keyword:
        return True
    folded = keyword.casefold()
    values = [concept.get("label", ""), *(concept.get("aliases") or []), *(concept.get("contexts") or [])]
    return any(folded in str(value).casefold() for value in values)


def _concept_id(label: str) -> str:
    normalized = normalize_concept_label(label)
    slug = slugify(normalized) or re.sub(r"[^\w]+", "-", normalized, flags=re.UNICODE).strip("-") or "unknown"
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:8]
    return f"concept:{slug[:48]}-{digest}"


def _concept_node(concept: dict[str, Any], weight: int) -> dict[str, Any]:
    return {
        "id": _concept_id(concept["label"]),
        "type": "concept",
        "label": concept["label"],
        "aliases": sorted(set(concept.get("aliases") or [])),
        "weight": weight,
        "chunks_count": len(concept.get("chunk_ids") or []),
        "documents_count": len(concept.get("doc_ids") or []),
        "match_count": concept.get("match_count"),
        "quality_score": concept.get("quality_score"),
        "source_types": concept.get("source_types"),
        "source_counts": concept.get("source_counts"),
        "sample_document_title": concept.get("sample_document_title"),
        "sample_preview": next(iter(concept.get("contexts") or []), None),
    }


def _prepare_entity_cooccurrence_graph(
    graph: dict[str, Any],
    max_nodes: int = 150,
    keyword: str | None = None,
    show_isolated: bool = True,
) -> dict[str, Any]:
    keyword = _clean_optional_text(keyword)
    node_limit = max(1, int(max_nodes))
    edge_limit = _graph_edge_limit(node_limit)
    entity_nodes = _nodes_by_type(graph, "entity")
    pair_counts, basis = _entity_pair_counts(graph)
    node_scores: Counter = Counter()
    for (left_id, right_id), weight in pair_counts.items():
        node_scores[left_id] += weight
        node_scores[right_id] += weight
    candidate_ids = [
        node_id
        for node_id, _score in node_scores.most_common()
        if node_id in entity_nodes and _graph_node_matches(entity_nodes[node_id], node_type="entity", keyword=keyword)
    ]
    if show_isolated:
        candidate_ids.extend(
            node_id
            for node_id, node in entity_nodes.items()
            if node_id not in candidate_ids and _graph_node_matches(node, node_type="entity", keyword=keyword)
        )
    selected_ids = set(candidate_ids[:node_limit])
    edges = [
        {
            "source_id": left_id,
            "source_type": "entity",
            "target_id": right_id,
            "target_type": "entity",
            "relation_type": "co_mentions" if basis == "chunk" else "co_occurs",
            "weight": weight,
            "evidence": f"{weight} shared {basis}{'' if weight == 1 else 's'}",
            "locator": None,
        }
        for (left_id, right_id), weight in pair_counts.most_common()
        if left_id in selected_ids and right_id in selected_ids
    ][:edge_limit]
    if not show_isolated:
        connected_ids = {edge["source_id"] for edge in edges} | {edge["target_id"] for edge in edges}
        selected_ids &= connected_ids
    nodes = [_graph_node_with_weight(entity_nodes[node_id], node_scores[node_id]) for node_id in candidate_ids if node_id in selected_ids]
    return _graph_view_payload(nodes, edges)


def _prepare_document_entity_graph(
    graph: dict[str, Any],
    max_nodes: int = 150,
    keyword: str | None = None,
    show_isolated: bool = True,
) -> dict[str, Any]:
    keyword = _clean_optional_text(keyword)
    node_limit = max(1, int(max_nodes))
    edge_limit = _graph_edge_limit(node_limit)
    document_nodes = _nodes_by_type(graph, "document")
    entity_nodes = _nodes_by_type(graph, "entity")
    available_nodes = {**document_nodes, **entity_nodes}
    all_edges = [
        {
            "source_id": edge.get("source_id"),
            "source_type": "document",
            "target_id": edge.get("target_id"),
            "target_type": "entity",
            "relation_type": "document_mentions_entity",
            "evidence": edge.get("evidence"),
            "locator": edge.get("locator"),
        }
        for edge in graph.get("edges", [])
        if edge.get("relation_type") == "document_mentions_entity"
        and edge.get("source_id") in document_nodes
        and edge.get("target_id") in entity_nodes
    ]
    if keyword:
        all_edges = [
            edge
            for edge in all_edges
            if _graph_node_matches(available_nodes[edge["source_id"]], node_type=None, keyword=keyword)
            or _graph_node_matches(available_nodes[edge["target_id"]], node_type=None, keyword=keyword)
        ]
    selected_ids: set[str] = set()
    selected_edges = []
    for edge in all_edges:
        edge_ids = {edge["source_id"], edge["target_id"]}
        if len(selected_ids | edge_ids) > node_limit:
            continue
        selected_ids |= edge_ids
        selected_edges.append(edge)
        if len(selected_edges) >= edge_limit or len(selected_ids) >= node_limit:
            break
    if show_isolated and keyword and len(selected_ids) < node_limit:
        for node_id, node in available_nodes.items():
            if node_id not in selected_ids and _graph_node_matches(node, node_type=None, keyword=keyword):
                selected_ids.add(node_id)
            if len(selected_ids) >= node_limit:
                break
    nodes = [available_nodes[node_id] for node_id in available_nodes if node_id in selected_ids]
    return _graph_view_payload(nodes, selected_edges)


def _entity_pair_counts(graph: dict[str, Any]) -> tuple[Counter, str]:
    chunk_entities: dict[str, set[str]] = defaultdict(set)
    for edge in graph.get("edges", []):
        if edge.get("relation_type") == "chunk_mentions_entity":
            chunk_id, entity_id = _edge_endpoint_by_type(edge, "chunk"), _edge_endpoint_by_type(edge, "entity")
            if chunk_id and entity_id:
                chunk_entities[chunk_id].add(entity_id)
    pair_counts = _cooccurrence_pairs(chunk_entities.values())
    if pair_counts:
        return pair_counts, "chunk"

    document_entities: dict[str, set[str]] = defaultdict(set)
    for edge in graph.get("edges", []):
        if edge.get("relation_type") == "document_mentions_entity":
            document_id, entity_id = _edge_endpoint_by_type(edge, "document"), _edge_endpoint_by_type(edge, "entity")
            if document_id and entity_id:
                document_entities[document_id].add(entity_id)
    return _cooccurrence_pairs(document_entities.values()), "document"


def _cooccurrence_pairs(groups: Any) -> Counter:
    counts: Counter = Counter()
    for group in groups:
        for left_id, right_id in itertools.combinations(sorted(group), 2):
            counts[(left_id, right_id)] += 1
    return counts


def _edge_endpoint_by_type(edge: dict[str, Any], endpoint_type: str) -> str | None:
    if edge.get("source_type") == endpoint_type:
        return edge.get("source_id")
    if edge.get("target_type") == endpoint_type:
        return edge.get("target_id")
    return None


def _nodes_by_type(graph: dict[str, Any], node_type: str) -> dict[str, dict[str, Any]]:
    return {
        node["id"]: node
        for node in graph.get("nodes", [])
        if node.get("id") and node.get("type") == node_type
    }


def _graph_node_with_weight(node: dict[str, Any], weight: int) -> dict[str, Any]:
    return {**node, "weight": weight}


def _graph_view_payload(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "nodes": nodes,
        "edges": edges,
        "node_rows": [_graph_node_row(node) for node in nodes],
        "edge_rows": [_graph_edge_row(edge) for edge in edges],
    }


def _graph_edge_limit(node_limit: int) -> int:
    return max(node_limit, min(1000, node_limit * 6))


def _graph_node_matches(node: dict[str, Any], node_type: str | None, keyword: str | None) -> bool:
    if node_type and node.get("type") != node_type:
        return False
    if not keyword:
        return True
    haystack = " ".join(str(value) for value in node.values() if value is not None).casefold()
    return keyword.casefold() in haystack


def _graph_node_row(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": node.get("id"),
        "type": node.get("type"),
        "label": node.get("label"),
        "document_kind": node.get("document_kind"),
        "weight": node.get("weight"),
    }


def _graph_edge_row(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": edge.get("source_id"),
        "source_type": edge.get("source_type"),
        "target_id": edge.get("target_id"),
        "target_type": edge.get("target_type"),
        "relation_type": edge.get("relation_type"),
        "weight": edge.get("weight"),
        "evidence": edge.get("evidence"),
        "locator": edge.get("locator"),
    }


def _graph_node_title(node: dict[str, Any]) -> str:
    return "<br>".join(f"{key}: {value}" for key, value in node.items() if value not in (None, "", []))


def _graph_edge_title(edge: dict[str, Any]) -> str:
    return "<br>".join(f"{key}: {value}" for key, value in edge.items() if value not in (None, "", []))


def _short_label(value: str, limit: int) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else f"{text[: limit - 1]}..."


def _clean_optional_text(value: str | None) -> str | None:
    text = (value or "").strip()
    return text or None
