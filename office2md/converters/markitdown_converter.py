from pathlib import Path

from office2md.converters.base import BaseConverter
from office2md.models import ConvertOptions, ConvertResult


class MarkItDownConverter(BaseConverter):
    name = "markitdown"

    def convert(self, path: Path, options: ConvertOptions) -> ConvertResult:
        try:
            from markitdown import MarkItDown
        except ImportError as exc:
            if path.suffix.lower() in {".txt", ".md", ".csv", ".json", ".html", ".htm"}:
                markdown = path.read_text(encoding="utf-8", errors="replace")
                return ConvertResult(
                    markdown=markdown,
                    raw_markdown=markdown,
                    engine=self.name,
                    metadata={"source": str(path), "fallback": "plain_text"},
                    warnings=["markitdown is not installed; used plain-text fallback"],
                )
            raise RuntimeError("MarkItDown is not installed. Run: pip install -e .") from exc

        md_converter = MarkItDown(enable_plugins=True)
        result = md_converter.convert(str(path))
        markdown = result.text_content
        return ConvertResult(
            markdown=markdown,
            raw_markdown=markdown,
            engine=self.name,
            metadata={"source": str(path)},
            raw_json=None,
            assets=[],
        )

