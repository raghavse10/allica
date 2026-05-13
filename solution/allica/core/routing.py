"""Map eligibility + ICP band to owner/queue; rationale is operator-facing."""

from __future__ import annotations

from .schemas import Eligibility, Routing, Score


def route_lead(score: Score, eligibility: Eligibility) -> Routing:
    if not eligibility.eligible:
        block_msgs = [f.message for f in eligibility.findings if f.severity == "block"]
        rationale = "Auto-decline: " + "; ".join(block_msgs) if block_msgs else "Auto-decline."
        return Routing(owner="Decline", queue="declined", rationale=rationale)

    if eligibility.requires_manual_review:
        warn_msgs = [
            f.message for f in eligibility.findings if f.severity == "warning"
        ]
        rationale = (
            "Manual review: " + "; ".join(warn_msgs)
            if warn_msgs
            else "Manual review required."
        )
        return Routing(owner="Manual-Review", queue="review", rationale=rationale)

    if score.band == "high":
        return Routing(
            owner="Growth-Inbound",
            queue="priority",
            rationale=f"High ICP ({score.value:.2f}) — priority response per playbook.",
        )
    if score.band == "medium":
        return Routing(
            owner="Growth-Inbound",
            queue="standard",
            rationale=f"Medium ICP ({score.value:.2f}) — standard Growth-Inbound flow.",
        )
    return Routing(
        owner="Triage",
        queue="standard",
        rationale=f"Low ICP ({score.value:.2f}) — Triage to qualify before outreach.",
    )
