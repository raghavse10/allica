"""Drop duplicates by normalised (company name, website host); first row wins."""

from __future__ import annotations

from typing import Iterable

from ..schemas import InboundLead
from ..text_utils import normalise_host, normalise_text


def _dedup_key(lead: InboundLead) -> tuple[str, str]:
    return (normalise_text(lead.company_name), normalise_host(lead.website))


def deduplicate(
    leads: Iterable[InboundLead],
) -> tuple[list[InboundLead], dict[str, str]]:
    """Return `(unique_leads, duplicates_map)`.

    `duplicates_map[duplicate_id] = kept_id`. The first occurrence wins,
    matching how a human triager would treat the earliest submission as
    canonical.
    """
    seen: dict[tuple[str, str], InboundLead] = {}
    unique: list[InboundLead] = []
    duplicates: dict[str, str] = {}

    for lead in leads:
        key = _dedup_key(lead)
        # A fully empty key (no company, no website) is treated as unique
        # so anonymous leads aren't all collapsed into one row.
        if key == ("", ""):
            unique.append(lead)
            continue
        if key in seen:
            kept = seen[key]
            if lead.id is not None:
                duplicates[lead.id] = kept.id or ""
        else:
            seen[key] = lead
            unique.append(lead)

    return unique, duplicates
