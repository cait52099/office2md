from pathlib import Path
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    path: Path
    file_type: str
    checksum: str


class ConvertOptions(BaseModel):
    engine: Literal["auto", "docling", "markitdown", "marker"] = "auto"
    profile: Literal["kb", "rag", "memory", "obsidian"] = "kb"
    recursive: bool = True
    with_json: bool = True
    with_chunks: bool = True
    with_assets: bool = True
    skip_existing: bool = True
    force_ocr: bool = False
    use_llm: bool = False
    render_pdf_pages: bool = False
    max_render_pages: int = 3
    max_text_pages: Optional[int] = None
    extract_all_page_text: bool = False
    use_ai: bool = False
    ai_backend: Literal["none", "http", "openai-compatible", "cli", "minimax"] = "none"
    ai_model: Optional[str] = None
    ai_base_url: Optional[str] = None
    ai_command: Optional[str] = None
    ai_timeout: int = 60


class ConvertResult(BaseModel):
    markdown: str
    raw_markdown: Optional[str] = None
    engine: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw_json: Optional[dict[str, Any]] = None
    assets: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    ocr_used: bool = False
