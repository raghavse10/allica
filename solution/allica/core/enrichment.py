"""Join inbound lead to Companies House stub; narrow field set for downstream."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from .registry import CompaniesHouseStub
from .schemas import Enrichment, InboundLead
from .sectors import sector_for_sic


def _years_since(iso_date: str | None) -> Optional[float]:
    if not iso_date:
        return None
    try:
        d = datetime.strptime(iso_date, "%Y-%m-%d").date()
    except ValueError:
        return None
    delta_days = (date.today() - d).days
    return round(delta_days / 365.25, 2)


def _derive_sector(
    sic_codes: list[str], sector_hint: str | None
) -> Optional[str]:
    """Prefer a SIC-derived sector; fall back to the form-supplied hint."""
    for code in sic_codes:
        sector = sector_for_sic(code)
        if sector:
            return sector
    if sector_hint:
        return sector_hint.strip()
    return None


def enrich_lead(lead: InboundLead, registry: CompaniesHouseStub) -> Enrichment:
    record = registry.lookup(lead.company_name)
    if not record:
        return Enrichment(
            matched=False,
            derived_sector=lead.sector_hint.strip() if lead.sector_hint else None,
        )

    sic_codes = list(record.get("sic_codes", []))
    incorporated_on = record.get("incorporated_on")
    return Enrichment(
        matched=True,
        company_number=record.get("company_number"),
        status=record.get("status"),
        sic_codes=sic_codes,
        derived_sector=_derive_sector(sic_codes, lead.sector_hint),
        registered_address=record.get("registered_address"),
        incorporated_on=incorporated_on,
        age_years=_years_since(incorporated_on),
    )
