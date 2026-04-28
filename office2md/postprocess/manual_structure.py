import re
from typing import Dict, List


MANUAL_KINDS = {"manual_pdf", "functional_description_pdf", "fault_catalog_pdf"}


def extract_title_page_metadata(pages: List[Dict]) -> Dict[str, str]:
    if not pages:
        return {}
    text = pages[0].get("text", "")
    return {
        key: value
        for key, value in {
            "manufacturer": _field_after_label(text, "Manufacturer"),
            "equipment_name": _equipment_name(text),
            "symex_number": _field_after_label(text, "Symex no.") or _field_after_label(text, "Machine No./Order no."),
            "customer": _field_after_label(text, "Customer"),
            "year_built": _field_after_label(text, "Year built") or _regex_first(text, r"\b(20\d{2})\b"),
            "issue": _field_after_label(text, "Issue"),
            "revision": _field_after_label(text, "Revision") or _regex_first(text, r"\b(Rev\.\s*\d+(?:\.\d+)?)\b"),
        }.items()
        if value
    }


def extract_toc_entries_from_pages(pages: List[Dict], limit: int = 200) -> List[Dict]:
    entries: List[Dict] = []
    seen = set()
    for page in pages:
        lines = [_clean_line(line) for line in (page.get("text") or "").splitlines()]
        lines = [line for line in lines if line]
        for index, line in enumerate(lines):
            parsed = _parse_toc_line(line)
            if not parsed and _is_section_number(line) and index + 1 < len(lines):
                parsed = _parse_toc_line(f"{line} {lines[index + 1]}")
            if not parsed:
                continue
            key = parsed["section_number"]
            if key in seen:
                continue
            seen.add(key)
            parsed.update(
                {
                    "level": parsed["section_number"].count(".") + 1,
                    "toc_page": page.get("page_number"),
                }
            )
            entries.append(parsed)
            if len(entries) >= limit:
                return entries
    return entries


def build_section_aware_content(pages: List[Dict], toc_entries: List[Dict]) -> str:
    entry_map = {entry["section_number"]: entry for entry in toc_entries}
    lines: List[str] = []
    emitted = set()
    for entry in toc_entries:
        hashes = "#" * min(entry["level"] + 1, 6)
        section_label = f"{entry['section_number']} {entry['title']}"
        lines.extend(
            [
                f"{hashes} {section_label}",
                "",
                f"Source page: {entry.get('page_hint')}",
                "",
            ]
        )
        emitted.add(entry["section_number"])
    for page in pages:
        if page.get("semantic_title") == "Table of Contents" or "table of contents" in (page.get("text") or "").lower():
            continue
        page_number = page.get("page_number")
        page_lines = [_clean_line(line) for line in (page.get("text") or "").splitlines()]
        page_lines = [line for line in page_lines if line]
        for index, line in enumerate(page_lines):
            heading = _parse_body_heading(line, entry_map)
            if not heading and _is_section_number(line) and index + 1 < len(page_lines):
                heading = _parse_body_heading(f"{line} {page_lines[index + 1]}", entry_map)
            if heading:
                if heading["section_number"] in emitted:
                    continue
                emitted.add(heading["section_number"])
                hashes = "#" * min(heading["level"] + 1, 6)
                lines.extend(
                    [
                        f"{hashes} {heading['section_number']} {heading['title']}",
                        "",
                        f"Source page: {page_number}",
                        "",
                    ]
                )
    return "\n".join(lines).strip()


def build_section_chunks(
    pages: List[Dict],
    source_file: str,
    doc_slug: str,
    existing_count: int,
    toc_entries: List[Dict],
) -> List[Dict]:
    entry_map = {entry["section_number"]: entry for entry in toc_entries}
    toc_pages = {entry.get("toc_page") for entry in toc_entries if entry.get("toc_page") is not None}
    chunks: List[Dict] = []
    seen = set()
    for page in pages:
        if page.get("page_number") in toc_pages:
            continue
        if page.get("semantic_title") == "Table of Contents" or "table of contents" in (page.get("text") or "").lower():
            continue
        page_number = page.get("page_number")
        page_text = (page.get("text") or "").strip()
        if not page_text:
            continue
        page_lines = [_clean_line(line) for line in page_text.splitlines()]
        page_lines = [line for line in page_lines if line]
        for index, line in enumerate(page_lines):
            heading = _parse_body_heading(line, entry_map)
            if not heading and _is_section_number(line) and index + 1 < len(page_lines):
                heading = _parse_body_heading(f"{line} {page_lines[index + 1]}", entry_map)
            if not heading or heading["section_number"] in seen:
                continue
            seen.add(heading["section_number"])
            text = _section_text(page_lines, index, heading, page_number)
            chunks.append(
                {
                    "chunk_id": f"{doc_slug}_{existing_count + len(chunks) + 1:04d}",
                    "source_file": source_file,
                    "heading_path": [f"{heading['section_number']} {heading['title']}"],
                    "text": text,
                    "char_count": len(text),
                    "page_number": page_number,
                    "source_page": page_number,
                    "locator": page.get("locator") or f"Page {page_number}",
                    "semantic_title": f"{heading['section_number']} {heading['title']}",
                    "page_start": page_number,
                    "page_end": None,
                    "source_page_start": page_number,
                    "source_page_end": None,
                    "section_number": heading["section_number"],
                    "section_title": heading["title"],
                    "evidence_type": "section",
                    "provenance_status": "section_from_page_text",
                }
            )
    return chunks


def _field_after_label(text: str, label: str) -> str:
    lines = [_clean_line(line) for line in text.splitlines()]
    if label.lower().rstrip(":") == "manufacturer" and "symex gmbh & co. kg" in text.lower():
        return "symex GmbH & Co. KG"
    for index, line in enumerate(lines):
        if line.lower().rstrip(":") != label.lower().rstrip(":"):
            continue
        for candidate in lines[index + 1 : index + 5]:
            if candidate and not _looks_like_label(candidate):
                return _fix_text(candidate)
    match = re.search(rf"{re.escape(label)}\s*:?\s*(.+)", text, flags=re.IGNORECASE)
    return _fix_text(match.group(1).strip()) if match else ""


def _equipment_name(text: str) -> str:
    normalized = " ".join(_clean_line(line) for line in text.splitlines())
    if "Production Mixer System" in normalized and "CML 125" in normalized:
        return "Production Mixer System CML 125"
    return _field_after_label(text, "Name")


def _parse_toc_line(line: str) -> Dict | None:
    match = re.match(r"^(\d+(?:\.\d+)*\.?)\s+(.+?)\s*\.{2,}\s*(\d{1,4})$", line)
    if not match:
        match = re.match(r"^(\d+(?:\.\d+)*\.?)\s+(.+?)\s+(\d{1,4})$", line)
    if not match:
        return None
    section_number = match.group(1).rstrip(".")
    title = _fix_title(match.group(2))
    if not title or title.lower() in {"print date", "page"}:
        return None
    return {
        "section_number": section_number,
        "title": title,
        "page_hint": int(match.group(3)),
    }


def _parse_body_heading(line: str, entry_map: Dict[str, Dict]) -> Dict | None:
    match = re.match(r"^(\d+(?:\.\d+)*\.?)\s+(.+?)\s*$", line)
    if not match:
        return None
    section_number = match.group(1).rstrip(".")
    if section_number not in entry_map:
        return None
    expected = entry_map[section_number]["title"]
    title = _fix_title(match.group(2))
    if not _similar_title(title, expected):
        return None
    return {
        "section_number": section_number,
        "title": expected,
        "level": entry_map[section_number]["level"],
    }


def _section_text(page_lines: List[str], start_index: int, heading: Dict, page_number: int) -> str:
    body = " ".join(page_lines[start_index : start_index + 24])
    body = body[:2500].rstrip()
    return "\n".join(
        [
            f"{heading['section_number']} {heading['title']}",
            f"Source page: {page_number}",
            body,
        ]
    ).strip()


def _is_section_number(line: str) -> bool:
    return bool(re.fullmatch(r"\d+(?:\.\d+)*\.?", line.strip()))


def _similar_title(value: str, expected: str) -> bool:
    left = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    right = re.sub(r"[^a-z0-9]+", " ", expected.lower()).strip()
    return left == right or left.startswith(right) or right.startswith(left)


def _clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def _fix_text(value: str) -> str:
    return value.replace("Est茅e", "Esteé").strip()


def _fix_title(value: str) -> str:
    title = re.sub(r"\s+", " ", value.strip(" ."))
    replacements = {
        "Media supply": "Media Supply",
        "Siemens touch panel": "Siemens Touch Panel",
        "Electrical Tempering": "Electrical Tempering",
        "Fault messages": "Fault Messages",
        "Secondary function": "Secondary Function",
        "System Start": "System Start",
        "System start": "System Start",
        "Main phases CML 125": "Main Phases CML 125",
        "Coaxial agitator": "Coaxial Agitator",
        "Co-Twister Homogenizer": "Co-Twister Homogenizer",
        "Pressure / Vacuum": "Pressure / Vacuum",
        "CIP-Advanced (Cleaning In Place)": "CIP-Advanced",
        "CIP-Drain": "CIP-Drain",
    }
    return replacements.get(title, title[:1].upper() + title[1:])


def _looks_like_label(value: str) -> bool:
    return value.rstrip(":").lower() in {
        "manufacturer",
        "name",
        "symex no.",
        "customer",
        "year built",
        "issue",
        "revision",
    }


def _regex_first(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else ""
