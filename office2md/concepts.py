import hashlib
import itertools
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from slugify import slugify


CONCEPT_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "system",
    "user texts",
    "page",
    "pages",
    "document",
    "documents",
    "file",
    "source",
    "asset",
    "assets",
    "image",
    "images",
    "locator",
    "locators",
    "extracted",
    "form",
    "group",
    "summary",
    "untitled",
    "png",
    "jpg",
    "jpeg",
    "table",
    "section",
    "text",
    "chapter",
    "title",
    "untitled source page",
}
NOISY_CONCEPT_PHRASES = {
    "cover sheet",
    "private confidential",
    "liang private",
    "selection new",
    "caner sheet",
}
CONCEPT_SOURCE_WEIGHTS = {
    "structured_header": 7.0,
    "entity": 6.0,
    "document_title": 4.0,
    "heading": 4.0,
    "text_phrase": 2.0,
    "weak_page_title": 0.5,
}


def load_curated_concept_index(library_path: Path) -> dict[str, Any]:
    db_path = library_db_path(library_path)
    concept_data: dict[str, dict[str, Any]] = {}
    doc_labels: dict[str, str] = {}
    hidden_noisy = 0

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT c.chunk_id, c.doc_id, c.title AS chunk_title, c.text, c.heading_path_json,
                   d.title AS document_title, d.source_file, d.document_kind
            FROM chunks c
            JOIN documents d ON d.doc_id = c.doc_id
            """
        ).fetchall()
        entity_rows = conn.execute(
            """
            SELECT e.entity_text, e.entity_type, e.normalized_text, m.doc_id, m.chunk_id
            FROM entities e
            JOIN entity_mentions m ON m.entity_id = e.entity_id
            """
        ).fetchall()

    for row in rows:
        doc_id = row["doc_id"]
        doc_labels[doc_id] = row["document_title"] or row["source_file"] or doc_id
        context = " ".join(str(value or "") for value in [row["document_title"], row["chunk_title"], row["text"]])
        candidates = []
        title_candidate = _direct_concept_candidate(row["document_title"] or "")
        if title_candidate:
            candidates.append((title_candidate, "document_title"))
        candidates.extend((label, "document_title") for label in _concept_candidates_from_text(row["document_title"] or "", max_terms=12))
        candidates.extend((label, "heading") for label in _heading_concept_candidates(row["heading_path_json"], row["chunk_title"]))
        candidates.extend((label, "text_phrase") for label in _concept_candidates_from_text(row["text"] or "", max_terms=24))
        for label, base_source_type in candidates:
            normalized = normalize_concept_label(label)
            if _is_short_ascii_acronym(normalized) and _looks_like_page_header_only(row["text"] or "", normalized):
                hidden_noisy += 1
                continue
            if base_source_type in {"document_title", "heading"} and _is_short_ascii_acronym(normalized) and not _contains_standalone_term(row["text"] or "", normalized):
                hidden_noisy += 1
                continue
            if is_noisy_concept_label(normalized):
                hidden_noisy += 1
                continue
            _add_library_native_concept(
                concept_data,
                normalized,
                label,
                _concept_source_type(label, base_source_type, row),
                doc_id,
                row["chunk_id"],
                row["document_title"] or row["source_file"] or doc_id,
                context,
            )

    doc_title_by_id = {row["doc_id"]: doc_labels[row["doc_id"]] for row in rows}
    chunk_context_by_id = {
        row["chunk_id"]: " ".join(str(value or "") for value in [row["document_title"], row["chunk_title"], row["text"]])
        for row in rows
    }
    for entity in entity_rows:
        label = entity["entity_text"] or entity["normalized_text"]
        normalized = normalize_concept_label(label)
        if is_noisy_concept_label(normalized):
            hidden_noisy += 1
            continue
        doc_id = entity["doc_id"]
        chunk_id = entity["chunk_id"]
        _add_library_native_concept(
            concept_data,
            normalized,
            label,
            "entity",
            doc_id,
            chunk_id,
            doc_title_by_id.get(doc_id, doc_id),
            chunk_context_by_id.get(chunk_id or "", doc_title_by_id.get(doc_id, "")),
        )

    concepts = {}
    for label, data in concept_data.items():
        if not (data["chunk_ids"] or data["doc_ids"]):
            continue
        score = _concept_quality_score(data)
        if not _passes_concept_quality(label, data, score):
            hidden_noisy += 1
            continue
        concepts[label] = {
            **data,
            "chunk_ids": data["chunk_ids"],
            "doc_ids": data["doc_ids"],
            "doc_counts": dict(data["doc_counts"]),
            "contexts": data["contexts"],
            "source_types": sorted(data["source_types"]),
            "source_counts": dict(data["source_counts"]),
            "match_count": sum(data["source_counts"].values()),
            "quality_score": round(score, 2),
            "weight": round(score + len(data["chunk_ids"]) + len(data["doc_ids"]), 2),
        }
    return {
        "concepts": concepts,
        "doc_labels": doc_labels,
        "hidden_noisy_concepts_count": hidden_noisy,
    }


def library_db_path(library_path: Path) -> Path:
    return library_path / "library.db" if library_path.is_dir() else library_path


def normalize_concept_label(label: str) -> str:
    return " ".join((label or "").strip().casefold().split())


def is_noisy_concept_label(label: str) -> bool:
    text = normalize_concept_label(label)
    if not text:
        return True
    if text in CONCEPT_STOPWORDS:
        return True
    if text in NOISY_CONCEPT_PHRASES:
        return True
    if "private" in text or "confidential" in text:
        return True
    if text.endswith(" sheet") and text.split(" ", 1)[0] not in {"data", "assessment", "score", "risk"}:
        return True
    if re.search(r"\d", text) and (" form " in f" {text} " or "group" in text):
        return True
    if "pm-group" in text:
        return True
    if len(text) < 3 and not re.search(r"[\u4e00-\u9fff]", text):
        return True
    if re.fullmatch(r"\d{4}|\d+(\.\d+)?", text):
        return True
    if re.fullmatch(r"[a-z]{2}-[a-z]{2}", text):
        return True
    if text in {"min", "degc", "%", "bar", "rpm"}:
        return True
    if text.startswith("assets/") or re.search(r"\.(png|jpg|jpeg|gif|bmp|tiff)$", text):
        return True
    if re.search(r"\.(pdf|docx?|xlsx?|pptx?|txt|md|html)$", text):
        return True
    if re.fullmatch(r"eng-\d+", text):
        return True
    if text in {"document_has_chunk", "document_has_asset", "chunk_has_source_locator"}:
        return True
    return False


def concept_id(label: str) -> str:
    normalized = normalize_concept_label(label)
    slug = slugify(normalized) or re.sub(r"[^\w]+", "-", normalized, flags=re.UNICODE).strip("-") or "unknown"
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:8]
    return f"concept:{slug[:48]}-{digest}"


def concept_pair_counts(concepts: dict[str, dict[str, Any]], key: str) -> Counter:
    chunk_concepts: dict[str, set[str]] = defaultdict(set)
    for label, concept in concepts.items():
        for item_id in concept.get(key, set()):
            chunk_concepts[item_id].add(label)
    return _cooccurrence_pairs(chunk_concepts.values())


def _add_library_native_concept(
    concepts: dict[str, dict[str, Any]],
    normalized: str,
    label: str,
    source_type: str,
    doc_id: str,
    chunk_id: str | None,
    document_title: str,
    context: str,
) -> None:
    item = concepts.setdefault(
        normalized,
        {
            "label": _display_concept_label(label),
            "aliases": set(),
            "chunk_ids": set(),
            "doc_ids": set(),
            "doc_counts": Counter(),
            "contexts": set(),
            "source_types": set(),
            "source_counts": Counter(),
            "sample_document_title": document_title,
        },
    )
    item["aliases"].add(label)
    item["source_types"].add(source_type)
    item["source_counts"][source_type] += 1
    item["doc_ids"].add(doc_id)
    item["doc_counts"][doc_id] += 1
    if chunk_id:
        item["chunk_ids"].add(chunk_id)
    if context:
        item["contexts"].add(_short_label(context, 240))


def _display_concept_label(label: str) -> str:
    text = " ".join(str(label or "").strip().split())
    return text[:1].upper() + text[1:] if text.islower() else text


def _heading_concept_candidates(heading_path_json: str | None, chunk_title: str | None) -> list[str]:
    values = []
    if heading_path_json:
        try:
            loaded = json.loads(heading_path_json)
        except json.JSONDecodeError:
            loaded = []
        if isinstance(loaded, list):
            values.extend(str(item) for item in loaded)
    if chunk_title:
        values.append(chunk_title)
    candidates = []
    for value in values:
        direct = _direct_concept_candidate(value)
        if direct:
            candidates.append(direct)
        candidates.extend(_concept_candidates_from_text(value, max_terms=10))
    return candidates


def _direct_concept_candidate(text: str) -> str | None:
    clean = re.sub(r"\s+", " ", (text or "").strip(" .:-|"))
    if not clean or len(clean) > 80:
        return None
    normalized = normalize_concept_label(clean)
    if is_noisy_concept_label(normalized):
        return None
    words = re.findall(r"[A-Za-z][A-Za-z0-9+.-]*|[\u4e00-\u9fff]{2,}", clean)
    if not (1 <= len(words) <= 8):
        return None
    if len(words) == 1 and not re.search(r"[\u4e00-\u9fff]", clean) and len(words[0]) < 5:
        return None
    return clean


def _concept_source_type(label: str, base_source_type: str, row: sqlite3.Row) -> str:
    if base_source_type in {"heading", "text_phrase"} and _looks_structured_header_label(label):
        return "structured_header"
    if base_source_type == "heading" and _is_weak_page_title_source(row):
        return "weak_page_title"
    return base_source_type


def _looks_structured_header_label(label: str) -> bool:
    text = normalize_concept_label(label)
    if is_noisy_concept_label(text):
        return False
    words = text.split()
    if 2 <= len(words) <= 6 and any(word in words for word in {"assessment", "leadership", "thinking", "background", "experience", "risk", "study"}):
        return True
    return text in {
        "leadership",
        "communication",
        "collaboration",
        "resilience",
        "english",
        "result",
        "case study",
        "logical thinking",
        "strategic thinking",
        "technical background",
        "learning agility",
        "background information",
    }


def _is_weak_page_title_source(row: sqlite3.Row) -> bool:
    document_kind = normalize_concept_label(row["document_kind"] or "")
    chunk_title = normalize_concept_label(row["chunk_title"] or "")
    if document_kind in {"generic_pdf", "low_structure_pdf"}:
        return True
    return chunk_title in {"cover", "cover sheet", "summary", "sheet", "untitled source page"}


def _concept_candidates_from_text(text: str, max_terms: int) -> list[str]:
    clean = re.sub(r"https?://\S+|[\w.+-]+@[\w.-]+\.\w+|\+?\d[\d\s().-]{7,}\d|[\\/_]+", " ", text or "")
    chinese_terms = re.findall(r"[\u4e00-\u9fff]{2,8}", clean)
    tokens = [
        token.strip(".-+").casefold()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9+.-]*", clean)
        if not is_noisy_concept_label(token.strip(".-+"))
    ]
    counts = Counter(tokens)
    phrases = Counter()
    for left, right in zip(tokens, tokens[1:]):
        if left not in CONCEPT_STOPWORDS and right not in CONCEPT_STOPWORDS:
            phrases[f"{left} {right}"] += 1
    selected = [label for label, _count in phrases.most_common(max_terms)]
    selected.extend(label for label, _count in counts.most_common(max_terms) if label not in selected)
    selected.extend(term for term in chinese_terms[:max_terms] if term not in selected)
    return [label for label in selected[:max_terms] if not is_noisy_concept_label(label)]


def _concept_quality_score(data: dict[str, Any]) -> float:
    source_counts = data.get("source_counts") or {}
    source_score = max((CONCEPT_SOURCE_WEIGHTS.get(source_type, 1.0) for source_type in source_counts), default=0.0)
    match_count = sum(source_counts.values())
    document_count = len(data.get("doc_ids") or [])
    repeated_bonus = min(match_count, 8) * 0.45
    document_bonus = min(document_count, 5) * 0.8
    if source_counts.get("weak_page_title") and len(source_counts) == 1:
        source_score = min(source_score, 0.5)
    return source_score + repeated_bonus + document_bonus


def _passes_concept_quality(label: str, data: dict[str, Any], score: float) -> bool:
    normalized = normalize_concept_label(label)
    if is_noisy_concept_label(normalized):
        return False
    source_counts = data.get("source_counts") or {}
    if source_counts.get("weak_page_title") and len(source_counts) == 1:
        return False
    if set(source_counts) == {"document_title"} and sum(source_counts.values()) == 1:
        return False
    if source_counts.get("text_phrase") and len(source_counts) == 1 and len(data.get("doc_ids") or []) == 1 and score < 3.0:
        return False
    return score >= 3.0


def _is_short_ascii_acronym(label: str) -> bool:
    return bool(re.fullmatch(r"[a-z]{2,3}", normalize_concept_label(label)))


def _contains_standalone_term(text: str, term: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", text or "", flags=re.IGNORECASE) is not None


def _looks_like_page_header_only(text: str, term: str) -> bool:
    value = text or ""
    if not re.match(rf"^\s*{re.escape(term)}\s*(\r?\n|$)", value, flags=re.IGNORECASE):
        return False
    marker = "Extracted text:"
    if marker not in value:
        return False
    extracted = value.split(marker, 1)[1]
    return not _contains_standalone_term(extracted, term)


def _cooccurrence_pairs(groups: Any) -> Counter:
    counts: Counter = Counter()
    for group in groups:
        for left_id, right_id in itertools.combinations(sorted(group), 2):
            counts[(left_id, right_id)] += 1
    return counts


def _short_label(value: str, limit: int) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else f"{text[: limit - 1]}..."
