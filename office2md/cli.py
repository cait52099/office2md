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
from office2md.library import build_library, library_report, locate_document, search_library, search_library_diagnostics, search_library_facets
from office2md.models import ConvertOptions, ConvertResult
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
from office2md.workspace import init_workspace


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


@app.command("locate-document")
def locate_document_command(library_db_or_output_dir: Path, query: str, limit: int = typer.Option(20, help="Maximum documents to print.")) -> None:
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
