from pathlib import Path

from office2md.converters.base import BaseConverter
from office2md.models import ConvertOptions, ConvertResult


class DoclingConverter(BaseConverter):
    name = "docling"

    def convert(self, path: Path, options: ConvertOptions) -> ConvertResult:
        try:
            from docling.document_converter import DocumentConverter
        except ImportError as exc:
            raise RuntimeError("Docling is not installed. Run: pip install -e .") from exc

        converter = DocumentConverter()
        result = converter.convert(str(path))
        markdown = result.document.export_to_markdown()
        raw_json = None
        if hasattr(result.document, "export_to_dict"):
            try:
                raw_json = result.document.export_to_dict()
            except Exception:
                raw_json = None

        return ConvertResult(
            markdown=markdown,
            raw_markdown=markdown,
            engine=self.name,
            metadata={"source": str(path)},
            raw_json=raw_json,
            assets=[],
        )

