import re
from typing import Dict, List


def extract_drawing_index(pages: List[Dict], limit: int = 200) -> List[Dict]:
    entries: List[Dict] = []
    for page in pages:
        text = page.get("text") or ""
        if "table of contents" not in text.lower():
            continue
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        lines = [line for line in lines if line]
        start = 0
        for index, line in enumerate(lines):
            if line.lower() == "page" and index + 4 < len(lines):
                start = index + 1
                break
        index = start
        while index + 4 < len(lines):
            page_code = lines[index]
            edited_by = lines[index + 1]
            page_description = lines[index + 2]
            page_type = lines[index + 3]
            date = lines[index + 4]
            if _looks_like_page_code(page_code) and _looks_like_date(date):
                entries.append(
                    {
                        "page_code": page_code,
                        "edited_by": edited_by,
                        "page_description": page_description,
                        "page_type": page_type,
                        "date": date,
                        "source_page": page.get("page_number"),
                        "locator": f"Table of Contents / {page.get('locator') or 'Page ' + str(page.get('page_number'))}",
                    }
                )
                if len(entries) >= limit:
                    return entries
                index += 5
                continue
            index += 1
    return entries


def build_drawing_index_chunks(entries: List[Dict], source_file: str, doc_slug: str, existing_count: int) -> List[Dict]:
    chunks = []
    for entry in entries:
        text = "\n".join(
            [
                f"Drawing index: {entry['page_description']}",
                f"Page code: {entry['page_code']}",
                f"Page type: {entry['page_type']}",
                f"Edited by: {entry['edited_by']}",
                f"Date: {entry['date']}",
            ]
        )
        chunks.append(
            {
                "chunk_id": f"{doc_slug}_{existing_count + len(chunks) + 1:04d}",
                "source_file": source_file,
                "heading_path": ["Drawing Index", entry["page_description"]],
                "text": text,
                "char_count": len(text),
                "evidence_type": "drawing_index",
                "provenance_status": "drawing_index_from_toc",
                "page_number": entry.get("source_page"),
                "locator": entry.get("locator"),
                "drawing_index_entry": entry,
            }
        )
    return chunks


def _looks_like_page_code(value: str) -> bool:
    return value.startswith("/") or value.startswith("+")


def _looks_like_date(value: str) -> bool:
    return bool(re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", value))
