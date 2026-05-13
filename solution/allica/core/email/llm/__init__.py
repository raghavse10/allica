"""`generate_email_via_llm`: env-based provider, None → use template."""

from .dispatcher import generate_email_via_llm, select_provider

__all__ = ["generate_email_via_llm", "select_provider"]
