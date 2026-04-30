import re
from pathlib import Path
from typing import Dict, List


TECHNICAL_DRAWING_KEYWORDS = {
    "wiring diagram",
    "schematic",
    "p&id",
    "p and id",
    "piping and instrumentation diagram",
}

FILENAME_DOCUMENT_KIND_RULES = [
    ("manual_pdf", ["operating manual", "operation manual"]),
    ("functional_description_pdf", ["functional description"]),
    ("fault_catalog_pdf", ["faults and measures", "fault catalog"]),
    ("technical_drawing_pdf", ["wiring diagram", "piping and instrumentation", "p&id", "p and id"]),
    ("certificate_pdf", ["egcon", "atex", "certificate", "declaration of conformity", "conformity"]),
    ("manual_pdf", ["manual", "montage", "installation", "anleitung"]),
    ("project_book_pdf", ["project book"]),
    ("report_pdf", ["report", "protokoll", "protocol", "quote", "price"]),
    ("datasheet_pdf", ["datasheet", "data sheet", "datenblatt"]),
    ("datasheet_pdf", [" data"]),
]

CONTENT_DOCUMENT_KIND_RULES = [
    ("manual_pdf", ["operating manual", "operation manual"]),
    ("functional_description_pdf", ["functional description"]),
    ("fault_catalog_pdf", ["faults and measures", "fault messages", "measures catalog", "fault catalog"]),
    ("technical_drawing_pdf", ["wiring diagram", "schematic", "p&id", "p and id", "piping and instrumentation diagram"]),
    ("datasheet_pdf", ["technical data", "datasheet", "data sheet"]),
]

PARENT_FOLDER_DOCUMENT_KIND_RULES = [
    ("technical_drawing_pdf", ["piping and instrumentation diagram", "wiring diagram"]),
]


SEMANTIC_TITLE_RULES = [
    ("terminal line-up", "Terminal Line-up Diagram"),
    ("terminal lineup", "Terminal Line-up Diagram"),
    ("general project information", "General Project Information"),
    ("cover sheet", "Cover Sheet"),
    ("enclosure legend", "Enclosure Legend"),
    ("schematic multi-line", "Schematic Multi-line"),
    ("power supply", "Power Supply"),
    ("valve station", "Valve Station"),
    ("panel layout", "Panel Layout"),
    ("parts list", "Parts List"),
    ("cable overview", "Cable Overview"),
    ("terminal diagram", "Terminal Diagram"),
    ("cover", "Cover Sheet"),
    ("terminal", "Terminal Diagram"),
    ("plc", "PLC"),
    ("wiring", "Wiring Diagram"),
    ("schematic", "Schematic"),
    ("cable", "Cable Overview"),
]


def classify_document_kind(path: Path, markdown: str) -> str:
    if path.suffix.lower() != ".pdf":
        from office2md.postprocess.office_structure import classify_office_document_kind

        return classify_office_document_kind(path, markdown)

    filename_text = _normalize_classification_text(path.name)
    stem_text = _normalize_classification_text(path.stem)
    parent_text = _normalize_classification_text(" ".join(part for part in path.parent.parts))
    content_text = _normalize_classification_text(markdown)

    for source_text in (filename_text, stem_text):
        document_kind = _match_document_kind(source_text, FILENAME_DOCUMENT_KIND_RULES)
        if document_kind:
            return document_kind

    document_kind = _match_document_kind(parent_text, PARENT_FOLDER_DOCUMENT_KIND_RULES)
    if document_kind:
        return document_kind

    document_kind = _match_document_kind(content_text, CONTENT_DOCUMENT_KIND_RULES)
    if document_kind:
        return document_kind

    document_kind = classify_obvious_pdf_subtype(path, markdown)
    if document_kind:
        return document_kind

    return "generic_pdf"


def classify_obvious_pdf_subtype(path: Path, markdown: str = "") -> str | None:
    if path.suffix.lower() != ".pdf":
        return None
    filename_text = _normalize_classification_text(path.name)
    stem_text = _normalize_classification_text(path.stem)
    content_text = _normalize_classification_text(markdown[:4000])
    filename_kind = _match_document_kind(f"{filename_text} {stem_text}", FILENAME_DOCUMENT_KIND_RULES)
    if filename_kind:
        return filename_kind
    content_kind = _match_document_kind(content_text, CONTENT_DOCUMENT_KIND_RULES)
    if content_kind:
        return content_kind
    filename_tokens = f"{filename_text} {stem_text}"
    if re.search(r"(^|\s)(\d{6,}|fbs\d|phoenix|block|eaton|pfannenberg|lapp|helukabel|insys|abb|st)(\s|$)", filename_tokens):
        return "component_document_pdf"
    return None


def _match_document_kind(text: str, rules: List[tuple[str, List[str]]]) -> str | None:
    for document_kind, needles in rules:
        if any(needle in text for needle in needles):
            return document_kind
    return None


def _normalize_classification_text(value: str) -> str:
    return value.lower().replace("_", " ").replace("-", " ")


def has_headings(markdown: str) -> bool:
    return any(line.lstrip().startswith("#") for line in markdown.splitlines())


def is_empty_document_json(raw_json: Dict | None) -> bool:
    if not raw_json:
        return True
    return not raw_json.get("pages") and not raw_json.get("elements")


def determine_quality_status(
    path: Path,
    markdown: str,
    fallback_used: bool,
    raw_json: Dict | None,
) -> str:
    if path.suffix.lower() == ".pdf" and (
        not has_headings(markdown) or fallback_used or is_empty_document_json(raw_json)
    ):
        return "low_structure"
    return "ok"


def render_pdf_pages(path: Path, assets_dir: Path, max_pages: int) -> List[Dict]:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for --render-pdf-pages. Install PyMuPDF.") from exc

    pages: List[Dict] = []
    assets_dir.mkdir(parents=True, exist_ok=True)
    with fitz.open(path) as document:
        limit = min(len(document), max(0, max_pages))
        for index in range(limit):
            page = document.load_page(index)
            image_name = f"page_{index + 1:03d}.png"
            image_path = assets_dir / image_name
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            pixmap.save(image_path)
            page_text = page.get_text("text") or ""
            pages.append(
                {
                    "page_number": index + 1,
                    "source_page": index + 1,
                    "locator": f"Page {index + 1}",
                    "semantic_title": None,
                    "image_path": f"assets/{image_name}",
                    "text": page_text,
                    "text_char_count": len(page_text),
                    "width": pixmap.width,
                    "height": pixmap.height,
                }
            )
    return pages


def extract_pdf_text_pages(path: Path, max_pages: int | None = None) -> List[Dict]:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF page text extraction. Install PyMuPDF.") from exc

    pages: List[Dict] = []
    with fitz.open(path) as document:
        limit = len(document) if max_pages is None else min(len(document), max(0, max_pages))
        for index in range(limit):
            page = document.load_page(index)
            page_text = page.get_text("text") or ""
            pages.append(
                {
                    "page_number": index + 1,
                    "source_page": index + 1,
                    "locator": f"Page {index + 1}",
                    "semantic_title": None,
                    "image_path": None,
                    "text": page_text,
                    "text_char_count": len(page_text),
                }
            )
    return pages


def merge_pdf_pages(text_pages: List[Dict], rendered_pages: List[Dict]) -> List[Dict]:
    merged = {page["page_number"]: dict(page) for page in text_pages}
    for rendered in rendered_pages:
        page_number = rendered["page_number"]
        item = merged.get(page_number, {})
        for key, value in rendered.items():
            if value is None:
                continue
            if key in {"text", "text_char_count", "semantic_title"} and item.get("text"):
                continue
            item[key] = value
        if not item.get("text") and rendered.get("text"):
            item["text"] = rendered.get("text", "")
            item["text_char_count"] = len(item["text"])
        merged[page_number] = item
    return [merged[key] for key in sorted(merged)]


def build_pdf_document_json(source_file: str, engine: str, pages: List[Dict], raw_json: Dict | None) -> Dict:
    base = raw_json or {}
    existing_pages = base.get("pages") or []
    final_pages = pages or existing_pages
    return {
        "source_file": source_file,
        "engine": engine,
        "pages_count": len(final_pages),
        "text_pages_count": sum(1 for page in final_pages if (page.get("text") or "").strip()),
        "rendered_pages_count": sum(1 for page in final_pages if page.get("image_path")),
        "pages": final_pages,
        "elements": base.get("elements") or [],
    }


def enrich_page_semantics(pages: List[Dict], extracted_text: str = "") -> List[Dict]:
    document_inferred = infer_semantic_title(extracted_text)
    enriched = []
    for index, page in enumerate(pages):
        item = dict(page)
        page_number = item.get("page_number") or item.get("source_page")
        page_text = item.get("text") or ""
        item["page_number"] = page_number
        item["source_page"] = page_number
        item["locator"] = item.get("locator") or f"Page {page_number}"
        item["text"] = page_text
        item["text_char_count"] = item.get("text_char_count", len(page_text))
        # Without page-level text, a document-level inferred title is only safe for the first page.
        page_inferred = infer_semantic_title(page_text) if page_text.strip() else None
        item["semantic_title"] = item.get("semantic_title") or page_inferred or (
            document_inferred if index == 0 else None
        )
        enriched.append(item)
    return enriched


def infer_semantic_title(text: str) -> str | None:
    normalized = text.lower()
    if _looks_like_title_page(normalized):
        return "Title Page"
    if _looks_like_table_of_contents(normalized):
        return "Table of Contents"
    if _looks_like_revision_overview(normalized):
        return "Revision Overview"
    for needle, title in SEMANTIC_TITLE_RULES:
        if needle in normalized:
            return title
    return None


def display_page_title(page: Dict) -> str:
    return page.get("semantic_title") or "Untitled Source Page"


def _looks_like_title_page(text: str) -> bool:
    markers = ["functional description", "production mixer system", "manufacturer", "customer", "year built"]
    if "operating manual" in text and ("machine no" in text or "order no" in text or "symex gmbh" in text):
        return True
    return sum(1 for marker in markers if marker in text) >= 2


def _looks_like_revision_overview(text: str) -> bool:
    markers = ["revision history", "revision overview", "revision table"]
    return any(marker in text for marker in markers)


def _looks_like_table_of_contents(text: str) -> bool:
    if "table of contents" in text:
        return True
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    toc_like = 0
    for line in lines:
        if len(line) > 120:
            continue
        has_section = bool(__import__("re").match(r"^\d+(?:\.\d+)*\s+\S+", line))
        has_page = bool(__import__("re").search(r"\s\d{1,4}$", line))
        has_dots = "..." in line or ". . ." in line
        if has_section and (has_page or has_dots):
            toc_like += 1
    return toc_like >= 3
