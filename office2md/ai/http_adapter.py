from office2md.ai.base import AIRequest, AIResponse, BaseAIAdapter


class HttpAIAdapter(BaseAIAdapter):
    def __init__(self, base_url: str | None = None, model: str | None = None, timeout: int = 60):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    def complete(self, request: AIRequest) -> AIResponse:
        return AIResponse(warnings=["http ai adapter is configured but not implemented in this MVP"])


class OpenAICompatibleAdapter(HttpAIAdapter):
    def complete(self, request: AIRequest) -> AIResponse:
        return AIResponse(warnings=["openai-compatible ai adapter is configured but not implemented in this MVP"])

