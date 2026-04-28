from typing import Dict, Tuple

from office2md.ai.base import AIRequest
from office2md.ai.cli_adapter import CliAIAdapter
from office2md.ai.http_adapter import HttpAIAdapter, OpenAICompatibleAdapter
from office2md.ai.minimax_adapter import MiniMaxAdapter
from office2md.ai.prompts import document_summary_prompt
from office2md.models import ConvertOptions


def run_ai_enrichment(markdown: str, metadata: Dict, options: ConvertOptions) -> Tuple[Dict | None, str, list[str]]:
    if not options.use_ai or options.ai_backend == "none":
        return None, "", []

    adapter = _adapter_for_options(options)
    prompt = document_summary_prompt(markdown, metadata)
    response = adapter.complete(AIRequest(prompt=prompt, model=options.ai_model))
    warnings = list(response.warnings)
    if warnings:
        return None, "", warnings
    if not response.text:
        return None, "", []
    ai_data = {"backend": options.ai_backend, "model": options.ai_model, "raw": response.text}
    ai_notes = "\n".join(["# AI Notes", "", response.text, ""])
    return ai_data, ai_notes, []


def _adapter_for_options(options: ConvertOptions):
    if options.ai_backend == "cli":
        return CliAIAdapter(options.ai_command or "", timeout=options.ai_timeout)
    if options.ai_backend == "minimax":
        return MiniMaxAdapter(options.ai_base_url, options.ai_model, timeout=options.ai_timeout)
    if options.ai_backend == "openai-compatible":
        return OpenAICompatibleAdapter(options.ai_base_url, options.ai_model, timeout=options.ai_timeout)
    return HttpAIAdapter(options.ai_base_url, options.ai_model, timeout=options.ai_timeout)

