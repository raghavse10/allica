"""Provider selection + dispatch.

Selection rules:

1. `ALLICA_LLM_PROVIDER=gemini|openai` — explicit override.
2. Otherwise: Gemini wins if its key is set, else OpenAI.
3. None available → return `None` so the caller falls back to the template.
"""

from __future__ import annotations

import os
from typing import Final

from ...schemas import InboundLead
from ..context import EmailContext
from .base import LLMProvider
from .gemini import GeminiProvider
from .openai import OpenAIProvider


_REGISTRY: Final[dict[str, LLMProvider]] = {
    "gemini": GeminiProvider(),
    "openai": OpenAIProvider(),
}


def select_provider() -> LLMProvider | None:
    """Return the provider that should handle this run, or None."""
    forced = (os.getenv("ALLICA_LLM_PROVIDER") or "").strip().lower()
    if forced in _REGISTRY and _REGISTRY[forced].is_available():
        return _REGISTRY[forced]

    # Auto-detect: Gemini takes priority when both keys are present.
    for name in ("gemini", "openai"):
        provider = _REGISTRY[name]
        if provider.is_available():
            return provider
    return None


def generate_email_via_llm(
    ctx: EmailContext, lead: InboundLead
) -> tuple[tuple[str, str], str] | None:
    """Try each available provider until one succeeds.

    Returns `((subject, body), provider_name)` on success, or `None`.
    """
    provider = select_provider()
    if provider is None:
        return None
    result = provider.generate(ctx, lead)
    if result is None:
        return None
    return result, provider.name
