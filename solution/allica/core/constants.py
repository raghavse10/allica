"""Centralised business constants.

Every threshold, limit, weight base, and label literal lives here so:

* The provenance of a number is one click away from where it is used.
* Tuning the system means editing one file, not chasing magic literals.
* Tests can import the same constants and stay in lock-step with prod code.

Values are grouped by the doc that justifies them (eligibility / GTM playbook).
"""

from __future__ import annotations

from typing import Final


# ---------------------------------------------------------------------------
# Eligibility — sourced from docs/eligibility.md
# ---------------------------------------------------------------------------

# Revenue thresholds in GBP.
REVENUE_FLOOR_GBP: Final[int] = 500_000
REVENUE_CEILING_GBP: Final[int] = 50_000_000

# Minimum trading history (years) before a company gets the standard flow.
MIN_TRADING_YEARS: Final[float] = 2.0

# Companies House statuses that immediately disqualify a lead.
BLOCKING_CH_STATUSES: Final[frozenset[str]] = frozenset(
    {"liquidation", "administration", "dissolved"}
)

# Tokens in free-text notes that signal a CCJ. Lower-cased.
CCJ_TOKENS: Final[tuple[str, ...]] = (
    "ccj",
    "county court judgment",
    "county court judgement",
)

# Tokens in free-text notes that signal an out-of-scope VC request.
VC_TOKENS: Final[tuple[str, ...]] = ("venture capital",)


# ---------------------------------------------------------------------------
# Scoring — additive ICP model
# ---------------------------------------------------------------------------

# Starting score for a well-formed but otherwise unremarkable inbound enquiry.
SCORE_BASE: Final[float] = 0.30

# Routing band thresholds — sourced from docs/gtm_playbook.md "Routing Logic".
SCORE_BAND_HIGH_MIN: Final[float] = 0.50  # > this is "high"
SCORE_BAND_MEDIUM_MIN: Final[float] = 0.30  # >= this is "medium"

# Revenue contribution weights, by band.
W_REVENUE_BELOW_FLOOR: Final[float] = -0.25
W_REVENUE_500K_2M: Final[float] = 0.10
W_REVENUE_2M_10M: Final[float] = 0.18
W_REVENUE_10M_50M: Final[float] = 0.13
W_REVENUE_ABOVE_CEILING: Final[float] = -0.10

# Sector contribution weights.
W_SECTOR_TARGET: Final[float] = 0.10
W_SECTOR_NON_TARGET: Final[float] = -0.10

# Headcount contribution weights.
HEADCOUNT_SOLE_TRADER_MAX: Final[int] = 5
HEADCOUNT_SME_MAX: Final[int] = 100
W_HEADCOUNT_SOLE_TRADER: Final[float] = -0.10
W_HEADCOUNT_SME: Final[float] = 0.05
W_HEADCOUNT_LARGE: Final[float] = 0.02

# Trading-history contribution weights.
TRADING_YEARS_SHORT_MAX: Final[float] = 5.0
W_TRADING_TOO_NEW: Final[float] = -0.20
W_TRADING_SHORT: Final[float] = 0.03
W_TRADING_ESTABLISHED: Final[float] = 0.07

# Use-case keyword contribution weights.
W_USE_CASE_HIT: Final[float] = 0.05
W_ANTI_SIGNAL: Final[float] = -0.40

# Final score is rounded to this many decimal places for stable display.
SCORE_DECIMALS: Final[int] = 3


# ---------------------------------------------------------------------------
# Email — GTM playbook constraints
# ---------------------------------------------------------------------------

EMAIL_MIN_WORDS: Final[int] = 110
EMAIL_MAX_WORDS: Final[int] = 170

# Greeting fallback when no contact name is available.
DEFAULT_GREETING: Final[str] = "there"

# Inferred need when nothing in the notes maps to a known product.
DEFAULT_NEED: Final[str] = "your growth plans"


# ---------------------------------------------------------------------------
# Safety — sourced from docs/eligibility.md "Prohibited Language"
# ---------------------------------------------------------------------------

REQUIRED_DISCLAIMER: Final[str] = "Subject to status and credit checks. Terms apply."


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

# RFC 5321 hard cap on a full email address.
EMAIL_MAX_LENGTH: Final[int] = 254


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

DEFAULT_GEMINI_MODEL: Final[str] = "gemini-2.0-flash"
DEFAULT_OPENAI_MODEL: Final[str] = "gpt-4o-mini"
LLM_TEMPERATURE: Final[float] = 0.4
LLM_MAX_RAW_NOTES_CHARS: Final[int] = 240
