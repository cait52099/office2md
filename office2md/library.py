import json
import re
import shutil
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


LIBRARY_SCHEMA_VERSION = "1"
LIBRARY_RELEASE_LABEL = "v0.2.0-rc1"


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
        documents.append(doc)
    return documents, warnings


def search_library(library_db: Path, query: str, limit: int = 10) -> List[Dict]:
    db_path = _resolve_db_path(library_db)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT c.chunk_id, c.title, c.text, c.evidence_type, c.locator,
                       d.title AS document_title, d.document_kind, bm25(chunks_fts) AS score
                FROM chunks_fts
                JOIN chunks c ON c.chunk_id = chunks_fts.chunk_id
                JOIN documents d ON d.doc_id = c.doc_id
                WHERE chunks_fts MATCH ?
                ORDER BY score
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            like = f"%{query}%"
            rows = conn.execute(
                """
                SELECT c.chunk_id, c.title, c.text, c.evidence_type, c.locator,
                       d.title AS document_title, d.document_kind, 0 AS score
                FROM chunks c
                JOIN documents d ON d.doc_id = c.doc_id
                WHERE c.text LIKE ? OR c.title LIKE ? OR c.heading_path_json LIKE ? OR c.locator LIKE ?
                LIMIT ?
                """,
                (like, like, like, like, limit),
            ).fetchall()
    return [
        {
            "rank": index + 1,
            "document_title": row["document_title"],
            "document_kind": row["document_kind"],
            "chunk_title": row["title"],
            "evidence_type": row["evidence_type"],
            "locator": row["locator"],
            "preview": _preview(row["text"], query),
        }
        for index, row in enumerate(rows)
    ]


def library_report(path: Path) -> Dict:
    output_or_db = path.expanduser().resolve()
    output_dir = output_or_db.parent if output_or_db.name == "library.db" else output_or_db
    index = _read_json(output_dir / "library_index.json", [])
    db_path = _resolve_db_path(output_or_db)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        evidence = dict(conn.execute("SELECT evidence_type, COUNT(*) FROM chunks GROUP BY evidence_type").fetchall())
        missing_assets = conn.execute(
            "SELECT title, json_extract(key_metadata_json, '$.missing_assets_count') AS missing FROM documents WHERE CAST(json_extract(key_metadata_json, '$.missing_assets_count') AS INTEGER) > 0"
        ).fetchall()
        low_quality = conn.execute(
            "SELECT title, quality_status FROM documents WHERE quality_status IN ('low_structure', 'visual_only')"
        ).fetchall()
        batches = conn.execute(
            "SELECT batch_id, COUNT(*) AS count FROM chunks WHERE batch_id IS NOT NULL AND batch_id != '' GROUP BY batch_id ORDER BY count DESC LIMIT 10"
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
        "low_quality_documents": [dict(row) for row in low_quality],
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

    for doc in docs:
        manifest = doc["manifest"]
        knowledge = doc.get("knowledge", {})
        source_map = doc.get("source_map", {})
        doc_chunks = doc.get("chunks", [])
        doc_id = _doc_id(manifest, knowledge, doc_chunks)
        output_dir = doc["output_dir"]
        rel_output = _relative_or_absolute(output_dir, input_root)
        title = knowledge.get("title") or Path(manifest.get("source_file") or output_dir.name).stem
        key_metadata = knowledge.get("key_metadata", {})
        tags = knowledge.get("tags", [])
        documents.append(
            {
                "doc_id": doc_id,
                "title": title,
                "source_file": manifest.get("source_file") or knowledge.get("source_file", ""),
                "source_path": manifest.get("source_path") or key_metadata.get("source_path", ""),
                "document_kind": manifest.get("document_kind") or knowledge.get("document_kind", ""),
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
            source = source_map.get(chunk.get("chunk_id"), {})
            heading_path = chunk.get("heading_path") or source.get("heading_path") or []
            chunk_title = _chunk_title(chunk, source, heading_path)
            chunk_record = {
                "chunk_id": chunk.get("chunk_id"),
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
                "source_map": source,
                "tags": chunk.get("tags") or tags,
            }
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
              source_map_json TEXT
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
                "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
                    chunk["text"],
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
        "top_entities": [
            {
                "entity_id": entity_id,
                "entity_text": entity_by_id[entity_id]["entity_text"],
                "entity_type": entity_by_id[entity_id]["entity_type"],
                "count": count,
            }
            for entity_id, count in entity_counts.most_common(25)
            if entity_id in entity_by_id
        ],
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
    lines.extend(f"- {item['entity_text']} ({item['entity_type']}): {item['count']}" for item in index["top_entities"][:15])
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
    lines.extend(["", "## Low Structure", ""])
    low = [doc for doc in rows["documents"] if doc["quality_status"] == "low_structure"]
    lines.extend(f"- {doc['title']}" for doc in low) or lines.append("_None._")
    lines.extend(["", "## Visual Only / Image Only", ""])
    visual = [doc for doc in rows["documents"] if doc["quality_status"] == "visual_only" or doc["extraction_status"] == "image_only"]
    lines.extend(f"- {doc['title']}" for doc in visual) or lines.append("_None._")
    lines.extend(["", "## Missing / Embedded Assets", ""])
    for doc in rows["documents"]:
        metadata = doc.get("key_metadata") or {}
        manifest = doc.get("manifest") or {}
        missing = metadata.get("missing_assets_count") or manifest.get("missing_assets_count") or 0
        embedded = metadata.get("embedded_images_count") or manifest.get("embedded_images_count") or 0
        if missing or embedded:
            lines.append(f"- {doc['title']}: missing_assets_count={missing}, embedded_images_count={embedded}")
    if lines[-1] == "## Missing / Embedded Assets":
        lines.append("_None._")
    lines.extend(["", "## Chunks Without Locator", ""])
    missing_locator = [chunk for chunk in rows["chunks"] if not chunk.get("locator")]
    lines.extend(f"- {chunk['chunk_id']}: {chunk['title']}" for chunk in missing_locator[:100]) or lines.append("_None._")
    lines.extend(["", "## Documents Without Entities", ""])
    doc_mentions = {mention["doc_id"] for mention in rows["entity_mentions"] if mention["chunk_id"] is None}
    no_entities = [doc for doc in rows["documents"] if doc["doc_id"] not in doc_mentions]
    lines.extend(f"- {doc['title']}" for doc in no_entities) or lines.append("_None._")
    return "\n".join(lines) + "\n"


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
        chunk.get("table_name"),
        source.get("slide_title"),
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
    clean = re.sub(r"\s+", " ", text or "").strip()
    if query:
        first_term = query.split()[0].casefold()
        index = clean.casefold().find(first_term)
        if index > 40:
            clean = "..." + clean[index - 40 :]
    return clean[:limit].rstrip() + ("..." if len(clean) > limit else "")


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
