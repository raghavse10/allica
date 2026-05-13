"""Cleaning step — normalise whitespace / case before validation."""

from __future__ import annotations

from ..schemas import InboundLead


# Trim + lowercase these string fields (explicit tuple, no model walk).
_STRING_FIELDS: tuple[str, ...] = (
    "company_name",
    "contact_name",
    "email",
    "website",
    "notes",
    "sector_hint",
)


def clean_lead(raw: dict) -> InboundLead:
    """Return an `InboundLead` built from a normalised copy of `raw`."""
    cleaned = dict(raw)
    for key in _STRING_FIELDS:
        val = cleaned.get(key)
        if isinstance(val, str):
            cleaned[key] = val.strip()
    if isinstance(cleaned.get("email"), str):
        cleaned["email"] = cleaned["email"].lower()
    return InboundLead(**cleaned)
