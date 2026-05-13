"""Idempotent POST /run: hash payload, cache hit or run_pipeline + persist."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from ..core.pipeline import run_pipeline
from ..core.schemas import LeadResult as LeadResultDTO
from ..core.schemas import RunResponse
from ..core.text_utils import normalise_text
from ..storage.hashing import compute_payload_hash
from ..storage.models import LeadResult, Run, SafetyEvent
from ..storage.redaction import excerpt_notes, hash_pii
from ..storage.repositories import LeadResultRepository, RunRepository


log = logging.getLogger(__name__)


class RunService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.runs = RunRepository(session)
        self.leads = LeadResultRepository(session)

    # ------------------------------------------------------------------
    # Read paths
    # ------------------------------------------------------------------

    def list_recent(self, limit: int = 50, *, offset: int = 0) -> list[dict[str, Any]]:
        return [
            self._summarise_run(r)
            for r in self.runs.list_recent(limit=limit, offset=offset)
        ]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        run = self.runs.get(run_id)
        if run is None:
            return None
        return self._serialise_run(run)

    def history_for_lead(
        self, *, external_id: str | None = None, company: str | None = None
    ) -> list[dict[str, Any]]:
        rows: list[LeadResult] = []
        if external_id:
            rows.extend(self.leads.history_by_external_id(external_id))
        if company:
            rows.extend(self.leads.history_by_company(normalise_text(company)))
        # De-duplicate on id while preserving recency order.
        seen: set[str] = set()
        unique: list[LeadResult] = []
        for row in rows:
            if row.id in seen:
                continue
            seen.add(row.id)
            unique.append(row)
        return [self._serialise_lead(r) for r in unique]

    # ------------------------------------------------------------------
    # Write path
    # ------------------------------------------------------------------

    def execute(
        self,
        payload: dict[str, Any],
        *,
        leads: list[dict],
        draft_email: bool,
        prefer_llm: bool,
    ) -> tuple[RunResponse, str, bool]:
        """Run pipeline (or return cached) and persist.

        Returns `(response, run_id, was_cached)`.
        """
        payload_hash = compute_payload_hash(payload)
        cached = self.runs.find_by_payload_hash(payload_hash)
        if cached is not None:
            log.info("idempotent_hit run_id=%s payload_hash=%s", cached.id, payload_hash[:12])
            return self._rehydrate_response(cached), cached.id, True

        response = run_pipeline(
            leads, draft_email=draft_email, prefer_llm=prefer_llm
        )

        # Build a {external_id -> raw input dict} map so we can hash PII and
        # capture a notes excerpt without leaking either through the pipeline
        # schemas (which intentionally don't carry email/notes downstream).
        raw_by_id: dict[str, dict] = {}
        for raw in leads:
            ext_id = raw.get("id")
            if ext_id:
                raw_by_id[str(ext_id)] = raw

        run = self._persist(payload_hash, response, raw_by_id)
        response.meta["run_id"] = run.id
        response.meta["cached"] = False
        return response, run.id, False

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _persist(
        self,
        payload_hash: str,
        response: RunResponse,
        raw_by_id: dict[str, dict] | None = None,
    ) -> Run:
        s = response.summary
        run = self.runs.create(
            payload_hash=payload_hash,
            received_count=s.received,
            processed_count=s.processed,
            dropped_count=s.dropped,
            duplicates_count=s.duplicates,
            elapsed_ms=s.elapsed_ms,
            by_owner=dict(s.by_owner),
            by_band=dict(s.by_band),
            email_drafting_enabled=bool(response.meta.get("email_drafting", True)),
            llm_preferred=bool(response.meta.get("llm_preferred", False)),
            meta_json=dict(response.meta),
        )
        # Surface the persisted row id back through `meta` keyed by external id
        # so the UI can wire feedback buttons even on the very first response.
        ids: dict[str, str] = {}
        for lead in response.leads:
            raw = (raw_by_id or {}).get(str(lead.id)) if lead.id else None
            row = self._persist_lead(run.id, lead, raw)
            if lead.id:
                ids[lead.id] = row.id
        response.meta["lead_result_ids"] = ids
        self.runs.mark_completed(
            run, datetime.now(timezone.utc).replace(tzinfo=None)
        )
        return run

    def _persist_lead(
        self, run_id: str, dto: LeadResultDTO, raw: dict | None
    ) -> LeadResult:
        raw_email = (raw or {}).get("email") if raw else None
        raw_notes = (raw or {}).get("notes") if raw else None

        row = LeadResult(
            run_id=run_id,
            lead_external_id=dto.id,
            company_name=dto.company_name,
            company_name_normalised=normalise_text(dto.company_name) or None,
            company_number_ch=dto.enrichment.company_number,
            email_hash=hash_pii(raw_email) if isinstance(raw_email, str) else None,
            notes_hash=hash_pii(raw_notes) if isinstance(raw_notes, str) else None,
            notes_excerpt=excerpt_notes(raw_notes) if isinstance(raw_notes, str) else None,
            validation_passed=dto.validation.passed,
            email_valid=dto.validation.email_valid,
            is_duplicate=dto.validation.is_duplicate,
            duplicate_of=dto.validation.duplicate_of,
            validation_issues=list(dto.validation.issues),
            score_value=dto.score.value,
            score_band=dto.score.band,
            score_contributions=[c.model_dump() for c in dto.score.contributions],
            eligibility_eligible=dto.eligibility.eligible,
            requires_manual_review=dto.eligibility.requires_manual_review,
            eligibility_findings=[f.model_dump() for f in dto.eligibility.findings],
            routing_owner=dto.routing.owner,
            routing_queue=dto.routing.queue,
            routing_rationale=dto.routing.rationale,
            email_subject=dto.email.subject if dto.email else None,
            email_body=dto.email.body if dto.email else None,
            email_word_count=dto.email.word_count if dto.email else None,
            email_cta_count=dto.email.cta_count if dto.email else None,
            email_used_disclaimer=dto.email.used_disclaimer if dto.email else None,
            email_generator=dto.email.generator if dto.email else None,
            enrichment=dto.enrichment.model_dump(),
            processed=dto.processed,
        )
        events = [
            SafetyEvent(
                code=f.code,
                severity=f.severity,
                message=f.message,
            )
            for f in dto.safety_flags
        ]
        return self.leads.add(row, events)

    # ------------------------------------------------------------------
    # Read-side serialisation (DB row → API dict)
    # ------------------------------------------------------------------

    @staticmethod
    def _summarise_run(run: Run) -> dict[str, Any]:
        return {
            "run_id": run.id,
            "received_at": run.received_at.isoformat() + "Z",
            "completed_at": run.completed_at.isoformat() + "Z" if run.completed_at else None,
            "received": run.received_count,
            "processed": run.processed_count,
            "duplicates": run.duplicates_count,
            "elapsed_ms": run.elapsed_ms,
            "by_owner": run.by_owner,
            "by_band": run.by_band,
            "llm_preferred": run.llm_preferred,
        }

    def _serialise_run(self, run: Run) -> dict[str, Any]:
        return {
            **self._summarise_run(run),
            "leads": [self._serialise_lead(l) for l in run.leads],
        }

    @staticmethod
    def _serialise_lead(row: LeadResult) -> dict[str, Any]:
        return {
            "lead_result_id": row.id,
            "run_id": row.run_id,
            "id": row.lead_external_id,
            "company_name": row.company_name,
            "processed": row.processed,
            "validation": {
                "passed": row.validation_passed,
                "email_valid": row.email_valid,
                "is_duplicate": row.is_duplicate,
                "duplicate_of": row.duplicate_of,
                "issues": row.validation_issues,
            },
            "enrichment": row.enrichment,
            "score": {
                "value": row.score_value,
                "band": row.score_band,
                "contributions": row.score_contributions,
            },
            "eligibility": {
                "eligible": row.eligibility_eligible,
                "requires_manual_review": row.requires_manual_review,
                "findings": row.eligibility_findings,
            },
            "routing": {
                "owner": row.routing_owner,
                "queue": row.routing_queue,
                "rationale": row.routing_rationale,
            },
            "email": (
                {
                    "subject": row.email_subject,
                    "body": row.email_body,
                    "word_count": row.email_word_count,
                    "cta_count": row.email_cta_count,
                    "used_disclaimer": row.email_used_disclaimer,
                    "generator": row.email_generator,
                }
                if row.email_subject
                else None
            ),
            "safety_flags": [
                {"code": e.code, "severity": e.severity, "message": e.message}
                for e in row.safety_events
            ],
            "overrides": [
                {
                    "id": o.id,
                    "original_owner": o.original_owner,
                    "corrected_owner": o.corrected_owner,
                    "operator_id": o.operator_id,
                    "reason": o.reason,
                    "created_at": o.created_at.isoformat() + "Z",
                }
                for o in row.overrides
            ],
            "processed_at": row.processed_at.isoformat() + "Z",
        }

    def _rehydrate_response(self, run: Run) -> RunResponse:
        """Build a `RunResponse` shaped exactly like the live pipeline would."""
        from ..core.schemas import (
            EligibilityFinding,
            EmailDraft,
            Enrichment,
            LeadResult as LeadResultDTO,
            RunSummary,
            SafetyFlag,
            Score,
            ScoreContribution,
            ValidationReport,
            Eligibility,
            Routing,
        )

        leads_dto: list[LeadResultDTO] = []
        for row in run.leads:
            leads_dto.append(
                LeadResultDTO(
                    id=row.lead_external_id,
                    company_name=row.company_name,
                    validation=ValidationReport(
                        passed=row.validation_passed,
                        email_valid=row.email_valid,
                        is_duplicate=row.is_duplicate,
                        duplicate_of=row.duplicate_of,
                        issues=list(row.validation_issues),
                    ),
                    enrichment=Enrichment(**row.enrichment),
                    eligibility=Eligibility(
                        eligible=row.eligibility_eligible,
                        requires_manual_review=row.requires_manual_review,
                        findings=[EligibilityFinding(**f) for f in row.eligibility_findings],
                    ),
                    score=Score(
                        value=row.score_value,
                        band=row.score_band,  # type: ignore[arg-type]
                        contributions=[
                            ScoreContribution(**c) for c in row.score_contributions
                        ],
                    ),
                    routing=Routing(
                        owner=row.routing_owner,  # type: ignore[arg-type]
                        queue=row.routing_queue,  # type: ignore[arg-type]
                        rationale=row.routing_rationale,
                    ),
                    email=(
                        EmailDraft(
                            subject=row.email_subject,
                            body=row.email_body or "",
                            word_count=row.email_word_count or 0,
                            cta_count=row.email_cta_count or 0,
                            used_disclaimer=bool(row.email_used_disclaimer),
                            generator=row.email_generator or "template",  # type: ignore[arg-type]
                        )
                        if row.email_subject
                        else None
                    ),
                    safety_flags=[
                        SafetyFlag(code=e.code, severity=e.severity, message=e.message)  # type: ignore[arg-type]
                        for e in row.safety_events
                    ],
                    processed=row.processed,
                )
            )

        return RunResponse(
            summary=RunSummary(
                received=run.received_count,
                processed=run.processed_count,
                dropped=run.dropped_count,
                duplicates=run.duplicates_count,
                by_owner=dict(run.by_owner),
                by_band=dict(run.by_band),
                elapsed_ms=run.elapsed_ms,
            ),
            leads=leads_dto,
            meta={
                **dict(run.meta_json),
                "run_id": run.id,
                "cached": True,
                "received_at": run.received_at.isoformat() + "Z",
            },
        )
