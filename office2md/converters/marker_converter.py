from pathlib import Path

from office2md.converters.base import BaseConverter
from office2md.models import ConvertOptions, ConvertResult


class MarkerConverter(BaseConverter):
    name = "marker"

    def convert(self, path: Path, options: ConvertOptions) -> ConvertResult:
        raise RuntimeError(
            "Marker converter is not implemented yet. Install office2md[marker] "
            "and implement marker integration in Phase 2."
        )

