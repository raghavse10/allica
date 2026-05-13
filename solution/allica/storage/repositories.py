"""Repository layer.

Each repository owns a single aggregate root (Run, LeadResult, RoutingOverride).
Repositories are *thin* — they translate between domain objects and ORM
rows. Business logic stays in the service layer.

Sessions are passed in (rather than created internally) so callers control
the transaction boundary. This is the explicit pattern recommended by the
SQLAlchemy 2.x docs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .models import LeadResult, RoutingOverride, Run, RunError, SafetyEvent


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------


class RunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, **fields) -> Run:
        run = Run(**fields)
        self.session.add(run)
        self.session.flush()
        return run

    def get(self, run_id: str) -> Optional[Run]:
        return self.session.get(
            Run,
            run_id,
            options=(
                selectinload(Run.leads).selectinload(LeadResult.safety_events),
                selectinload(Run.leads).selectinload(LeadResult.overrides),
            ),
        )

    def find_by_payload_hash(self, payload_hash: str) -> Optional[Run]:
        stmt = (
            select(Run)
            .where(Run.payload_hash == payload_hash)
            .options(
                selectinload(Run.leads).selectinload(LeadResult.safety_events),
                selectinload(Run.leads).selectinload(LeadResult.overrides),
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_recent(self, limit: int = 50, *, offset: int = 0) -> list[Run]:
        stmt = (
            select(Run)
            .order_by(Run.received_at.desc())
            .offset(max(0, offset))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def mark_completed(self, run: Run, completed_at: datetime) -> None:
        run.completed_at = completed_at
        self.session.flush()

    def add_error(
        self,
        run: Run,
        *,
        stage: str,
        lead_external_id: str | None,
        error_class: str,
        error_message: str,
    ) -> RunError:
        err = RunError(
            run_id=run.id,
            stage=stage,
            lead_external_id=lead_external_id,
            error_class=error_class,
            error_message=error_message[:2000],
        )
        self.session.add(err)
        self.session.flush()
        return err


# ---------------------------------------------------------------------------
# Lead results
# ---------------------------------------------------------------------------


class LeadResultRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, lead: LeadResult, events: list[SafetyEvent]) -> LeadResult:
        self.session.add(lead)
        # Flush so the model default (uuid4().hex) populates lead.id before
        # we attach foreign keys on the safety events.
        self.session.flush()
        for event in events:
            event.lead_result_id = lead.id
            self.session.add(event)
        if events:
            self.session.flush()
        return lead

    def get(self, lead_result_id: str) -> Optional[LeadResult]:
        return self.session.get(
            LeadResult,
            lead_result_id,
            options=(
                selectinload(LeadResult.safety_events),
                selectinload(LeadResult.overrides),
            ),
        )

    def history_by_external_id(self, lead_external_id: str) -> list[LeadResult]:
        stmt = (
            select(LeadResult)
            .where(LeadResult.lead_external_id == lead_external_id)
            .order_by(LeadResult.processed_at.desc())
            .options(selectinload(LeadResult.overrides))
        )
        return list(self.session.execute(stmt).scalars())

    def history_by_company(self, company_normalised: str) -> list[LeadResult]:
        stmt = (
            select(LeadResult)
            .where(LeadResult.company_name_normalised == company_normalised)
            .order_by(LeadResult.processed_at.desc())
            .options(selectinload(LeadResult.overrides))
        )
        return list(self.session.execute(stmt).scalars())


# ---------------------------------------------------------------------------
# Routing overrides
# ---------------------------------------------------------------------------


class OverrideRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(
        self,
        *,
        lead_result_id: str,
        original_owner: str,
        corrected_owner: str,
        operator_id: str | None,
        reason: str | None,
    ) -> RoutingOverride:
        override = RoutingOverride(
            lead_result_id=lead_result_id,
            original_owner=original_owner,
            corrected_owner=corrected_owner,
            operator_id=operator_id,
            reason=reason,
        )
        self.session.add(override)
        self.session.flush()
        return override

    def list_recent(self, limit: int = 50) -> list[RoutingOverride]:
        stmt = (
            select(RoutingOverride)
            .order_by(RoutingOverride.created_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())
