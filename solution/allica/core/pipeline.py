"""Orchestrate clean → dedup → validate → enrich → eligibility → score → route,
optional email + safety; logging/timing only I/O here."""

from __future__ import annotations

import logging
import time
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Optional

from .email import compose_email
from .eligibility import assess_eligibility
from .enrichment import enrich_lead
from .paths import DEFAULT_REGISTRY_PATH
from .registry import CompaniesHouseStub
from .routing import route_lead
from .safety import scan_input_for_risk
from .schemas import (
    InboundLead,
    LeadResult,
    RunResponse,
    RunSummary,
)
from .scoring import score_lead
from .validation import clean_lead, deduplicate, validate_lead


log = logging.getLogger("allica.pipeline")


# ---------------------------------------------------------------------------
# Per-lead processing
# ---------------------------------------------------------------------------


def _process_one(
    lead: InboundLead,
    duplicate_of: Optional[str],
    registry: CompaniesHouseStub,
    *,
    draft_email: bool,
    prefer_llm: bool,
) -> LeadResult:
    validation = validate_lead(lead, duplicate_of)
    enrichment = enrich_lead(lead, registry)
    eligibility = assess_eligibility(lead, enrichment)
    score = score_lead(lead, enrichment)
    routing = route_lead(score, eligibility)

    safety_flags = scan_input_for_risk(lead.notes)

    email = None
    will_send = (
        draft_email
        and validation.passed
        and validation.email_valid
        and routing.owner not in {"Decline", "Manual-Review"}
    )
    if will_send:
        email, email_flags = compose_email(lead, enrichment, prefer_llm=prefer_llm)
        safety_flags.extend(email_flags)

    return LeadResult(
        id=lead.id,
        company_name=lead.company_name,
        validation=validation,
        enrichment=enrichment,
        eligibility=eligibility,
        score=score,
        routing=routing,
        email=email,
        safety_flags=safety_flags,
        processed=validation.passed,
    )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_pipeline(
    raw_leads: Iterable[dict],
    *,
    registry_path: Optional[Path] = None,
    draft_email: bool = True,
    prefer_llm: bool = False,
) -> RunResponse:
    """Run the full inbound-lead pipeline and return a structured response."""
    started = time.perf_counter()
    raw_list = list(raw_leads)
    received = len(raw_list)

    registry = CompaniesHouseStub.from_path(registry_path or DEFAULT_REGISTRY_PATH)

    cleaned = [clean_lead(r) for r in raw_list]
    unique, dup_map = deduplicate(cleaned)
    unique_ids = {l.id for l in unique}

    results: list[LeadResult] = []
    for lead in cleaned:
        duplicate_of = dup_map.get(lead.id or "")
        is_kept = lead.id in unique_ids and duplicate_of is None
        results.append(
            _process_one(
                lead,
                duplicate_of=None if is_kept else duplicate_of,
                registry=registry,
                draft_email=draft_email if is_kept else False,
                prefer_llm=prefer_llm if is_kept else False,
            )
        )

    elapsed_ms = int((time.perf_counter() - started) * 1000)

    by_owner = Counter(r.routing.owner for r in results if r.processed)
    by_band = Counter(r.score.band for r in results if r.processed)
    duplicates = sum(1 for r in results if r.validation.is_duplicate)
    dropped = sum(1 for r in results if not r.processed)
    processed = received - dropped

    summary = RunSummary(
        received=received,
        processed=processed,
        dropped=dropped,
        duplicates=duplicates,
        by_owner=dict(by_owner),
        by_band=dict(by_band),
        elapsed_ms=elapsed_ms,
    )

    log.info(
        "pipeline_complete received=%s processed=%s dropped=%s dupes=%s elapsed_ms=%s",
        received,
        processed,
        dropped,
        duplicates,
        elapsed_ms,
    )

    return RunResponse(
        summary=summary,
        leads=results,
        meta={
            "registry_path": str(registry_path or DEFAULT_REGISTRY_PATH),
            "email_drafting": draft_email,
            "llm_preferred": prefer_llm,
        },
    )
