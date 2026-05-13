"""SQLAlchemy ORM models.

Design notes:

* IDs are stored as 32-char hex UUIDs (no dashes) so they are portable across
  SQLite and Postgres without dialect-specific UUID columns.
* Timestamps are stored UTC-naive — the engine layer is responsible for
  setting them. Consumers should treat them as UTC.
* Large/complex shapes (enrichment, contributions, findings) are stored as
  JSON. We don't query inside them today, but they are essential for replay
  and a future audit UI.
* Foreign keys cascade DELETE — wiping a `Run` wipes its `LeadResult`s and
  their `SafetyEvent`s. This is what GDPR erasure expects.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _new_id() -> str:
    return uuid4().hex


def _utc_now() -> datetime:
    # Naive UTC — consumers must treat the value as UTC. Storing tz-naive keeps
    # the column type portable across SQLite and Postgres.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Run(Base):
    """One pipeline execution."""

    __tablename__ = "runs"
    __table_args__ = (
        UniqueConstraint("payload_hash", name="uq_runs_payload_hash"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    payload_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    received_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utc_now, nullable=False, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    received_count: Mapped[int] = mapped_column(Integer, nullable=False)
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False)
    dropped_count: Mapped[int] = mapped_column(Integer, nullable=False)
    duplicates_count: Mapped[int] = mapped_column(Integer, nullable=False)
    elapsed_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    by_owner: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=dict)
    by_band: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=dict)

    email_drafting_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    llm_preferred: Mapped[bool] = mapped_column(Boolean, nullable=False)
    meta_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    leads: Mapped[list["LeadResult"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    errors: Mapped[list["RunError"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class LeadResult(Base):
    """One lead's verdict within a run."""

    __tablename__ = "lead_results"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    run_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("runs.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # External identifiers (NOT unique — same lead can appear in many runs)
    lead_external_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_name_normalised: Mapped[str | None] = mapped_column(
        String(255), index=True, nullable=True
    )
    company_number_ch: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)

    # PII — hashed, never raw.
    email_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    notes_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes_excerpt: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Validation
    validation_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    email_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    duplicate_of: Mapped[str | None] = mapped_column(String(64), nullable=True)
    validation_issues: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # Score
    score_value: Mapped[float] = mapped_column(Float, nullable=False)
    score_band: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    score_contributions: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)

    # Eligibility
    eligibility_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    requires_manual_review: Mapped[bool] = mapped_column(Boolean, nullable=False)
    eligibility_findings: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)

    # Routing
    routing_owner: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    routing_queue: Mapped[str] = mapped_column(String(32), nullable=False)
    routing_rationale: Mapped[str] = mapped_column(Text, nullable=False)

    # Email
    email_subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    email_cta_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    email_used_disclaimer: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    email_generator: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Enrichment snapshot (full Pydantic dump for replay)
    enrichment: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utc_now, nullable=False, index=True
    )

    run: Mapped["Run"] = relationship(back_populates="leads")
    safety_events: Mapped[list["SafetyEvent"]] = relationship(
        back_populates="lead_result",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    overrides: Mapped[list["RoutingOverride"]] = relationship(
        back_populates="lead_result",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SafetyEvent(Base):
    __tablename__ = "safety_events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    lead_result_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("lead_results.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, nullable=False)

    lead_result: Mapped["LeadResult"] = relationship(back_populates="safety_events")


class RoutingOverride(Base):
    """Operator feedback — the labelled data we'd train on later."""

    __tablename__ = "routing_overrides"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    lead_result_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("lead_results.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    original_owner: Mapped[str] = mapped_column(String(32), nullable=False)
    corrected_owner: Mapped[str] = mapped_column(String(32), nullable=False)
    operator_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utc_now, nullable=False, index=True
    )

    lead_result: Mapped["LeadResult"] = relationship(back_populates="overrides")


class RunError(Base):
    __tablename__ = "run_errors"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    run_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    lead_external_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_class: Mapped[str] = mapped_column(String(128), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, nullable=False)

    run: Mapped["Run"] = relationship(back_populates="errors")
