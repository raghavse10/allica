"""Sector data.

Three independent maps are needed across the pipeline:

* `SIC_TO_SECTOR` — registry SIC code → human-readable sector.
* `TARGET_SECTORS` — sectors the GTM playbook calls in-scope.
* `SECTOR_PROPS`  — per-sector value-prop fragment used by the email template.

They live together because they are about the same domain concept (sectors)
and each is a small, bounded table.
"""

from __future__ import annotations

from typing import Final


# SIC code → sector. Sourced from data/SIC_CODES.md.
SIC_TO_SECTOR: Final[dict[str, str]] = {
    "10710": "Food & Beverage",
    "10830": "Food & Beverage",
    "46370": "Food & Beverage",
    "25110": "Manufacturing",
    "25620": "Manufacturing",
    "28990": "Manufacturing",
    "75000": "Healthcare",
    "86230": "Healthcare",
    "49410": "Logistics",
    "52101": "Logistics",
    "41201": "Construction",
    "43999": "Construction",
    "62012": "Technology",
    "64999": "Technology",
}

# Sectors the GTM playbook explicitly targets.
TARGET_SECTORS: Final[frozenset[str]] = frozenset(
    {
        "Manufacturing",
        "Healthcare",
        "Food & Beverage",
        "Construction",
        "Logistics",
    }
)


# Sector → (value-prop sentence, primary product mention).
# Used by the email template; fall-through is handled at the call site.
SECTOR_PROPS: Final[dict[str, tuple[str, str]]] = {
    "Manufacturing": (
        "We work with UK manufacturing businesses on asset-backed lending and invoice finance,",
        "asset-backed and invoice finance",
    ),
    "Healthcare": (
        "We support healthcare practices with flexible equipment finance and growth capital,",
        "practice growth capital",
    ),
    "Food & Beverage": (
        "We help food and beverage operators smooth seasonal cash-flow with predictable repayment structures,",
        "seasonal cash-flow facilities",
    ),
    "Logistics": (
        "We finance fleet expansion and working capital for established logistics businesses,",
        "fleet and working-capital finance",
    ),
    "Construction": (
        "We back construction businesses with project-based and equipment finance,",
        "project and equipment finance",
    ),
    "Technology": (
        "We are primarily focused on revenue-generating SMEs in traditional sectors,",
        "SME lending",
    ),
}

# Used when a sector is unknown or has no specific prop.
DEFAULT_SECTOR_PROP: Final[tuple[str, str]] = (
    "We support established UK SMEs with specialist lending,",
    "specialist SME lending",
)


def sector_for_sic(sic_code: str) -> str | None:
    return SIC_TO_SECTOR.get(sic_code)


def is_target_sector(sector: str | None) -> bool:
    return bool(sector) and sector in TARGET_SECTORS
