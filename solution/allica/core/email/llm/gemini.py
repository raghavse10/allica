"""Google Gemini email provider."""

from __future__ import annotations

import logging
import os

from ...constants import DEFAULT_GEMINI_MODEL, LLM_TEMPERATURE
from ...schemas import InboundLead
from ..context import EmailContext
from ..prompt import SYSTEM_PROMPT, build_user_payload, parse_subject_body


log = logging.getLogger(__name__)


def _api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


class GeminiProvider:
    name = "gemini"

    def is_available(self) -> bool:
        return _api_key() is not None

    def generate(
        self, ctx: EmailContext, lead: InboundLead
    ) -> tuple[str, str] | None:
        api_key = _api_key()
        if not api_key:
            return None
        try:
            # Imported lazily so the package works without google-genai installed.
            from google import genai  # type: ignore
            from google.genai import types  # type: ignore
        except ImportError:
            log.info("google-genai package not installed; cannot use Gemini.")
            return None

        model = os.getenv("ALLICA_LLM_MODEL", DEFAULT_GEMINI_MODEL)
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model,
                contents=build_user_payload(ctx, lead),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=LLM_TEMPERATURE,
                    response_mime_type="application/json",
                ),
            )
            return parse_subject_body(response.text or "")
        except Exception as exc:  # noqa: BLE001 — fail open to template
            log.warning("Gemini email generation failed: %s", exc)
            return None
