from allica.core.validation import (
    clean_lead,
    deduplicate,
    is_valid_email,
    validate_lead,
)


def test_email_validation():
    assert is_valid_email("foo@bar.com")
    assert is_valid_email("dr.priya+test@x.co.uk")
    assert not is_valid_email("invalid-email")
    assert not is_valid_email("")
    assert not is_valid_email(None)


def test_clean_normalises_whitespace_and_case():
    raw = {"company_name": "  Acme  ", "email": " A@B.COM "}
    cleaned = clean_lead(raw)
    assert cleaned.company_name == "Acme"
    assert cleaned.email == "a@b.com"


def test_dedup_collapses_same_company_and_host():
    leads = [
        clean_lead({"id": "L1", "company_name": "Acme", "website": "https://acme.example"}),
        clean_lead({"id": "L2", "company_name": "ACME ", "website": "http://www.acme.example"}),
        clean_lead({"id": "L3", "company_name": "Other", "website": "https://other.example"}),
    ]
    unique, dup_map = deduplicate(leads)
    assert len(unique) == 2
    assert dup_map.get("L2") == "L1"


def test_validation_marks_duplicate_and_bad_email():
    lead = clean_lead({"id": "L1", "company_name": "Acme", "email": "broken"})
    report = validate_lead(lead, duplicate_of="L0")
    assert report.is_duplicate
    assert "duplicate" in report.issues
    assert not report.email_valid
    assert "malformed_email" in report.issues
    assert not report.passed
