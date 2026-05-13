"""Persist operator routing overrides against a lead_result row."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..storage.repositories import LeadResultRepository, OverrideRepository


class OverrideRecordError(Exception):
    """Raised when the lead_result_id doesn't exist."""


class OverrideService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.leads = LeadResultRepository(session)
        self.overrides = OverrideRepository(session)

    def record(
        self,
        *,
        lead_result_id: str,
        corrected_owner: str,
        operator_id: str | None = None,
        reason: str | None = None,
    ) -> dict:
        lead = self.leads.get(lead_result_id)
        if lead is None:
            raise OverrideRecordError(f"lead_result {lead_result_id!r} not found")

        override = self.overrides.record(
            lead_result_id=lead.id,
            original_owner=lead.routing_owner,
            corrected_owner=corrected_owner,
            operator_id=operator_id,
            reason=reason,
        )
        return {
            "id": override.id,
            "lead_result_id": override.lead_result_id,
            "original_owner": override.original_owner,
            "corrected_owner": override.corrected_owner,
            "operator_id": override.operator_id,
            "reason": override.reason,
            "created_at": override.created_at.isoformat() + "Z",
        }
