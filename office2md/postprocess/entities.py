import re
from pathlib import Path
from typing import Dict, List


ENTITY_RULES = {
    "organization": [r"\bSymex\b"],
    "line": [r"\bCML\s*125\b", r"\bCML125\b"],
    "document_type": [r"\bwiring diagram\b", r"\bhmi translation\b", r"\bhmi text table\b"],
    "manual_topic": [
        r"\bfunctional description\b",
        r"\boperating manual\b",
        r"\bfault messages\b",
        r"\bfaults and measures\b",
        r"\bsiemens touch panel\b",
        r"\btemperature control\b",
        r"\bCIP\b",
    ],
    "drawing_number": [r"(?<![A-Za-z0-9])ENG-\d{6,}(?![A-Za-z0-9])"],
    "project_number": [r"(?<![A-Za-z0-9])SY\d{6,}(?![A-Za-z0-9])"],
    "order_number": [r"(?<![A-Za-z0-9])SY\d{6,}(?![A-Za-z0-9])"],
    "commission_number": [
        r"\bcommission\s+(?:number|no\.?)\s*[:#-]?\s*([A-Z0-9][A-Z0-9_-]{2,})\b",
        r"\bcommission\s*[:#-]\s*([A-Z0-9][A-Z0-9_-]{2,})\b",
    ],
    "equipment": [
        r"\bPLC\b",
        r"\bHMI\b",
        r"\bterminal\b",
        r"\bvalve\b",
        r"\bmotor\b",
        r"\bpump\b",
        r"\bcontrol panel\b",
    ],
}


def extract_entities(source_path: Path, markdown: str, document_kind: str = "", metadata: Dict | None = None) -> Dict[str, List[str]]:
    text = f"{source_path}\n{markdown}"
    entities: Dict[str, List[str]] = {}
    for group, patterns in ENTITY_RULES.items():
        values = []
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                value = match.group(1) if match.groups() else match.group(0)
                normalized = _normalize_entity(value)
                if group == "commission_number" and not _valid_commission_number(normalized):
                    continue
                if normalized not in values:
                    values.append(normalized)
        entities[group] = values
    entities.update(_extract_title_page_entities(markdown))
    metadata = metadata or {}
    extracted = metadata.get("extracted_metadata", {})
    for key, value in extracted.items():
        if isinstance(value, list):
            entities[key] = value
        elif value not in ("", None):
            entities[key] = [str(value)]
    if document_kind == "manual_pdf":
        entities["document_type"] = ["operating manual"]
        entities["manual_topic"] = [item for item in entities.get("manual_topic", []) if item != "functional description"]
    if document_kind == "technical_drawing_pdf" and "wiring diagram" in text.lower():
        entities["document_type"] = ["wiring diagram"]
    if document_kind == "release_rationale_docx":
        entities["document_type"] = ["release rationale"]
        if extracted.get("pathfinder_mass_code"):
            entities["mass_code"] = [extracted["pathfinder_mass_code"]]
    if document_kind == "mpdp_table_xlsx":
        entities["document_type"] = ["MPDP", "scale-up plan"]
    if document_kind == "process_development_presentation":
        entities["document_type"] = ["project presentation"]
    if document_kind == "hmi_translation_xlsx":
        entities["document_type"] = ["hmi translation", "hmi text table"]
        equipment = entities.get("equipment", [])
        for value in ["PLC", "HMI"]:
            if value not in equipment:
                equipment.append(value)
        entities["equipment"] = equipment
    return entities


def _normalize_entity(value: str) -> str:
    compact = re.sub(r"\s+", " ", value.strip())
    lower = compact.lower()
    if re.fullmatch(r"cml\s*125", compact, flags=re.IGNORECASE):
        return "CML125"
    if lower == "symex":
        return "Symex"
    if lower == "plc":
        return "PLC"
    if lower == "hmi":
        return "HMI"
    if lower == "hmi translation":
        return "hmi translation"
    if lower == "hmi text table":
        return "hmi text table"
    if lower == "wiring diagram":
        return "wiring diagram"
    manual_topics = {
        "functional description": "functional description",
        "operating manual": "operating manual",
        "fault messages": "fault messages",
        "faults and measures": "faults and measures",
        "siemens touch panel": "Siemens touch panel",
        "temperature control": "temperature control",
        "cip": "CIP",
    }
    if lower in manual_topics:
        return manual_topics[lower]
    equipment = {
        "terminal": "terminal",
        "valve": "valve",
        "motor": "motor",
        "pump": "pump",
        "control panel": "control panel",
    }
    if lower in equipment:
        return equipment[lower]
    return compact


def _valid_commission_number(value: str) -> bool:
    if value.lower() in {"make", "control", "panel"}:
        return False
    return any(char.isdigit() for char in value)


def _extract_title_page_entities(text: str) -> Dict[str, List[str]]:
    fields = {
        "manufacturer": _metadata_value(text, "manufacturer"),
        "equipment_name": _metadata_value(text, "equipment_name"),
        "symex_number": _metadata_value(text, "symex_number"),
        "customer": _metadata_value(text, "customer"),
        "year_built": _metadata_value(text, "year_built"),
        "issue": _metadata_value(text, "issue"),
        "revision": _metadata_value(text, "revision"),
    }
    return {key: [value] if value else [] for key, value in fields.items()}


def _metadata_value(text: str, key: str) -> str:
    match = re.search(rf"^-\s+{re.escape(key)}:\s*(.+)$", text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""
