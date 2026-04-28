import re
from typing import Dict, List


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def chunk_markdown(markdown: str, source_file: str, doc_slug: str, max_chars: int = 1600) -> List[Dict]:
    sections = []
    heading_stack: List[str] = []
    current_lines: List[str] = []
    current_headings: List[str] = []

    def flush() -> None:
        text = "\n".join(current_lines).strip()
        if text:
            sections.append((list(current_headings), text))

    for line in markdown.splitlines():
        match = HEADING_RE.match(line)
        if match:
            flush()
            level = len(match.group(1))
            title = match.group(2).strip()
            heading_stack[:] = heading_stack[: level - 1]
            heading_stack.append(title)
            current_headings = list(heading_stack)
            current_lines = [line]
        else:
            current_lines.append(line)
    flush()

    if not sections:
        body = markdown.strip()
        sections = [([], body)] if body else []

    chunks = []
    for headings, text in sections:
        for part in _split_text(text, max_chars=max_chars):
            if not part.strip():
                continue
            chunk_id = f"{doc_slug}_{len(chunks) + 1:04d}"
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "source_file": source_file,
                    "heading_path": headings,
                    "text": part.strip(),
                    "char_count": len(part.strip()),
                }
            )
    return chunks


def chunk_pdf_pages(
    pages: List[Dict],
    source_file: str,
    doc_slug: str,
    extracted_text: str = "",
) -> List[Dict]:
    chunks: List[Dict] = []
    for page in pages:
        page_number = page["page_number"]
        image_path = page.get("image_path")
        locator = page.get("locator") or f"Page {page_number}"
        semantic_title = page.get("semantic_title")
        heading_title = semantic_title or "Untitled Source Page"
        page_text = (page.get("text") or "").strip() or extracted_text.strip()
        clipped_text = _clip_text(page_text, max_chars=2500)
        text_parts = [
            heading_title,
            f"Locator: {locator}",
        ]
        if image_path:
            text_parts.append(f"Image: {image_path}")
        if clipped_text:
            text_parts.extend(["Extracted text:", clipped_text])
        text = "\n".join(text_parts)
        chunks.append(
            {
                "chunk_id": f"{doc_slug}_{len(chunks) + 1:04d}",
                "source_file": source_file,
                "page_number": page_number,
                "source_page": page_number,
                "locator": locator,
                "semantic_title": semantic_title,
                "page_start": page_number,
                "page_end": page_number,
                "heading_path": [heading_title],
                "text": text,
                "image_path": image_path,
                "page_text": clipped_text,
                "page_text_char_count": len(clipped_text),
                "provenance_status": "page_text" if (page.get("text") or "").strip() else "page_image_only",
                "char_count": len(text),
            }
        )
    if not chunks and extracted_text.strip():
        text = extracted_text.strip()
        chunks.append(
            {
                "chunk_id": f"{doc_slug}_0001",
                "source_file": source_file,
                "heading_path": ["Extracted text"],
                "text": text[:1600],
                "page_number": None,
                "locator": None,
                "semantic_title": None,
                "image_path": None,
                "provenance_status": "raw_markdown",
                "char_count": min(len(text), 1600),
            }
        )
    return chunks


def _clip_text(text: str, max_chars: int) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 3].rstrip() + "..."


def _split_text(text: str, max_chars: int) -> List[str]:
    if len(text) <= max_chars:
        return [text]

    paragraphs = re.split(r"\n\s*\n", text)
    parts: List[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            parts.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            parts.extend(paragraph[i : i + max_chars] for i in range(0, len(paragraph), max_chars))
            current = ""
    if current:
        parts.append(current)
    return parts
