"""OpenAI email provider."""

from __future__ import annotations

import logging
import os

from ...constants import DEFAULT_OPENAI_MODEL, LLM_TEMPERATURE
from ...schemas import InboundLead
from ..context import EmailContext
from ..prompt import SYSTEM_PROMPT, build_user_payload, parse_subject_body


log = logging.getLogger(__name__)


def _api_key() -> str | None:
    return os.getenv("OPENAI_API_KEY")


class OpenAIProvider:
    name = "openai"

    def is_available(self) -> bool:
        return _api_key() is not None

    def generate(
        self, ctx: EmailContext, lead: InboundLead
    ) -> tuple[str, str] | None:
        api_key = _api_key()
        if not api_key:
            return None
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            log.info("openai package not installed; cannot use OpenAI.")
            return None

        model = os.getenv("ALLICA_LLM_MODEL", DEFAULT_OPENAI_MODEL)
        try:
            client = OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model=model,
                temperature=LLM_TEMPERATURE,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_payload(ctx, lead)},
                ],
            )
            return parse_subject_body(completion.choices[0].message.content or "")
        except Exception as exc:  # noqa: BLE001 — fail open to template
            log.warning("OpenAI email generation failed: %s", exc)
            return None
