from pathlib import Path
from typing import List


def generate_tags(source_path: Path, document_kind: str, quality_status: str) -> List[str]:
    text = str(source_path).lower().replace("_", " ").replace("-", " ")
    tags = []
    rules = [
        ("symex", "symex"),
        ("cml125", "cml125"),
        ("cml 125", "cml125"),
        ("wiring diagram", "wiring-diagram"),
        ("schematic", "schematic"),
        ("terminal diagram", "terminal-diagram"),
        ("cable overview", "cable-overview"),
        ("electrical and software design", "electrical-design"),
        ("electrical/software design", "electrical-design"),
        ("functional description", "functional-description"),
        ("operating manual", "operating-manual"),
        ("operation manual", "operating-manual"),
        ("fault catalog", "fault-catalog"),
        ("fault messages", "fault-messages"),
        ("faults and measures", "fault-catalog"),
        ("safety", "safety"),
        ("operation", "operation"),
        ("siemens touch panel", "siemens-touch-panel"),
        ("cip", "cip"),
        ("temperature control", "temperature-control"),
        ("flowsheet", "flowsheet"),
        ("p&id", "p-id"),
        ("p and id", "p-id"),
        ("piping and instrumentation diagram", "piping-instrumentation-diagram"),
        ("mechanical design", "mechanical-design"),
    ]
    for needle, tag in rules:
        if needle in text and tag not in tags:
            tags.append(tag)
    if (
        any(tag in tags for tag in ["flowsheet", "p-id", "piping-instrumentation-diagram"])
        and "mechanical-design" not in tags
    ):
        tags.append("mechanical-design")

    file_type = source_path.suffix.lower().lstrip(".")
    if file_type:
        tags.append(file_type)
    if quality_status == "low_structure":
        tags.append("low-structure")
    if quality_status == "visual_only":
        tags.append("visual-only")
    if document_kind == "technical_drawing_pdf":
        tags.append("technical-drawing")
    kind_tags = {
        "manual_pdf": "operating-manual",
        "functional_description_pdf": "functional-description",
        "fault_catalog_pdf": "fault-catalog",
        "generic_pdf": "generic-pdf",
        "mpdp_table_xlsx": "mpdp",
        "process_development_presentation": "project-presentation",
        "release_rationale_docx": "release-rationale",
    }
    if document_kind in kind_tags and kind_tags[document_kind] not in tags:
        tags.append(kind_tags[document_kind])
    from office2md.postprocess.office_structure import office_tags

    for tag in office_tags(document_kind, {}):
        if tag not in tags:
            tags.append(tag)
    return tags
