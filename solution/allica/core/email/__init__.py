"""Template or LLM draft + mandatory safety pass (`compose_email`)."""

from .composer import compose_email
from .context import EmailContext

__all__ = ["EmailContext", "compose_email"]
