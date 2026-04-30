from pathlib import Path
from typing import Dict, List
import re

from office2md.postprocess.pdf_structure import display_page_title
from office2md.postprocess.manual_structure import (
    build_section_aware_content,
    extract_toc_entries_from_pages,
)
from office2md.postprocess.office_structure import (
    build_process_development_narrative,
    hmi_translation_document_markdown,
)


def image_link(label: str, image_path: str, profile: str) -> str:
    if profile == "obsidian":
        return f"![[{image_path}]]"
    return f"![{label}]({image_path})"


def build_document_body(
    source_path: Path,
    markdown: str,
    metadata: Dict,
    profile: str,
    pages: List[Dict],
) -> str:
    if metadata["document_kind"] == "technical_drawing_pdf":
        return build_technical_drawing_body(source_path, markdown, metadata, profile, pages)
    if metadata["document_kind"] in {"manual_pdf", "functional_description_pdf", "fault_catalog_pdf"}:
        return build_manual_body(source_path, markdown, metadata, pages)
    if metadata["document_kind"] in {"process_development_presentation", "project_presentation_pptx"}:
        return build_process_development_presentation_body(source_path, markdown, metadata)
    if metadata["document_kind"] == "release_rationale_docx":
        return build_release_rationale_body(source_path, markdown, metadata)
    if metadata["document_kind"] == "hmi_translation_xlsx":
        return hmi_translation_document_markdown(source_path, markdown, metadata)

    return "\n".join(
        [
            f"# {metadata['title']}",
            "",
            "## Document Summary",
            "",
            "_No summary generated._",
            "",
            "## Key Metadata",
            "",
            f"- source_file: {metadata['source_file']}",
            f"- document_kind: {metadata['document_kind']}",
            f"- quality_status: {metadata['quality_status']}",
            f"- extraction_status: {metadata.get('extraction_status', 'text')}",
            f"- requires_ocr_or_vision: {str(metadata.get('requires_ocr_or_vision', False)).lower()}",
            f"- converter: {metadata['converter']}",
            "",
            "## Source Traceability",
            "",
            f"- source_path: {metadata['source_path']}",
            f"- checksum: {metadata['checksum']}",
            "",
            "## Content",
            "",
            markdown.strip(),
            "",
        ]
    )


def build_process_development_presentation_body(source_path: Path, markdown: str, metadata: Dict) -> str:
    extracted = metadata.get("extracted_metadata", {})
    slide_index = extracted.get("slide_index", [])
    topic_outline = extracted.get("topic_outline", [])
    batch_summary = extracted.get("batch_study_summary", [])
    narrative = extracted.get("process_development_narrative") or build_process_development_narrative(metadata, markdown)
    lines = [
        f"# {metadata['title']}",
        "",
        "## Presentation Summary",
        "",
        _presentation_summary(extracted),
        "",
        "## Key Project Metadata",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    for key in [
        "project_number",
        "project_name",
        "annual_volume",
        "production_size",
        "formula_structure",
        "technology",
        "manloc",
        "package_type",
        "batch_ids",
        "equipment",
        "process_parameters",
    ]:
        lines.append(f"| {key} | {_table_value(extracted.get(key))} |")
    lines.extend(["", "## Slide Index", "", "| Slide | Title | Topic | Visual Evidence Needed | Key Entities |", "|---|---|---|---|---|"])
    for slide in slide_index:
        lines.append(
            "| {number} | {title} | {topic} | {visual} | {entities} |".format(
                number=slide.get("slide_number", ""),
                title=slide.get("slide_title", ""),
                topic=slide.get("topic_label", ""),
                visual=str(slide.get("visual_evidence_needed", False)).lower(),
                entities=_table_value(slide.get("key_entities", [])),
            )
        )
    lines.extend(["", "## Topic Outline", ""])
    if topic_outline:
        for topic in topic_outline:
            lines.append(f"- {topic.get('topic_label')}: {topic.get('locator')}")
    else:
        lines.append("_No topic outline generated._")
    lines.extend(["", "## Process Development Narrative", ""])
    lines.extend(f"- {item}" for item in narrative)
    lines.extend(
        [
            "",
            "## Batch Study Summary",
            "",
            "| Batch ID | Batch Size | Equipment / Route | M4E Parameter | Result / Status | Confidence | Evidence Slides | Evidence Snippet |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for row in batch_summary:
        lines.append(
            "| {batch_id} | {batch_size} | {route} | {m4e} | {status} | {confidence} | {locators} | {snippet} |".format(
                batch_id=row.get("batch_id", ""),
                batch_size=row.get("batch_size", ""),
                route=row.get("equipment_process_route", ""),
                m4e=row.get("m4e_parameter", ""),
                status=row.get("result_status", ""),
                confidence=row.get("confidence", ""),
                locators=_table_value(row.get("locators") or row.get("locator", "")),
                snippet=(row.get("evidence_snippet") or "").replace("|", "/"),
            )
        )
    lines.extend(["", "## Source Traceability", "", f"- source_path: {metadata['source_path']}", f"- checksum: {metadata['checksum']}", ""])
    lines.extend(["## Slides", ""])
    for slide in slide_index:
        slide_number = slide.get("slide_number")
        slide_text = _slide_text(markdown, slide_number)
        slide_heading = slide.get("slide_title") or "Untitled Slide"
        lines.extend(
            [
                f"### {slide_heading}",
                "",
                f"Source: Slide {slide_number}",
                f"Topic: {slide.get('topic_label')}",
                f"Visual evidence needed: {str(slide.get('visual_evidence_needed', False)).lower()}",
                "",
                slide_text,
                "",
            ]
        )
    if not slide_index:
        lines.extend(["## Content", "", markdown.strip(), ""])
    return "\n".join(lines)


def build_release_rationale_body(source_path: Path, markdown: str, metadata: Dict) -> str:
    extracted = metadata.get("extracted_metadata", {})
    lines = [
        f"# {metadata['title']}",
        "",
        "## Release Summary",
        "",
        _release_summary(extracted),
        "",
        "## Key Release Metadata",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    for key in [
        "document_title",
        "project_number",
        "product_name",
        "pathfinder_mass_code",
        "manufacturing_location",
        "filling_location",
        "formula_system",
        "release_phase",
        "annual_volume",
    ]:
        lines.append(f"| {key} | {_table_value(extracted.get(key))} |")
    lines.extend(["", "## Key Process Parameters", ""])
    params = extracted.get("process_parameters") or []
    if params:
        lines.extend(f"- {item}" for item in params)
    else:
        lines.append("_No key process parameters detected._")
    lines.extend(["", "## Recommendation", "", extracted.get("recommendation") or "_No recommendation detected._", ""])
    lines.extend(["## Source Traceability", "", f"- source_path: {metadata['source_path']}", f"- checksum: {metadata['checksum']}", ""])
    lines.extend(["## Content", "", markdown.strip(), ""])
    return "\n".join(lines)


def build_manual_body(source_path: Path, markdown: str, metadata: Dict, pages: List[Dict]) -> str:
    toc_entries = metadata.get("section_outline") or extract_toc_entries_from_pages(pages)
    outline = [f"{entry['section_number']} {entry['title']}" for entry in toc_entries] or extract_section_outline(
        "\n".join(page.get("text", "") for page in pages) or markdown
    )
    title = _manual_title(metadata)
    lines = [
        f"# {title}",
        "",
        "## Document Summary",
        "",
        "_No summary generated._",
        "",
        "## Key Metadata",
        "",
        f"- source_file: {metadata['source_file']}",
        f"- document_kind: {metadata['document_kind']}",
        f"- quality_status: {metadata['quality_status']}",
        f"- extraction_status: {metadata.get('extraction_status', 'text')}",
        f"- requires_ocr_or_vision: {str(metadata.get('requires_ocr_or_vision', False)).lower()}",
        f"- converter: {metadata['converter']}",
        f"- tags: {', '.join(metadata.get('tags', []))}",
        *[f"- {key}: {value}" for key, value in metadata.get("extracted_metadata", {}).items()],
        "",
        "## Source Traceability",
        "",
        f"- source_path: {metadata['source_path']}",
        f"- checksum: {metadata['checksum']}",
        "",
        "## Revision History",
        "",
    ]
    revision_pages = [page for page in pages if page.get("semantic_title") == "Revision Overview"]
    if revision_pages:
        for page in revision_pages:
            lines.extend([f"Source page: {page.get('page_number')}", "", (page.get("text") or "").strip(), ""])
    else:
        lines.extend(["_No revision history detected._", ""])
    lines.extend(
        [
        "## Table of Contents",
        "",
        ]
    )
    if outline:
        lines.extend(f"- {item}" for item in outline)
    else:
        lines.append("_No table of contents detected._")
    lines.extend(["", "## Page Overview", ""])
    if pages:
        for page in pages:
            lines.append(f"- {display_page_title(page)}: {page.get('locator')}")
    else:
        lines.append("_No page overview available._")
    lines.extend(["", "## Section Outline", ""])
    if outline:
        lines.extend(f"- {item}" for item in outline)
    else:
        lines.append("_No section outline detected._")
    lines.extend(["", "## Content", ""])
    section_content = build_section_aware_content(pages, toc_entries)
    if section_content:
        lines.extend([section_content, ""])
    if pages:
        for page in pages:
            title = display_page_title(page)
            lines.extend(
                [
                    f"### {title}",
                    "",
                    f"Source page: {page.get('page_number')}",
                    "",
                    (page.get("text") or "").strip() or "_No text extracted for this page._",
                    "",
                ]
            )
    else:
        lines.append(markdown.strip())
    return "\n".join(lines)


def _manual_title(metadata: Dict) -> str:
    extracted = metadata.get("extracted_metadata", {})
    if metadata.get("document_kind") == "functional_description_pdf" and extracted.get("equipment_name"):
        return f"Functional Description - {extracted['equipment_name']}"
    return metadata["title"]


def extract_section_outline(text: str, limit: int = 40) -> List[str]:
    items: List[str] = []
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line or len(line) > 140:
            continue
        match = re.match(r"^(\d+(?:\.\d+)*)\s+(.+?)(?:\s+\.{2,}\s*|\s{2,}|\s+)(\d{1,4})?$", line)
        if not match:
            match = re.match(r"^(\d+(?:\.\d+)*)\s+([A-Z][A-Za-z0-9 /()_-]{2,})$", line)
        if not match:
            continue
        section = match.group(1)
        title = match.group(2).strip(" .")
        item = f"{section} {title}"
        if item not in items:
            items.append(item)
        if len(items) >= limit:
            break
    return items


def build_technical_drawing_body(
    source_path: Path,
    extracted_text: str,
    metadata: Dict,
    profile: str,
    pages: List[Dict],
) -> str:
    lines = [
        f"# {source_path.stem}",
        "",
        "## Document Summary",
        "",
        "_No summary generated._",
        "",
        "## Document Classification",
        "",
        f"- document_kind: {metadata['document_kind']}",
        f"- quality_status: {metadata['quality_status']}",
        f"- extraction_status: {metadata.get('extraction_status', 'text')}",
        f"- requires_ocr_or_vision: {str(metadata.get('requires_ocr_or_vision', False)).lower()}",
        *(
            ["- note: No text was extracted; page image preserved for visual review."]
            if metadata.get("requires_ocr_or_vision")
            else []
        ),
        "",
        "## Key Metadata",
        "",
        f"- source_file: {metadata['source_file']}",
        f"- converter: {metadata['converter']}",
        f"- tags: {', '.join(metadata.get('tags', []))}",
        "",
        "## Source Traceability",
        "",
        f"- source_path: {metadata['source_path']}",
        f"- checksum: {metadata['checksum']}",
        "",
        "## Page Index",
        "",
    ]
    drawing_index = metadata.get("drawing_index") or []
    if drawing_index:
        lines.extend(["## Drawing Index", ""])
        lines.extend(["| Page Code | Description | Type | Date | Edited By | Source |", "|---|---|---|---|---|---|"])
        for entry in drawing_index:
            lines.append(
                "| {page_code} | {desc} | {kind} | {date} | {edited} | {locator} |".format(
                    page_code=entry.get("page_code", ""),
                    desc=entry.get("page_description", ""),
                    kind=entry.get("page_type", ""),
                    date=entry.get("date", ""),
                    edited=entry.get("edited_by", ""),
                    locator=entry.get("locator", ""),
                )
            )
        lines.append("")
    if pages:
        for page in pages:
            page_number = page["page_number"]
            title = display_page_title(page)
            lines.append(f"- {title}: {page.get('locator', f'Page {page_number}')} - {page['image_path']}")
        lines.append("")
        for page in pages:
            page_number = page["page_number"]
            image_path = page["image_path"]
            title = display_page_title(page)
            lines.extend(
                [
                    f"## {title}",
                    "",
                    f"Source page: {page_number}",
                    "",
                    image_link(f"Page {page_number}", image_path, profile),
                    "",
                    "### Extracted Text",
                    "",
                    (page.get("text") or extracted_text).strip() or "_No text extracted._",
                    "",
                    "### Notes",
                    "",
                    "",
                ]
            )
    else:
        lines.extend(["No page images rendered. Re-run with --render-pdf-pages.", ""])
        lines.extend(["## Extracted Text", "", extracted_text.strip() or "_No text extracted._", ""])
    return "\n".join(lines)


def build_knowledge_json(
    metadata: Dict,
    chunks_count: int,
    assets_count: int,
    pages: List[Dict] | None = None,
    summary: str = "",
    ai: Dict | None = None,
) -> Dict:
    pages = pages or []
    image_chunks_count = metadata.get("image_chunks_count", 0)
    data = {
        "title": metadata["title"],
        "summary": summary,
        "key_metadata": {
            "source_path": metadata["source_path"],
            "checksum": metadata["checksum"],
            "converter": metadata["converter"],
            **metadata.get("extracted_metadata", {}),
        },
        "tags": metadata.get("tags", []),
        "document_kind": metadata["document_kind"],
        "quality_status": metadata["quality_status"],
        "extraction_status": metadata.get("extraction_status", "text"),
        "requires_ocr_or_vision": metadata.get("requires_ocr_or_vision", False),
        "chunks_count": chunks_count,
        "assets_count": assets_count,
        "pages_count": metadata.get("pages_count", len(pages)),
        "text_pages_count": metadata.get("text_pages_count", sum(1 for page in pages if (page.get("text") or "").strip())),
        "pages_with_text_count": metadata.get("text_pages_count", sum(1 for page in pages if (page.get("text") or "").strip())),
        "rendered_pages_count": metadata.get("rendered_pages_count", sum(1 for page in pages if page.get("image_path"))),
        "text_chunks_count": max(chunks_count - image_chunks_count, 0),
        "image_chunks_count": image_chunks_count,
        "page_chunks_count": metadata.get("page_chunks_count", 0),
        "image_only_chunks_count": metadata.get("image_only_chunks_count", image_chunks_count),
        "searchable_page_chunks_count": metadata.get("searchable_page_chunks_count", 0),
        "section_chunks_count": metadata.get("section_chunks_count", 0),
        "section_chunks_with_body_count": metadata.get("section_chunks_with_body_count", 0),
        "section_outline": metadata.get("section_outline", []),
        "slide_chunks_count": metadata.get("slide_chunks_count", 0),
        "table_chunks_count": metadata.get("table_chunks_count", 0),
        "topic_chunks_count": metadata.get("topic_chunks_count", 0),
        "batch_study_chunks_count": metadata.get("batch_study_chunks_count", 0),
        "visual_heavy_slides_count": metadata.get("visual_heavy_slides_count", 0),
        "drawing_index_count": metadata.get("drawing_index_count", 0),
        "drawing_index": metadata.get("drawing_index", []),
        "embedded_images_count": metadata.get("embedded_images_count", 0),
        "embedded_image_detected": metadata.get("embedded_image_detected", False),
        "missing_assets_count": metadata.get("missing_assets_count", 0),
        "source_file": metadata["source_file"],
    }
    for key in [
        "document_type",
        "project_number",
        "project_name",
        "product_name",
        "mass_code",
        "formula_structure",
        "formula_system",
        "annual_volume",
        "production_size",
        "manufacturing_location",
        "filling_location",
        "equipment",
        "process_parameters",
        "batch_ids",
        "slide_count",
        "slide_index",
        "topic_outline",
        "batch_study_summary",
        "process_development_narrative",
        "sheet_names",
        "table_count",
        "line",
        "source_system",
        "languages",
        "sheets_count",
        "rows_count",
        "hmi_text_rows_count",
        "unique_screen_paths_count",
        "units_found",
        "hmi_groups",
    ]:
        if key in metadata.get("extracted_metadata", {}):
            data[key] = metadata["extracted_metadata"][key]
    if ai is not None:
        data["ai"] = ai
    return data


def build_source_map(chunks: List[Dict]) -> Dict:
    return {
        chunk["chunk_id"]: {
            "source_file": chunk.get("source_file"),
            "page_number": chunk.get("page_number"),
            "image_path": chunk.get("image_path"),
            "heading_path": chunk.get("heading_path", []),
            "locator": chunk.get("locator"),
            "semantic_title": chunk.get("semantic_title"),
            "evidence_type": chunk.get("evidence_type"),
            "provenance_status": chunk.get("provenance_status"),
            "section_number": chunk.get("section_number"),
            "section_title": chunk.get("section_title"),
            "source_page_start": chunk.get("source_page_start"),
            "source_page_end": chunk.get("source_page_end"),
            "slide_number": chunk.get("slide_number"),
            "slide_title": chunk.get("slide_title"),
            "sheet_name": chunk.get("sheet_name"),
            "table_name": chunk.get("table_name"),
            "table_index": chunk.get("table_index"),
            "row_start": chunk.get("row_start"),
            "row_end": chunk.get("row_end"),
            "row_number": chunk.get("row_number"),
            "drawing_index_entry": chunk.get("drawing_index_entry"),
            "topic_label": chunk.get("topic_label"),
            "slide_numbers": chunk.get("slide_numbers"),
            "batch_id": chunk.get("batch_id"),
            "group_path": chunk.get("group_path"),
            "hmi_path_tail": chunk.get("hmi_path_tail"),
            "english_text": chunk.get("english_text"),
            "chinese_text": chunk.get("chinese_text"),
            "unit": chunk.get("unit"),
            "locators": chunk.get("locators"),
            "evidence_slides": chunk.get("evidence_slides"),
            "confidence": chunk.get("confidence"),
            "evidence_snippet": chunk.get("evidence_snippet"),
            "visual_evidence_needed": chunk.get("visual_evidence_needed"),
            "requires_image_export_later": chunk.get("requires_image_export_later"),
        }
        for chunk in chunks
    }


def enrich_chunks(
    chunks: List[Dict],
    doc_id: str,
    source_path: Path,
    document_kind: str,
    quality_status: str,
    tags: List[str],
) -> List[Dict]:
    enriched = []
    for chunk in chunks:
        item = dict(chunk)
        page_number = item.get("page_number") or item.get("page_start")
        image_path = item.get("image_path")
        item.update(
            {
                "doc_id": doc_id,
                "source_path": str(source_path),
                "document_kind": document_kind,
                "quality_status": quality_status,
                "page_number": page_number,
                "image_path": image_path,
                "tags": tags,
                "evidence_type": _evidence_type(item),
                "provenance_status": item.get("provenance_status") or ("page_text" if page_number else "raw_markdown"),
            }
        )
        enriched.append(item)
    return enriched


def _evidence_type(chunk: Dict) -> str:
    if chunk.get("evidence_type") in {
        "section",
        "slide",
        "table",
        "table_section",
        "topic",
        "batch_study",
        "drawing_index",
        "hmi_translation_table",
        "hmi_translation_group",
        "hmi_translation_row",
    }:
        return chunk["evidence_type"]
    if chunk.get("image_path"):
        if (chunk.get("page_text") or "").strip() or int(chunk.get("page_text_char_count") or 0) > 0:
            return "page"
        return "image"
    if chunk.get("page_start") or chunk.get("page_number"):
        if (chunk.get("page_text") or "").strip() or int(chunk.get("page_text_char_count") or 0) > 0:
            return "text_page"
        return "page"
    if chunk.get("heading_path") == ["Key Metadata"]:
        return "metadata"
    return "text"


def _presentation_summary(extracted: Dict) -> str:
    project = extracted.get("project_name") or "Daily Rescue Eye Serum"
    project_number = extracted.get("project_number") or "PN77563"
    formula = extracted.get("formula_structure") or "W/O"
    return (
        f"Project: {project} / PN{str(project_number).removeprefix('PN')}. "
        f"Formula: {formula} / high internal water phase. "
        "Key process concern: viscosity is strongly linked to M4E venturi speed and timer. "
        "Scale-up challenge: Symex has recirculation / M4E connection challenges. "
        "Current direction: M4E / Lee Trimix / Oevel route based on batch evidence."
    )


def _release_summary(extracted: Dict) -> str:
    product = extracted.get("product_name") or extracted.get("document_title") or "release rationale"
    formula = extracted.get("formula_system") or "formula system not detected"
    recommendation = extracted.get("recommendation") or "recommendation not detected"
    return f"{product} is summarized as a {formula} release package; {recommendation}."


def _table_value(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return "" if value is None else str(value)


def _slide_text(markdown: str, slide_number: int | None) -> str:
    if slide_number is None:
        return ""
    pattern = rf"<!--\s*Slide number:\s*{slide_number}\s*-->(.*?)(?=<!--\s*Slide number:|\Z)"
    match = re.search(pattern, markdown, flags=re.DOTALL)
    return match.group(1).strip() if match else ""
