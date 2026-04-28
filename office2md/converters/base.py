from abc import ABC, abstractmethod
from pathlib import Path

from office2md.models import ConvertOptions, ConvertResult


class BaseConverter(ABC):
    name: str

    @abstractmethod
    def convert(self, path: Path, options: ConvertOptions) -> ConvertResult:
        raise NotImplementedError

