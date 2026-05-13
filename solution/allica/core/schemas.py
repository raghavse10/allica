"""Shared Pydantic models for API responses and pipeline stages."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


class InboundLead(BaseModel):
    """A raw inbound lead as it arrives from a form / referral / event."""

    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    employees: Optional[int] = None
    annual_revenue_gbp: Optional[float] = None
    notes: Optional[str] = None
    sector_hint: Optional[str] = None


# ---------------------------------------------------------------------------
# Intermediate / output structures
# ---------------------------------------------------------------------------


class ValidationReport(BaseModel):
    """Result of cleaning + structural validation of a single lead."""

    passed: bool
    email_valid: bool
    is_duplicate: bool
    duplicate_of: Optional[str] = None
    issues: list[str] = Field(default_factory=list)


class Enrichment(BaseModel):
    """The (small) subset of registry fields we actually use downstream."""

    matched: bool
    company_number: Optional[str] = None
    status: Optional[str] = None
    sic_codes: list[str] = Field(default_factory=list)
    derived_sector: Optional[str] = None
    registered_address: Optional[str] = None
    incorporated_on: Optional[str] = None
    age_years: Optional[float] = None


class ScoreContribution(BaseModel):
    """A single named contribution to the ICP score (for explainability)."""

    feature: str
    weight: float
    reason: str


class Score(BaseModel):
    """ICP / priority score with the breakdown that produced it."""

    value: float = Field(ge=0.0, le=1.0)
    band: Literal["high", "medium", "low"]
    contributions: list[ScoreContribution] = Field(default_factory=list)


class EligibilityFinding(BaseModel):
    """A single eligibility / risk observation."""

    code: str
    severity: Literal["info", "warning", "block"]
    message: str


class Eligibility(BaseModel):
    eligible: bool
    requires_manual_review: bool
    findings: list[EligibilityFinding] = Field(default_factory=list)


class Routing(BaseModel):
    owner: Literal["Growth-Inbound", "Triage", "Manual-Review", "Decline"]
    queue: Literal["priority", "standard", "review", "declined"]
    rationale: str


class SafetyFlag(BaseModel):
    code: str
    severity: Literal["info", "warning", "block"]
    message: str


class EmailDraft(BaseModel):
    subject: str
    body: str
    word_count: int
    cta_count: int
    used_disclaimer: bool
    generator: Literal["template", "llm", "llm+sanitised"]


class LeadResult(BaseModel):
    """Full result for one inbound lead."""

    id: Optional[str]
    company_name: Optional[str]
    validation: ValidationReport
    enrichment: Enrichment
    eligibility: Eligibility
    score: Score
    routing: Routing
    email: Optional[EmailDraft] = None
    safety_flags: list[SafetyFlag] = Field(default_factory=list)
    processed: bool


class RunSummary(BaseModel):
    received: int
    processed: int
    dropped: int
    duplicates: int
    by_owner: dict[str, int]
    by_band: dict[str, int]
    elapsed_ms: int


class RunResponse(BaseModel):
    summary: RunSummary
    leads: list[LeadResult]
    meta: dict[str, Any] = Field(default_factory=dict)
