import itertools
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
from office2md.library import library_report
from office2md.library import search_library, search_library_diagnostics, search_library_facets
from office2md.scanner import scan_input


DOMAIN_CONCEPTS: list[tuple[str, list[str]]] = [
    ("maintenance", ["maintenance", "maintain", "servicing", "维护", "保养"]),
    ("operation manual", ["operation manual", "operating manual", "manual", "操作手册"]),
    ("vacuum pump", ["vacuum pump", "真空泵"]),
    ("cooling water", ["cooling water", "cooling", "冷却水"]),
    ("alarm", ["alarm", "报警"]),
    ("alarm history", ["alarm history", "报警历史"]),
    ("fault", ["fault", "failure", "trouble", "故障"]),
    ("motor protection switch", ["motor protection switch", "motor protection"]),
    ("agitator", ["agitator", "agitation", "stirrer", "搅拌"]),
    ("temperature probe", ["temperature probe", "temperature sensor", "温度探头"]),
    ("sealing liquid", ["sealing liquid", "seal liquid", "密封液"]),
    ("CIP", ["CIP", "clean in place"]),
    ("PLC", ["PLC", "S7-300"]),
    ("valve", ["valve"]),
    ("terminal", ["terminal"]),
    ("homogenizer", ["homogenizer"]),
    ("cleaning", ["cleaning", "clean", "清洁"]),
    ("calibration", ["calibration", "calibrate", "校准"]),
    ("sensor", ["sensor"]),
    ("VFD", ["VFD", "frequency converter", "variable frequency"]),
    ("compressor", ["compressor"]),
    ("heating", ["heating", "heat"]),
    ("jacket", ["jacket"]),
    ("lid lift", ["lid lift", "cover lift"]),
    ("recipe", ["recipe"]),
    ("password", ["password"]),
    ("user group", ["user group", "user role"]),
]

DEFAULT_RUNNER_PYTHON = r".\.venv\Scripts\python.exe"


def normalize_library_path(value: str) -> Path | None:
    text = (value or "").strip().strip('"')
    return Path(text).expanduser() if text else None


def is_valid_library_path(path: Path | None) -> bool:
    if path is None:
        return False
    if path.is_dir():
        return (path / "library.db").exists()
    return path.name == "library.db" and path.exists()


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
    concept_aliases = {label: aliases for label, aliases in DOMAIN_CONCEPTS}
    concept_chunks: dict[str, set[str]] = defaultdict(set)
    concept_docs: dict[str, set[str]] = defaultdict(set)
    concept_doc_counts: dict[str, Counter] = defaultdict(Counter)
    concept_context: dict[str, set[str]] = defaultdict(set)
    doc_labels: dict[str, str] = {}
    hidden_noisy = 0

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT c.chunk_id, c.doc_id, c.title AS chunk_title, c.text,
                   d.title AS document_title, d.source_file, d.document_kind
            FROM chunks c
            JOIN documents d ON d.doc_id = c.doc_id
            """
        ).fetchall()

    for row in rows:
        doc_id = row["doc_id"]
        doc_labels[doc_id] = row["document_title"] or row["source_file"] or doc_id
        searchable = " ".join(
            str(value or "")
            for value in [row["document_title"], row["source_file"], row["document_kind"], row["chunk_title"], row["text"]]
        )
        matched_labels = _matched_concept_labels(searchable, concept_aliases)
        for label in matched_labels:
            if is_noisy_concept_label(label):
                hidden_noisy += 1
                continue
            concept_chunks[label].add(row["chunk_id"])
            concept_docs[label].add(doc_id)
            concept_doc_counts[label][doc_id] += 1
            context = " ".join(str(value or "") for value in [row["document_title"], row["chunk_title"], row["text"]])
            concept_context[label].add(_short_label(context, 240))

    concepts = {
        label: {
            "label": label,
            "aliases": concept_aliases[label],
            "chunk_ids": concept_chunks[label],
            "doc_ids": concept_docs[label],
            "doc_counts": dict(concept_doc_counts[label]),
            "contexts": concept_context[label],
            "weight": len(concept_chunks[label]),
        }
        for label in concept_aliases
        if concept_chunks.get(label)
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
    if re.fullmatch(r"\d{4}|\d+(\.\d+)?", text):
        return True
    if re.fullmatch(r"[a-z]{2}-[a-z]{2}", text):
        return True
    if text in {"min", "°c", "℃", "%", "bar", "rpm", "user texts", "system", "untitled source page"}:
        return True
    if text.startswith("assets/") or re.search(r"\.(png|jpg|jpeg|gif|bmp|tiff)$", text):
        return True
    if re.fullmatch(r"eng-\d+", text):
        return True
    return False


def _matched_concept_labels(text: str, concept_aliases: dict[str, list[str]]) -> list[str]:
    return [
        label
        for label, aliases in concept_aliases.items()
        if any(_contains_concept_alias(text, alias) for alias in [label, *aliases])
    ]


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
    slug = re.sub(r"[^a-z0-9]+", "-", normalize_concept_label(label)).strip("-")
    return f"concept:{slug or 'unknown'}"


def _concept_node(concept: dict[str, Any], weight: int) -> dict[str, Any]:
    return {
        "id": _concept_id(concept["label"]),
        "type": "concept",
        "label": concept["label"],
        "aliases": sorted(set(concept.get("aliases") or [])),
        "weight": weight,
        "chunks_count": len(concept.get("chunk_ids") or []),
        "documents_count": len(concept.get("doc_ids") or []),
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
