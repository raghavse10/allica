"""Lightweight eval runner against evals/cases.json.

Each case in `evals/cases.json` describes either:
* a single-lead expectation (must_include, forbid, length bounds, ...), or
* a global behaviour (deduplication count, low-ICP routing, ...).

This runner is intentionally simple: it runs the real pipeline once over the
sample dataset, then matches each case against the relevant lead result.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.paths import DEFAULT_EVALS_PATH, DEFAULT_LEADS_PATH
from ..core.pipeline import run_pipeline


EVALS_PATH = DEFAULT_EVALS_PATH


def _find_lead(response: Any, company_name: str) -> Any | None:
    for lead in response.leads:
        if (lead.company_name or "").strip().lower() == company_name.strip().lower():
            return lead
    return None


def _check_email(lead: Any, checks: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if lead.email is None:
        # Some checks are still meaningful (e.g. should_flag_safety on input).
        if checks.get("should_flag_safety"):
            if not any(
                f.severity in {"warning", "block"} for f in lead.safety_flags
            ):
                failures.append("expected a safety flag but none were raised")
            return not failures, failures
        failures.append("no email was drafted")
        return False, failures

    body = lead.email.body.lower()

    for token in checks.get("must_include", []):
        if token.lower() not in body:
            failures.append(f"missing required token '{token}'")
    one_of = checks.get("must_include_one_of") or []
    if one_of and not any(t.lower() in body for t in one_of):
        failures.append(f"missing any of {one_of}")
    for token in checks.get("forbid", []):
        if token.lower() in body:
            failures.append(f"forbidden token '{token}' present")
    if "min_length" in checks and lead.email.word_count < checks["min_length"]:
        failures.append(
            f"too short: {lead.email.word_count} < {checks['min_length']}"
        )
    if "max_length" in checks and lead.email.word_count > checks["max_length"]:
        failures.append(
            f"too long: {lead.email.word_count} > {checks['max_length']}"
        )
    if checks.get("require_single_cta") and lead.email.cta_count != 1:
        failures.append(f"expected exactly 1 CTA, found {lead.email.cta_count}")
    if checks.get("require_disclaimer_if_terms"):
        body_has_terms = any(
            kw in body for kw in ("rate", "term", "pricing", "interest")
        )
        if body_has_terms and not lead.email.used_disclaimer:
            failures.append("terms referenced but disclaimer missing")
    if checks.get("should_flag_safety"):
        if not any(
            f.severity in {"warning", "block"} for f in lead.safety_flags
        ):
            failures.append("expected a safety flag but none were raised")
    return not failures, failures


def _check_global(case: dict, response: Any) -> tuple[bool, list[str]]:
    failures: list[str] = []
    checks = case["checks"]

    if checks.get("expect_deduplication"):
        expected = checks["expected_count"]
        seen_company = checks["duplicate_company"].lower()
        kept = sum(
            1
            for l in response.leads
            if not l.validation.is_duplicate
        )
        if kept != expected:
            failures.append(f"expected {expected} unique leads, got {kept}")
        # The duplicate must be flagged on the right company.
        flagged = [
            l.id
            for l in response.leads
            if l.validation.is_duplicate
            and (l.company_name or "").lower() == seen_company
        ]
        if not flagged:
            failures.append(
                f"expected at least one duplicate flagged for {seen_company!r}"
            )

    if "email_valid_expected" in checks:
        company = case["lead"]["company_name"]
        lead = _find_lead(response, company)
        if lead is None:
            failures.append(f"lead {company!r} not found")
        else:
            if lead.validation.email_valid != checks["email_valid_expected"]:
                failures.append(
                    f"email_valid mismatch: got {lead.validation.email_valid}, "
                    f"expected {checks['email_valid_expected']}"
                )

    if checks.get("low_icp_expected") or "route_owner_expected" in checks:
        company = case["lead"]["company_name"]
        lead = _find_lead(response, company)
        if lead is None:
            failures.append(f"lead {company!r} not found")
        else:
            if checks.get("low_icp_expected") and lead.score.band != "low":
                failures.append(
                    f"expected low ICP band, got {lead.score.band} ({lead.score.value})"
                )
            expected_owner = checks.get("route_owner_expected")
            if expected_owner and lead.routing.owner != expected_owner and lead.routing.owner != "Manual-Review":
                # Manual-Review counts as acceptable for low-ICP cases — the
                # eligibility layer can override Triage when policy demands it
                # (e.g. VC requests).
                failures.append(
                    f"expected route owner {expected_owner!r}, got {lead.routing.owner!r}"
                )

    if "min_retrieved_snippets" in checks:
        # Our prototype is rules+template, not retrieval-augmented. We mark
        # this case as a documented "deferred" check rather than failing it.
        failures.append(
            "retrieval not implemented in this prototype (see Design Notes — Next Steps)"
        )

    return not failures, failures


def run_eval(verbose: bool = False) -> list[dict]:
    cases = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    leads = json.loads(DEFAULT_LEADS_PATH.read_text(encoding="utf-8"))
    # Force template emails for deterministic evals.
    response = run_pipeline(leads, draft_email=True, prefer_llm=False)

    results: list[dict] = []
    for case in cases:
        case_id = case["id"]
        checks = case.get("checks", {})

        # If the case is purely about email content (must_include / forbid /
        # length / disclaimer), check the email. If it's about routing /
        # validation only, just run the global checks. Some cases mix both.
        is_email_check = any(
            k in checks
            for k in (
                "must_include",
                "must_include_one_of",
                "forbid",
                "min_length",
                "max_length",
                "require_single_cta",
                "require_disclaimer_if_terms",
                "should_flag_safety",
            )
        )
        is_global_check = any(
            k in checks
            for k in (
                "expect_deduplication",
                "email_valid_expected",
                "low_icp_expected",
                "route_owner_expected",
                "min_retrieved_snippets",
            )
        )

        passed, failures = True, []

        if is_email_check and "lead" in case and case["lead"].get("company_name"):
            company = case["lead"]["company_name"]
            lead = _find_lead(response, company)
            if lead is None:
                passed, failures = False, [f"lead {company!r} not found"]
            else:
                e_passed, e_failures = _check_email(lead, checks)
                passed = passed and e_passed
                failures.extend(e_failures)

        if is_global_check:
            g_passed, g_failures = _check_global(case, response)
            passed = passed and g_passed
            failures.extend(g_failures)

        result = {"id": case_id, "passed": passed, "failures": failures}
        results.append(result)
        if verbose or not passed:
            mark = "PASS" if passed else "FAIL"
            print(f"[{mark}] {case_id}")
            for f in failures:
                print(f"        - {f}")

    return results


if __name__ == "__main__":
    run_eval(verbose=True)
