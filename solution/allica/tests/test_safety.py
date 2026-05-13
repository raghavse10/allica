from allica.core.safety import (
    REQUIRED_DISCLAIMER,
    count_ctas,
    sanitise_email,
    scan_input_for_risk,
)


def test_sanitiser_removes_guarantee_language():
    subject, body, flags, _disc = sanitise_email(
        "Guaranteed approval today",
        "We can offer guaranteed approval within 24 hours at the lowest rates.",
    )
    assert "guaranteed" not in body.lower()
    assert "24 hour" not in body.lower()
    assert "lowest rates" not in body.lower()
    codes = {f.code for f in flags}
    assert "guarantee_language" in codes
    assert "timeline_language" in codes
    assert "superlative_pricing" in codes


def test_disclaimer_appended_when_terms_referenced():
    _s, body, _f, used = sanitise_email(
        "Test",
        "Happy to share indicative pricing and terms after a chat.",
    )
    assert used is True
    assert REQUIRED_DISCLAIMER in body


def test_disclaimer_not_added_when_no_pricing_language():
    _s, body, _f, used = sanitise_email("Test", "Hi there, just saying hello.")
    assert used is False
    assert REQUIRED_DISCLAIMER not in body


def test_specific_rate_is_removed():
    _s, body, flags, _ = sanitise_email("Test", "We offer 4.5% APR on this.")
    assert "4.5%" not in body
    assert any(f.code == "specific_rate" for f in flags)


def test_input_scan_flags_prospect_language():
    flags = scan_input_for_risk("Need approval within 24 hours guaranteed")
    codes = {f.code for f in flags}
    assert "prospect_guarantee_language" in codes
    assert "prospect_timeline_language" in codes


def test_count_ctas_handles_one_clear_call():
    body = (
        "Hi Sam, thanks for reaching out. We support businesses like yours. "
        "Would a short 20-minute call next week work for you? Best, Allica."
    )
    assert count_ctas(body) == 1
