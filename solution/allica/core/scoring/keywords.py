"""Keyword tables that drive use-case scoring.

Kept as data (not code) so the GTM team can edit this file without touching
scoring logic.
"""

from __future__ import annotations

from typing import Final


# Phrase → human reason for the contribution.
USE_CASE_KEYWORDS: Final[dict[str, str]] = {
    "equipment": "Equipment finance is a core Allica product.",
    "invoice": "Invoice finance is a core Allica product.",
    "refinance": "Refinancing existing facilities is a stated use case.",
    "working capital": "Working capital fits the SME lending playbook.",
    "expansion": "Growth/expansion capital fits the playbook.",
    "fleet": "Fleet financing is called out in the GTM playbook.",
    "property development": "Property development finance is in scope.",
}

NEGATIVE_KEYWORDS: Final[dict[str, str]] = {
    "venture capital": "VC is explicitly outside Allica's SME lending scope.",
}
