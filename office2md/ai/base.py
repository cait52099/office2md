from dataclasses import dataclass, field
from typing import List


@dataclass
class AIRequest:
    prompt: str
    model: str | None = None


@dataclass
class AIResponse:
    text: str = ""
    warnings: List[str] = field(default_factory=list)


class BaseAIAdapter:
    def complete(self, request: AIRequest) -> AIResponse:
        raise NotImplementedError

