import os

from office2md.ai.base import AIRequest, AIResponse
from office2md.ai.http_adapter import HttpAIAdapter


class MiniMaxAdapter(HttpAIAdapter):
    def complete(self, request: AIRequest) -> AIResponse:
        if not os.environ.get("MINIMAX_API_KEY"):
            return AIResponse(warnings=["minimax ai adapter selected but MINIMAX_API_KEY is not set"])
        return AIResponse(warnings=["minimax ai adapter is a placeholder; no request was sent"])

