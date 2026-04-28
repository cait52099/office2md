import json
from typing import Dict


def document_summary_prompt(text: str, metadata: Dict) -> str:
    return (
        "Summarize this document for a knowledge base. Return JSON with keys: "
        "summary, key_points, tags, entities, suggested_links, questions_for_search.\n\n"
        f"Metadata:\n{json.dumps(metadata, ensure_ascii=False, indent=2)}\n\n"
        f"Text:\n{text[:6000]}"
    )


def technical_drawing_page_prompt(page_text: str, metadata: Dict, image_path: str) -> str:
    return (
        "Analyze this technical drawing page for a knowledge base. Return JSON with keys: "
        "page_summary, page_type, components, signals, equipment, search_keywords.\n\n"
        f"Image path: {image_path}\n"
        f"Metadata:\n{json.dumps(metadata, ensure_ascii=False, indent=2)}\n\n"
        f"Page text:\n{page_text[:4000]}"
    )

