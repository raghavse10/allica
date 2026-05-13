"""Regex rules consumed by `sanitiser.py` (data rows, not logic)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, Literal

from ..constants import REQUIRED_DISCLAIMER

__all__ = ["BANNED_RULES", "BannedRule", "REQUIRED_DISCLAIMER", "TERMS_TRIGGER_RE"]

Severity = Literal["info", "warning", "block"]


@dataclass(frozen=True)
class BannedRule:
    pattern: re.Pattern[str]
    replacement: str
    code: str
    severity: Severity
    message: str


BANNED_RULES: Final[tuple[BannedRule, ...]] = (
    BannedRule(
        pattern=re.compile(r"\bguaranteed approval\b", re.IGNORECASE),
        replacement="potential approval",
        code="guarantee_language",
        severity="block",
        message="Removed 'guaranteed approval' (prohibited per eligibility policy).",
    ),
    BannedRule(
        pattern=re.compile(r"\bguaranteed\b", re.IGNORECASE),
        replacement="potential",
        code="guarantee_language",
        severity="warning",
        message="Removed 'guaranteed' to avoid implying a certain outcome.",
    ),
    BannedRule(
        pattern=re.compile(r"\bapproval within \d+\s*hours?\b", re.IGNORECASE),
        replacement="a quick initial review",
        code="timeline_language",
        severity="block",
        message="Removed exact approval-timeline language.",
    ),
    BannedRule(
        pattern=re.compile(r"\bwithin 24 hours?\b", re.IGNORECASE),
        replacement="quickly",
        code="timeline_language",
        severity="warning",
        message="Replaced '24 hour' timeline with a softer phrasing.",
    ),
    BannedRule(
        pattern=re.compile(r"\bwithin 48 hours?\b", re.IGNORECASE),
        replacement="shortly",
        code="timeline_language",
        severity="warning",
        message="Replaced '48 hour' timeline with a softer phrasing.",
    ),
    BannedRule(
        pattern=re.compile(r"\b(?:lowest|best)\s+(?:rates|terms)\b", re.IGNORECASE),
        replacement="competitive options",
        code="superlative_pricing",
        severity="warning",
        message="Replaced superlative pricing claim with a neutral phrase.",
    ),
    BannedRule(
        pattern=re.compile(r"\bteaser rates?\b", re.IGNORECASE),
        replacement="introductory options",
        code="teaser_rate",
        severity="warning",
        message="Removed 'teaser rate' language.",
    ),
    BannedRule(
        pattern=re.compile(r"\b\d+(?:\.\d+)?\s*%\s*(?:apr|interest|rate)\b", re.IGNORECASE),
        replacement="indicative pricing",
        code="specific_rate",
        severity="block",
        message="Removed a specific interest rate (must come from formal quote only).",
    ),
)

# Phrases that, if present, mean the disclaimer must follow.
TERMS_TRIGGER_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(rate|rates|term|terms|pricing|apr|interest)\b", re.IGNORECASE
)
