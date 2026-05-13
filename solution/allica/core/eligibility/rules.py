"""Small rule functions from `docs/eligibility.md`; see `assessor.py` for wiring."""

from __future__ import annotations

from typing import Optional

from ..constants import (
    BLOCKING_CH_STATUSES,
    CCJ_TOKENS,
    MIN_TRADING_YEARS,
    REVENUE_CEILING_GBP,
    REVENUE_FLOOR_GBP,
    VC_TOKENS,
)
from ..schemas import EligibilityFinding, Enrichment, InboundLead


RuleResult = tuple[Optional[EligibilityFinding], bool, bool]  # finding, manual, block


def companies_house_status_rule(
    lead: InboundLead, enrichment: Enrichment
) -> RuleResult:
    if not enrichment.matched:
        return (
            EligibilityFinding(
                code="ch_no_match",
                severity="warning",
                message="No Companies House match — verify entity before outreach.",
            ),
            True,
            False,
        )
    status = (enrichment.status or "").lower()
    if status in BLOCKING_CH_STATUSES:
        return (
            EligibilityFinding(
                code="ch_status_inactive",
                severity="block",
                message=f"Companies House status is '{status}': automatic decline.",
            ),
            False,
            True,
        )
    if status and status != "active":
        return (
            EligibilityFinding(
                code="ch_status_unusual",
                severity="warning",
                message=f"Companies House status '{status}' — confirm manually.",
            ),
            True,
            False,
        )
    return (None, False, False)


def revenue_band_rule(lead: InboundLead, enrichment: Enrichment) -> RuleResult:
    revenue = lead.annual_revenue_gbp
    if revenue is None:
        return (
            EligibilityFinding(
                code="revenue_unknown",
                severity="info",
                message="Revenue not provided — qualify on call.",
            ),
            False,
            False,
        )
    if revenue < REVENUE_FLOOR_GBP:
        return (
            EligibilityFinding(
                code="revenue_below_target",
                severity="warning",
                message=(
                    f"Revenue £{revenue:,.0f} is below the £{REVENUE_FLOOR_GBP:,.0f} "
                    "target floor — typically out of segment."
                ),
            ),
            True,
            False,
        )
    if revenue > REVENUE_CEILING_GBP:
        return (
            EligibilityFinding(
                code="revenue_above_ceiling",
                severity="warning",
                message=(
                    f"Revenue £{revenue:,.0f} exceeds the £{REVENUE_CEILING_GBP:,.0f} "
                    "ceiling — escalate to specialist."
                ),
            ),
            True,
            False,
        )
    return (None, False, False)


def trading_history_rule(lead: InboundLead, enrichment: Enrichment) -> RuleResult:
    age = enrichment.age_years
    if age is None or age >= MIN_TRADING_YEARS:
        return (None, False, False)
    return (
        EligibilityFinding(
            code="trading_history_short",
            severity="warning",
            message=f"Only {age} years trading — route to alternate flow.",
        ),
        True,
        False,
    )


def ccj_mention_rule(lead: InboundLead, enrichment: Enrichment) -> RuleResult:
    notes = (lead.notes or "").lower()
    if not any(token in notes for token in CCJ_TOKENS):
        return (None, False, False)
    return (
        EligibilityFinding(
            code="ccj_mentioned",
            severity="warning",
            message="CCJ language detected in notes — escalate per policy.",
        ),
        True,
        False,
    )


def vc_request_rule(lead: InboundLead, enrichment: Enrichment) -> RuleResult:
    notes = (lead.notes or "").lower()
    if not any(token in notes for token in VC_TOKENS):
        return (None, False, False)
    return (
        EligibilityFinding(
            code="vc_request",
            severity="warning",
            message="Venture capital request — outside SME lending product scope.",
        ),
        True,
        False,
    )


# The full ordered list of rules. Order is *not* significant for correctness
# (every rule contributes independently) but matches the document order in
# docs/eligibility.md for readability.
ALL_RULES: tuple = (
    companies_house_status_rule,
    revenue_band_rule,
    trading_history_rule,
    ccj_mention_rule,
    vc_request_rule,
)
