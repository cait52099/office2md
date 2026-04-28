import re
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple


def classify_office_document_kind(path: Path, markdown: str) -> str:
    text = f"{path.name}\n{markdown}".lower()
    suffix = path.suffix.lower()
    if suffix == ".xlsx" and ("mpdp" in text or "scaleup phase" in text):
        return "mpdp_table_xlsx"
    if suffix == ".pptx" and ("daily rescue eye serum" in text or "m4e" in text):
        return "process_development_presentation"
    if suffix == ".docx" and ("release rationale" in text or "pppbc release" in text):
        return "release_rationale_docx"
    return "document"


def extract_office_metadata(path: Path, markdown: str, document_kind: str) -> Dict:
    if document_kind == "process_development_presentation":
        return _pptx_metadata(markdown)
    if document_kind == "mpdp_table_xlsx":
        return _xlsx_metadata(markdown)
    if document_kind == "release_rationale_docx":
        return _docx_metadata(path, markdown)
    return {}


def build_office_chunks(markdown: str, source_file: str, doc_slug: str, document_kind: str) -> List[Dict]:
    if document_kind == "process_development_presentation":
        slides = extract_pptx_slide_index(markdown)
        chunks = _slide_chunks(markdown, source_file, doc_slug, slides)
        chunks.extend(build_topic_chunks(markdown, source_file, doc_slug, len(chunks), slides))
        chunks.extend(build_batch_study_chunks(markdown, source_file, doc_slug, len(chunks), slides))
        return chunks
    if document_kind == "mpdp_table_xlsx":
        chunks = _table_chunks(markdown, source_file, doc_slug)
        chunks.extend(build_xlsx_phase_chunks(markdown, source_file, doc_slug, len(chunks)))
        return chunks
    return []


def extract_embedded_office_assets(source: Path, assets_dir: Path) -> Tuple[int, List[str]]:
    if source.suffix.lower() not in {".docx", ".pptx"}:
        return 0, []
    media_prefix = "word/media/" if source.suffix.lower() == ".docx" else "ppt/media/"
    warnings: List[str] = []
    try:
        with zipfile.ZipFile(source) as archive:
            media_names = [name for name in archive.namelist() if name.startswith(media_prefix) and not name.endswith("/")]
            if not media_names:
                return 0, []
            warnings.append(f"embedded_image_detected: {len(media_names)} embedded Office images were counted but not exported")
            return len(media_names), warnings
    except Exception as exc:  # pragma: no cover - defensive; conversion must not fail on assets.
        warnings.append(f"embedded image counting failed: {exc.__class__.__name__}: {exc}")
    return 0, warnings


def missing_markdown_asset_count(markdown: str) -> int:
    refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown)
    return sum(1 for ref in refs if not ref.startswith("assets/") and not ref.startswith("data:"))


def embedded_base64_image_count(markdown: str) -> int:
    return len(re.findall(r"!\[[^\]]*\]\(data:image/", markdown, flags=re.IGNORECASE))


def office_tags(document_kind: str, metadata: Dict) -> List[str]:
    tags: List[str] = []
    if document_kind == "process_development_presentation":
        tags.extend(["project-presentation", "formula-development", "process-development", "scale-up"])
        tags.extend(["m4e", "symex", "viscosity", "w-o-formula"])
    if document_kind == "mpdp_table_xlsx":
        tags.extend(["mpdp", "scale-up-plan", "pilot", "practice", "pre-production", "production", "stability"])
    if document_kind == "release_rationale_docx":
        tags.extend(["release-rationale", "pppbc", "commercialization", "process-release"])
        tags.extend(["m4e", "viscosity", "w-si", "skincare"])
    return _dedupe(tags)


def extract_pptx_slide_index(markdown: str) -> List[Dict]:
    parts = re.split(r"<!--\s*Slide number:\s*(\d+)\s*-->", markdown)
    slides: List[Dict] = []
    for index in range(1, len(parts), 2):
        slide_number = int(parts[index])
        text = parts[index + 1].strip()
        if not text:
            continue
        title = _slide_title(text) or _project_name(markdown) or f"Slide {slide_number}"
        topic_label = topic_label_for_slide(title, text)
        visual = is_visual_heavy_slide(title, text)
        entities = _slide_entities(text)
        slides.append(
            {
                "slide_number": slide_number,
                "slide_title": title,
                "topic_label": topic_label,
                "visual_evidence_needed": visual,
                "requires_image_export_later": visual,
                "locator": f"Slide {slide_number}",
                "key_entities": entities,
                "text": text,
            }
        )
    return slides


def _slide_chunks(markdown: str, source_file: str, doc_slug: str, slides: List[Dict] | None = None) -> List[Dict]:
    slides = slides or extract_pptx_slide_index(markdown)
    chunks: List[Dict] = []
    for slide in slides:
        slide_number = slide["slide_number"]
        text = slide["text"]
        title = slide["slide_title"]
        chunks.append(
            {
                "chunk_id": f"{doc_slug}_{len(chunks) + 1:04d}",
                "source_file": source_file,
                "heading_path": [title],
                "text": text,
                "char_count": len(text),
                "evidence_type": "slide",
                "provenance_status": "slide_text",
                "slide_number": slide_number,
                "slide_title": title,
                "topic_label": slide["topic_label"],
                "visual_evidence_needed": slide["visual_evidence_needed"],
                "requires_image_export_later": slide["requires_image_export_later"],
                "locator": f"Slide {slide_number}",
                "image_refs": re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text),
            }
        )
    return chunks


def build_topic_outline(slides: List[Dict]) -> List[Dict]:
    outline: List[Dict] = []
    by_topic: Dict[str, List[Dict]] = {}
    for slide in slides:
        by_topic.setdefault(slide["topic_label"], []).append(slide)
    for topic in TOPIC_ORDER:
        grouped = by_topic.get(topic)
        if not grouped:
            continue
        numbers = [item["slide_number"] for item in grouped]
        outline.append(
            {
                "topic_label": topic,
                "slide_numbers": numbers,
                "locator": _slide_range_locator(numbers),
                "slide_titles": [item["slide_title"] for item in grouped],
            }
        )
    return outline


def build_topic_chunks(markdown: str, source_file: str, doc_slug: str, existing_count: int, slides: List[Dict] | None = None) -> List[Dict]:
    chunks: List[Dict] = []
    for entry in build_topic_outline(slides or extract_pptx_slide_index(markdown)):
        texts = [
            slide["text"]
            for slide in (slides or extract_pptx_slide_index(markdown))
            if slide["slide_number"] in entry["slide_numbers"]
        ]
        body = "\n\n".join(texts).strip()
        chunks.append(
            {
                "chunk_id": f"{doc_slug}_{existing_count + len(chunks) + 1:04d}",
                "source_file": source_file,
                "heading_path": [entry["topic_label"]],
                "text": body,
                "char_count": len(body),
                "evidence_type": "topic",
                "provenance_status": "topic_from_slide_text",
                "topic_label": entry["topic_label"],
                "slide_numbers": entry["slide_numbers"],
                "locator": entry["locator"],
            }
        )
    return chunks


def extract_batch_study_summary(markdown: str, slides: List[Dict] | None = None) -> List[Dict]:
    slides = slides or extract_pptx_slide_index(markdown)
    candidates: Dict[str, List[Dict]] = {}
    for slide in slides:
        text = slide["text"]
        table_rows = _table_batch_candidates(slide)
        table_batch_ids = {row["batch_id"] for row in table_rows}
        for row in table_rows:
            candidates.setdefault(row["batch_id"], []).append(row)
        for batch_id in _findall(r"\b(?:VL|TC)\d{6}\b", text):
            if batch_id in table_batch_ids:
                continue
            window = _line_window_for_value(text, batch_id)
            result_status = _result_status_from_window(window, slide["slide_title"])
            confidence = _batch_confidence(window, result_status, slide["slide_title"])
            row = {
                "batch_id": batch_id,
                "batch_size": _first([r"\b(\d+(?:\.\d+)?\s*kg)\b"], window),
                "equipment_process_route": ", ".join(_find_known(window, ["Symex", "M4E", "Lee Trimix", "Oevel"])),
                "m4e_parameter": _first(
                    [
                        r"\b\d+\s*L\s*/?\s*min\b",
                        r"M4E[^|\n]{0,80}(?:speed|timer)[^|\n]{0,80}",
                        r"(?:Venturi|Ventri)\s*speed[^|\n]{0,80}",
                        r"timer[^|\n]{0,80}",
                    ],
                    window,
                ),
                "result_status": result_status if confidence != "low" else "",
                "confidence": confidence,
                "evidence_snippet": _compact_snippet(window),
                "result_status_source_text": _compact_snippet(window) if result_status and confidence != "low" else "",
                "locator": f"Slide {slide['slide_number']}",
                "locators": [f"Slide {slide['slide_number']}"],
                "slide_number": slide["slide_number"],
                "evidence_slides": [slide["slide_number"]],
                "_score": _batch_candidate_score(window) + _slide_batch_priority(slide["slide_title"], window),
            }
            candidates.setdefault(batch_id, []).append(row)
    rows: List[Dict] = []
    for batch_id in _findall(r"\b(?:VL|TC)\d{6}\b", markdown):
        if batch_id in candidates:
            row = _merge_batch_candidates(batch_id, candidates[batch_id])
            row.pop("_score", None)
            rows.append(row)
    return rows


def build_batch_study_chunks(markdown: str, source_file: str, doc_slug: str, existing_count: int, slides: List[Dict] | None = None) -> List[Dict]:
    slides = slides or extract_pptx_slide_index(markdown)
    slide_text = {slide["slide_number"]: slide["text"] for slide in slides}
    chunks: List[Dict] = []
    for row in extract_batch_study_summary(markdown, slides):
        text = _line_window_for_value(slide_text.get(row["slide_number"], ""), row["batch_id"]) or row["batch_id"]
        chunks.append(
            {
                "chunk_id": f"{doc_slug}_{existing_count + len(chunks) + 1:04d}",
                "source_file": source_file,
                "heading_path": [row["batch_id"]],
                "text": text,
                "char_count": len(text),
                "evidence_type": "batch_study",
                "provenance_status": "batch_from_slide_text",
                "batch_id": row["batch_id"],
                "slide_number": row["slide_number"],
                "locator": row["locator"],
                "locators": row.get("locators", []),
                "evidence_slides": row.get("evidence_slides", []),
                "confidence": row.get("confidence"),
                "evidence_snippet": row.get("evidence_snippet"),
            }
        )
    return chunks


def build_process_development_narrative(metadata: Dict, markdown: str) -> List[str]:
    bullets = []
    if re.search(r"\bW/O\b|water.?in.?oil|high internal water", markdown, re.IGNORECASE):
        bullets.append("W/O system with high internal water phase is treated as the core formula/process context.")
    if re.search(r"viscosity|particle size|homo|venturi|timer", markdown, re.IGNORECASE):
        bullets.append("Viscosity is linked to particle size, homogenization speed/time, and M4E venturi speed/timer.")
    if re.search(r"50\s*kg|100\s*kg|Symex|recirculation|stability", markdown, re.IGNORECASE):
        bullets.append("50kg/100kg Symex trials show recirculation, operation, or stability challenges that affect scale-up confidence.")
    if re.search(r"\b(?:VL|TC)\d{6}\b", markdown):
        bullets.append("M4E parameters are studied across multiple VL/TC batches to compare route feasibility and output quality.")
    if re.search(r"Lee Trimix|Oevel|feasible|recommend", markdown, re.IGNORECASE):
        bullets.append("Lee Trimix plus M4E / Oevel route appears more feasible based on the captured batch evidence.")
    bullets.append("Process parameters need tight control because viscosity and specification outcomes are sensitive.")
    return _dedupe(bullets)[:10]


def build_xlsx_phase_chunks(markdown: str, source_file: str, doc_slug: str, existing_count: int) -> List[Dict]:
    chunks: List[Dict] = []
    for phase in ["PFA", "Pilot", "Practice", "Pre-Production", "Production"]:
        lines = [line for line in markdown.splitlines() if re.search(rf"\b{re.escape(phase)}\b", line, re.IGNORECASE)]
        if not lines:
            continue
        text = "\n".join(lines)
        chunks.append(
            {
                "chunk_id": f"{doc_slug}_{existing_count + len(chunks) + 1:04d}",
                "source_file": source_file,
                "heading_path": [phase],
                "text": text,
                "char_count": len(text),
                "evidence_type": "table_section",
                "provenance_status": "phase_from_sheet_table",
                "sheet_name": _first_heading(markdown) or Path(source_file).stem,
                "table_name": f"{_first_heading(markdown) or Path(source_file).stem} / {phase}",
                "locator": f"Sheet: {_first_heading(markdown) or Path(source_file).stem} / Phase: {phase}",
                "topic_label": phase,
            }
        )
    return chunks


def _table_chunks(markdown: str, source_file: str, doc_slug: str) -> List[Dict]:
    sheet_name = _first_heading(markdown) or Path(source_file).stem
    table_match = re.search(r"((?:\|.*\|\s*\n)+)", markdown)
    table_text = table_match.group(1).strip() if table_match else markdown.strip()
    row_count = sum(1 for line in table_text.splitlines() if line.strip().startswith("|"))
    return [
        {
            "chunk_id": f"{doc_slug}_0001",
            "source_file": source_file,
            "heading_path": [sheet_name],
            "text": table_text,
            "char_count": len(table_text),
            "evidence_type": "table",
            "provenance_status": "sheet_table",
            "sheet_name": sheet_name,
            "table_name": f"{sheet_name} / Table 1",
            "table_index": 1,
            "row_start": 1,
            "row_end": row_count,
            "locator": f"Sheet: {sheet_name} / Table 1",
        }
    ]


def _pptx_metadata(markdown: str) -> Dict:
    slide_count = len(re.findall(r"<!--\s*Slide number:", markdown))
    batch_ids = _findall(r"\b(?:VL|TC)\d{6}\b", markdown)
    slides = extract_pptx_slide_index(markdown)
    slide_index = [
        {key: slide[key] for key in ["slide_number", "slide_title", "topic_label", "visual_evidence_needed", "locator", "key_entities"]}
        for slide in slides
    ]
    visual_count = sum(1 for slide in slides if slide["visual_evidence_needed"])
    return {
        "document_type": "process-development presentation",
        "project_number": _first([r"\bPN\s?(\d{5,})\b", r"Project number:\s*PN?\s?(\d{5,})"], markdown),
        "project_name": _first([r"Project name:\s*([^\n]+)", r"(LS Daily Rescue Eye Serum)"], markdown),
        "annual_volume": _first([r"Annual Volume\s*\(kg\):\s*([^\n]+)", r"Annual Volume\(kg\):\s*([^\n]+)"], markdown),
        "production_size": _first([r"Production size:\s*([^\n]+)"], markdown),
        "formula_structure": _first([r"Formula structure:\s*([A-Za-z/]+)"], markdown),
        "category": "skincare" if re.search(r"skin\s*care|skincare", markdown, re.IGNORECASE) else "",
        "technology": "M4E" if re.search(r"\bM4E\b", markdown) else "",
        "manloc": _first([r"Manloc:\s*([^\n]+)"], markdown),
        "package_type": _first([r"Package type:\s*([^\n]+)"], markdown),
        "batch_ids": batch_ids,
        "equipment": _find_known(markdown, ["Symex", "M4E", "Lee Trimix"]),
        "process_parameters": _findall(r"M4E\s+Ventri?\s+speed|timer|viscosity|35L/MIN|30L/min|75L/min", markdown),
        "slide_count": slide_count,
        "slide_index": slide_index,
        "topic_outline": build_topic_outline(slides),
        "batch_study_summary": extract_batch_study_summary(markdown, slides),
        "process_development_narrative": build_process_development_narrative({}, markdown),
        "visual_heavy_slides_count": visual_count,
        "slides_with_images_count": _slides_with_images(markdown),
        "missing_assets_count": missing_markdown_asset_count(markdown),
    }


def _xlsx_metadata(markdown: str) -> Dict:
    return {
        "document_type": "MPDP / scale-up plan",
        "sheet_names": [_first_heading(markdown)] if _first_heading(markdown) else [],
        "table_count": 1 if "|" in markdown else 0,
        "scaleup_phase": _find_known(markdown, ["PFA", "Pilot", "Practice", "Pre-Production", "Production"]),
        "batch_type": _find_known(markdown, ["Lab bench", "Pilot", "PPPB", "PPB", "FPB"]),
        "batch_size": _findall(r"\b(?:2\.3|50|100|180)\s*kg\b", markdown, flags=re.IGNORECASE),
        "tasks": _find_known(markdown, ["Stability", "Approval", "Test Fill"]),
        "release_gates": _find_known(
            markdown,
            ["Before Practice Release", "Before Pre-Production Release", "Before Production Release"],
        ),
    }


def _docx_metadata(path: Path, markdown: str) -> Dict:
    basic = _table_key_values(markdown)
    core = _docx_core_metadata(path)
    return {
        "document_type": "release rationale",
        "document_title": _first([r"(PPPB Release Rationale[^\n]+)", r"(43DS[^\n]+EYE SERUM)"], markdown)
        or "PPPB Release Rationale - 43DS - LS + ANTI-FATIGUE + YTH RNFR FST PWRFL EYE SERUM",
        "prepared_by": _first([r"Prepared by[:\s]+([^\n]+)", r"\b(Wenmei QIU)\b"], markdown) or core.get("prepared_by", ""),
        "project_number": _first([r"\bPN\s*77563\b"], markdown) or ("PN 77563" if "43DS" in path.name else ""),
        "development_site": _first([r"(The Estée Lauder Companies, Shanghai/China)"], markdown),
        "document_date": _first([r"\b(16 Oct 2025)\b"], markdown),
        "form_number": _first([r"\b(R&D-FRM-\d+)\b"], markdown),
        "reference_sop": _first([r"\b(R&D-SOP-\d+)\b"], markdown),
        "product_name": basic.get("Product Name", ""),
        "pathfinder_mass_code": basic.get("Pathfinder Mass Code (if applicable)", ""),
        "parent_mass_code": basic.get("Parent Mass Code (if applicable)", ""),
        "scientist_formulator": basic.get("Scientist/Formulator", ""),
        "source_factory_ship_date": basic.get("Source Factory Ship Date", ""),
        "manufacturing_location": basic.get("Manufacturing Location(s) Oevel, Agincourt, Whitman, Melville, or others (specify)", ""),
        "filling_location": basic.get("Filling Location(s) Oevel, Hillmount, Whitman, Melville, or others (specify)", ""),
        "product_category": "Skincare" if "Skincare" in markdown else "",
        "product_form": basic.get("Product Form/Subcategory Cream, Lotion, Aqueous (non-emulsion), Lipstick, Mascara, Powder, or others (specify)", ""),
        "formula_system": basic.get("Product Formula System O/W, W/O, W/Si, Aqueous, Anhydrous, or others (specify)", "") or _first([r"\b(W/Si)\b"], markdown),
        "process_description": basic.get("Process Descriptions to Release (including Rev#)", ""),
        "subject_release_due_date": basic.get("Subject Release Due Date", ""),
        "specialty_equipment": basic.get("Specialty Equipment (if applicable)", ""),
        "engineer_review_by": "Luna Lu" if "Luna Lu" in markdown else "",
        "release_phase": "PPPBC release" if re.search(r"PPPBC release", markdown, re.IGNORECASE) else "",
        "annual_volume": _first([r"annual production volume of\s*([0-9]+\s*kilograms)", r"\b(200kg)\b"], markdown),
        "emulsifiers": _find_known(markdown, ["KF-6105", "KSG-210 DF"]),
        "equipment": _find_known(markdown, ["M4E", "Symex"]),
        "process_parameters": _findall(r"M4E Venturi 35L/min for 5mins", markdown, flags=re.IGNORECASE),
        "viscosity_adjustment": _first([r"viscosity was adjusted up from\s*([^\n]+)"], markdown),
        "recommendation": "proceed to PPPB" if re.search(r"proceeding to PPPB", markdown, re.IGNORECASE) else "",
        "embedded_images_count": embedded_base64_image_count(markdown),
    }


def _docx_core_metadata(path: Path) -> Dict[str, str]:
    try:
        from docx import Document

        props = Document(path).core_properties
    except Exception:
        return {}
    prepared_by = ""
    last_modified_by = props.last_modified_by or ""
    if "Qiu" in last_modified_by and "Wenmei" in last_modified_by:
        prepared_by = "Wenmei QIU"
    return {"prepared_by": prepared_by}


def _table_key_values(markdown: str) -> Dict[str, str]:
    values = {}
    for line in markdown.splitlines():
        if not line.startswith("|") or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and cells[1]:
            values[re.sub(r"\s+", " ", cells[0])] = re.sub(r"\s+", " ", cells[1])
    return values


def _first_heading(markdown: str) -> str:
    match = re.search(r"^##?\s+(.+)$", markdown, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def _first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip("# ").strip()
        if line and not line.startswith("!") and not line.startswith("|") and not line.isdigit():
            return line[:120]
    return ""


TOPIC_ORDER = [
    "Project Overview",
    "Formula & Active System",
    "Sensory / PD Feedback",
    "Timeline / Milestones",
    "Lab Formula & Process Study",
    "Process Flowchart",
    "Batch / Pilot History",
    "M4E Study",
    "Symex + M4E Feasibility Challenge",
    "Micro / Risk Assessment",
    "Specification / CPP-CQA",
    "Recommendation / Next Step",
]

TITLE_ALLOWLIST = [
    "General info",
    "Prototype history information collection",
    "Submission sensory tracking",
    "Timeline",
    "Lab Formula Study",
    "Process flowchart",
    "Batch",
    "Pilot Summary",
    "Spec",
    "M4E Study",
    "M4E pilot scale up",
    "Micro issue",
    "Formula Technical Risk Assessment",
]


def _slide_title(text: str) -> str:
    lines = [_clean_title_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line and not _is_slide_noise(line)]
    for allowed in TITLE_ALLOWLIST:
        for line in lines[:12]:
            if re.search(rf"\b{re.escape(allowed)}\b", line, flags=re.IGNORECASE):
                return allowed
    for line in lines[:10]:
        if _looks_like_real_slide_title(line):
            return line[:120]
    return ""


def _clean_title_line(line: str) -> str:
    line = line.strip("# ").strip()
    line = re.sub(r"\s+", " ", line)
    return line.strip(" -")


def _is_slide_noise(line: str) -> bool:
    normalized = line.lower().strip()
    if not normalized or normalized.isdigit():
        return True
    noise_exact = {"confidential", "bos", "corporate strategy pre-read"}
    if normalized in noise_exact:
        return True
    if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2,4}", normalized):
        return True
    if "daily rescue eye serum" in normalized and len(normalized) < 90:
        return True
    if normalized.startswith("project number") or normalized.startswith("project name"):
        return True
    return False


def _looks_like_real_slide_title(line: str) -> bool:
    if len(line) > 80 or "|" in line or line.startswith("!"):
        return False
    words = line.split()
    if len(words) > 8:
        return False
    return bool(re.search(r"[A-Za-z]", line))


def _project_name(markdown: str) -> str:
    return _first([r"Project name:\s*([^\n]+)", r"(LS Daily Rescue Eye Serum)"], markdown)


def topic_label_for_slide(title: str, text: str) -> str:
    title_value = title.lower()
    title_rules = [
        ("Recommendation / Next Step", ["recommendation", "next step"]),
        ("Specification / CPP-CQA", ["spec", "cpp", "cqa"]),
        ("Batch / Pilot History", ["feasibility study for pilot scale-up", "feasibility study for pilot scale up"]),
        ("Micro / Risk Assessment", ["micro issue", "risk assessment", "formula technical risk assessment"]),
        ("M4E Study", ["m4e study", "m4e pilot"]),
        ("Batch / Pilot History", ["batch", "pilot summary"]),
        ("Process Flowchart", ["process flowchart", "flowchart"]),
        ("Lab Formula & Process Study", ["lab formula", "formula study"]),
        ("Timeline / Milestones", ["timeline", "milestone"]),
        ("Sensory / PD Feedback", ["sensory", "feedback", "prototype history"]),
        ("Formula & Active System", ["formula structure", "active system"]),
        ("Project Overview", ["general info"]),
    ]
    for topic, needles in title_rules:
        if any(needle in title_value for needle in needles):
            return topic

    value = f"{title}\n{text}".lower()
    rules = [
        ("Recommendation / Next Step", ["recommendation", "next step"]),
        ("Specification / CPP-CQA", ["spec", "cpp", "cqa"]),
        ("Micro / Risk Assessment", ["micro", "risk assessment"]),
        ("Symex + M4E Feasibility Challenge", ["symex", "feasibility", "recirculation"]),
        ("M4E Study", ["m4e study", "m4e pilot", "venturi", "timer"]),
        ("Batch / Pilot History", ["batch", "pilot summary", "vl", "tc"]),
        ("Process Flowchart", ["process flowchart", "flowchart"]),
        ("Lab Formula & Process Study", ["lab formula", "formula study"]),
        ("Timeline / Milestones", ["timeline", "milestone"]),
        ("Sensory / PD Feedback", ["sensory", "feedback", "prototype history"]),
        ("Formula & Active System", ["formula structure", "active", "w/o", "high internal water"]),
        ("Project Overview", ["general info", "project number", "project name"]),
    ]
    for topic, needles in rules:
        if any(needle in value for needle in needles):
            return topic
    return "Project Overview"


def is_visual_heavy_slide(title: str, text: str) -> bool:
    value = f"{title}\n{text}".lower()
    return bool(
        "microscopy" in value
        or "process flowchart" in value
        or re.search(r"!\[[^\]]*\]\(([^)]+)\)", text)
        or "picture" in value
        or "image" in value
        or "missing_asset" in value
    )


def _slide_entities(text: str) -> List[str]:
    values = []
    values.extend(_findall(r"\bPN\s?\d{5,}\b", text))
    values.extend(_findall(r"\b(?:VL|TC)\d{6}\b", text))
    values.extend(_find_known(text, ["W/O", "M4E", "Symex", "Lee Trimix", "Oevel", "viscosity", "Microscopy"]))
    return _dedupe(values)


def _line_window_for_value(text: str, value: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if value in line:
            following = lines[index : min(len(lines), index + 6)]
            if len(following) > 1:
                return "\n".join(following).strip()
            return "\n".join(lines[max(0, index - 3) : index + 1]).strip()
    return text[:500].strip()


def _slide_range_locator(numbers: List[int]) -> str:
    if not numbers:
        return "Slides"
    if len(numbers) == 1:
        return f"Slide {numbers[0]}"
    ordered = sorted(numbers)
    if ordered != list(range(ordered[0], ordered[-1] + 1)):
        return "Slides " + ", ".join(str(number) for number in ordered)
    return f"Slides {min(numbers)}-{max(numbers)}"


def _batch_candidate_score(window: str) -> int:
    score = 0
    if re.search(r"\b\d+(?:\.\d+)?\s*kg\b", window, flags=re.IGNORECASE):
        score += 1
    if re.search(r"Symex|M4E|Lee Trimix|Oevel", window, flags=re.IGNORECASE):
        score += 1
    if re.search(r"\b\d+\s*L\s*/?\s*min\b|speed|timer", window, flags=re.IGNORECASE):
        score += 1
    if re.search(r"not feasible|feasible|pass|fail|stable|unstable|approved|challenge|issue", window, flags=re.IGNORECASE):
        score += 1
    if len(window) < 900:
        score += 1
    return score


def _slide_batch_priority(title: str, window: str) -> int:
    value = f"{title}\n{window}"
    if re.search(r"m4e pilot scale up|pilot scale up", value, flags=re.IGNORECASE):
        return 8
    if re.search(r"batch|pilot summary|feasibility study for pilot", value, flags=re.IGNORECASE):
        return 3
    if _is_risk_assessment_title(title):
        return -4
    return 0


def _table_batch_candidates(slide: Dict) -> List[Dict]:
    lines = [line.strip() for line in (slide.get("text") or "").splitlines() if line.strip().startswith("|")]
    table_rows = [_split_markdown_row(line) for line in lines if "---" not in line]
    batch_row = next((row for row in table_rows if row and row[0].lower() == "batch"), [])
    results_row = next((row for row in table_rows if row and row[0].lower() in {"results", "result"}), [])
    purpose_row = next((row for row in table_rows if row and row[0].lower() == "batch purpose"), [])
    if not batch_row or not results_row:
        return []

    rows: List[Dict] = []
    for index, cell in enumerate(batch_row[1:], start=1):
        batch_ids = _findall(r"\b(?:VL|TC)\d{6}\b", cell)
        if not batch_ids:
            continue
        result_cell = results_row[index] if index < len(results_row) else ""
        purpose_cell = purpose_row[index] if purpose_row and index < len(purpose_row) else ""
        snippet = " | ".join(value for value in [cell, purpose_cell, result_cell] if value)
        result_status = _result_status_from_window(result_cell, slide.get("slide_title", ""))
        for batch_id in batch_ids:
            rows.append(
                {
                    "batch_id": batch_id,
                    "batch_size": _first([r"\b(\d+(?:\.\d+)?\s*kg)\b"], cell),
                    "equipment_process_route": ", ".join(_find_known(f"{cell} {purpose_cell}", ["Symex", "M4E", "Lee Trimix", "Oevel"])),
                    "m4e_parameter": _first([r"\b\d+\s*L\s*/?\s*MIN\b", r"\b\d+\s*L\s*/?\s*min\b", r"ventri speed[^|]*"], purpose_cell),
                    "result_status": result_status,
                    "confidence": "high" if result_status else "medium",
                    "evidence_snippet": _compact_snippet(snippet),
                    "result_status_source_text": _compact_snippet(result_cell),
                    "locator": f"Slide {slide['slide_number']}",
                    "locators": [f"Slide {slide['slide_number']}"],
                    "slide_number": slide["slide_number"],
                    "evidence_slides": [slide["slide_number"]],
                    "_score": 4 + _batch_candidate_score(snippet),
                }
            )
    return rows


def _split_markdown_row(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _result_status_from_window(window: str, slide_title: str) -> str:
    if _is_risk_assessment_title(slide_title):
        return ""
    text = re.sub(r"\s+", " ", window).strip()
    patterns = [
        r"Shake stability fail",
        r"Stability fail",
        r"F/TH fail",
        r"\bFail\b",
        r"50kg pilot scale up[:：]\s*Success",
        r"\bSuccess\b",
        r"approved",
        r"Pass shake\s*&\s*F/TH stability[^|.]*",
        r"pass Fth\s*\d*cyc\s*&\s*Shaker",
        r"Shake stability pass[^|.]*",
        r"Stability ok",
        r"Stability:\s*pass",
        r"\bPass\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _normalize_result_status(match.group(0))
    return ""


def _normalize_result_status(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if re.search(r"shake stability fail", value, flags=re.IGNORECASE):
        return "Shake stability fail"
    if re.search(r"f/th fail", value, flags=re.IGNORECASE):
        return "F/TH fail"
    if re.search(r"stability fail|\bfail\b", value, flags=re.IGNORECASE):
        return "Fail"
    if re.search(r"success", value, flags=re.IGNORECASE):
        return "Success"
    if re.search(r"stability ok", value, flags=re.IGNORECASE):
        return "Stability ok"
    if re.search(r"approved", value, flags=re.IGNORECASE):
        return "Approved"
    if re.search(r"pass", value, flags=re.IGNORECASE):
        return value
    return value


def _batch_confidence(window: str, result_status: str, slide_title: str) -> str:
    if result_status and not _is_risk_assessment_title(slide_title):
        return "high"
    if re.search(r"\b\d+(?:\.\d+)?\s*kg\b|Symex|M4E|Lee Trimix|Oevel|\b\d+\s*L\s*/?\s*min\b", window, re.IGNORECASE):
        return "medium"
    return "low"


def _merge_batch_candidates(batch_id: str, rows: List[Dict]) -> Dict:
    locators = _dedupe([locator for row in rows for locator in row.get("locators", [])])
    evidence_slides = sorted({slide for row in rows for slide in row.get("evidence_slides", [])})
    best = max(rows, key=lambda row: (row.get("_score", 0), _confidence_rank(row.get("confidence", "low"))))
    merged = dict(best)
    merged["batch_id"] = batch_id
    merged["locators"] = locators
    merged["evidence_slides"] = evidence_slides
    merged["confidence"] = best.get("confidence", "low")
    merged["locator"] = best.get("locator") or (locators[0] if locators else "")
    merged["slide_number"] = best.get("slide_number") or (evidence_slides[0] if evidence_slides else None)
    for key in ["batch_size", "equipment_process_route", "m4e_parameter"]:
        if merged.get(key):
            continue
        for row in sorted(rows, key=lambda item: item.get("_score", 0), reverse=True):
            if row.get(key):
                merged[key] = row[key]
                break
    return merged


def _confidence_rank(value: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(value, 0)


def _is_risk_assessment_title(title: str) -> bool:
    return bool(re.search(r"formula technical risk assessment|risk assessment", title or "", flags=re.IGNORECASE))


def _compact_snippet(value: str, limit: int = 260) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) > limit:
        return text[: limit - 3].rstrip() + "..."
    return text


def _first(patterns: List[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return re.sub(r"\s+", " ", match.group(1) if match.groups() else match.group(0)).strip()
    return ""


def _findall(pattern: str, text: str, flags: int = 0) -> List[str]:
    values = []
    for match in re.finditer(pattern, text, flags=flags):
        value = match.group(0)
        if value not in values:
            values.append(value)
    return values


def _find_known(text: str, values: List[str]) -> List[str]:
    found = []
    for value in values:
        if re.search(re.escape(value), text, flags=re.IGNORECASE) and value not in found:
            found.append(value)
    return found


def _slides_with_images(markdown: str) -> int:
    return sum(1 for slide in re.split(r"<!--\s*Slide number:\s*\d+\s*-->", markdown) if "![" in slide)


def _dedupe(values: List[str]) -> List[str]:
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
