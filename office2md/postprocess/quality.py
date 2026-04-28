import re
from typing import List


def collect_warnings(markdown: str, chunk_count: int) -> List[str]:
    warnings: List[str] = []
    text = markdown.strip()
    if not text:
        warnings.append("output markdown is empty")
    elif len(text) < 20:
        warnings.append("output markdown is very short")
    if not re.search(r"^#{1,6}\s+", markdown, re.MULTILINE):
        warnings.append("no headings detected")
    if chunk_count == 0:
        warnings.append("no chunks generated")
    return warnings

