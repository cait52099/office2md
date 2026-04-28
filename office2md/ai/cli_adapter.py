import subprocess

from office2md.ai.base import AIRequest, AIResponse, BaseAIAdapter


class CliAIAdapter(BaseAIAdapter):
    def __init__(self, command: str, timeout: int = 60):
        self.command = command
        self.timeout = timeout

    def complete(self, request: AIRequest) -> AIResponse:
        if not self.command:
            return AIResponse(warnings=["ai cli backend selected but --ai-command was not provided"])
        try:
            completed = subprocess.run(
                self.command,
                input=request.prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                shell=True,
            )
        except Exception as exc:
            return AIResponse(warnings=[f"ai cli adapter failed: {exc.__class__.__name__}: {exc}"])
        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            return AIResponse(warnings=[f"ai cli adapter failed with exit code {completed.returncode}: {stderr}"])
        return AIResponse(text=completed.stdout.strip())

