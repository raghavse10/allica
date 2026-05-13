"""Common protocol for LLM email providers."""

from __future__ import annotations

from typing import Protocol

from ..context import EmailContext
from ...schemas import InboundLead


class LLMProvider(Protocol):
    """Anything that can turn (context, lead) into a (subject, body) tuple."""

    name: str

    def is_available(self) -> bool:
        """Return True if this provider has the keys / SDK it needs."""
        ...

    def generate(
        self, ctx: EmailContext, lead: InboundLead
    ) -> tuple[str, str] | None:
        """Return `(subject, body)` or `None` on failure."""
        ...
