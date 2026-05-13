"""Score aggregator — combines per-feature contributions into a final Score."""

from __future__ import annotations

from ..constants import SCORE_BASE, SCORE_DECIMALS
from ..schemas import Enrichment, InboundLead, Score, ScoreContribution
from .banding import band_for_score
from .features import (
    headcount_contribution,
    revenue_contribution,
    sector_contribution,
    trading_history_contribution,
    use_case_contributions,
)


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_lead(lead: InboundLead, enrichment: Enrichment) -> Score:
    contributions: list[ScoreContribution] = [
        revenue_contribution(lead.annual_revenue_gbp),
        sector_contribution(enrichment.derived_sector),
        headcount_contribution(lead.employees),
        trading_history_contribution(enrichment.age_years),
    ]
    contributions.extend(use_case_contributions(lead.notes))

    raw = SCORE_BASE + sum(c.weight for c in contributions)
    value = round(_clamp_unit(raw), SCORE_DECIMALS)

    return Score(value=value, band=band_for_score(value), contributions=contributions)
