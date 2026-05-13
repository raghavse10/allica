"""Eligibility orchestrator — runs every rule and aggregates the verdict."""

from __future__ import annotations

from ..schemas import Eligibility, EligibilityFinding, Enrichment, InboundLead
from .rules import ALL_RULES


def assess_eligibility(lead: InboundLead, enrichment: Enrichment) -> Eligibility:
    findings: list[EligibilityFinding] = []
    requires_manual = False
    blocked = False

    for rule in ALL_RULES:
        finding, manual, blocks = rule(lead, enrichment)
        if finding is not None:
            findings.append(finding)
        requires_manual = requires_manual or manual
        blocked = blocked or blocks

    eligible = not blocked
    return Eligibility(
        eligible=eligible,
        # A blocked lead doesn't go to manual review — it goes to Decline.
        requires_manual_review=requires_manual and eligible,
        findings=findings,
    )
