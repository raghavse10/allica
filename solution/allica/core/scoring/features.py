"""Per-feature scoring contributions.

One function per feature, each returning a `ScoreContribution`. The functions
are intentionally tiny so the wiring in `scorer.py` reads top-to-bottom like
a checklist.
"""

from __future__ import annotations

from ..constants import (
    HEADCOUNT_SME_MAX,
    HEADCOUNT_SOLE_TRADER_MAX,
    MIN_TRADING_YEARS,
    REVENUE_CEILING_GBP,
    REVENUE_FLOOR_GBP,
    TRADING_YEARS_SHORT_MAX,
    W_ANTI_SIGNAL,
    W_HEADCOUNT_LARGE,
    W_HEADCOUNT_SME,
    W_HEADCOUNT_SOLE_TRADER,
    W_REVENUE_10M_50M,
    W_REVENUE_2M_10M,
    W_REVENUE_500K_2M,
    W_REVENUE_ABOVE_CEILING,
    W_REVENUE_BELOW_FLOOR,
    W_SECTOR_NON_TARGET,
    W_SECTOR_TARGET,
    W_TRADING_ESTABLISHED,
    W_TRADING_SHORT,
    W_TRADING_TOO_NEW,
    W_USE_CASE_HIT,
)
from ..schemas import ScoreContribution
from ..sectors import is_target_sector
from .keywords import NEGATIVE_KEYWORDS, USE_CASE_KEYWORDS


def revenue_contribution(revenue: float | None) -> ScoreContribution:
    if revenue is None:
        return ScoreContribution(
            feature="revenue", weight=0.0, reason="Revenue unknown — neutral."
        )
    if revenue < REVENUE_FLOOR_GBP:
        return ScoreContribution(
            feature="revenue",
            weight=W_REVENUE_BELOW_FLOOR,
            reason=f"£{revenue:,.0f} below £{REVENUE_FLOOR_GBP // 1000}k target floor.",
        )
    if revenue < 2_000_000:
        return ScoreContribution(
            feature="revenue",
            weight=W_REVENUE_500K_2M,
            reason=f"£{revenue:,.0f} fits the £500k–£2m equipment / seasonal band.",
        )
    if revenue < 10_000_000:
        return ScoreContribution(
            feature="revenue",
            weight=W_REVENUE_2M_10M,
            reason=f"£{revenue:,.0f} fits the £2m–£10m core lending sweet-spot.",
        )
    if revenue <= REVENUE_CEILING_GBP:
        return ScoreContribution(
            feature="revenue",
            weight=W_REVENUE_10M_50M,
            reason=f"£{revenue:,.0f} fits the £10m+ structured-facility band.",
        )
    return ScoreContribution(
        feature="revenue",
        weight=W_REVENUE_ABOVE_CEILING,
        reason=f"£{revenue:,.0f} exceeds the £{REVENUE_CEILING_GBP:,.0f} ceiling.",
    )


def sector_contribution(sector: str | None) -> ScoreContribution:
    if not sector:
        return ScoreContribution(
            feature="sector", weight=0.0, reason="Sector unknown — neutral."
        )
    if is_target_sector(sector):
        return ScoreContribution(
            feature="sector",
            weight=W_SECTOR_TARGET,
            reason=f"{sector} is a target sector in the GTM playbook.",
        )
    return ScoreContribution(
        feature="sector",
        weight=W_SECTOR_NON_TARGET,
        reason=f"{sector} is outside Allica's core target sectors.",
    )


def headcount_contribution(employees: int | None) -> ScoreContribution:
    if employees is None:
        return ScoreContribution(
            feature="headcount", weight=0.0, reason="Headcount unknown — neutral."
        )
    if employees < HEADCOUNT_SOLE_TRADER_MAX:
        return ScoreContribution(
            feature="headcount",
            weight=W_HEADCOUNT_SOLE_TRADER,
            reason=f"{employees} employees suggests a sole-trader-like operation.",
        )
    if employees <= HEADCOUNT_SME_MAX:
        return ScoreContribution(
            feature="headcount",
            weight=W_HEADCOUNT_SME,
            reason=f"{employees} employees consistent with established SME.",
        )
    return ScoreContribution(
        feature="headcount",
        weight=W_HEADCOUNT_LARGE,
        reason=f"{employees} employees is large — likely out of standard SME flow.",
    )


def trading_history_contribution(age_years: float | None) -> ScoreContribution:
    if age_years is None:
        return ScoreContribution(
            feature="trading_history",
            weight=0.0,
            reason="Trading history unknown.",
        )
    if age_years < MIN_TRADING_YEARS:
        return ScoreContribution(
            feature="trading_history",
            weight=W_TRADING_TOO_NEW,
            reason=f"Only {age_years} years trading — alternate flow per policy.",
        )
    if age_years < TRADING_YEARS_SHORT_MAX:
        return ScoreContribution(
            feature="trading_history",
            weight=W_TRADING_SHORT,
            reason=f"{age_years} years trading — short but viable.",
        )
    return ScoreContribution(
        feature="trading_history",
        weight=W_TRADING_ESTABLISHED,
        reason=f"{age_years} years trading — established business, lower risk.",
    )


def use_case_contributions(notes: str | None) -> list[ScoreContribution]:
    if not notes:
        return []
    text = notes.lower()
    contributions: list[ScoreContribution] = []
    # Cap positive use-case keywords at the first match so notes that happen
    # to mention several products don't dominate the score.
    for keyword, reason in USE_CASE_KEYWORDS.items():
        if keyword in text:
            contributions.append(
                ScoreContribution(
                    feature=f"use_case:{keyword}",
                    weight=W_USE_CASE_HIT,
                    reason=reason,
                )
            )
            break
    for keyword, reason in NEGATIVE_KEYWORDS.items():
        if keyword in text:
            contributions.append(
                ScoreContribution(
                    feature=f"anti_signal:{keyword}",
                    weight=W_ANTI_SIGNAL,
                    reason=reason,
                )
            )
    return contributions
