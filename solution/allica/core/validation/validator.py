"""Build `ValidationReport`: mark dupes/bad email; drop only zero-identity rows."""

from __future__ import annotations

from ..schemas import InboundLead, ValidationReport
from .email_check import is_valid_email


def validate_lead(lead: InboundLead, duplicate_of: str | None) -> ValidationReport:
    issues: list[str] = []

    if not lead.company_name:
        issues.append("missing_company_name")
    if not lead.email:
        issues.append("missing_email")

    email_ok = is_valid_email(lead.email)
    if lead.email and not email_ok:
        issues.append("malformed_email")

    is_dup = duplicate_of is not None
    if is_dup:
        issues.append("duplicate")

    has_identity = bool(lead.company_name) or bool(lead.email)
    passed = has_identity and not is_dup

    return ValidationReport(
        passed=passed,
        email_valid=email_ok,
        is_duplicate=is_dup,
        duplicate_of=duplicate_of,
        issues=issues,
    )
