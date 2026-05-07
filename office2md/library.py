import json
import re
import shutil
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from office2md.postprocess.office_structure import (
    build_hmi_translation_chunks,
    is_hmi_translation_xlsx,
)
from office2md.postprocess.pdf_structure import classify_obvious_pdf_subtype


LIBRARY_SCHEMA_VERSION = "1"
LIBRARY_RELEASE_LABEL = "v0.2.0-rc1"
TOKEN_FALLBACK_POOL_LIMIT = 250


def build_library(input_output_root: Path, library_output_dir: Path) -> Dict:
    input_root = input_output_root.expanduser().resolve()
    output_dir = library_output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    docs, warnings = load_document_outputs(input_root)
    db_path = output_dir / "library.db"
    if db_path.exists():
        db_path.unlink()
    rows = _normalize_records(docs, input_root)
    _write_database(db_path, rows)
    index = _build_index(rows, warnings)
    graph = _build_graph(rows)
    manifest = _build_library_manifest(input_root, rows, warnings)
    _write_json(output_dir / "library_index.json", index)
    _write_json(output_dir / "library_graph.json", graph)
    _write_json(output_dir / "library_manifest.json", manifest)
    _write_markdown_portal(output_dir, rows, index, warnings)
    _write_interop_exports(output_dir / "exports", rows)
    return {
        "library_db": str(db_path),
        "documents_count": len(rows["documents"]),
        "chunks_count": len(rows["chunks"]),
        "entities_count": len(rows["entities"]),
        "library_manifest": str(output_dir / "library_manifest.json"),
        "warnings": warnings,
        "output_dir": str(output_dir),
    }


def load_document_outputs(input_root: Path) -> tuple[List[Dict], List[str]]:
    documents = []
    warnings = []
    for manifest_path in sorted(input_root.rglob("manifest.json")):
        doc_dir = manifest_path.parent
        manifest = _read_json(manifest_path, warnings)
        if not manifest:
            continue
        if manifest.get("status") == "failed":
            warnings.append(f"skipped failed manifest: {manifest_path}")
            continue
        doc = {"output_dir": doc_dir, "manifest": manifest}
        for name in ["knowledge.json", "entities.json", "source_map.json"]:
            path = doc_dir / name
            if path.exists():
                doc[name[:-5]] = _read_json(path, warnings)
            else:
                warnings.append(f"missing {name}: {doc_dir}")
                doc[name[:-5]] = {}
        chunks_path = doc_dir / "chunks.jsonl"
        if chunks_path.exists():
            doc["chunks"] = _read_jsonl(chunks_path, warnings)
        else:
            warnings.append(f"missing chunks.jsonl: {doc_dir}")
            doc["chunks"] = []
        document_path = doc_dir / "document.md"
        if document_path.exists():
            doc["document_md"] = document_path
        else:
            warnings.append(f"missing document.md: {doc_dir}")
            doc["document_md"] = None
        raw_path = doc_dir / "document.raw.md"
        doc["document_raw_md"] = raw_path if raw_path.exists() else None
        documents.append(doc)
    return documents, warnings


def search_library(
    library_db: Path,
    query: str,
    limit: int = 10,
    offset: int = 0,
    kinds: List[str] | None = None,
    evidences: List[str] | None = None,
    document: str | None = None,
    output_dir: str | None = None,
    entities: List[str] | None = None,
    exclude_docs: List[str] | None = None,
    has_locator: bool = False,
    related: int = 0,
) -> List[Dict]:
    db_path = _resolve_db_path(library_db)
    filters, params = _search_filters(kinds or [], evidences or [], document, output_dir, entities or [], exclude_docs or [], has_locator)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        search_query = query
        alias_used = None
        normalized_used = False
        rows = _search_rows(conn, search_query, filters, params, limit, offset)
        fallback_used = False
        if not rows:
            for candidate in _query_expansions(query):
                rows = _search_rows(conn, candidate["query"], filters, params, limit, offset)
                if not rows and candidate["kind"] == "normalized" and candidate["query"].endswith("*"):
                    rows = _prefix_like_search_rows(conn, candidate["query"].rstrip("*"), filters, params, limit, offset)
                if rows:
                    search_query = candidate["query"]
                    alias_used = candidate["label"]
                    normalized_used = candidate["kind"] == "normalized"
                    break
        if not rows and _is_multi_term_query(query):
            rows = _fallback_token_search(conn, query, filters, params, limit, offset)
            fallback_used = bool(rows)
        if not rows:
            for candidate in _query_expansions(query):
                if _is_multi_term_query(candidate["query"]):
                    rows = _fallback_token_search(conn, candidate["query"], filters, params, limit, offset)
                    if rows:
                        search_query = candidate["query"]
                        alias_used = candidate["label"]
                        normalized_used = candidate["kind"] == "normalized"
                        fallback_used = True
                        break
        results = _search_results(rows, search_query, offset, fallback_used, alias_used, normalized_used, query)
        if related > 0:
            for result in results:
                result["related_chunks"] = _related_chunks(conn, result["chunk_id"], related)
    return results


def _prefix_like_search_rows(
    conn: sqlite3.Connection,
    prefix: str,
    filters: str,
    params: List[Any],
    limit: int,
    offset: int,
) -> List[sqlite3.Row]:
    if len(prefix) < 4 and not re.fullmatch(r"\d+[A-Za-z]{2,}", prefix):
        return []
    like = f"%{prefix}%"
    sql = f"""
        SELECT c.chunk_id, c.title, c.text, c.evidence_type, c.locator,
               c.is_noisy, c.noise_score, c.noise_reasons_json,
               d.title AS document_title, d.document_kind, d.source_file, d.output_dir,
               0 AS score,
               COUNT(*) OVER() AS total_hits
        FROM chunks c
        JOIN documents d ON d.doc_id = c.doc_id
        WHERE (c.text LIKE ? OR c.title LIKE ? OR c.heading_path_json LIKE ? OR c.locator LIKE ?)
        {filters}
        ORDER BY {_rank_adjustment_sql()}
        LIMIT ? OFFSET ?
        """
    return conn.execute(sql, [like, like, like, like, *params, limit, offset]).fetchall()


def _search_rows(conn: sqlite3.Connection, query: str, filters: str, params: List[Any], limit: int, offset: int) -> List[sqlite3.Row]:
    try:
        rank_adjustment = _rank_adjustment_sql()
        sql = f"""
            SELECT c.chunk_id, c.title, c.text, c.evidence_type, c.locator,
                   c.is_noisy, c.noise_score, c.noise_reasons_json,
                   d.title AS document_title, d.document_kind, d.source_file, d.output_dir,
                   bm25(chunks_fts) + {rank_adjustment} AS score,
                   COUNT(*) OVER() AS total_hits
            FROM chunks_fts
            JOIN chunks c ON c.chunk_id = chunks_fts.chunk_id
            JOIN documents d ON d.doc_id = c.doc_id
            WHERE chunks_fts MATCH ?
            {filters}
            ORDER BY score
            LIMIT ? OFFSET ?
            """
        return conn.execute(sql, [query, *params, limit, offset]).fetchall()
    except sqlite3.OperationalError:
        like = f"%{query}%"
        sql = f"""
            SELECT c.chunk_id, c.title, c.text, c.evidence_type, c.locator,
                   c.is_noisy, c.noise_score, c.noise_reasons_json,
                   d.title AS document_title, d.document_kind, d.source_file, d.output_dir,
                   0 AS score,
                   COUNT(*) OVER() AS total_hits
            FROM chunks c
            JOIN documents d ON d.doc_id = c.doc_id
            WHERE (c.text LIKE ? OR c.title LIKE ? OR c.heading_path_json LIKE ? OR c.locator LIKE ?)
            {filters}
            ORDER BY {_rank_adjustment_sql()}
            LIMIT ? OFFSET ?
            """
        return conn.execute(sql, [like, like, like, like, *params, limit, offset]).fetchall()


def _fallback_token_search(conn: sqlite3.Connection, query: str, filters: str, params: List[Any], limit: int, offset: int) -> List[Dict]:
    merged: Dict[str, Dict] = {}
    candidate_limit = max(TOKEN_FALLBACK_POOL_LIMIT, offset + limit)
    tokens = _search_tokens(query)
    for token in tokens:
        for index, row in enumerate(_search_rows(conn, token, filters, params, candidate_limit, 0), start=1):
            item = dict(row)
            current = merged.setdefault(
                item["chunk_id"],
                {**item, "token_hits": 0, "best_rank": index, "matched_tokens": set()},
            )
            current["token_hits"] += 1
            current["best_rank"] = min(current["best_rank"], index)
            current["matched_tokens"].add(token)
    ranked = sorted(
        merged.values(),
        key=lambda item: (
            -len(item["matched_tokens"]),
            _fallback_rank_adjustment_value(item, tokens),
            item["best_rank"],
            bool(item["is_noisy"]),
            item.get("noise_score") or 0,
        ),
    )
    selected = ranked[offset : offset + limit]
    total_hits = len(ranked)
    return [{**item, "total_hits": total_hits} for item in selected]


def _search_results(
    rows: List[Any],
    query: str,
    offset: int,
    fallback_used: bool = False,
    alias_used: str | None = None,
    normalized_used: bool = False,
    original_query: str | None = None,
) -> List[Dict]:
    return [
        {
            "rank": index + 1,
            "chunk_id": row["chunk_id"],
            "document_title": row["document_title"],
            "document_kind": row["document_kind"],
            "source_file": row["source_file"],
            "output_dir": row["output_dir"],
            "chunk_title": row["title"],
            "evidence_type": row["evidence_type"],
            "locator": row["locator"],
            "is_noisy": bool(row["is_noisy"]),
            "noise_score": row["noise_score"],
            "noise_reasons": _json_list(row["noise_reasons_json"]),
            "total_hits": row["total_hits"],
            "fallback_used": fallback_used,
            "mode": "token_fallback" if fallback_used else "fts",
            "query_used": query,
            "original_query": original_query or query,
            "alias_used": alias_used,
            "normalized_used": normalized_used,
            "matched_tokens": sorted(row.get("matched_tokens", [])) if isinstance(row, dict) else [],
            "preview": _preview(row["text"], query),
        }
        for index, row in enumerate(rows, start=offset)
    ]


def search_library_diagnostics(
    query: str,
    results: List[Dict],
    kinds: List[str] | None = None,
    evidences: List[str] | None = None,
    document: str | None = None,
    output_dir: str | None = None,
    entities: List[str] | None = None,
    exclude_docs: List[str] | None = None,
    has_locator: bool = False,
) -> Dict:
    first = results[0] if results else {}
    mode = first.get("mode", "fts")
    effective_query = first.get("query_used", query)
    fallback_used = bool(first.get("fallback_used"))
    alias_used = first.get("alias_used")
    normalized_query = first.get("query_used") if first.get("normalized_used") else None
    token_list = _search_tokens(effective_query) if fallback_used else []
    total_hits = first.get("total_hits", 0) if results else 0
    locator_count = sum(1 for item in results if item.get("locator"))
    return {
        "original_query": query,
        "effective_query": effective_query,
        "mode": mode,
        "alias_used": alias_used,
        "normalized_query": normalized_query,
        "token_fallback_used": fallback_used,
        "fallback_tokens": token_list,
        "filters": {
            "kind": kinds or [],
            "evidence": evidences or [],
            "document": document,
            "output_dir": output_dir,
            "entity": entities or [],
            "has_locator": has_locator,
            "exclude_doc": exclude_docs or [],
        },
        "result_count": total_hits,
        "shown_count": len(results),
        "top_evidence_types": _count_facet(results, "evidence_type", 5),
        "top_document_kinds": _count_facet(results, "document_kind", 5),
        "locator_coverage": {
            "shown_with_locator": locator_count,
            "shown_count": len(results),
        },
        "hints": _search_diagnostic_hints(query, results, fallback_used, alias_used, normalized_query, token_list),
    }


def _search_diagnostic_hints(
    query: str,
    results: List[Dict],
    fallback_used: bool,
    alias_used: str | None,
    normalized_query: str | None,
    token_list: List[str],
) -> List[str]:
    if not results:
        return ["no results found; try an identifier, known alias, or shorter terms"]
    hints = []
    if normalized_query:
        hints.append("normalized identifier query was used after the original query returned 0 hits")
    elif alias_used:
        hints.append("alias was used after the original query returned 0 hits")
    elif fallback_used:
        hints.append("token fallback was used after the original query returned 0 hits")
        hints.append("token fallback ranking prioritized chunks matching more query tokens")
    else:
        hints.append("exact query matched")
    broad_terms = {"issue", "problem", "fault", "error", "control", "system"}
    if any(token in broad_terms for token in token_list or _search_tokens(query)):
        hints.append("broad terms may be causing wider results")
    if results and not any(item.get("locator") for item in results):
        hints.append("shown results have no locators; try --has-locator or a more specific query")
    return hints


_QUERY_ALIASES = {
    "冷却水": ["cooling water", "cooling"],
    "报警历史": ["alarm history", "alarm", "fault"],
    "密封液": ["sealing liquid", "seal liquid"],
    "操作手册": ["operation manual", "operating manual", "manual"],
    "均质器": ["homogenizer"],
    "cip sequence": ["CIP", "CIP process"],
    "cooling circuit": ["cooling water", "cooling"],
    "vacuum pump fault": ["vacuum pump alarm", "vacuum pump fault", "pump alarm", "fault pump"],
    "user password": ["user password", "password"],
}


def _query_expansions(query: str) -> List[Dict[str, str]]:
    variants = []
    seen = {query.casefold()}
    folded = " ".join(query.casefold().split())
    for key, aliases in _QUERY_ALIASES.items():
        if key.casefold() in folded:
            for alias in aliases:
                if alias.casefold() not in seen:
                    variants.append({"query": alias, "label": f"{key} -> {alias}", "kind": "alias"})
                    seen.add(alias.casefold())
    for variant in _identifier_query_variants(query):
        if variant.casefold() not in seen:
            variants.append({"query": variant, "label": f"{query} -> {variant}", "kind": "normalized"})
            seen.add(variant.casefold())
    return variants


def _identifier_query_variants(query: str) -> List[str]:
    compact = re.sub(r"[^A-Za-z0-9]", "", query).upper()
    if not re.fullmatch(r"[A-Z0-9]{6,}", compact):
        return []
    variants = []
    if compact != query:
        variants.append(compact)
    if re.search(r"\d", compact) and re.search(r"[A-Z]", compact):
        prefixes = [compact[:length] for length in range(min(len(compact), 6), 3, -1)]
        variants.extend(f"{prefix}*" for prefix in prefixes)
        th_match = re.match(r"(\d+TH)[A-Z]+", compact)
        if th_match:
            variants.append(f"{th_match.group(1)}*")
    return variants


def search_library_facets(
    library_db: Path,
    query: str,
    kinds: List[str] | None = None,
    evidences: List[str] | None = None,
    document: str | None = None,
    output_dir: str | None = None,
    entities: List[str] | None = None,
    exclude_docs: List[str] | None = None,
    has_locator: bool = False,
    limit: int = 8,
) -> Dict[str, List[Dict]]:
    results = search_library(
        library_db,
        query,
        limit=250,
        kinds=kinds or [],
        evidences=evidences or [],
        document=document,
        output_dir=output_dir,
        entities=entities or [],
        exclude_docs=exclude_docs or [],
        has_locator=has_locator,
    )
    chunk_ids = [item["chunk_id"] for item in results]
    facets: Dict[str, List[Dict]] = {
        "document_kind": _count_facet(results, "document_kind", limit),
        "evidence_type": _count_facet(results, "evidence_type", limit),
        "source_file": _count_facet(results, "source_file", limit),
        "output_dir": _count_facet(results, "output_dir", limit),
        "has_locator": _count_locator_facet(results),
        "entity": [],
    }
    if chunk_ids:
        db_path = _resolve_db_path(library_db)
        placeholders = ",".join("?" for _ in chunk_ids)
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"""
                SELECT e.entity_text AS value, COUNT(*) AS count
                FROM entity_mentions m
                JOIN entities e ON e.entity_id = m.entity_id
                WHERE m.chunk_id IN ({placeholders})
                GROUP BY e.entity_text
                ORDER BY count DESC, value
                LIMIT ?
                """,
                [*chunk_ids, limit],
            ).fetchall()
        facets["entity"] = [dict(row) for row in rows]
    return facets


def _count_facet(results: List[Dict], key: str, limit: int) -> List[Dict]:
    counts = Counter(item.get(key) or "" for item in results)
    counts.pop("", None)
    return [{"value": value, "count": count} for value, count in counts.most_common(limit)]


def _count_locator_facet(results: List[Dict]) -> List[Dict]:
    counts = Counter("yes" if item.get("locator") else "no" for item in results)
    return [{"value": value, "count": counts[value]} for value in ["yes", "no"] if counts[value]]


def _rank_adjustment_sql() -> str:
    return """
        CASE WHEN c.is_noisy THEN 10.0 + c.noise_score ELSE 0 END
        + CASE WHEN c.locator IS NOT NULL AND c.locator != '' THEN -0.30 ELSE 0.30 END
        + CASE c.evidence_type
            WHEN 'hmi_translation_row' THEN -0.45
            WHEN 'hmi_translation_table' THEN -0.35
            WHEN 'hmi_translation_group' THEN -0.35
            WHEN 'drawing_index' THEN -0.35
            WHEN 'page' THEN -0.25
            WHEN 'text_page' THEN -0.25
            WHEN 'section' THEN -0.10
            WHEN 'text' THEN 0.20
            ELSE 0
          END
    """


def _rank_adjustment_value(item: Dict) -> float:
    evidence_weights = {
        "hmi_translation_row": -0.45,
        "hmi_translation_table": -0.35,
        "hmi_translation_group": -0.35,
        "drawing_index": -0.35,
        "page": -0.25,
        "text_page": -0.25,
        "section": -0.10,
        "text": 0.20,
    }
    score = 0.0
    if item.get("is_noisy"):
        score += 10.0 + float(item.get("noise_score") or 0)
    score += -0.30 if item.get("locator") else 0.30
    score += evidence_weights.get(item.get("evidence_type"), 0)
    return score


def _fallback_rank_adjustment_value(item: Dict, tokens: List[str]) -> float:
    score = _rank_adjustment_value(item)
    failure_intent_tokens = {"alarm", "error", "fault", "problem", "trouble"}
    if item.get("document_kind") == "fault_catalog_pdf" and any(token in failure_intent_tokens for token in tokens):
        score -= 0.30
    return score


def _related_chunks(conn: sqlite3.Connection, chunk_id: str, limit: int) -> List[Dict]:
    target = conn.execute(
        """
        SELECT rowid AS row_number, doc_id, page_number, slide_number, sheet_name, section_number, locator
        FROM chunks
        WHERE chunk_id = ?
        """,
        (chunk_id,),
    ).fetchone()
    if target is None:
        return []
    rows = conn.execute(
        """
        SELECT c.chunk_id, c.title, c.text, c.evidence_type, c.locator,
               d.title AS document_title, d.source_file,
               CASE
                 WHEN c.page_number IS NOT NULL AND c.page_number = ? THEN 0
                 WHEN c.slide_number IS NOT NULL AND c.slide_number = ? THEN 0
                 WHEN c.sheet_name IS NOT NULL AND c.sheet_name = ? THEN 1
                 WHEN c.section_number IS NOT NULL AND c.section_number = ? THEN 1
                 ELSE 2
               END AS context_rank,
               ABS(c.rowid - ?) AS distance
        FROM chunks c
        JOIN documents d ON d.doc_id = c.doc_id
        WHERE c.doc_id = ? AND c.chunk_id != ?
        ORDER BY context_rank, distance
        LIMIT ?
        """,
        (
            target["page_number"],
            target["slide_number"],
            target["sheet_name"],
            target["section_number"],
            target["row_number"],
            target["doc_id"],
            chunk_id,
            limit,
        ),
    ).fetchall()
    return [
        {
            "chunk_id": row["chunk_id"],
            "document_title": row["document_title"],
            "source_file": row["source_file"],
            "chunk_title": row["title"],
            "evidence_type": row["evidence_type"],
            "locator": row["locator"],
            "preview": _preview(row["text"], limit=140),
        }
        for row in rows
    ]


def _is_multi_term_query(query: str) -> bool:
    return len(_search_tokens(query)) > 1


def _search_tokens(query: str) -> List[str]:
    stopwords = {"and", "or", "the", "a", "an", "of", "for", "to", "in", "on", "with"}
    tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9_]+", query)]
    return [token for token in tokens if len(token) >= 3 and token not in stopwords]


def locate_document(path: Path, query: str, limit: int = 20) -> List[Dict]:
    db_path = _resolve_db_path(path)
    like = f"%{query}%"
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT d.title, d.source_file, d.document_kind, d.output_dir, d.source_path,
                   COUNT(c.chunk_id) AS chunks_count
            FROM documents d
            LEFT JOIN chunks c ON c.doc_id = d.doc_id
            WHERE d.title LIKE ? OR d.source_file LIKE ? OR d.source_path LIKE ?
            GROUP BY d.doc_id
            ORDER BY d.source_file
            LIMIT ?
            """,
            (like, like, like, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def library_report(path: Path) -> Dict:
    output_or_db = path.expanduser().resolve()
    output_dir = output_or_db.parent if output_or_db.name == "library.db" else output_or_db
    index = _read_json(output_dir / "library_index.json", [])
    db_path = _resolve_db_path(output_or_db)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        evidence = dict(conn.execute("SELECT evidence_type, COUNT(*) FROM chunks GROUP BY evidence_type").fetchall())
        documents = [dict(row) for row in conn.execute("SELECT * FROM documents").fetchall()]
        chunks = [dict(row) for row in conn.execute("SELECT * FROM chunks").fetchall()]
        assets = [dict(row) for row in conn.execute("SELECT * FROM assets").fetchall()]
        page_level_docs = _page_level_searchable_documents(documents, chunks, assets)
        page_level_doc_ids = {doc["doc_id"] for doc in page_level_docs}
        missing_assets = conn.execute(
            "SELECT title, json_extract(key_metadata_json, '$.missing_assets_count') AS missing FROM documents WHERE CAST(json_extract(key_metadata_json, '$.missing_assets_count') AS INTEGER) > 0"
        ).fetchall()
        low_quality = conn.execute(
            "SELECT doc_id, title, quality_status FROM documents WHERE quality_status IN ('low_structure', 'visual_only')"
        ).fetchall()
        batches = conn.execute(
            "SELECT batch_id, COUNT(*) AS count FROM chunks WHERE batch_id IS NOT NULL AND batch_id != '' GROUP BY batch_id ORDER BY count DESC LIMIT 10"
        ).fetchall()
        noisy_chunks_count = conn.execute("SELECT COUNT(*) FROM chunks WHERE is_noisy = 1").fetchone()[0]
        noisy_documents = conn.execute(
            """
            SELECT d.title, d.source_file, COUNT(c.chunk_id) AS noisy_chunks_count
            FROM chunks c
            JOIN documents d ON d.doc_id = c.doc_id
            WHERE c.is_noisy = 1
            GROUP BY d.doc_id
            ORDER BY noisy_chunks_count DESC
            """
        ).fetchall()
        hmi_documents = conn.execute(
            "SELECT title, source_file, output_dir FROM documents WHERE document_kind = 'hmi_translation_xlsx'"
        ).fetchall()
    exports_dir = output_dir / "exports"
    export_files = sorted(path.name for path in exports_dir.glob("*.jsonl")) if exports_dir.exists() else []
    return {
        "documents_count": index.get("documents_count", 0),
        "chunks_count": index.get("chunks_count", 0),
        "entities_count": index.get("entities_count", 0),
        "document_kind_distribution": index.get("document_kind_distribution", {}),
        "evidence_type_distribution": evidence,
        "top_entities": index.get("top_entities", [])[:10],
        "top_batches": [dict(row) for row in batches],
        "missing_assets_summary": [dict(row) for row in missing_assets],
        "low_quality_documents": [dict(row) for row in low_quality if row["doc_id"] not in page_level_doc_ids],
        "page_level_pdf_documents": page_level_docs,
        "noisy_chunks_count": noisy_chunks_count,
        "noisy_documents": [dict(row) for row in noisy_documents],
        "hmi_translation_documents": [dict(row) for row in hmi_documents],
        "export_files_generated": export_files,
    }


def _normalize_records(docs: List[Dict], input_root: Path) -> Dict[str, List[Dict]]:
    documents = []
    chunks = []
    entity_index: Dict[tuple[str, str], Dict] = {}
    entity_mentions = []
    assets = []
    relations = []
    asset_seen = set()
    used_doc_ids = set()
    used_chunk_ids = set()

    for doc in docs:
        manifest = doc["manifest"]
        knowledge = doc.get("knowledge", {})
        source_map = doc.get("source_map", {})
        doc_chunks = doc.get("chunks", [])
        output_dir = doc["output_dir"]
        rel_output = _relative_or_absolute(output_dir, input_root)
        doc_id = _unique_record_id(_doc_id(manifest, knowledge, doc_chunks), rel_output, used_doc_ids)
        doc_kind = manifest.get("document_kind") or knowledge.get("document_kind", "")
        hmi_markdown = _hmi_markdown_for_doc(doc)
        if hmi_markdown and is_hmi_translation_xlsx(Path(manifest.get("source_file") or "document.xlsx"), hmi_markdown):
            doc_kind = "hmi_translation_xlsx"
            manifest = {**manifest, "document_kind": doc_kind, "quality_status": "structured_with_noise"}
            knowledge = {**knowledge, "document_kind": doc_kind, "quality_status": "structured_with_noise"}
            if not any(str(chunk.get("evidence_type", "")).startswith("hmi_translation_") for chunk in doc_chunks):
                doc_chunks = build_hmi_translation_chunks(hmi_markdown, manifest.get("source_file", ""), Path(manifest.get("source_file", "hmi_translation")).stem)
                source_map = {chunk["chunk_id"]: _source_map_from_chunk(chunk) for chunk in doc_chunks}
        title = knowledge.get("title") or Path(manifest.get("source_file") or output_dir.name).stem
        if doc_kind == "generic_pdf":
            doc_kind = _refine_generic_pdf_kind(manifest, title, doc)
        key_metadata = knowledge.get("key_metadata", {})
        tags = _dedupe_list([*(knowledge.get("tags", []) or []), *("hmi translation plc-hmi bilingual-text".split() if doc_kind == "hmi_translation_xlsx" else [])])
        documents.append(
            {
                "doc_id": doc_id,
                "title": title,
                "source_file": manifest.get("source_file") or knowledge.get("source_file", ""),
                "source_path": manifest.get("source_path") or key_metadata.get("source_path", ""),
                "document_kind": doc_kind,
                "quality_status": manifest.get("quality_status") or knowledge.get("quality_status", ""),
                "extraction_status": manifest.get("extraction_status") or knowledge.get("extraction_status", ""),
                "checksum": manifest.get("checksum") or key_metadata.get("checksum", ""),
                "converter": manifest.get("engine") or key_metadata.get("converter", ""),
                "tags": tags,
                "key_metadata": key_metadata,
                "output_dir": rel_output,
                "knowledge": knowledge,
                "manifest": manifest,
            }
        )
        doc_entities = _entities_from_json(doc.get("entities", {}))
        for entity in doc_entities:
            entity_id = _entity_id(entity["entity_type"], entity["entity_text"])
            entity_record = entity_index.setdefault(
                (entity["entity_type"], entity["normalized_text"]),
                {
                    "entity_id": entity_id,
                    "entity_text": entity["entity_text"],
                    "entity_type": entity["entity_type"],
                    "normalized_text": entity["normalized_text"],
                    "mentions": 0,
                },
            )
            entity_record["mentions"] += 1
            entity_mentions.append(
                {
                    "entity_id": entity_record["entity_id"],
                    "doc_id": doc_id,
                    "chunk_id": None,
                    "source_file": manifest.get("source_file", ""),
                    "locator": None,
                }
            )
            relations.append(
                {
                    "source_id": doc_id,
                    "source_type": "document",
                    "target_id": entity_record["entity_id"],
                    "target_type": "entity",
                    "relation_type": "document_mentions_entity",
                    "evidence": entity["entity_text"],
                    "locator": None,
                }
            )

        for chunk in doc_chunks:
            original_chunk_id = chunk.get("chunk_id")
            chunk_id = _unique_record_id(original_chunk_id or f"{doc_id}_chunk", doc_id, used_chunk_ids)
            source = source_map.get(original_chunk_id, {})
            heading_path = chunk.get("heading_path") or source.get("heading_path") or []
            chunk_title = _chunk_title(chunk, source, heading_path)
            chunk_record = {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "source_file": chunk.get("source_file") or manifest.get("source_file", ""),
                "evidence_type": chunk.get("evidence_type") or source.get("evidence_type"),
                "heading_path": heading_path,
                "title": chunk_title,
                "text": chunk.get("text", ""),
                "locator": chunk.get("locator") or source.get("locator"),
                "page_number": chunk.get("page_number") or source.get("page_number"),
                "slide_number": chunk.get("slide_number") or source.get("slide_number"),
                "sheet_name": chunk.get("sheet_name") or source.get("sheet_name"),
                "table_name": chunk.get("table_name") or source.get("table_name"),
                "section_number": chunk.get("section_number") or source.get("section_number"),
                "section_title": chunk.get("section_title") or source.get("section_title"),
                "topic_label": chunk.get("topic_label") or source.get("topic_label"),
                "batch_id": chunk.get("batch_id") or source.get("batch_id"),
                "confidence": chunk.get("confidence") or source.get("confidence"),
                "provenance_status": chunk.get("provenance_status") or source.get("provenance_status"),
                "group_path": chunk.get("group_path") or source.get("group_path"),
                "row_number": chunk.get("row_number") or source.get("row_number"),
                "source_map": source,
                "tags": chunk.get("tags") or tags,
            }
            noise = _noise_profile(chunk_record)
            chunk_record.update(noise)
            chunks.append(chunk_record)
            relations.append(_relation(doc_id, "document", chunk_record["chunk_id"], "chunk", "document_has_chunk", chunk_title, chunk_record["locator"]))
            if chunk_record["locator"]:
                relations.append(_relation(chunk_record["chunk_id"], "chunk", chunk_record["locator"], "locator", "chunk_has_source_locator", chunk_title, chunk_record["locator"]))
            if chunk_record["topic_label"] and chunk_record["slide_number"]:
                topic_id = _topic_id(chunk_record["topic_label"])
                relations.append(_relation(topic_id, "topic", chunk_record["chunk_id"], "chunk", "topic_contains_slide", chunk_title, chunk_record["locator"]))
            if chunk_record["batch_id"]:
                batch_id = _batch_node_id(chunk_record["batch_id"])
                relations.append(_relation(batch_id, "batch", chunk_record["chunk_id"], "chunk", "batch_mentioned_in_slide", chunk.get("evidence_snippet") or chunk_title, chunk_record["locator"]))
            image_path = chunk.get("image_path") or source.get("image_path")
            if image_path:
                asset_record = _asset_record(doc_id, image_path, chunk_record)
                key = (asset_record["doc_id"], asset_record["path"])
                if key not in asset_seen:
                    assets.append(asset_record)
                    asset_seen.add(key)
                    relations.append(_relation(doc_id, "document", asset_record["asset_id"], "asset", "document_has_asset", asset_record["path"], chunk_record["locator"]))
            for entity_record in entity_index.values():
                if _contains_entity(chunk_record, entity_record["entity_text"]):
                    entity_mentions.append(
                        {
                            "entity_id": entity_record["entity_id"],
                            "doc_id": doc_id,
                            "chunk_id": chunk_record["chunk_id"],
                            "source_file": chunk_record["source_file"],
                            "locator": chunk_record["locator"],
                        }
                    )
                    relations.append(
                        _relation(
                            chunk_record["chunk_id"],
                            "chunk",
                            entity_record["entity_id"],
                            "entity",
                            "chunk_mentions_entity",
                            entity_record["entity_text"],
                            chunk_record["locator"],
                        )
                    )
        assets_dir = output_dir / "assets"
        if assets_dir.exists():
            for path in sorted(p for p in assets_dir.rglob("*") if p.is_file()):
                rel_path = _relative_or_absolute(path, output_dir)
                key = (doc_id, rel_path)
                if key in asset_seen:
                    continue
                asset_record = {
                    "asset_id": _asset_id(doc_id, rel_path),
                    "doc_id": doc_id,
                    "path": rel_path,
                    "type": path.suffix.lower().lstrip(".") or "file",
                    "page_number": _number_from_name(path.name, "page"),
                    "slide_number": None,
                }
                assets.append(asset_record)
                asset_seen.add(key)
                relations.append(_relation(doc_id, "document", asset_record["asset_id"], "asset", "document_has_asset", rel_path, None))

    return {
        "documents": documents,
        "chunks": [chunk for chunk in chunks if chunk.get("chunk_id")],
        "entities": list(entity_index.values()),
        "entity_mentions": entity_mentions,
        "assets": assets,
        "relations": relations,
    }


def _write_database(db_path: Path, rows: Dict[str, List[Dict]]) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE documents (
              doc_id TEXT PRIMARY KEY,
              title TEXT,
              source_file TEXT,
              source_path TEXT,
              document_kind TEXT,
              quality_status TEXT,
              extraction_status TEXT,
              checksum TEXT,
              converter TEXT,
              tags_json TEXT,
              key_metadata_json TEXT,
              output_dir TEXT
            );
            CREATE TABLE chunks (
              chunk_id TEXT PRIMARY KEY,
              doc_id TEXT,
              evidence_type TEXT,
              heading_path_json TEXT,
              title TEXT,
              text TEXT,
              locator TEXT,
              page_number INTEGER,
              slide_number INTEGER,
              sheet_name TEXT,
              table_name TEXT,
              section_number TEXT,
              section_title TEXT,
              topic_label TEXT,
              batch_id TEXT,
              confidence TEXT,
              provenance_status TEXT,
              source_map_json TEXT,
              is_noisy INTEGER,
              noise_score REAL,
              noise_reasons_json TEXT
            );
            CREATE TABLE entities (
              entity_id TEXT PRIMARY KEY,
              entity_text TEXT,
              entity_type TEXT,
              normalized_text TEXT
            );
            CREATE TABLE entity_mentions (
              entity_id TEXT,
              doc_id TEXT,
              chunk_id TEXT,
              source_file TEXT,
              locator TEXT
            );
            CREATE TABLE assets (
              asset_id TEXT PRIMARY KEY,
              doc_id TEXT,
              path TEXT,
              type TEXT,
              page_number INTEGER,
              slide_number INTEGER
            );
            CREATE TABLE relations (
              source_id TEXT,
              source_type TEXT,
              target_id TEXT,
              target_type TEXT,
              relation_type TEXT,
              evidence TEXT,
              locator TEXT
            );
            CREATE VIRTUAL TABLE documents_fts USING fts5(doc_id UNINDEXED, title, source_file, document_kind, tags, entities);
            CREATE VIRTUAL TABLE chunks_fts USING fts5(chunk_id UNINDEXED, doc_id UNINDEXED, title, text, heading_path, locator, entities);
            """
        )
        for doc in rows["documents"]:
            conn.execute(
                "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    doc["doc_id"],
                    doc["title"],
                    doc["source_file"],
                    doc["source_path"],
                    doc["document_kind"],
                    doc["quality_status"],
                    doc["extraction_status"],
                    doc["checksum"],
                    doc["converter"],
                    _json(doc["tags"]),
                    _json(doc["key_metadata"]),
                    doc["output_dir"],
                ),
            )
            entity_text = " ".join(entity["entity_text"] for entity in rows["entities"] if any(m["doc_id"] == doc["doc_id"] and m["entity_id"] == entity["entity_id"] for m in rows["entity_mentions"]))
            conn.execute(
                "INSERT INTO documents_fts VALUES (?, ?, ?, ?, ?, ?)",
                (doc["doc_id"], doc["title"], doc["source_file"], doc["document_kind"], " ".join(doc["tags"]), entity_text),
            )
        for chunk in rows["chunks"]:
            conn.execute(
            "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    chunk["chunk_id"],
                    chunk["doc_id"],
                    chunk["evidence_type"],
                    _json(chunk["heading_path"]),
                    chunk["title"],
                    chunk["text"],
                    chunk["locator"],
                    chunk["page_number"],
                    chunk["slide_number"],
                    chunk["sheet_name"],
                    chunk["table_name"],
                    chunk["section_number"],
                    chunk["section_title"],
                    chunk["topic_label"],
                    chunk["batch_id"],
                    chunk["confidence"],
                    chunk["provenance_status"],
                    _json(chunk["source_map"]),
                    1 if chunk.get("is_noisy") else 0,
                    chunk.get("noise_score", 0),
                    _json(chunk.get("noise_reasons", [])),
                ),
            )
            chunk_entities = " ".join(
                entity["entity_text"]
                for entity in rows["entities"]
                if _contains_entity(chunk, entity["entity_text"])
            )
            conn.execute(
                "INSERT INTO chunks_fts VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    chunk["chunk_id"],
                    chunk["doc_id"],
                    chunk["title"],
                    _searchable_text(chunk["text"]),
                    " ".join(chunk["heading_path"]),
                    chunk["locator"] or "",
                    chunk_entities,
                ),
            )
        conn.executemany(
            "INSERT INTO entities VALUES (?, ?, ?, ?)",
            [(e["entity_id"], e["entity_text"], e["entity_type"], e["normalized_text"]) for e in rows["entities"]],
        )
        conn.executemany(
            "INSERT INTO entity_mentions VALUES (?, ?, ?, ?, ?)",
            [(m["entity_id"], m["doc_id"], m["chunk_id"], m["source_file"], m["locator"]) for m in rows["entity_mentions"]],
        )
        conn.executemany(
            "INSERT INTO assets VALUES (?, ?, ?, ?, ?, ?)",
            [(a["asset_id"], a["doc_id"], a["path"], a["type"], a["page_number"], a["slide_number"]) for a in rows["assets"]],
        )
        conn.executemany(
            "INSERT INTO relations VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(r["source_id"], r["source_type"], r["target_id"], r["target_type"], r["relation_type"], r["evidence"], r["locator"]) for r in rows["relations"]],
        )
        conn.commit()


def _build_index(rows: Dict[str, List[Dict]], warnings: List[str]) -> Dict:
    doc_counts = Counter(doc["document_kind"] for doc in rows["documents"])
    evidence_counts = Counter(chunk["evidence_type"] for chunk in rows["chunks"])
    entity_counts = Counter()
    for mention in rows["entity_mentions"]:
        if mention["chunk_id"] is None:
            entity_counts[mention["entity_id"]] += 1
    entity_by_id = {entity["entity_id"]: entity for entity in rows["entities"]}
    top_entities = _top_entities_by_normalized_text(entity_counts, entity_by_id)
    doc_entities = defaultdict(list)
    for mention in rows["entity_mentions"]:
        if mention["chunk_id"] is None:
            entity = entity_by_id.get(mention["entity_id"])
            if entity and entity["entity_text"] not in doc_entities[mention["doc_id"]]:
                doc_entities[mention["doc_id"]].append(entity["entity_text"])
    chunks_by_doc = Counter(chunk["doc_id"] for chunk in rows["chunks"])
    return {
        "documents_count": len(rows["documents"]),
        "chunks_count": len(rows["chunks"]),
        "entities_count": len(rows["entities"]),
        "document_kind_distribution": dict(doc_counts),
        "evidence_type_distribution": dict(evidence_counts),
        "top_entities": top_entities,
        "documents": [
            {
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "source_file": doc["source_file"],
                "document_kind": doc["document_kind"],
                "tags": doc["tags"],
                "key_metadata": doc["key_metadata"],
                "chunks_count": chunks_by_doc[doc["doc_id"]],
                "entities": doc_entities[doc["doc_id"]],
                "output_dir": doc["output_dir"],
            }
            for doc in rows["documents"]
        ],
        "warnings": warnings,
    }


def _top_entities_by_normalized_text(entity_counts: Counter, entity_by_id: Dict[str, Dict]) -> List[Dict]:
    grouped: Dict[str, Dict] = {}
    for entity_id, count in entity_counts.items():
        entity = entity_by_id.get(entity_id)
        if not entity:
            continue
        normalized = entity["normalized_text"]
        item = grouped.setdefault(
            normalized,
            {
                "entity_id": entity_id,
                "entity_ids": [],
                "entity_text": entity["entity_text"],
                "entity_type": entity["entity_type"],
                "entity_types": [],
                "normalized_text": normalized,
                "count": 0,
            },
        )
        item["entity_ids"].append(entity_id)
        if entity["entity_type"] not in item["entity_types"]:
            item["entity_types"].append(entity["entity_type"])
        item["count"] += count
        if len(entity["entity_text"]) < len(item["entity_text"]):
            item["entity_text"] = entity["entity_text"]
            item["entity_id"] = entity_id
            item["entity_type"] = entity["entity_type"]
    return sorted(grouped.values(), key=lambda item: (-item["count"], item["entity_text"].casefold()))[:25]


def _build_library_manifest(input_root: Path, rows: Dict[str, List[Dict]], warnings: List[str]) -> Dict:
    return {
        "schema_version": LIBRARY_SCHEMA_VERSION,
        "built_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "input_output_root": str(input_root),
        "documents_count": len(rows["documents"]),
        "chunks_count": len(rows["chunks"]),
        "entities_count": len(rows["entities"]),
        "warnings_count": len(warnings),
        "exports_count": 4,
        "office2md_version": LIBRARY_RELEASE_LABEL,
        "release_label": LIBRARY_RELEASE_LABEL,
    }


def _build_graph(rows: Dict[str, List[Dict]]) -> Dict:
    nodes = []
    edges = []
    for doc in rows["documents"]:
        nodes.append({"id": doc["doc_id"], "type": "document", "label": doc["title"], "document_kind": doc["document_kind"]})
    for chunk in rows["chunks"]:
        nodes.append({"id": chunk["chunk_id"], "type": "chunk", "label": chunk["title"], "evidence_type": chunk["evidence_type"]})
        if chunk.get("topic_label"):
            nodes.append({"id": _topic_id(chunk["topic_label"]), "type": "topic", "label": chunk["topic_label"]})
        if chunk.get("batch_id"):
            nodes.append({"id": _batch_node_id(chunk["batch_id"]), "type": "batch", "label": chunk["batch_id"]})
    for entity in rows["entities"]:
        nodes.append({"id": entity["entity_id"], "type": "entity", "label": entity["entity_text"], "entity_type": entity["entity_type"]})
    for asset in rows["assets"]:
        nodes.append({"id": asset["asset_id"], "type": "asset", "label": asset["path"]})
    seen_nodes = {}
    for node in nodes:
        seen_nodes[node["id"]] = node
    for relation in rows["relations"]:
        edges.append(relation)
    return {"nodes": list(seen_nodes.values()), "edges": edges}


def _write_markdown_portal(output_dir: Path, rows: Dict[str, List[Dict]], index: Dict, warnings: List[str]) -> None:
    docs = rows["documents"]
    chunks = rows["chunks"]
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "_library.md").write_text(_library_md(rows, index, warnings), encoding="utf-8")
    (output_dir / "_documents.md").write_text(_documents_md(docs), encoding="utf-8")
    (output_dir / "_entities.md").write_text(_entities_md(rows), encoding="utf-8")
    (output_dir / "_topics.md").write_text(_topics_md(chunks), encoding="utf-8")
    (output_dir / "_batches.md").write_text(_batches_md(chunks, docs), encoding="utf-8")
    (output_dir / "_quality_report.md").write_text(_quality_md(rows, warnings), encoding="utf-8")


def _library_md(rows: Dict[str, List[Dict]], index: Dict, warnings: List[str]) -> str:
    lines = ["# Knowledge Library", "", "## Library Summary", ""]
    lines.extend(
        [
            f"- documents_count: {index['documents_count']}",
            f"- chunks_count: {index['chunks_count']}",
            f"- entities_count: {index['entities_count']}",
            "",
            "## Document Kind Distribution",
            "",
        ]
    )
    lines.extend(f"- {kind}: {count}" for kind, count in index["document_kind_distribution"].items())
    lines.extend(["", "## Documents by Type", ""])
    by_kind = defaultdict(list)
    for doc in rows["documents"]:
        by_kind[doc["document_kind"]].append(doc)
    for kind, docs in sorted(by_kind.items()):
        lines.extend([f"### {kind}", ""])
        lines.extend(f"- [{doc['title']}]({doc['output_dir']}/document.md)" for doc in docs)
        lines.append("")
    lines.extend(["## Key Entities", ""])
    lines.extend(
        f"- {item['entity_text']} ({', '.join(item.get('entity_types') or [item.get('entity_type', '')])}): {item['count']}"
        for item in index["top_entities"][:15]
    )
    lines.extend(["", "## Key Topics", ""])
    lines.extend(f"- {topic}" for topic in sorted({c["topic_label"] for c in rows["chunks"] if c.get("topic_label")})[:30])
    lines.extend(["", "## Batch IDs", ""])
    lines.extend(f"- {batch}" for batch in sorted({c["batch_id"] for c in rows["chunks"] if c.get("batch_id")})[:50])
    lines.extend(["", "## Quality Issues", ""])
    issues = _quality_issues(rows, warnings)
    lines.extend(f"- {issue}" for issue in issues) if issues else lines.append("_No quality issues detected._")
    return "\n".join(lines) + "\n"


def _documents_md(docs: List[Dict]) -> str:
    lines = ["# Documents", ""]
    by_kind = defaultdict(list)
    for doc in docs:
        by_kind[doc["document_kind"]].append(doc)
    for kind, items in sorted(by_kind.items()):
        lines.extend([f"## {kind}", "", "| Title | Source File | Quality | Output |", "|---|---|---|---|"])
        for doc in items:
            lines.append(f"| {doc['title']} | {doc['source_file']} | {doc['quality_status']} | {doc['output_dir']} |")
        lines.append("")
    return "\n".join(lines)


def _entities_md(rows: Dict[str, List[Dict]]) -> str:
    lines = ["# Entities", ""]
    by_type = defaultdict(list)
    docs_by_id = {doc["doc_id"]: doc for doc in rows["documents"]}
    mentions_by_entity = defaultdict(set)
    for mention in rows["entity_mentions"]:
        if mention["chunk_id"] is None and mention["doc_id"] in docs_by_id:
            mentions_by_entity[mention["entity_id"]].add(docs_by_id[mention["doc_id"]]["title"])
    for entity in rows["entities"]:
        by_type[entity["entity_type"]].append(entity)
    for entity_type, entities in sorted(by_type.items()):
        lines.extend([f"## {entity_type}", ""])
        for entity in sorted(entities, key=lambda item: item["entity_text"].lower()):
            docs = ", ".join(sorted(mentions_by_entity[entity["entity_id"]]))
            lines.append(f"- {entity['entity_text']}: {docs}")
        lines.append("")
    return "\n".join(lines)


def _topics_md(chunks: List[Dict]) -> str:
    topics = defaultdict(list)
    for chunk in chunks:
        label = chunk.get("topic_label") or chunk.get("section_title")
        if not label and chunk.get("evidence_type") == "drawing_index":
            heading = chunk.get("heading_path") or []
            label = heading[-1] if heading else chunk.get("title")
        if not label and chunk.get("evidence_type") == "table_section":
            label = chunk.get("title")
        if label:
            topics[label].append(chunk)
    lines = ["# Topics", ""]
    for topic, items in sorted(topics.items()):
        locators = ", ".join(sorted({item.get("locator") or "" for item in items if item.get("locator")})[:10])
        lines.append(f"- {topic}: {len(items)} chunks; {locators}")
    return "\n".join(lines) + "\n"


def _batches_md(chunks: List[Dict], docs: List[Dict]) -> str:
    docs_by_id = {doc["doc_id"]: doc for doc in docs}
    by_batch = defaultdict(list)
    for chunk in chunks:
        if chunk.get("batch_id"):
            by_batch[chunk["batch_id"]].append(chunk)
    lines = ["# Batches", ""]
    for batch_id, items in sorted(by_batch.items()):
        lines.extend([f"## {batch_id}", ""])
        for item in items:
            doc = docs_by_id.get(item["doc_id"], {})
            source = doc.get("title", item["source_file"])
            source_map = item.get("source_map") or {}
            evidence = source_map.get("evidence_snippet") or _preview(item.get("text", ""), batch_id)
            locators = source_map.get("locators") or [item.get("locator")]
            lines.append(
                f"- {source}: {', '.join(str(locator) for locator in locators if locator)}; confidence={item.get('confidence') or ''}; {evidence}"
            )
        lines.append("")
    return "\n".join(lines)


def _quality_md(rows: Dict[str, List[Dict]], warnings: List[str]) -> str:
    lines = ["# Quality Report", "", "## Failed Documents", ""]
    lines.extend(f"- {warning}" for warning in warnings if "failed" in warning.lower()) or lines.append("_None._")
    page_level_docs = _page_level_searchable_documents(rows["documents"], rows["chunks"], rows["assets"])
    page_level_doc_ids = {doc["doc_id"] for doc in page_level_docs}
    lines.extend(["", "## Page-Level Searchable PDFs", ""])
    lines.append(f"- page_level_pdf_count: {len(page_level_docs)}")
    for doc in page_level_docs[:100]:
        lines.append(f"- {doc['title']}: {doc['document_kind']}, {doc['quality_status']}, locators={doc['locator_chunks']}, assets={doc['asset_count']}")
    if not page_level_docs:
        lines.append("_None._")
    lines.extend(["", "## Low Structure", ""])
    low = [doc for doc in rows["documents"] if doc["quality_status"] == "low_structure" and doc["doc_id"] not in page_level_doc_ids]
    lines.extend(f"- {doc['title']}" for doc in low) or lines.append("_None._")
    lines.extend(["", "## Visual Only / Image Only", ""])
    visual = [doc for doc in rows["documents"] if doc["quality_status"] == "visual_only" or doc["extraction_status"] == "image_only"]
    lines.extend(f"- {doc['title']}" for doc in visual) or lines.append("_None._")
    lines.extend(["", "## Missing / Embedded Assets", ""])
    asset_rows = 0
    for doc in rows["documents"]:
        metadata = doc.get("key_metadata") or {}
        manifest = doc.get("manifest") or {}
        missing = metadata.get("missing_assets_count") or manifest.get("missing_assets_count") or 0
        embedded = metadata.get("embedded_images_count") or manifest.get("embedded_images_count") or 0
        if missing or embedded:
            asset_rows += 1
            lines.append(f"- {doc['title']}: missing_assets_count={missing}, embedded_images_count={embedded}")
    if not asset_rows:
        lines.append("_None._")
    lines.extend(["", "## Chunks Without Locator", ""])
    missing_locator = [chunk for chunk in rows["chunks"] if not chunk.get("locator")]
    lines.extend(f"- {chunk['chunk_id']}: {chunk['title']}" for chunk in missing_locator[:100]) or lines.append("_None._")
    lines.extend(["", "## Noisy Chunks", ""])
    noisy = [chunk for chunk in rows["chunks"] if chunk.get("is_noisy")]
    lines.append(f"- noisy_chunks_count: {len(noisy)}")
    noisy_by_doc = Counter(chunk["doc_id"] for chunk in noisy)
    docs_by_id = {doc["doc_id"]: doc for doc in rows["documents"]}
    if noisy_by_doc:
        for doc_id, count in noisy_by_doc.most_common(20):
            doc = docs_by_id.get(doc_id, {})
            lines.append(f"- {doc.get('title', doc_id)}: {count}")
    else:
        lines.append("_None._")
    lines.extend(["", "## HMI Translation Documents", ""])
    hmi_docs = [doc for doc in rows["documents"] if doc["document_kind"] == "hmi_translation_xlsx"]
    lines.extend(f"- {doc['title']}: {doc['output_dir']}" for doc in hmi_docs) or lines.append("_None._")
    raw_text = [chunk for chunk in rows["chunks"] if chunk.get("evidence_type") == "text" and chunk.get("provenance_status") == "raw_markdown"]
    lines.extend(["", "## Raw Text Chunks", "", f"- raw_text_chunks_count: {len(raw_text)}"])
    lines.extend(["", "## Documents Without Entities", ""])
    doc_mentions = {mention["doc_id"] for mention in rows["entity_mentions"] if mention["chunk_id"] is None}
    no_entities = [doc for doc in rows["documents"] if doc["doc_id"] not in doc_mentions]
    lines.extend(f"- {doc['title']}" for doc in no_entities) or lines.append("_None._")
    lines.extend(
        [
            "",
            "## Search Recommendations",
            "",
            "- PLC/HMI translation can be filtered with `--kind hmi_translation_xlsx`.",
            "- Wiring/PLC drawing search can use `--evidence drawing_index --kind technical_drawing_pdf`.",
            "- Suppress translation table hits with `--exclude-doc Translation`.",
        ]
    )
    return "\n".join(lines) + "\n"


def _page_level_searchable_documents(documents: List[Dict], chunks: List[Dict], assets: List[Dict]) -> List[Dict]:
    chunks_by_doc: Dict[str, List[Dict]] = defaultdict(list)
    assets_by_doc = Counter(asset["doc_id"] for asset in assets)
    for chunk in chunks:
        chunks_by_doc[chunk["doc_id"]].append(chunk)
    docs = []
    for doc in documents:
        if doc.get("quality_status") != "low_structure":
            continue
        if not str(doc.get("document_kind", "")).endswith("_pdf") and doc.get("document_kind") != "generic_pdf":
            continue
        doc_chunks = chunks_by_doc.get(doc["doc_id"], [])
        page_chunks = [chunk for chunk in doc_chunks if chunk.get("evidence_type") in {"page", "text_page", "drawing_index"}]
        locator_chunks = [chunk for chunk in page_chunks if chunk.get("locator")]
        if page_chunks and locator_chunks and assets_by_doc[doc["doc_id"]] and not any(chunk.get("is_noisy") for chunk in doc_chunks):
            docs.append(
                {
                    "doc_id": doc["doc_id"],
                    "title": doc["title"],
                    "source_file": doc.get("source_file", ""),
                    "document_kind": doc.get("document_kind", ""),
                    "quality_status": doc.get("quality_status", ""),
                    "page_level_chunks": len(page_chunks),
                    "locator_chunks": len(locator_chunks),
                    "asset_count": assets_by_doc[doc["doc_id"]],
                }
            )
    return docs


def _write_interop_exports(exports_dir: Path, rows: Dict[str, List[Dict]]) -> None:
    if exports_dir.exists():
        shutil.rmtree(exports_dir)
    exports_dir.mkdir(parents=True, exist_ok=True)
    docs_by_id = {doc["doc_id"]: doc for doc in rows["documents"]}
    paths = {
        "llamaindex": exports_dir / "llamaindex_documents.jsonl",
        "haystack": exports_dir / "haystack_documents.jsonl",
        "txtai": exports_dir / "txtai_rows.jsonl",
        "graphrag": exports_dir / "graphrag_input.jsonl",
    }
    handles = {name: path.open("w", encoding="utf-8") for name, path in paths.items()}
    try:
        for chunk in rows["chunks"]:
            doc = docs_by_id.get(chunk["doc_id"], {})
            metadata = _chunk_metadata(chunk, doc)
            handles["llamaindex"].write(_jsonl({"id": chunk["chunk_id"], "text": chunk["text"], "metadata": metadata}))
            handles["haystack"].write(_jsonl({"id": chunk["chunk_id"], "content": chunk["text"], "meta": metadata}))
            handles["txtai"].write(_jsonl({"id": chunk["chunk_id"], "text": chunk["text"], "tags": doc.get("tags", []), "metadata": metadata}))
            handles["graphrag"].write(
                _jsonl(
                    {
                        "id": chunk["chunk_id"],
                        "text": chunk["text"],
                        "title": chunk["title"],
                        "source": doc.get("source_file", ""),
                        "metadata": metadata,
                    }
                )
            )
    finally:
        for handle in handles.values():
            handle.close()


def _chunk_metadata(chunk: Dict, doc: Dict) -> Dict:
    return {
        "doc_id": chunk["doc_id"],
        "source_file": doc.get("source_file", chunk.get("source_file", "")),
        "document_kind": doc.get("document_kind", ""),
        "evidence_type": chunk.get("evidence_type"),
        "locator": chunk.get("locator"),
        "heading_path": chunk.get("heading_path", []),
        "page_number": chunk.get("page_number"),
        "slide_number": chunk.get("slide_number"),
        "sheet_name": chunk.get("sheet_name"),
        "table_name": chunk.get("table_name"),
        "topic_label": chunk.get("topic_label"),
        "batch_id": chunk.get("batch_id"),
        "group_path": chunk.get("group_path") or (chunk.get("source_map") or {}).get("group_path"),
        "row_number": chunk.get("row_number") or (chunk.get("source_map") or {}).get("row_number"),
        "is_noisy": chunk.get("is_noisy", False),
        "noise_score": chunk.get("noise_score", 0),
    }


def _read_json(path: Path, warnings: List[str]) -> Dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"could not read json {path}: {exc}")
        return {}


def _read_jsonl(path: Path, warnings: List[str]) -> List[Dict]:
    rows = []
    try:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                warnings.append(f"could not read jsonl {path}:{line_number}: {exc}")
    except OSError as exc:
        warnings.append(f"could not read jsonl {path}: {exc}")
    return rows


def _write_json(path: Path, data: Dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def _jsonl(data: Dict) -> str:
    return json.dumps(data, ensure_ascii=False) + "\n"


def _doc_id(manifest: Dict, knowledge: Dict, chunks: List[Dict]) -> str:
    for chunk in chunks:
        if chunk.get("doc_id"):
            return str(chunk["doc_id"])
    checksum = manifest.get("checksum") or knowledge.get("key_metadata", {}).get("checksum") or manifest.get("source_file", "document")
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(checksum).split(":", 1)[-1][:32])


def _unique_record_id(base_id: Any, suffix_hint: Any, used: set[str]) -> str:
    base = re.sub(r"[^A-Za-z0-9_-]+", "_", str(base_id or "record")).strip("_") or "record"
    if base not in used:
        used.add(base)
        return base
    suffix = re.sub(r"[^A-Za-z0-9_-]+", "_", str(suffix_hint or "duplicate")).strip("_") or "duplicate"
    candidate = f"{base}-{suffix}"
    counter = 2
    while candidate in used:
        candidate = f"{base}-{suffix}-{counter}"
        counter += 1
    used.add(candidate)
    return candidate


def _refine_generic_pdf_kind(manifest: Dict, title: str, doc: Dict) -> str:
    source_file = manifest.get("source_file") or f"{title}.pdf"
    if not str(source_file).lower().endswith(".pdf"):
        return "generic_pdf"
    text = f"{title}\n{_document_preview_text(doc)}"
    return classify_obvious_pdf_subtype(Path(source_file), text) or "generic_pdf"


def _document_preview_text(doc: Dict, limit: int = 4000) -> str:
    path = doc.get("document_md") or doc.get("document_raw_md")
    if not path:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def _entities_from_json(data: Dict) -> List[Dict]:
    entities = []
    for entity_type, values in data.items():
        if not isinstance(values, list):
            continue
        for value in values:
            if not isinstance(value, (str, int, float)):
                continue
            text = str(value).strip()
            if not text:
                continue
            entities.append(
                {
                    "entity_text": text,
                    "entity_type": entity_type,
                    "normalized_text": _normalize_entity(text),
                }
            )
    return entities


def _entity_id(entity_type: str, text: str) -> str:
    return f"entity:{entity_type}:{_normalize_entity(text)}"


def _normalize_entity(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def _chunk_title(chunk: Dict, source: Dict, heading_path: List[str]) -> str:
    for value in [
        chunk.get("slide_title"),
        chunk.get("topic_label"),
        chunk.get("batch_id"),
        chunk.get("section_title"),
        chunk.get("group_path"),
        chunk.get("table_name"),
        source.get("slide_title"),
        source.get("group_path"),
    ]:
        if value:
            return str(value)
    return str(heading_path[-1]) if heading_path else chunk.get("chunk_id", "chunk")


def _contains_entity(chunk: Dict, entity_text: str) -> bool:
    if not entity_text or len(entity_text) < 2:
        return False
    haystack = " ".join(
        [
            chunk.get("title") or "",
            chunk.get("text") or "",
            chunk.get("locator") or "",
            " ".join(chunk.get("heading_path") or []),
        ]
    ).casefold()
    return entity_text.casefold() in haystack


def _relation(source_id: str, source_type: str, target_id: str, target_type: str, relation_type: str, evidence: str | None, locator: str | None) -> Dict:
    return {
        "source_id": source_id,
        "source_type": source_type,
        "target_id": target_id,
        "target_type": target_type,
        "relation_type": relation_type,
        "evidence": evidence,
        "locator": locator,
    }


def _asset_record(doc_id: str, image_path: str, chunk: Dict) -> Dict:
    return {
        "asset_id": _asset_id(doc_id, image_path),
        "doc_id": doc_id,
        "path": image_path,
        "type": Path(image_path).suffix.lower().lstrip(".") or "image",
        "page_number": chunk.get("page_number"),
        "slide_number": chunk.get("slide_number"),
    }


def _asset_id(doc_id: str, path: str) -> str:
    return f"asset:{doc_id}:{re.sub(r'[^A-Za-z0-9_-]+', '_', path)}"


def _topic_id(topic: str) -> str:
    return f"topic:{re.sub(r'[^A-Za-z0-9_-]+', '_', topic.casefold()).strip('_')}"


def _batch_node_id(batch_id: str) -> str:
    return f"batch:{batch_id}"


def _relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _number_from_name(name: str, prefix: str) -> int | None:
    match = re.search(rf"{re.escape(prefix)}[_-]?(\d+)", name, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def _preview(text: str, query: str = "", limit: int = 220) -> str:
    clean = _searchable_text(text)
    if query:
        terms = _search_tokens(query) or query.split()
        index = min(
            (found for term in terms if (found := clean.casefold().find(term.casefold())) >= 0),
            default=-1,
        )
        if index > 40:
            clean = "..." + clean[index - 40 :]
    return clean[:limit].rstrip() + ("..." if len(clean) > limit else "")


def _search_filters(
    kinds: List[str],
    evidences: List[str],
    document: str | None,
    output_dir: str | None,
    entities: List[str],
    exclude_docs: List[str],
    has_locator: bool,
) -> tuple[str, List[Any]]:
    clauses = []
    params: List[Any] = []
    if kinds:
        clauses.append(f"d.document_kind IN ({', '.join('?' for _ in kinds)})")
        params.extend(kinds)
    if evidences:
        clauses.append(f"c.evidence_type IN ({', '.join('?' for _ in evidences)})")
        params.extend(evidences)
    if document:
        clauses.append("(d.title LIKE ? OR d.source_file LIKE ? OR d.source_path LIKE ?)")
        like = f"%{document}%"
        params.extend([like, like, like])
    if output_dir:
        clauses.append("d.output_dir LIKE ?")
        params.append(f"%{output_dir}%")
    for entity in entities:
        clauses.append(
            """
            EXISTS (
                SELECT 1
                FROM entity_mentions m
                JOIN entities e ON e.entity_id = m.entity_id
                WHERE m.chunk_id = c.chunk_id
                  AND (e.entity_text LIKE ? OR e.normalized_text LIKE ?)
            )
            """
        )
        like = f"%{entity}%"
        params.extend([like, like.casefold()])
    for value in exclude_docs:
        clauses.append("d.title NOT LIKE ? AND d.source_file NOT LIKE ?")
        like = f"%{value}%"
        params.extend([like, like])
    if has_locator:
        clauses.append("c.locator IS NOT NULL AND c.locator != ''")
    return (" AND " + " AND ".join(f"({clause})" for clause in clauses)) if clauses else "", params


def _hmi_markdown_for_doc(doc: Dict) -> str:
    for key in ["document_raw_md", "document_md"]:
        path = doc.get(key)
        if path:
            try:
                return Path(path).read_text(encoding="utf-8")
            except OSError:
                continue
    return "\n".join(chunk.get("text", "") for chunk in doc.get("chunks", []))


def _source_map_from_chunk(chunk: Dict) -> Dict:
    keys = [
        "source_file",
        "heading_path",
        "locator",
        "evidence_type",
        "provenance_status",
        "sheet_name",
        "table_name",
        "row_start",
        "row_end",
        "row_number",
        "group_path",
        "hmi_path_tail",
        "english_text",
        "chinese_text",
        "unit",
    ]
    return {key: chunk.get(key) for key in keys}


def _noise_profile(chunk: Dict) -> Dict:
    text = chunk.get("text") or ""
    reasons = []
    score = 0.0
    tokens = max(len(re.findall(r"\S+", text)), 1)
    nan_count = len(re.findall(r"\bNaN\b", text, flags=re.IGNORECASE))
    if nan_count / tokens > 0.08:
        reasons.append("nan_density")
        score += min(nan_count / tokens * 5, 3)
    base64_count = len(_BASE64_RE.findall(text))
    if base64_count:
        reasons.append("base64_like")
        score += min(base64_count * 1.5, 4)
    path_count = len(re.findall(r"[A-Za-z]:\\|\\\\|PLC\+HMI|\\Bilder\\|\\Textfeld", text))
    if path_count / tokens > 0.03:
        reasons.append("windows_or_hmi_path_density")
        score += min(path_count / tokens * 5, 2.5)
    tag_count = len(re.findall(r"<[^>\n]{2,40}>", text))
    if tag_count / tokens > 0.05:
        reasons.append("xml_html_tag_density")
        score += min(tag_count / tokens * 4, 2)
    if not chunk.get("locator"):
        reasons.append("missing_locator")
        score += 1
    alpha_words = len(re.findall(r"\b[A-Za-z]{3,}\b", text))
    if alpha_words / tokens < 0.15 and len(text) > 200:
        reasons.append("low_natural_language_ratio")
        score += 1
    return {
        "is_noisy": score >= 2.0,
        "noise_score": round(score, 3),
        "noise_reasons": _dedupe_list(reasons),
    }


_BASE64_RE = re.compile(r"\b[A-Za-z0-9+/]{60,}={0,2}\b")


def _searchable_text(text: str) -> str:
    clean = text or ""
    clean = _BASE64_RE.sub("[base64]", clean)
    clean = re.sub(r"\bNaN\b(?:\s*[|,;]\s*\bNaN\b){2,}", "[NaN omitted]", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bNaN\b", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"(?:[A-Za-z]:\\|\\\\|SY\d+_PLC\+HMI)[^\s|]{40,}", _path_tail, clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def _path_tail(match: re.Match) -> str:
    value = match.group(0).replace("\\_", "_")
    parts = [part for part in value.split("\\") if part]
    return ".../" + "/".join(parts[-3:]) if len(parts) > 3 else value


def _json_list(value: str | None) -> List:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _dedupe_list(values: List[Any]) -> List[Any]:
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _quality_issues(rows: Dict[str, List[Dict]], warnings: List[str]) -> List[str]:
    issues = list(warnings)
    for doc in rows["documents"]:
        if doc["quality_status"] in {"low_structure", "visual_only"} or doc["extraction_status"] == "image_only":
            issues.append(f"{doc['title']}: quality_status={doc['quality_status']}, extraction_status={doc['extraction_status']}")
        metadata = doc.get("key_metadata") or {}
        manifest = doc.get("manifest") or {}
        missing = metadata.get("missing_assets_count") or manifest.get("missing_assets_count") or 0
        embedded = metadata.get("embedded_images_count") or manifest.get("embedded_images_count") or 0
        if missing or embedded:
            issues.append(f"{doc['title']}: missing_assets_count={missing}, embedded_images_count={embedded}")
    missing_locator = sum(1 for chunk in rows["chunks"] if not chunk.get("locator"))
    if missing_locator:
        issues.append(f"chunks without locator: {missing_locator}")
    doc_mentions = {mention["doc_id"] for mention in rows["entity_mentions"] if mention["chunk_id"] is None}
    without_entities = [doc["title"] for doc in rows["documents"] if doc["doc_id"] not in doc_mentions]
    if without_entities:
        issues.append(f"documents without entities: {', '.join(without_entities)}")
    return issues


def _resolve_db_path(path: Path) -> Path:
    candidate = path.expanduser().resolve()
    if candidate.is_dir():
        candidate = candidate / "library.db"
    return candidate
