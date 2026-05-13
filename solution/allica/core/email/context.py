"""Build the lead-derived context that template + LLM share."""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import DEFAULT_NEED
from ..schemas import Enrichment, InboundLead
from ..text_utils import derive_first_name


@dataclass(frozen=True)
class EmailContext:
    """Lead slice passed to template and LLM paths."""

    contact_first_name: str
    company_name: str
    sector: str | None
    inferred_need: str
    incorporated_on: str | None
    company_status: str | None


# Free-text-note keyword → concise, jargon-light need description.
# Order matters: more specific needs (e.g. "property development") come first.
_NEED_RULES: tuple[tuple[str, str], ...] = (
    ("property development", "property-development financing"),
    ("equipment", "an equipment upgrade"),
    ("fleet", "fleet expansion"),
    ("invoice", "invoice finance to smooth cash flow"),
    ("refinance", "refinancing existing facilities"),
    ("seasonal", "seasonal working capital"),
    ("working capital", "working capital"),
    ("expansion", "an expansion plan"),
    ("growth capital", "growth capital"),
    # We never promise VC — but we do soften the framing.
    ("venture capital", "your funding needs"),
)


def infer_need(notes: str | None) -> str:
    if not notes:
        return DEFAULT_NEED
    text = notes.lower()
    for keyword, phrase in _NEED_RULES:
        if keyword in text:
            return phrase
    return DEFAULT_NEED


def build_context(lead: InboundLead, enrichment: Enrichment) -> EmailContext:
    return EmailContext(
        contact_first_name=derive_first_name(lead.contact_name),
        company_name=lead.company_name or "your business",
        sector=enrichment.derived_sector,
        inferred_need=infer_need(lead.notes),
        incorporated_on=enrichment.incorporated_on,
        company_status=enrichment.status,
    )
