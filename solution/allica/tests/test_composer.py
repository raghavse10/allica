"""Email composer: LLM fallbacks (safety + CTA policy)."""

from __future__ import annotations

from unittest.mock import patch

from allica.core.email.composer import compose_email
from allica.core.schemas import Enrichment, InboundLead


def _lead() -> InboundLead:
    return InboundLead(
        id="T-CTA",
        company_name="Test Co Ltd",
        contact_name="Sam Jones",
        email="sam@test.example",
        notes="Equipment financing enquiry.",
    )


def _enrichment() -> Enrichment:
    return Enrichment(matched=False)


@patch("allica.core.email.composer.generate_email_via_llm")
def test_llm_reverts_to_template_when_multiple_ctas(mock_llm):
    """GTM playbook expects a single clear ask; stacked CTAs → template."""
    mock_llm.return_value = (
        (
            "Quick note",
            "Hi Sam.\n\n"
            "Thanks for your interest.\n\n"
            "Would a short call next week work for you? "
            "Please reply to confirm when suits.\n\n"
            "Best,\nAllica",
        ),
        "mock-provider",
    )
    draft, flags = compose_email(_lead(), _enrichment(), prefer_llm=True)
    assert draft.generator == "template"
    assert draft.cta_count == 1
    codes = {f.code for f in flags}
    assert "llm_cta_count" in codes


@patch("allica.core.email.composer.generate_email_via_llm")
def test_llm_kept_when_single_cta_after_sanitise(mock_llm):
    mock_llm.return_value = (
        (
            "Quick note",
            "Hi Sam.\n\n"
            "Thanks for your interest in equipment options for Test Co Ltd.\n\n"
            "Would a short 20-minute call next week work for you?\n\n"
            "Best,\nAllica",
        ),
        "mock-provider",
    )
    draft, flags = compose_email(_lead(), _enrichment(), prefer_llm=True)
    assert draft.generator in {"llm", "llm+sanitised"}
    assert draft.cta_count == 1
