import json
from pathlib import Path
import tempfile
from typing import List

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from office2md.ai.doctor import run_ai_checks
from office2md.ai.enricher import run_ai_enrichment
from office2md.converters.docling_converter import DoclingConverter
from office2md.converters.libreoffice_converter import convert_legacy_office
from office2md.converters.marker_converter import MarkerConverter
from office2md.converters.markitdown_converter import MarkItDownConverter
from office2md.detector import detect_file_type, is_legacy_office, sha256_file
from office2md.docling_diagnostics import diagnose_docling, warmup_docling
from office2md.doctor import run_checks
from office2md.exports.obsidian import ObsidianExportError, export_obsidian
from office2md.incremental import library_status, scan_changes
from office2md.library import build_library, library_report, locate_document, open_chunk, search_library, search_library_diagnostics, search_library_facets
from office2md.models import ConvertOptions, ConvertResult
from office2md.officecli_benchmark import run_officecli_benchmark
from office2md.postprocess.chunker import chunk_markdown, chunk_pdf_pages
from office2md.postprocess.drawing_index import build_drawing_index_chunks, extract_drawing_index
from office2md.postprocess.entities import extract_entities
from office2md.postprocess.frontmatter import add_frontmatter
from office2md.postprocess.knowledge_pack import (
    build_document_body,
    build_knowledge_json,
    build_source_map,
    enrich_chunks,
)
from office2md.postprocess.markdown_cleaner import clean_markdown
from office2md.postprocess.manual_structure import (
    MANUAL_KINDS,
    build_section_chunks,
    extract_title_page_metadata,
    extract_toc_entries_from_pages,
)
from office2md.postprocess.office_structure import (
    build_office_chunks,
    embedded_base64_image_count,
    extract_embedded_office_assets,
    extract_office_metadata,
    missing_markdown_asset_count,
)
from office2md.postprocess.pdf_structure import (
    build_pdf_document_json,
    classify_document_kind,
    determine_quality_status,
    enrich_page_semantics,
    extract_pdf_text_pages,
    has_headings,
    is_empty_document_json,
    merge_pdf_pages,
    render_pdf_pages,
)
from office2md.postprocess.quality import collect_warnings
from office2md.postprocess.tags import generate_tags
from office2md.scanner import scan_input
from office2md.storage.index import rebuild_output_index
from office2md.storage.manifest import build_manifest
from office2md.storage.writer import output_dir_for_source, write_document_output
from office2md.utils import ensure_directory, utc_now_iso
from office2md.workspace import init_workspace, register_library_version, register_output_version, scan_workspace_sources, summarize_workspace_status


app = typer.Typer(help="Convert Office/PDF documents to knowledge-base-ready Markdown.")
console = Console()


def choose_engine(path: Path, options: ConvertOptions) -> str:
    ext = path.suffix.lower()
    if options.engine != "auto":
        return options.engine
    if ext == ".pdf":
        return "docling"
    if ext in {".docx", ".pptx", ".xlsx", ".html", ".htm", ".txt", ".csv", ".json", ".md"}:
        return "markitdown"
    if ext in {".doc", ".ppt", ".xls"}:
        return "markitdown"
    return "docling"


def get_converter(engine: str):
    converters = {
        "docling": DoclingConverter(),
        "markitdown": MarkItDownConverter(),
        "marker": MarkerConverter(),
    }
    return converters[engine]


@app.command()
def doctor(output_dir: Path = typer.Option(None, help="Optional output directory to test writability.")) -> None:
    """Check local conversion environment."""
    table = Table(title="office2md doctor")
    table.add_column("Check")
    table.add_column("Status")
    for name, status in run_checks(output_dir).items():
        table.add_row(name, status)
    console.print(table)


@app.command("doctor-docling")
def doctor_docling() -> None:
    """Run Docling-specific import, initialization, and fixture conversion diagnostics."""
    _print_docling_diagnostics(diagnose_docling())


@app.command("warmup-docling")
def warmup_docling_command() -> None:
    """Trigger Docling initialization/model download using a tiny PDF fixture."""
    ok, result = warmup_docling()
    _print_docling_diagnostics(result)
    if ok:
        console.print("[green]Docling warm-up completed successfully.[/green]")
        return
    console.print(
        Panel(
            "Docling warm-up failed. This is usually a network/model download issue.\n"
            "Check proxy settings, retry under a stable network, or pre-populate the Hugging Face cache.\n"
            "office2md auto mode fallback remains available, but PDF quality_status may be low_structure.",
            title="Docling Warm-up Failed",
        )
    )


@app.command("doctor-ai")
def doctor_ai() -> None:
    """Check optional AI backend availability without reading secrets."""
    table = Table(title="office2md doctor-ai")
    table.add_column("Check")
    table.add_column("Status")
    for name, status in run_ai_checks().items():
        table.add_row(name, status)
    console.print(table)


@app.command("workspace-init")
def workspace_init_command(
    workspace_path: Path,
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview directories and manifests without writing files."),
    overwrite_manifests: bool = typer.Option(
        False,
        "--overwrite-manifests",
        help="Replace source/version manifests if they already exist. workspace_manifest.json always refreshes updated_at.",
    ),
) -> None:
    """Create the conservative office2md workspace folder foundation."""
    result = init_workspace(workspace_path, dry_run=dry_run, overwrite_manifests=overwrite_manifests)
    table = Table(title="office2md workspace-init")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("workspace_path", result["workspace_path"])
    table.add_row("dry_run", str(result["dry_run"]))
    table.add_row("planned_directories", str(len(result["directories"])))
    table.add_row("planned_manifests", str(len(result["manifest_files"])))
    table.add_row("created_directories", str(len(result["created_directories"])))
    table.add_row("written_manifests", str(len(result["written_manifests"])))
    table.add_row("preserved_manifests", str(len(result["preserved_manifests"])))
    console.print(table)
    if dry_run:
        console.print("planned_directories:")
        for item in result["directories"]:
            console.print(item)
        console.print("planned_manifest_files:")
        for item in result["manifest_files"]:
            console.print(item)


@app.command("workspace-scan")
def workspace_scan_command(
    workspace_path: Path,
    source_path: Path,
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview source manifest changes without writing files."),
    include_hidden: bool = typer.Option(False, "--include-hidden", help="Include supported files under dot-prefixed paths."),
    hash_files: bool = typer.Option(True, "--hash/--no-hash", help="Compute SHA-256 checksums for scanned files."),
    max_files: int = typer.Option(None, "--max-files", help="Limit the number of selected source files scanned."),
    relative_paths: bool = typer.Option(True, "--relative-paths/--absolute-paths", help="Store relative paths when safe."),
) -> None:
    """Register source files and checksums in a workspace source manifest."""
    try:
        result = scan_workspace_sources(
            workspace_path,
            source_path,
            dry_run=dry_run,
            include_hidden=include_hidden,
            hash_files=hash_files,
            max_files=max_files,
            relative_paths=relative_paths,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    counts = result["counts"]
    table = Table(title="office2md workspace-scan")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("workspace_path", result["workspace_path"])
    table.add_row("source_path", result["source_path"])
    table.add_row("dry_run", str(result["dry_run"]))
    table.add_row("discovered_files", str(result["discovered_files"]))
    table.add_row("scanned_files", str(result["scanned_files"]))
    table.add_row("scan_limited", str(result["scan_limited"]))
    table.add_row("total_sources", str(counts["total_sources"]))
    table.add_row("active_sources", str(counts["active_sources"]))
    table.add_row("new_sources", str(counts["new_sources"]))
    table.add_row("changed_sources", str(counts["changed_sources"]))
    table.add_row("missing_sources", str(counts["missing_sources"]))
    console.print(table)
    if result["scan_limited"]:
        console.print(f"[yellow]limited scan:[/yellow] max_files={result['max_files']}")
    if dry_run:
        console.print("Dry run: source_manifest.json was not written.")


@app.command("workspace-register-library")
def workspace_register_library_command(
    workspace_path: Path,
    library_path: Path,
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview the library version record without writing files."),
    label: str = typer.Option(None, "--label", help="Optional human-readable version label."),
    notes: str = typer.Option(None, "--notes", help="Optional registration notes."),
    allow_dirty_source: bool = typer.Option(
        False,
        "--allow-dirty-source",
        help="Allow registration when source_manifest.json reports changed or missing sources.",
    ),
    library_version_id: str = typer.Option(None, "--library-version-id", help="Optional explicit library version id."),
) -> None:
    """Register a built Knowledge Library as a workspace library version."""
    try:
        result = register_library_version(
            workspace_path,
            library_path,
            dry_run=dry_run,
            label=label,
            notes=notes,
            allow_dirty_source=allow_dirty_source,
            library_version_id=library_version_id,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    record = result["record"]
    metrics = record["library_metrics"]
    counts = record["source_counts"]
    table = Table(title="office2md workspace-register-library")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("workspace_path", result["workspace_path"])
    table.add_row("library_path", result["library_path"])
    table.add_row("dry_run", str(result["dry_run"]))
    table.add_row("library_version_id", record["library_version_id"])
    table.add_row("versions_count", str(result["versions_count"]))
    table.add_row("documents_count", str(metrics["documents_count"]))
    table.add_row("chunks_count", str(metrics["chunks_count"]))
    table.add_row("entities_count", str(metrics["entities_count"]))
    table.add_row("source_total", str(counts["total_sources"]))
    table.add_row("source_changed", str(counts["changed_sources"]))
    table.add_row("source_missing", str(counts["missing_sources"]))
    console.print(table)
    for warning in result["warnings"]:
        console.print(f"[yellow]warning:[/yellow] {warning}")
    if dry_run:
        console.print("Dry run: versions/library_versions.json was not written.")


@app.command("workspace-register-output")
def workspace_register_output_command(
    workspace_path: Path,
    output_path: Path,
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview the output version record without writing files."),
    label: str = typer.Option(None, "--label", help="Optional human-readable output label."),
    notes: str = typer.Option(None, "--notes", help="Optional registration notes."),
    output_type: str = typer.Option("auto", "--output-type", help="Output type. Use auto to detect common outputs."),
    library_version_id: str = typer.Option(None, "--library-version-id", help="Library version id to link this output to."),
    output_version_id: str = typer.Option(None, "--output-version-id", help="Optional explicit output version id."),
    allow_missing_library_version: bool = typer.Option(
        False,
        "--allow-missing-library-version",
        help="Allow registration when no library version is available.",
    ),
) -> None:
    """Register a generated output as a workspace output version."""
    try:
        result = register_output_version(
            workspace_path,
            output_path,
            dry_run=dry_run,
            label=label,
            notes=notes,
            output_type=output_type,
            library_version_id=library_version_id,
            output_version_id=output_version_id,
            allow_missing_library_version=allow_missing_library_version,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    record = result["record"]
    files = record["output_files"]
    table = Table(title="office2md workspace-register-output")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("workspace_path", result["workspace_path"])
    table.add_row("output_path", result["output_path"])
    table.add_row("dry_run", str(result["dry_run"]))
    table.add_row("output_version_id", record["output_version_id"])
    table.add_row("versions_count", str(result["versions_count"]))
    table.add_row("output_type", record["output_type"])
    table.add_row("library_version_id", str(record["library_version_id"] or ""))
    table.add_row("file_count", str(files["file_count"]))
    table.add_row("total_size_bytes", str(files["total_size_bytes"]))
    console.print(table)
    for warning in result["warnings"]:
        console.print(f"[yellow]warning:[/yellow] {warning}")
    if dry_run:
        console.print("Dry run: versions/output_versions.json was not written.")


@app.command("workspace-status")
def workspace_status_command(
    workspace_path: Path,
    json_output: bool = typer.Option(False, "--json", help="Print stable JSON only."),
    show_history: bool = typer.Option(False, "--show-history", help="Show recent library and output version history."),
    limit: int = typer.Option(5, "--limit", help="Maximum history records to show."),
    strict: bool = typer.Option(False, "--strict", help="Fail if expected manifests are missing or linkage is broken."),
) -> None:
    """Show a read-only workspace traceability summary."""
    try:
        status = summarize_workspace_status(workspace_path, show_history=show_history, limit=limit)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    if json_output:
        print(json.dumps(status, ensure_ascii=False, indent=2))
    else:
        _print_workspace_status(status, show_history=show_history)
    if strict and status["errors"]:
        raise typer.Exit(1)


@app.command("officecli-benchmark")
def officecli_benchmark_command(
    input_path: Path,
    output_dir: Path,
    officecli_path: Path = typer.Option(None, "--officecli-path", help="OfficeCLI executable path. Defaults to officecli on PATH."),
    max_files: int = typer.Option(None, "--max-files", help="Maximum Office files to benchmark."),
    include_hidden: bool = typer.Option(False, "--include-hidden", help="Include Office files under dot-prefixed paths."),
    formats: str = typer.Option("docx,xlsx,pptx", "--formats", help="Comma-separated Office extensions to include."),
    timeout_seconds: int = typer.Option(60, "--timeout-seconds", help="Per-command timeout in seconds."),
    skip_html: bool = typer.Option(False, "--skip-html", help="Skip OfficeCLI HTML preview command."),
    skip_structure_json: bool = typer.Option(False, "--skip-structure-json", help="Skip OfficeCLI structure JSON command."),
    skip_issues: bool = typer.Option(False, "--skip-issues", help="Skip OfficeCLI issues command."),
    skip_validate: bool = typer.Option(False, "--skip-validate", help="Skip OfficeCLI validate command."),
    large_file_size_mb: int = typer.Option(25, "--large-file-size-mb", help="Warn when selected files are at least this many MB. Use 0 to disable."),
    json_output: bool = typer.Option(False, "--json", help="Print benchmark summary JSON."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview selected files and commands without writing artifacts."),
) -> None:
    """Run a read-only OfficeCLI benchmark without changing conversion behavior."""
    parsed_formats = tuple(item.strip().lower().lstrip(".") for item in formats.split(",") if item.strip())
    if not parsed_formats:
        raise typer.BadParameter("--formats must include at least one extension")
    try:
        summary = run_officecli_benchmark(
            input_path,
            output_dir,
            officecli_path=officecli_path,
            max_files=max_files,
            include_hidden=include_hidden,
            formats=parsed_formats,
            timeout_seconds=timeout_seconds,
            skip_html=skip_html,
            skip_structure_json=skip_structure_json,
            skip_validate=skip_validate,
            skip_issues=skip_issues,
            large_file_size_mb=large_file_size_mb,
            dry_run=dry_run,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    if json_output:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    counts = summary["counts"]
    table = Table(title="office2md officecli-benchmark")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("input_path", summary["input_path"])
    table.add_row("output_dir", summary["output_dir"])
    table.add_row("officecli_path", summary["officecli_path"])
    table.add_row("officecli_version", str(summary.get("officecli_version") or ""))
    table.add_row("dry_run", str(summary["dry_run"]))
    table.add_row("files_selected", str(counts["files_selected"]))
    table.add_row("files_succeeded", str(counts["files_succeeded"]))
    table.add_row("files_failed", str(counts["files_failed"]))
    table.add_row("checksum_changed", str(counts["checksum_changed"]))
    table.add_row("json_parse_success", str(counts["json_parse_success"]))
    table.add_row("html_generated", str(counts["html_generated"]))
    table.add_row("recommendation", str(summary.get("recommendation") or ""))
    table.add_row("timeouts", str(sum(item.get("timeouts", 0) for item in summary.get("timeout_summary", []))))
    console.print(table)
    if dry_run:
        console.print("Dry run: OfficeCLI was not executed and no artifacts were written.")
        console.print("planned_commands:")
        for command in summary["planned_commands"]:
            console.print(" ".join(command))
    else:
        console.print(f"Summary: {Path(summary['output_dir']) / 'officecli_benchmark_summary.json'}")
        console.print(f"Report: {Path(summary['output_dir']) / 'officecli_benchmark_report.md'}")


@app.command("build-library")
def build_library_command(input_output_root: Path, library_output_dir: Path) -> None:
    """Build a local searchable Knowledge Library from an office2md output root."""
    result = build_library(input_output_root, library_output_dir)
    table = Table(title="office2md build-library")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("library_db", result["library_db"])
    table.add_row("documents_count", str(result["documents_count"]))
    table.add_row("chunks_count", str(result["chunks_count"]))
    table.add_row("entities_count", str(result["entities_count"]))
    table.add_row("warnings", str(len(result["warnings"])))
    console.print(table)
    for warning in result["warnings"][:20]:
        console.print(f"[yellow]warning:[/yellow] {warning}")


@app.command("library-status")
def library_status_command(
    library_path: Path,
    change_plan: Path = typer.Option(None, "--change-plan", help="Optional change_plan.json to summarize pending changes."),
    registry: Path = typer.Option(None, "--registry", help="Optional source_registry.json path."),
    json_output: bool = typer.Option(False, "--json", help="Print stable JSON only."),
) -> None:
    """Show read-only incremental library freshness status."""
    try:
        status = library_status(library_path, change_plan_path=change_plan, registry_path=registry)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    if json_output:
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return
    table = Table(title="office2md library-status")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("library_path", status["library_path"])
    table.add_row("library_db_exists", str(status["library_db_exists"]))
    table.add_row("source_registry_exists", str(status["source_registry_exists"]))
    table.add_row("status", status["status"])
    counts = status["counts"]
    table.add_row("registered_sources", str(counts["registered_sources"]))
    table.add_row("current_sources", str(counts["current_sources"]))
    table.add_row("stale_sources", str(counts["stale_sources"]))
    table.add_row("missing_sources", str(counts["missing_sources"]))
    if status.get("pending_changes"):
        table.add_row("pending_changes", json.dumps(status["pending_changes"], ensure_ascii=False))
    console.print(table)
    for warning in status["warnings"]:
        console.print(f"[yellow]warning:[/yellow] {warning}")


@app.command("scan-changes")
def scan_changes_command(
    source_path: Path,
    library_path: Path,
    export_json: Path = typer.Option(None, "--export-json", help="Write UTF-8 change_plan.json to PATH; creates parent directories."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without writing change_plan.json."),
    include_hidden: bool = typer.Option(False, "--include-hidden", help="Include files under dot-prefixed paths where feasible."),
    registry: Path = typer.Option(None, "--registry", help="Optional source_registry.json path."),
    json_output: bool = typer.Option(False, "--json", help="Print change plan JSON only."),
) -> None:
    """Compare source files against registry/library state without updating the library."""
    try:
        plan = scan_changes(
            source_path,
            library_path,
            registry_path=registry,
            export_json=export_json,
            dry_run=dry_run,
            include_hidden=include_hidden,
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    if json_output:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return
    counts = plan["counts"]
    table = Table(title="office2md scan-changes")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("source_path", plan["source_path"])
    table.add_row("library_path", plan["library_path"])
    table.add_row("new", str(counts["new"]))
    table.add_row("modified", str(counts["modified"]))
    table.add_row("unchanged", str(counts["unchanged"]))
    table.add_row("deleted_missing", str(counts["deleted_missing"]))
    table.add_row("moved_or_renamed_candidate", str(counts["moved_or_renamed_candidate"]))
    table.add_row("unsupported", str(counts["unsupported"]))
    table.add_row("stale", str(counts["stale"]))
    console.print(table)
    if export_json and not dry_run:
        console.print(f"change_plan_json: {export_json.expanduser().resolve()}")
    else:
        console.print("Dry run: change_plan.json was not written.")
    for warning in plan["warnings"]:
        console.print(f"[yellow]warning:[/yellow] {warning}")


@app.command("search-library")
def search_library_command(
    library_db: Path,
    query: str,
    limit: int = typer.Option(10, help="Maximum results to print."),
    offset: int = typer.Option(0, help="Number of matching results to skip."),
    kind: List[str] = typer.Option(None, "--kind", help="Filter by document_kind. Can be repeated."),
    evidence: List[str] = typer.Option(None, "--evidence", help="Filter by evidence_type. Can be repeated."),
    document: str = typer.Option(None, "--doc", "--document", help="Filter by document title or source_file."),
    output_dir: str = typer.Option(None, "--output-dir", help="Filter by output directory name."),
    entity: List[str] = typer.Option(None, "--entity", help="Filter by entity text. Can be repeated."),
    exclude_doc: List[str] = typer.Option(None, "--exclude-doc", help="Exclude document title/source_file match. Can be repeated."),
    has_locator: bool = typer.Option(False, "--has-locator", help="Only show chunks with source locators."),
    facets: bool = typer.Option(False, "--facets", help="Print facet counts for the current query and filters."),
    context: int = typer.Option(0, "--context", "--related", help="Show N nearby chunks from the same document. Requires an integer."),
    diagnostics: bool = typer.Option(False, "--diagnostics", help="Print query handling diagnostics without changing results."),
    diagnostics_json: bool = typer.Option(False, "--diagnostics-json", help="Append machine-readable diagnostics JSON after normal output."),
    export_json: Path = typer.Option(None, "--export-json", help="Write UTF-8 search results JSON to PATH; creates parent directories."),
) -> None:
    """Search a local Knowledge Library with SQLite FTS and optional token fallback."""
    results = search_library(
        library_db,
        query,
        limit=limit,
        offset=offset,
        kinds=kind or [],
        evidences=evidence or [],
        document=document,
        output_dir=output_dir,
        entities=entity or [],
        exclude_docs=exclude_doc or [],
        has_locator=has_locator,
        related=context,
    )
    total_hits = results[0].get("total_hits", 0) if results else 0
    mode = results[0].get("mode", "fts") if results else "fts"
    search_notes = []
    if results and results[0].get("alias_used"):
        search_notes.append(f"alias: {results[0]['alias_used']}")
    if results and results[0].get("normalized_used"):
        search_notes.append(f"normalized_query: {results[0]['query_used']}")
    note_text = "; " + "; ".join(search_notes) if search_notes else ""
    console.print(f"mode: {mode}; total_hits: {total_hits}; showing: {len(results)}; offset: {offset}{note_text}")
    table = Table(title=f"office2md search-library: {query}")
    table.add_column("Rank")
    table.add_column("Chunk ID")
    table.add_column("Document")
    table.add_column("Source File")
    table.add_column("Kind")
    table.add_column("Chunk")
    table.add_column("Evidence")
    table.add_column("Locator")
    table.add_column("Output Dir")
    table.add_column("Preview")
    for item in results:
        table.add_row(
            str(item["rank"]),
            item["chunk_id"] or "",
            item["document_title"] or "",
            item["source_file"] or "",
            item["document_kind"] or "",
            item["chunk_title"] or "",
            item["evidence_type"] or "",
            item["locator"] or "",
            item["output_dir"] or "",
            item["preview"] or "",
        )
    console.print(table)
    diagnostic_data = None
    if diagnostics or diagnostics_json or export_json is not None:
        diagnostic_data = search_library_diagnostics(
            query,
            results,
            kinds=kind or [],
            evidences=evidence or [],
            document=document,
            output_dir=output_dir,
            entities=entity or [],
            exclude_docs=exclude_doc or [],
            has_locator=has_locator,
        )
    if diagnostics and diagnostic_data is not None:
        diagnostics_table = Table(title="Diagnostics")
        diagnostics_table.add_column("Field")
        diagnostics_table.add_column("Value")
        diagnostics_table.add_row("original_query", str(diagnostic_data["original_query"]))
        diagnostics_table.add_row("effective_query", str(diagnostic_data["effective_query"]))
        diagnostics_table.add_row("mode", str(diagnostic_data["mode"]))
        diagnostics_table.add_row("alias_used", str(diagnostic_data["alias_used"] or ""))
        diagnostics_table.add_row("normalized_query", str(diagnostic_data["normalized_query"] or ""))
        diagnostics_table.add_row("token_fallback_used", str(diagnostic_data["token_fallback_used"]))
        diagnostics_table.add_row("fallback_tokens", ", ".join(diagnostic_data["fallback_tokens"]))
        diagnostics_table.add_row("filters", str(diagnostic_data["filters"]))
        diagnostics_table.add_row("result_count", str(diagnostic_data["result_count"]))
        diagnostics_table.add_row("top_evidence_types", str(diagnostic_data["top_evidence_types"]))
        diagnostics_table.add_row("top_document_kinds", str(diagnostic_data["top_document_kinds"]))
        diagnostics_table.add_row("locator_coverage", str(diagnostic_data["locator_coverage"]))
        diagnostics_table.add_row("hints", " | ".join(diagnostic_data["hints"]))
        console.print(diagnostics_table)
    if context > 0:
        related_table = Table(title="Related chunks")
        related_table.add_column("Result")
        related_table.add_column("Chunk ID")
        related_table.add_column("Evidence")
        related_table.add_column("Locator")
        related_table.add_column("Preview")
        for item in results:
            for related_item in item.get("related_chunks", []):
                related_table.add_row(
                    str(item["rank"]),
                    related_item["chunk_id"] or "",
                    related_item["evidence_type"] or "",
                    related_item["locator"] or "",
                    related_item["preview"] or "",
                )
        console.print(related_table)
    if facets:
        facet_data = search_library_facets(
            library_db,
            query,
            kinds=kind or [],
            evidences=evidence or [],
            document=document,
            output_dir=output_dir,
            entities=entity or [],
            exclude_docs=exclude_doc or [],
            has_locator=has_locator,
        )
        facet_table = Table(title="Facets")
        facet_table.add_column("Facet")
        facet_table.add_column("Value")
        facet_table.add_column("Count")
        for facet_name, rows in facet_data.items():
            for row in rows:
                facet_table.add_row(facet_name, row["value"], str(row["count"]))
        console.print(facet_table)
    if export_json is not None and diagnostic_data is not None:
        _write_search_export_json(export_json, diagnostic_data, results)
        console.print(f"export_json: {export_json}")
    if diagnostics_json and diagnostic_data is not None:
        print("diagnostics_json:")
        print(json.dumps(_search_diagnostics_json_payload(diagnostic_data, results), ensure_ascii=False, indent=2))


def _search_diagnostics_json_payload(diagnostics: dict, results: List[dict]) -> dict:
    return {
        "original_query": diagnostics["original_query"],
        "effective_query": diagnostics["effective_query"],
        "mode": diagnostics["mode"],
        "alias_used": diagnostics["alias_used"],
        "normalized_query": diagnostics["normalized_query"],
        "token_fallback_used": diagnostics["token_fallback_used"],
        "fallback_tokens": diagnostics["fallback_tokens"],
        "filters": diagnostics["filters"],
        "result_count": diagnostics["result_count"],
        "shown_count": diagnostics["shown_count"],
        "top_evidence_types": diagnostics["top_evidence_types"],
        "top_document_kinds": diagnostics["top_document_kinds"],
        "locator_coverage": diagnostics["locator_coverage"],
        "hints": diagnostics["hints"],
        "results": [_search_diagnostics_result_summary(item) for item in results],
    }


def _search_diagnostics_result_summary(item: dict) -> dict:
    return {
        "rank": item.get("rank"),
        "chunk_id": item.get("chunk_id"),
        "document_title": item.get("document_title"),
        "source_file": item.get("source_file"),
        "document_kind": item.get("document_kind"),
        "evidence_type": item.get("evidence_type"),
        "locator": item.get("locator"),
        "output_dir": item.get("output_dir"),
    }


def _search_export_json_payload(diagnostics: dict, results: List[dict]) -> dict:
    return {
        "query": {
            "original_query": diagnostics["original_query"],
            "effective_query": diagnostics["effective_query"],
            "mode": diagnostics["mode"],
            "alias_used": diagnostics["alias_used"],
            "normalized_query": diagnostics["normalized_query"],
            "token_fallback_used": diagnostics["token_fallback_used"],
            "fallback_tokens": diagnostics["fallback_tokens"],
            "filters": diagnostics["filters"],
        },
        "diagnostics": {
            "top_evidence_types": diagnostics["top_evidence_types"],
            "top_document_kinds": diagnostics["top_document_kinds"],
            "locator_coverage": diagnostics["locator_coverage"],
            "hints": diagnostics["hints"],
        },
        "result_count": diagnostics["result_count"],
        "shown_count": diagnostics["shown_count"],
        "results": [_search_export_result_summary(item) for item in results],
    }


def _search_export_result_summary(item: dict) -> dict:
    return {
        **_search_diagnostics_result_summary(item),
        "preview": item.get("preview"),
    }


def _write_search_export_json(path: Path, diagnostics: dict, results: List[dict]) -> None:
    target = path.expanduser()
    if target.parent != Path("."):
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_search_export_json_payload(diagnostics, results), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_library_report_export_json(path: Path, report: dict) -> None:
    target = path.expanduser()
    if target.parent != Path("."):
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _open_chunk_json_payload(library_path: Path, chunk_id: str, context: int, result: dict) -> dict:
    target_chunk = result["target_chunk"]
    context_chunks = result["context_chunks"]
    limitations = [target_chunk["limitation"]] if target_chunk.get("limitation") else []
    limitations.extend(item["limitation"] for item in context_chunks if item.get("limitation"))
    return {
        "schema_version": "office2md.open_chunk.v1",
        "request": {
            "library_path": str(library_path),
            "chunk_id": chunk_id,
            "context": context,
        },
        "target_chunk": target_chunk,
        "context_chunks": context_chunks,
        "evidence": {
            "source_file": target_chunk.get("source_file"),
            "locator": target_chunk.get("locator"),
            "chunk_id": target_chunk.get("chunk_id"),
            "document_id": target_chunk.get("document_id"),
            "document_title": target_chunk.get("document_title"),
            "document_kind": target_chunk.get("document_kind"),
            "evidence_type": target_chunk.get("evidence_type"),
            "confidence": target_chunk.get("confidence"),
            "limitation": target_chunk.get("limitation"),
        },
        "limitations": limitations,
        "warnings": [],
    }


def _write_open_chunk_export_json(path: Path, payload: dict) -> None:
    target = path.expanduser()
    if target.parent != Path("."):
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _chunk_evidence_packet(item: dict) -> dict:
    return {
        "source_file": item.get("source_file"),
        "locator": item.get("locator"),
        "chunk_id": item.get("chunk_id"),
        "document_id": item.get("document_id") or item.get("doc_id"),
        "document_title": item.get("document_title"),
        "document_kind": item.get("document_kind"),
        "evidence_type": item.get("evidence_type"),
        "confidence": item.get("confidence"),
        "limitation": _evidence_limitation(item),
    }


def _evidence_limitation(item: dict) -> str | None:
    limitations = []
    if not item.get("locator"):
        limitations.append("missing locator")
    if item.get("is_noisy"):
        limitations.append("chunk marked noisy")
    return "; ".join(limitations) if limitations else None


def _locate_document_export_json_payload(library_path: Path, query: str, limit: int, results: List[dict]) -> dict:
    return {
        "schema_version": "office2md.locate_document.v1",
        "request": {
            "library_path": str(library_path),
            "query": query,
            "limit": limit,
        },
        "matches": [
            {
                "document_id": item.get("doc_id"),
                "document_title": item.get("title"),
                "source_file": item.get("source_file"),
                "document_kind": item.get("document_kind"),
                "output_dir": item.get("output_dir"),
                "source_path": item.get("source_path"),
                "chunks_count": item.get("chunks_count"),
            }
            for item in results
        ],
        "limitations": [],
        "warnings": [],
    }


def _write_locate_document_export_json(path: Path, payload: dict) -> None:
    target = path.expanduser()
    if target.parent != Path("."):
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _report_context_json_payload(
    library_path: Path,
    query: str,
    limit: int,
    context: int,
    filters: dict,
    results: List[dict],
    diagnostics: dict,
) -> dict:
    selected_evidence = []
    supporting_chunks = []
    limitations = []
    for item in results:
        evidence = {
            "rank": item.get("rank"),
            **_chunk_evidence_packet(item),
            "chunk_title": item.get("chunk_title"),
            "output_dir": item.get("output_dir"),
            "preview": item.get("preview"),
            "matched_tokens": item.get("matched_tokens", []),
        }
        selected_evidence.append(evidence)
        if evidence["limitation"]:
            limitations.append(evidence["limitation"])
        for related in item.get("related_chunks", []):
            supporting = {
                "for_rank": item.get("rank"),
                **_chunk_evidence_packet(related),
                "chunk_title": related.get("chunk_title"),
                "preview": related.get("preview"),
            }
            supporting_chunks.append(supporting)
            if supporting["limitation"]:
                limitations.append(supporting["limitation"])
    with_locator = sum(1 for item in selected_evidence if item.get("locator"))
    return {
        "schema_version": "office2md.report_context.v1",
        "request": {
            "library_path": str(library_path),
            "query": query,
            "limit": limit,
            "context": context,
            "filters": filters,
        },
        "diagnostics": diagnostics,
        "matches": {
            "result_count": diagnostics["result_count"],
            "shown_count": diagnostics["shown_count"],
        },
        "selected_evidence": selected_evidence,
        "supporting_chunks": supporting_chunks,
        "coverage": {
            "selected_evidence_count": len(selected_evidence),
            "supporting_chunks_count": len(supporting_chunks),
            "with_locator": with_locator,
            "without_locator": len(selected_evidence) - with_locator,
            "documents": len({item.get("document_title") for item in selected_evidence if item.get("document_title")}),
        },
        "limitations": _dedupe_strings(limitations),
        "warnings": [] if results else ["no results found"],
    }


def _write_report_context_export_json(path: Path, payload: dict) -> None:
    target = path.expanduser()
    if target.parent != Path("."):
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _dedupe_strings(values: list[str | None]) -> list[str]:
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _print_workspace_status(status: dict, *, show_history: bool) -> None:
    workspace = status["workspace"]
    source = status["source_manifest"]
    library = status["library_versions"]
    output = status["output_versions"]
    traceability = status["traceability"]
    table = Table(title="office2md workspace-status")
    table.add_column("Area")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("workspace", "workspace_path", workspace["workspace_path"])
    table.add_row("workspace", "schema_version", str(workspace["schema_version"] or ""))
    table.add_row("workspace", "created_at", str(workspace["created_at"] or ""))
    table.add_row("workspace", "updated_at", str(workspace["updated_at"] or ""))
    table.add_row("workspace", "missing_folders", str(len(workspace["missing_expected_folders"])))
    table.add_row("workspace", "missing_manifests", str(len(workspace["missing_expected_manifests"])))
    table.add_row("source", "total_sources", str(source["total_sources"]))
    table.add_row("source", "active_sources", str(source["active_sources"]))
    table.add_row("source", "changed_sources", str(source["changed_sources"]))
    table.add_row("source", "missing_sources", str(source["missing_sources"]))
    table.add_row("source", "source_roots_count", str(source["source_roots_count"]))
    table.add_row("library", "total_versions", str(library["total_versions"]))
    if library["latest"]:
        table.add_row("library", "latest_library_version_id", str(library["latest"]["library_version_id"] or ""))
        table.add_row("library", "latest_label", str(library["latest"]["label"] or ""))
        metrics = library["latest"]["metrics"]
        table.add_row("library", "documents_count", str(metrics.get("documents_count") or 0))
        table.add_row("library", "chunks_count", str(metrics.get("chunks_count") or 0))
        table.add_row("library", "entities_count", str(metrics.get("entities_count") or 0))
    table.add_row("output", "total_versions", str(output["total_versions"]))
    if output["latest"]:
        table.add_row("output", "latest_output_version_id", str(output["latest"]["output_version_id"] or ""))
        table.add_row("output", "latest_output_type", str(output["latest"]["output_type"] or ""))
        table.add_row("output", "latest_label", str(output["latest"]["label"] or ""))
        table.add_row("output", "linked_library_version_id", str(output["latest"]["library_version_id"] or ""))
        files = output["latest"]["output_files"]
        table.add_row("output", "file_count", str(files.get("file_count") or 0))
        table.add_row("output", "total_size_bytes", str(files.get("total_size_bytes") or 0))
    table.add_row("traceability", "source_manifest_hash", str(traceability["source_manifest_hash"] or ""))
    table.add_row("traceability", "library_version_id", str(traceability["library_version_id"] or ""))
    table.add_row("traceability", "output_version_id", str(traceability["output_version_id"] or ""))
    console.print(table)
    if show_history:
        _print_workspace_status_history("Library Version History", library["history"], "library_version_id")
        _print_workspace_status_history("Output Version History", output["history"], "output_version_id")
    for warning in status["warnings"]:
        console.print(f"[yellow]warning:[/yellow] {warning}")
    for error in status["errors"]:
        console.print(f"[red]error:[/red] {error}")


def _print_workspace_status_history(title: str, rows: list[dict], id_key: str) -> None:
    table = Table(title=title)
    table.add_column("ID")
    table.add_column("Registered At")
    table.add_column("Label")
    for row in rows:
        table.add_row(str(row.get(id_key) or ""), str(row.get("registered_at") or ""), str(row.get("label") or ""))
    console.print(table)


@app.command("locate-document")
def locate_document_command(
    library_db_or_output_dir: Path,
    query: str,
    limit: int = typer.Option(20, help="Maximum documents to print."),
    export_json: Path = typer.Option(None, "--export-json", help="Write UTF-8 locate-document JSON to PATH; creates parent directories."),
) -> None:
    """Locate source documents in a built Knowledge Library by title or source filename."""
    results = locate_document(library_db_or_output_dir, query, limit=limit)
    table = Table(title=f"office2md locate-document: {query}")
    table.add_column("Title")
    table.add_column("Source File")
    table.add_column("Kind")
    table.add_column("Output Dir")
    table.add_column("Source Path")
    table.add_column("Chunks")
    for item in results:
        table.add_row(
            item.get("title", ""),
            item.get("source_file", ""),
            item.get("document_kind", ""),
            item.get("output_dir", ""),
            item.get("source_path", ""),
            str(item.get("chunks_count", "")),
        )
    console.print(table)
    if export_json is not None:
        _write_locate_document_export_json(export_json, _locate_document_export_json_payload(library_db_or_output_dir, query, limit, results))
        console.print(f"export_json: {export_json}")


@app.command("open-chunk")
def open_chunk_command(
    library_db_or_output_dir: Path,
    chunk_id: str,
    context: int = typer.Option(0, "--context", help="Number of same-document context chunks to include."),
    export_json: Path = typer.Option(None, "--export-json", help="Write UTF-8 open-chunk JSON to PATH; creates parent directories."),
) -> None:
    """Open one library chunk by exact chunk_id without changing the library."""
    result = open_chunk(library_db_or_output_dir, chunk_id, context=context)
    if result is None:
        raise typer.BadParameter(f"chunk_id not found: {chunk_id}")
    payload = _open_chunk_json_payload(library_db_or_output_dir, chunk_id, context, result)
    target = payload["target_chunk"]
    table = Table(title=f"office2md open-chunk: {chunk_id}")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("chunk_id", target.get("chunk_id") or "")
    table.add_row("document_id", target.get("document_id") or "")
    table.add_row("document_title", target.get("document_title") or "")
    table.add_row("source_file", target.get("source_file") or "")
    table.add_row("document_kind", target.get("document_kind") or "")
    table.add_row("evidence_type", target.get("evidence_type") or "")
    table.add_row("locator", target.get("locator") or "")
    table.add_row("context_chunks", str(len(payload["context_chunks"])))
    table.add_row("preview", target.get("preview") or "")
    console.print(table)
    if payload["limitations"]:
        for limitation in payload["limitations"]:
            console.print(f"[yellow]limitation:[/yellow] {limitation}")
    if export_json is not None:
        _write_open_chunk_export_json(export_json, payload)
        console.print(f"export_json: {export_json}")


@app.command("build-report-context")
def build_report_context_command(
    library_db: Path,
    query: str,
    limit: int = typer.Option(10, help="Maximum search results to include."),
    context: int = typer.Option(2, "--context", "--related", help="Same-document context chunks per result."),
    kind: List[str] = typer.Option(None, "--kind", help="Filter by document_kind. Can be repeated."),
    evidence: List[str] = typer.Option(None, "--evidence", help="Filter by evidence_type. Can be repeated."),
    document: str = typer.Option(None, "--doc", "--document", help="Filter by document title or source_file."),
    output_dir: str = typer.Option(None, "--output-dir", help="Filter by output directory name."),
    entity: List[str] = typer.Option(None, "--entity", help="Filter by entity text. Can be repeated."),
    exclude_doc: List[str] = typer.Option(None, "--exclude-doc", help="Exclude document title/source_file match. Can be repeated."),
    has_locator: bool = typer.Option(False, "--has-locator", help="Only include chunks with source locators."),
    export_json: Path = typer.Option(None, "--export-json", help="Write UTF-8 report context JSON to PATH; creates parent directories."),
) -> None:
    """Build a read-only evidence context package for agent report drafting."""
    filters = {
        "kind": kind or [],
        "evidence": evidence or [],
        "document": document,
        "output_dir": output_dir,
        "entity": entity or [],
        "exclude_doc": exclude_doc or [],
        "has_locator": has_locator,
    }
    results = search_library(
        library_db,
        query,
        limit=limit,
        kinds=kind or [],
        evidences=evidence or [],
        document=document,
        output_dir=output_dir,
        entities=entity or [],
        exclude_docs=exclude_doc or [],
        has_locator=has_locator,
        related=max(context, 0),
    )
    diagnostics = search_library_diagnostics(
        query,
        results,
        kinds=kind or [],
        evidences=evidence or [],
        document=document,
        output_dir=output_dir,
        entities=entity or [],
        exclude_docs=exclude_doc or [],
        has_locator=has_locator,
    )
    payload = _report_context_json_payload(library_db, query, limit, max(context, 0), filters, results, diagnostics)
    table = Table(title=f"office2md build-report-context: {query}")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("result_count", str(payload["matches"]["result_count"]))
    table.add_row("selected_evidence", str(len(payload["selected_evidence"])))
    table.add_row("supporting_chunks", str(len(payload["supporting_chunks"])))
    table.add_row("with_locator", str(payload["coverage"]["with_locator"]))
    table.add_row("without_locator", str(payload["coverage"]["without_locator"]))
    console.print(table)
    for warning in payload["warnings"]:
        console.print(f"[yellow]warning:[/yellow] {warning}")
    if export_json is not None:
        _write_report_context_export_json(export_json, payload)
        console.print(f"export_json: {export_json}")


@app.command("library-report")
def library_report_command(
    library_db_or_output_dir: Path,
    export_json: Path = typer.Option(None, "--export-json", help="Write UTF-8 library report JSON to PATH; creates parent directories."),
) -> None:
    """Print counts, distributions, and quality metrics for a built Knowledge Library."""
    report = library_report(library_db_or_output_dir)
    table = Table(title="office2md library-report")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("documents_count", str(report["documents_count"]))
    table.add_row("chunks_count", str(report["chunks_count"]))
    table.add_row("entities_count", str(report["entities_count"]))
    table.add_row("document_kind_distribution", _format_counts(report["document_kind_distribution"]))
    table.add_row("evidence_type_distribution", _format_counts(report["evidence_type_distribution"]))
    table.add_row("top_entities", ", ".join(item["entity_text"] for item in report["top_entities"][:10]))
    table.add_row("top_batches", ", ".join(item["batch_id"] for item in report["top_batches"][:10]))
    table.add_row("missing_assets_summary", str(len(report["missing_assets_summary"])))
    table.add_row("low_quality_documents", str(len(report["low_quality_documents"])))
    table.add_row("page_level_pdf_documents", str(len(report.get("page_level_pdf_documents", []))))
    table.add_row("noisy_chunks_count", str(report["noisy_chunks_count"]))
    table.add_row("chunks_without_locator", str(report.get("chunks_without_locator", 0)))
    table.add_row("chunks_without_locator_by_document_kind", _format_counts(report.get("chunks_without_locator_by_document_kind", {})))
    table.add_row("chunks_without_locator_by_evidence_type", _format_counts(report.get("chunks_without_locator_by_evidence_type", {})))
    table.add_row("chunks_without_locator_by_extension", _format_counts(report.get("chunks_without_locator_by_extension", {})))
    table.add_row("chunks_without_locator_top_sources", _format_missing_locator_sources(report.get("chunks_without_locator_top_sources", [])))
    table.add_row("noisy_documents", str(len(report["noisy_documents"])))
    table.add_row("hmi_translation_documents", str(len(report["hmi_translation_documents"])))
    table.add_row("export_files_generated", ", ".join(report["export_files_generated"]))
    console.print(table)
    if export_json is not None:
        _write_library_report_export_json(export_json, report)
        console.print(f"export_json: {export_json}")


@app.command("export-obsidian")
def export_obsidian_command(
    library_path: Path,
    vault_output: Path,
    overwrite: bool = typer.Option(False, "--overwrite", help="Replace an existing non-empty vault output folder."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview export counts without writing files."),
    max_concepts: int = typer.Option(100, "--max-concepts", help="Maximum concept notes to export."),
    max_evidence_per_concept: int = typer.Option(5, "--max-evidence-per-concept", help="Maximum evidence snippets per concept note."),
) -> None:
    """Export a built office2md library to an Obsidian-friendly vault folder."""
    try:
        result = export_obsidian(
            library_path,
            vault_output,
            overwrite=overwrite,
            dry_run=dry_run,
            max_concepts=max_concepts,
            max_evidence_per_concept=max_evidence_per_concept,
        )
    except ObsidianExportError as exc:
        raise typer.BadParameter(str(exc)) from exc
    table = Table(title="office2md export-obsidian")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("library_path", result["library_path"])
    table.add_row("vault_output", result["vault_output"])
    table.add_row("documents_exported", str(result["documents_exported"]))
    table.add_row("concepts_exported", str(result["concepts_exported"]))
    table.add_row("dry_run", str(result["options"]["dry_run"]))
    table.add_row("warnings", str(len(result["warnings"])))
    console.print(table)
    for warning in result["warnings"]:
        console.print(f"[yellow]warning:[/yellow] {warning}")


@app.command("convert-file")
def convert_file_command(
    input_file: Path,
    output: Path,
    engine: str = typer.Option("auto", help="auto, docling, markitdown, or marker"),
    profile: str = typer.Option("kb", help="Output profile: kb, rag, memory, or obsidian."),
    with_json: bool = typer.Option(True, help="Write document.json."),
    with_chunks: bool = typer.Option(True, help="Write chunks.jsonl."),
    with_assets: bool = typer.Option(True, help="Create assets directory."),
    skip_existing: bool = typer.Option(False, help="Skip when output folder exists."),
    render_pdf_pages: bool = typer.Option(False, help="Render PDF pages to assets/page_001.png."),
    max_render_pages: int = typer.Option(3, help="Maximum PDF pages to render."),
    max_text_pages: int = typer.Option(None, help="Maximum PDF pages to extract text from."),
    extract_all_page_text: bool = typer.Option(False, help="Extract text from all PDF pages without rendering all pages."),
    use_ai: bool = typer.Option(False, help="Enable optional AI enrichment. Off by default."),
    ai_backend: str = typer.Option("none", help="AI backend for --use-ai: none, http, openai-compatible, cli, or minimax."),
    ai_model: str = typer.Option(None, help="AI model name."),
    ai_base_url: str = typer.Option(None, help="AI backend base URL."),
    ai_command: str = typer.Option(None, help="AI CLI command."),
    ai_timeout: int = typer.Option(60, help="AI adapter timeout in seconds."),
) -> None:
    options = ConvertOptions(
        engine=engine,
        profile=profile,
        recursive=False,
        with_json=with_json,
        with_chunks=with_chunks,
        with_assets=with_assets,
        skip_existing=skip_existing,
        render_pdf_pages=render_pdf_pages,
        max_render_pages=max_render_pages,
        max_text_pages=max_text_pages,
        extract_all_page_text=extract_all_page_text,
        use_ai=use_ai,
        ai_backend=ai_backend,
        ai_model=ai_model,
        ai_base_url=ai_base_url,
        ai_command=ai_command,
        ai_timeout=ai_timeout,
    )
    out_dir, status = convert_one(input_file, output, options)
    rebuild_output_index(output, profile=options.profile)
    console.print(f"{status}: {input_file} -> {out_dir}")


@app.command()
def convert(
    input_path: Path,
    output: Path,
    engine: str = typer.Option("auto", help="auto, docling, markitdown, or marker"),
    profile: str = typer.Option("kb", help="Output profile: kb, rag, memory, or obsidian."),
    recursive: bool = typer.Option(False, "--recursive", help="Scan input directory recursively."),
    with_json: bool = typer.Option(True, help="Write document.json."),
    with_chunks: bool = typer.Option(True, help="Write chunks.jsonl."),
    with_assets: bool = typer.Option(True, help="Create assets directory."),
    skip_existing: bool = typer.Option(False, help="Skip when output folder exists."),
    force_ocr: bool = typer.Option(False, help="Reserved; validated path does not use OCR."),
    use_llm: bool = typer.Option(False, help="Reserved; validated path does not use LLM enrichment."),
    render_pdf_pages: bool = typer.Option(False, help="Render PDF pages to assets/page_001.png."),
    max_render_pages: int = typer.Option(3, help="Maximum PDF pages to render."),
    max_text_pages: int = typer.Option(None, help="Maximum PDF pages to extract text from."),
    extract_all_page_text: bool = typer.Option(False, help="Extract text from all PDF pages without rendering all pages."),
    use_ai: bool = typer.Option(False, help="Enable optional AI enrichment. Off by default."),
    ai_backend: str = typer.Option("none", help="AI backend for --use-ai: none, http, openai-compatible, cli, or minimax."),
    ai_model: str = typer.Option(None, help="AI model name."),
    ai_base_url: str = typer.Option(None, help="AI backend base URL."),
    ai_command: str = typer.Option(None, help="AI CLI command."),
    ai_timeout: int = typer.Option(60, help="AI adapter timeout in seconds."),
    max_files: int = typer.Option(None, help="Maximum number of files to process."),
    dry_run: bool = typer.Option(False, help="List files that would be processed without converting."),
    include: List[str] = typer.Option(None, help="Glob include filter. Can be provided multiple times."),
    exclude: List[str] = typer.Option(None, help="Glob exclude filter. Can be provided multiple times."),
) -> None:
    """Convert INPUT_PATH into OUTPUT using the selected engine and profile."""
    options = ConvertOptions(
        engine=engine,
        profile=profile,
        recursive=recursive,
        with_json=with_json,
        with_chunks=with_chunks,
        with_assets=with_assets,
        skip_existing=skip_existing,
        force_ocr=force_ocr,
        use_llm=use_llm,
        render_pdf_pages=render_pdf_pages,
        max_render_pages=max_render_pages,
        max_text_pages=max_text_pages,
        extract_all_page_text=extract_all_page_text,
        use_ai=use_ai,
        ai_backend=ai_backend,
        ai_model=ai_model,
        ai_base_url=ai_base_url,
        ai_command=ai_command,
        ai_timeout=ai_timeout,
    )
    ensure_directory(output)
    console.print("Scanning input directory...")
    files = filter_files(scan_input(input_path, recursive=recursive), include or [], exclude or [])
    if max_files is not None:
        files = files[: max(0, max_files)]
    console.print(f"Found {len(files)} supported files.")
    if dry_run:
        console.print("Dry run: no files will be converted.")
        for file_path in files:
            console.print(str(file_path))
        rebuild_output_index(output, profile=options.profile)
        return

    success = 0
    failed = 0
    skipped = 0
    for index, file_path in enumerate(files, start=1):
        console.print(f"[{index}/{len(files)}] {file_path.name}")
        try:
            out_dir, status = convert_one(file_path, output, options)
            if status == "skipped":
                skipped += 1
            else:
                success += 1
            console.print(f"  status: {status}")
            console.print(f"  output: {out_dir / 'document.md'}")
        except Exception as exc:
            failed += 1
            failed_dir = write_failure_manifest(file_path, output, options, exc)
            console.print("  status: failed")
            console.print(f"  error: {exc}")
            console.print(f"  output: {failed_dir}")

    console.print("Done.")
    rebuild_output_index(output, profile=options.profile)
    console.print(f"Success: {success}")
    console.print(f"Failed: {failed}")
    console.print(f"Skipped: {skipped}")
    console.print(f"Output: {output}")


def convert_one(source_path: Path, output_root: Path, options: ConvertOptions):
    source = source_path.expanduser().resolve()
    checksum = sha256_file(source)
    if options.skip_existing:
        candidate = output_dir_for_source(source, output_root, checksum)
        if (candidate / "document.md").exists():
            return candidate, "skipped"

    converted_source = source
    warnings: List[str] = []
    with tempfile.TemporaryDirectory(prefix="office2md_") as temp_name:
        if is_legacy_office(source):
            try:
                converted_source = convert_legacy_office(source, Path(temp_name))
                warnings.append(f"preprocessed legacy office file to {converted_source.suffix}")
            except Exception as exc:
                warnings.append(f"legacy office preprocessing failed: {exc}")

        selected_engine = choose_engine(converted_source, options)
        console.print(f"  engine: {selected_engine}")
        fallback_used = False
        try:
            result = get_converter(selected_engine).convert(converted_source, options)
        except Exception as exc:
            if options.engine == "auto" and selected_engine == "docling":
                warnings.append(f"docling failed; fell back to markitdown: {_brief_error(exc)}")
                console.print("  fallback: markitdown")
                result = get_converter("markitdown").convert(converted_source, options)
                result.metadata["fallback"] = "docling_to_markitdown"
                fallback_used = True
            else:
                raise

    cleaned = clean_markdown(result.markdown)
    if result.metadata.get("fallback") is not None:
        fallback_used = True

    document_kind = classify_document_kind(source, cleaned)
    planned_output_dir = output_dir_for_source(source, output_root, checksum)
    rendered_pages = []
    text_pages = []
    pages = []
    if source.suffix.lower() == ".pdf":
        if options.render_pdf_pages:
            assets_dir = planned_output_dir / "assets"
            rendered_pages = render_pdf_pages(source, assets_dir, options.max_render_pages)
        text_limit = _pdf_text_page_limit(options, document_kind)
        if text_limit is not None or options.extract_all_page_text or document_kind in MANUAL_KINDS:
            try:
                text_pages = extract_pdf_text_pages(source, text_limit)
            except Exception as exc:
                warnings.append(f"page text extraction failed; using rendered page text only: {_brief_error(exc)}")
        pages = merge_pdf_pages(text_pages, rendered_pages) if text_pages or rendered_pages else []
        pages = enrich_page_semantics(pages, result.markdown)
        if document_kind in MANUAL_KINDS:
            pages = [_remove_manual_semantic_noise(page) for page in pages]

    result.raw_json = build_pdf_document_json(source.name, result.engine, pages, result.raw_json) if source.suffix.lower() == ".pdf" else result.raw_json
    quality_status = determine_quality_status(source, cleaned, fallback_used, result.raw_json)
    pages_with_text_count = sum(1 for page in pages if (page.get("text") or "").strip())
    extraction_status = "text"
    requires_ocr_or_vision = False

    if source.suffix.lower() == ".pdf" and fallback_used:
        warnings.append("low_structure: pdf fallback used")
    if source.suffix.lower() == ".pdf" and not has_headings(cleaned):
        warnings.append("low_structure: no headings detected")
    if source.suffix.lower() == ".pdf" and is_empty_document_json(result.raw_json):
        warnings.append("low_structure: document.json has no pages/elements")

    if document_kind == "technical_drawing_pdf":
        quality_status = "low_structure"
    if document_kind == "hmi_translation_xlsx":
        quality_status = "structured_with_noise"
    if source.suffix.lower() == ".pdf" and pages and pages_with_text_count == 0:
        extraction_status = "image_only"
        quality_status = "visual_only"
        requires_ocr_or_vision = True

    doc_slug = source.stem
    doc_id = checksum.split(":", 1)[-1][:16]
    tags = generate_tags(source, document_kind, quality_status)
    extracted_metadata = extract_title_page_metadata(pages) if document_kind in MANUAL_KINDS else {}
    office_metadata = extract_office_metadata(source, cleaned, document_kind)
    extracted_metadata.update({key: value for key, value in office_metadata.items() if value not in ("", [], None)})
    section_outline = extract_toc_entries_from_pages(pages) if document_kind in MANUAL_KINDS else []
    if section_outline and pages and document_kind == "manual_pdf":
        pages_count = max((int(page.get("page_number") or 0) for page in pages), default=0)
        section_outline = [
            entry
            for entry in section_outline
            if int(entry.get("page_hint") or 0) <= pages_count and _clean_manual_section_title(entry.get("title", ""))
        ]
    drawing_index = extract_drawing_index(pages) if document_kind == "technical_drawing_pdf" else []
    if options.with_chunks and source.suffix.lower() == ".pdf" and pages:
        chunks = chunk_pdf_pages(pages, source.name, doc_slug, result.markdown)
    else:
        office_chunks = build_office_chunks(cleaned, source.name, doc_slug, document_kind) if options.with_chunks else []
        chunks = office_chunks or (chunk_markdown(cleaned, source.name, doc_slug) if options.with_chunks else [])
    if options.with_chunks and document_kind in MANUAL_KINDS and pages:
        chunks.extend(build_section_chunks(pages, source.name, doc_slug, len(chunks), section_outline))
    if options.with_chunks and drawing_index:
        chunks.extend(build_drawing_index_chunks(drawing_index, source.name, doc_slug, len(chunks)))
    embedded_images_count, asset_warnings = extract_embedded_office_assets(source, planned_output_dir / "assets")
    warnings.extend(asset_warnings)
    missing_assets_count = missing_markdown_asset_count(cleaned)
    if missing_assets_count:
        warnings.append(f"missing_asset: {missing_assets_count} markdown image references do not map to extracted assets")
    embedded_base64_count = embedded_base64_image_count(cleaned)
    page_chunks_count = sum(1 for chunk in chunks if (chunk.get("page_number") is not None or chunk.get("page_start") is not None) and chunk.get("evidence_type") != "section")
    section_chunks_count = sum(1 for chunk in chunks if chunk.get("evidence_type") == "section")
    slide_chunks_count = sum(1 for chunk in chunks if chunk.get("evidence_type") == "slide")
    table_chunks_count = sum(1 for chunk in chunks if chunk.get("evidence_type") == "table")
    drawing_index_chunks_count = sum(1 for chunk in chunks if chunk.get("evidence_type") == "drawing_index")
    topic_chunks_count = sum(1 for chunk in chunks if chunk.get("evidence_type") == "topic")
    batch_study_chunks_count = sum(1 for chunk in chunks if chunk.get("evidence_type") == "batch_study")
    hmi_translation_chunks_count = sum(1 for chunk in chunks if str(chunk.get("evidence_type") or "").startswith("hmi_translation_"))
    section_chunks_with_body_count = sum(
        1
        for chunk in chunks
        if chunk.get("evidence_type") == "section" and len((chunk.get("text") or "").splitlines()) > 2
    )
    image_only_chunks_count = sum(1 for chunk in chunks if chunk.get("image_path") and chunk.get("provenance_status") == "page_image_only")
    searchable_page_chunks_count = sum(
        1
        for chunk in chunks
        if (chunk.get("page_number") is not None or chunk.get("page_start") is not None)
        and ((chunk.get("page_text") or "").strip() or int(chunk.get("page_text_char_count") or 0) > 0)
    )
    warnings.extend(result.warnings)
    warnings.extend(collect_warnings(cleaned, len(chunks)))
    converted_at = utc_now_iso()
    metadata = {
        "title": source.stem,
        "source_file": source.name,
        "source_path": str(source),
        "file_type": detect_file_type(source),
        "converter": result.engine,
        "converted_at": converted_at,
        "checksum": checksum,
        "ocr_used": result.ocr_used,
        "page_count": result.metadata.get("page_count"),
        "quality_status": quality_status,
        "document_kind": document_kind,
        "asset_count": len(rendered_pages) if rendered_pages else len(result.assets),
        "pages_count": len(pages),
        "text_pages_count": pages_with_text_count,
        "rendered_pages_count": len(rendered_pages),
        "extraction_status": extraction_status,
        "requires_ocr_or_vision": requires_ocr_or_vision,
        "tags": tags,
        "aliases": [source.stem],
        "extracted_metadata": extracted_metadata,
        "section_outline": section_outline,
        "page_chunks_count": page_chunks_count,
        "image_chunks_count": image_only_chunks_count,
        "image_only_chunks_count": image_only_chunks_count,
        "searchable_page_chunks_count": searchable_page_chunks_count,
        "section_chunks_count": section_chunks_count,
        "section_chunks_with_body_count": section_chunks_with_body_count,
        "slide_chunks_count": slide_chunks_count,
        "table_chunks_count": table_chunks_count,
        "drawing_index_count": len(drawing_index),
        "drawing_index": drawing_index,
        "drawing_index_chunks_count": drawing_index_chunks_count,
        "topic_chunks_count": topic_chunks_count,
        "batch_study_chunks_count": batch_study_chunks_count,
        "hmi_translation_chunks_count": hmi_translation_chunks_count,
        "visual_heavy_slides_count": extracted_metadata.get("visual_heavy_slides_count", 0),
        "embedded_images_count": embedded_images_count or embedded_base64_count,
        "embedded_image_detected": bool(embedded_images_count or embedded_base64_count),
        "missing_assets_count": missing_assets_count,
    }
    body_markdown = clean_markdown(build_document_body(source, cleaned, metadata, options.profile, pages))
    chunks = enrich_chunks(chunks, doc_id, source, document_kind, quality_status, tags)
    entities = extract_entities(source, body_markdown, document_kind=document_kind, metadata=metadata)
    source_map = build_source_map(chunks)

    ai_data, ai_notes, ai_warnings = run_ai_enrichment(body_markdown, metadata, options)
    ai_used = ai_data is not None
    warnings.extend(ai_warnings)
    if ai_data:
        body_markdown = clean_markdown(
            body_markdown
            + "\n## AI Notes\n\n"
            + ai_notes.replace("# AI Notes", "").strip()
            + "\n\n## AI Summary\n\n"
            + ai_data.get("raw", "")
            + "\n\n## AI Suggested Tags\n\n"
        )

    knowledge = build_knowledge_json(
        metadata,
        chunks_count=len(chunks),
        assets_count=metadata["asset_count"],
        pages=pages,
        ai=ai_data,
    )
    final_markdown = add_frontmatter(body_markdown, metadata)
    if result.raw_json is not None:
        result.raw_json["document_kind"] = document_kind
        result.raw_json["quality_status"] = quality_status
        result.raw_json["extraction_status"] = extraction_status
        result.raw_json["requires_ocr_or_vision"] = requires_ocr_or_vision
    manifest = build_manifest(
        source_path=source,
        checksum=checksum,
        engine=result.engine,
        status="success",
        warnings=warnings,
        errors=result.errors,
        fallback_used=fallback_used,
        ocr_used=result.ocr_used,
        quality_status=quality_status,
        document_kind=document_kind,
        asset_count=metadata["asset_count"],
        ai_used=ai_used,
        extraction_status=extraction_status,
        requires_ocr_or_vision=requires_ocr_or_vision,
        converted_at=converted_at,
    )
    out_dir = write_document_output(
        source,
        output_root,
        result,
        final_markdown,
        chunks,
        manifest,
        output_dir=planned_output_dir,
        knowledge=knowledge,
        entities=entities,
        source_map=source_map,
        ai_notes=ai_notes,
    )
    return out_dir, "success"


def _pdf_text_page_limit(options: ConvertOptions, document_kind: str) -> int | None:
    if options.extract_all_page_text:
        return None
    if options.max_text_pages is not None:
        return max(0, options.max_text_pages)
    if document_kind in MANUAL_KINDS:
        return None
    if options.render_pdf_pages:
        return max(0, options.max_render_pages)
    return None


def filter_files(files: List[Path], include: List[str], exclude: List[str]) -> List[Path]:
    filtered = []
    for file_path in files:
        path_text = file_path.as_posix()
        name = file_path.name
        if include and not any(file_path.match(pattern) or name_matches(name, pattern) or _glob_text(path_text, pattern) for pattern in include):
            continue
        if exclude and any(file_path.match(pattern) or name_matches(name, pattern) or _glob_text(path_text, pattern) for pattern in exclude):
            continue
        filtered.append(file_path)
    return filtered


def name_matches(name: str, pattern: str) -> bool:
    from fnmatch import fnmatch

    return fnmatch(name, pattern)


def _glob_text(path_text: str, pattern: str) -> bool:
    from fnmatch import fnmatch

    return fnmatch(path_text, pattern)


def write_failure_manifest(source_path: Path, output_root: Path, options: ConvertOptions, exc: Exception) -> Path:
    source = source_path.expanduser().resolve()
    checksum = sha256_file(source) if source.exists() else "sha256:"
    engine = choose_engine(source, options)
    result = ConvertResult(markdown="", raw_markdown="", engine=engine, errors=[str(exc)])
    manifest = build_manifest(
        source_path=source,
        checksum=checksum,
        engine=engine,
        status="failed",
        warnings=[],
        errors=[str(exc)],
    )
    return write_document_output(source, output_root, result, "", [], manifest)


def _brief_error(exc: Exception) -> str:
    first_line = str(exc).encode("ascii", errors="ignore").decode("ascii").splitlines()[0].strip()
    if len(first_line) > 240:
        first_line = first_line[:237] + "..."
    return f"{exc.__class__.__name__}: {first_line}" if first_line else exc.__class__.__name__


def _format_counts(values: dict) -> str:
    return ", ".join(f"{key}: {value}" for key, value in values.items())


def _format_missing_locator_sources(values: List[dict]) -> str:
    return "; ".join(f"{item.get('source_file', '')}: {item.get('chunks_without_locator', 0)}" for item in values[:5])


def _clean_manual_section_title(title: str) -> bool:
    normalized = title.lower().strip()
    if not normalized or len(normalized) > 120:
        return False
    if normalized in {"print date", "page", "confidential"}:
        return False
    return bool(__import__("re").search(r"[a-zA-Z]", normalized))


def _remove_manual_semantic_noise(page: dict) -> dict:
    item = dict(page)
    if item.get("semantic_title") in {"Cable Overview", "Power Supply", "Cover Sheet"}:
        item["semantic_title"] = None
    return item


def _print_docling_diagnostics(result: dict) -> None:
    table = Table(title="office2md doctor-docling")
    table.add_column("Check")
    table.add_column("Status")
    for key in ["python", "docling_import", "docling_version", "document_converter", "fixture_conversion"]:
        if key in result:
            table.add_row(key, str(result[key]))
    console.print(table)

    env_table = Table(title="Docling-related environment")
    env_table.add_column("Variable")
    env_table.add_column("Value")
    for key, value in result.get("environment", {}).items():
        env_table.add_row(key, value or "(not set)")
    console.print(env_table)

    exception = result.get("exception")
    if exception:
        console.print("[red]Docling exception captured[/red]")
        console.print(f"type: {exception.get('type')}")
        console.print(f"message: {exception.get('message')}")
        console.print("traceback:")
        console.print(exception.get("traceback"))


if __name__ == "__main__":
    app()
