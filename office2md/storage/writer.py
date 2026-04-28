import json
from pathlib import Path
from typing import Dict, List

from slugify import slugify

from office2md.models import ConvertResult
from office2md.utils import ensure_directory


def output_dir_for_source(source_path: Path, output_root: Path, checksum: str) -> Path:
    slug = slugify(source_path.stem) or "document"
    base_target = output_root / slug
    if not base_target.exists() or not any(base_target.iterdir()):
        return base_target

    if _matches_existing_source(base_target, source_path, checksum):
        return base_target

    short_hash = checksum.split(":", 1)[-1][:8]
    return output_root / f"{slug}-{short_hash}"


def _matches_existing_source(output_dir: Path, source_path: Path, checksum: str) -> bool:
    manifest_path = output_dir / "manifest.json"
    if not manifest_path.exists():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        manifest.get("source_path") == str(source_path.resolve())
        and manifest.get("checksum") == checksum
        and manifest.get("status") == "success"
    )


def write_document_output(
    source_path: Path,
    output_root: Path,
    result: ConvertResult,
    final_markdown: str,
    chunks: List[Dict],
    manifest: Dict,
    output_dir: Path = None,
    knowledge: Dict = None,
    entities: Dict = None,
    source_map: Dict = None,
    ai_notes: str = "",
) -> Path:
    out_dir = output_dir or output_dir_for_source(source_path, output_root, manifest["checksum"])
    ensure_directory(out_dir)
    ensure_directory(out_dir / "assets")

    (out_dir / "document.md").write_text(final_markdown, encoding="utf-8")
    (out_dir / "document.raw.md").write_text(result.raw_markdown or result.markdown, encoding="utf-8")
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with (out_dir / "chunks.jsonl").open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    document_json = result.raw_json or {
        "source_file": source_path.name,
        "engine": result.engine,
        "pages": [],
        "elements": [],
    }
    (out_dir / "document.json").write_text(
        json.dumps(document_json, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if knowledge is not None:
        (out_dir / "knowledge.json").write_text(
            json.dumps(knowledge, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if entities is not None:
        (out_dir / "entities.json").write_text(
            json.dumps(entities, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if source_map is not None:
        (out_dir / "source_map.json").write_text(
            json.dumps(source_map, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if ai_notes:
        (out_dir / "ai_notes.md").write_text(ai_notes, encoding="utf-8")
    return out_dir
