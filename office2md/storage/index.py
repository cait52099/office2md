import json
from pathlib import Path
from typing import Dict, List


def rebuild_output_index(output_root: Path, profile: str = "kb") -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    entries = []
    for manifest_path in sorted(output_root.rglob("manifest.json")):
        if manifest_path.parent == output_root:
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        knowledge = _read_json(manifest_path.parent / "knowledge.json")
        chunks_count = knowledge.get("chunks_count", 0)
        assets_count = knowledge.get("assets_count", manifest.get("asset_count", 0))
        tags = knowledge.get("tags", [])
        rel_doc = (manifest_path.parent / "document.md").relative_to(output_root).as_posix()
        entries.append(
            {
                "title": manifest_path.parent.name,
                "document": rel_doc,
                "source_file": manifest.get("source_file"),
                "document_kind": manifest.get("document_kind", "document"),
                "quality_status": manifest.get("quality_status", "unknown"),
                "tags": tags,
                "chunks_count": chunks_count,
                "assets_count": assets_count,
            }
        )

    (output_root / "_index.json").write_text(
        json.dumps({"documents": entries}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_root / "_index.md").write_text(_build_index_markdown(entries, profile), encoding="utf-8")


def _read_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _build_index_markdown(entries: List[Dict], profile: str) -> str:
    lines = [
        "# Knowledge Pack Index",
        "",
        "| Document | Kind | Quality | Tags | Chunks | Assets |",
        "|---|---|---|---|---:|---:|",
    ]
    for entry in entries:
        label = entry["source_file"] or entry["title"]
        if profile == "obsidian":
            link = f"[[{entry['document']}|{label}]]"
        else:
            link = f"[{label}]({entry['document']})"
        lines.append(
            "| {doc} | {kind} | {quality} | {tags} | {chunks} | {assets} |".format(
                doc=link,
                kind=entry["document_kind"],
                quality=entry["quality_status"],
                tags=", ".join(entry["tags"]),
                chunks=entry["chunks_count"],
                assets=entry["assets_count"],
            )
        )
    return "\n".join(lines) + "\n"

