import json
import re
import shutil
import sqlite3
import hashlib
from collections import defaultdict
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from slugify import slugify

from office2md.concepts import library_db_path, load_curated_concept_index, normalize_concept_label
from office2md.library import library_report


class ObsidianExportError(RuntimeError):
    pass


def safe_note_name(value: str, fallback: str = "note") -> str:
    text = re.sub(r"[\x00-\x1f<>:\"/\\|?*]+", " ", value or "")
    text = re.sub(r"\s+", " ", text).strip(" .")
    text = text or fallback
    return text[:120].strip(" .") or fallback


def unique_note_name(base_name: str, used: set[str], stable_key: str) -> str:
    candidate = safe_note_name(base_name)
    folded = candidate.casefold()
    if folded not in used:
        used.add(folded)
        return candidate
    suffix = slugify(stable_key)[:16] or hashlib.sha1(stable_key.encode("utf-8")).hexdigest()[:8]
    candidate = safe_note_name(f"{base_name} {suffix}")
    folded = candidate.casefold()
    counter = 2
    while folded in used:
        candidate = safe_note_name(f"{base_name} {suffix}-{counter}")
        folded = candidate.casefold()
        counter += 1
    used.add(folded)
    return candidate


def export_obsidian(
    library_path: Path,
    vault_output: Path,
    overwrite: bool = False,
    dry_run: bool = False,
    max_concepts: int = 100,
    max_evidence_per_concept: int = 5,
) -> dict[str, Any]:
    library = library_path.expanduser().resolve()
    vault = vault_output.expanduser().resolve()
    db_path = library_db_path(library)
    if not db_path.exists():
        raise ObsidianExportError(f"built library not found: {db_path}")
    if max_concepts < 0:
        raise ObsidianExportError("--max-concepts must be >= 0")
    if max_evidence_per_concept < 0:
        raise ObsidianExportError("--max-evidence-per-concept must be >= 0")
    if vault.exists() and any(vault.iterdir()) and not overwrite:
        raise ObsidianExportError(f"output folder exists and is non-empty: {vault}")

    documents, chunks_by_doc, asset_count = _load_documents(db_path)
    concept_index = load_curated_concept_index(library)
    selected_concepts = _select_concepts(concept_index.get("concepts", {}), max_concepts)
    document_note_names = _document_note_names(documents)
    concept_note_names = _concept_note_names(selected_concepts)
    doc_concepts = _document_concepts(selected_concepts)
    warnings = []
    if asset_count:
        warnings.append(f"assets were not copied in Obsidian MVP export: {asset_count} library assets")

    manifest = _manifest(
        library,
        vault,
        documents_exported=len(documents),
        concepts_exported=len(selected_concepts),
        warnings=warnings,
        overwrite=overwrite,
        dry_run=dry_run,
        max_concepts=max_concepts,
        max_evidence_per_concept=max_evidence_per_concept,
    )

    if dry_run:
        return {**manifest, "dry_run": True, "planned_files": _planned_files(documents, selected_concepts)}

    if vault.exists() and overwrite:
        _empty_directory(vault)
    (vault / "Documents").mkdir(parents=True, exist_ok=True)
    (vault / "Concepts").mkdir(parents=True, exist_ok=True)
    (vault / "_office2md").mkdir(parents=True, exist_ok=True)

    for doc in documents:
        body = _document_note(doc, chunks_by_doc.get(doc["doc_id"], []), doc_concepts.get(doc["doc_id"], []), concept_note_names)
        (vault / "Documents" / f"{document_note_names[doc['doc_id']]}.md").write_text(body, encoding="utf-8")

    for label, concept in selected_concepts:
        body = _concept_note(concept, document_note_names, max_evidence_per_concept)
        (vault / "Concepts" / f"{concept_note_names[label]}.md").write_text(body, encoding="utf-8")

    (vault / "00_Index.md").write_text(_index_note(documents, selected_concepts, document_note_names, concept_note_names), encoding="utf-8")
    (vault / "00_Library_Report.md").write_text(_library_report_note(library), encoding="utf-8")
    (vault / "_office2md" / "export_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def _load_documents(db_path: Path) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], int]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        documents = [
            dict(row)
            for row in conn.execute(
                """
                SELECT doc_id, title, source_file, source_path, document_kind, quality_status,
                       extraction_status, output_dir
                FROM documents
                ORDER BY title, source_file, doc_id
                """
            ).fetchall()
        ]
        chunks = [
            dict(row)
            for row in conn.execute(
                """
                SELECT chunk_id, doc_id, title, text, evidence_type, locator
                FROM chunks
                ORDER BY rowid
                """
            ).fetchall()
        ]
        asset_count = int(conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0] or 0)
    chunks_by_doc: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        chunks_by_doc[chunk["doc_id"]].append(chunk)
    return documents, chunks_by_doc, asset_count


def _select_concepts(concepts: dict[str, dict[str, Any]], max_concepts: int) -> list[tuple[str, dict[str, Any]]]:
    ranked = sorted(
        concepts.items(),
        key=lambda item: (
            -float(item[1].get("weight") or 0),
            -int(item[1].get("match_count") or 0),
            normalize_concept_label(item[1].get("label") or item[0]),
        ),
    )
    return ranked[:max_concepts]


def _document_note_names(documents: list[dict[str, Any]]) -> dict[str, str]:
    used: set[str] = set()
    return {
        doc["doc_id"]: unique_note_name(doc.get("title") or doc.get("source_file") or doc["doc_id"], used, doc["doc_id"])
        for doc in documents
    }


def _concept_note_names(concepts: list[tuple[str, dict[str, Any]]]) -> dict[str, str]:
    used: set[str] = set()
    return {
        label: unique_note_name(concept.get("label") or label, used, label)
        for label, concept in concepts
    }


def _document_concepts(concepts: list[tuple[str, dict[str, Any]]]) -> dict[str, list[str]]:
    by_doc: dict[str, list[str]] = defaultdict(list)
    for label, concept in concepts:
        for doc_id in sorted(concept.get("doc_ids") or []):
            by_doc[doc_id].append(label)
    return by_doc


def _document_note(doc: dict[str, Any], chunks: list[dict[str, Any]], concept_labels: list[str], concept_note_names: dict[str, str]) -> str:
    related = [f"- [[{concept_note_names[label]}]]" for label in concept_labels if label in concept_note_names]
    preview = _document_preview(chunks)
    lines = [
        "---",
        "office2md_type: document",
        f"office2md_id: {_yaml_scalar(doc['doc_id'])}",
        f"source_file: {_yaml_scalar(doc.get('source_file') or '')}",
        f"document_kind: {_yaml_scalar(doc.get('document_kind') or '')}",
        "created_by: office2md",
        "---",
        "",
        f"# {doc.get('title') or doc.get('source_file') or doc['doc_id']}",
        "",
        "## Metadata",
        "",
        f"- Source file: {doc.get('source_file') or ''}",
        f"- Document kind: {doc.get('document_kind') or ''}",
        f"- Quality status: {doc.get('quality_status') or ''}",
        f"- Output dir: {doc.get('output_dir') or ''}",
        "",
        "## Related Concepts",
        "",
        *(related or ["_No related concepts exported._"]),
        "",
        "## Content Preview",
        "",
        preview or "_No chunk preview available._",
        "",
    ]
    return "\n".join(lines)


def _concept_note(concept: dict[str, Any], document_note_names: dict[str, str], max_evidence: int) -> str:
    doc_ids = sorted(concept.get("doc_ids") or [])
    related_docs = [f"- [[{document_note_names[doc_id]}]]" for doc_id in doc_ids if doc_id in document_note_names]
    contexts = sorted(concept.get("contexts") or [])[:max_evidence]
    lines = [
        "---",
        "office2md_type: concept",
        f"concept: {_yaml_scalar(concept.get('label') or '')}",
        f"match_count: {int(concept.get('match_count') or 0)}",
        f"document_count: {len(doc_ids)}",
        "created_by: office2md",
        "---",
        "",
        f"# {concept.get('label') or 'Concept'}",
        "",
        "## Related Documents",
        "",
        *(related_docs or ["_No related documents exported._"]),
        "",
        "## Evidence",
        "",
        *(f"- {context}" for context in contexts),
        "",
    ]
    return "\n".join(lines)


def _index_note(
    documents: list[dict[str, Any]],
    concepts: list[tuple[str, dict[str, Any]]],
    document_note_names: dict[str, str],
    concept_note_names: dict[str, str],
) -> str:
    lines = [
        "---",
        "office2md_type: obsidian_index",
        "created_by: office2md",
        "---",
        "",
        "# office2md Library Index",
        "",
        "## Documents",
        "",
    ]
    lines.extend(f"- [[{document_note_names[doc['doc_id']]}]]" for doc in documents)
    lines.extend(["", "## Concepts", ""])
    lines.extend(f"- [[{concept_note_names[label]}]]" for label, _concept in concepts)
    lines.append("")
    return "\n".join(lines)


def _library_report_note(library_path: Path) -> str:
    report = library_report(library_path)
    lines = [
        "---",
        "office2md_type: library_report",
        "created_by: office2md",
        "---",
        "",
        "# Library Report",
        "",
        f"- documents_count: {report.get('documents_count', 0)}",
        f"- chunks_count: {report.get('chunks_count', 0)}",
        f"- entities_count: {report.get('entities_count', 0)}",
        f"- noisy_chunks_count: {report.get('noisy_chunks_count', 0)}",
        f"- chunks_without_locator: {report.get('chunks_without_locator', 0)}",
        "",
        "## Document Kinds",
        "",
    ]
    for key, value in (report.get("document_kind_distribution") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Evidence Types", ""])
    for key, value in (report.get("evidence_type_distribution") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines)


def _document_preview(chunks: list[dict[str, Any]], limit: int = 1800) -> str:
    parts = []
    for chunk in chunks[:8]:
        title = chunk.get("title") or chunk.get("evidence_type") or "Chunk"
        locator = f" ({chunk['locator']})" if chunk.get("locator") else ""
        text = " ".join((chunk.get("text") or "").split())
        if text:
            parts.append(f"### {title}{locator}\n\n{text[:500]}")
    preview = "\n\n".join(parts)
    return preview[:limit].strip()


def _manifest(
    library_path: Path,
    vault_output: Path,
    documents_exported: int,
    concepts_exported: int,
    warnings: list[str],
    overwrite: bool,
    dry_run: bool,
    max_concepts: int,
    max_evidence_per_concept: int,
) -> dict[str, Any]:
    return {
        "export_type": "obsidian",
        "office2md_version": _office2md_version(),
        "library_path": str(library_path),
        "vault_output": str(vault_output),
        "documents_exported": documents_exported,
        "concepts_exported": concepts_exported,
        "warnings": warnings,
        "options": {
            "overwrite": overwrite,
            "dry_run": dry_run,
            "max_concepts": max_concepts,
            "max_evidence_per_concept": max_evidence_per_concept,
            "copy_assets": False,
        },
    }


def _planned_files(documents: list[dict[str, Any]], concepts: list[tuple[str, dict[str, Any]]]) -> dict[str, int]:
    return {
        "root_notes": 2,
        "document_notes": len(documents),
        "concept_notes": len(concepts),
        "manifest_files": 1,
    }


def _office2md_version() -> str:
    try:
        return version("office2md")
    except PackageNotFoundError:
        return "unknown"


def _empty_directory(path: Path) -> None:
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def _yaml_scalar(value: str) -> str:
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'
