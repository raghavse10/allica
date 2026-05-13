import json
from pathlib import Path

from allica.core.paths import DEFAULT_LEADS_PATH
from allica.core.pipeline import run_pipeline


def _load_sample():
    return json.loads(Path(DEFAULT_LEADS_PATH).read_text(encoding="utf-8"))


def test_pipeline_runs_end_to_end():
    response = run_pipeline(_load_sample())
    assert response.summary.received == 10
    assert response.summary.duplicates == 1  # L-2004 duplicates L-2001
    assert response.summary.processed == 9


def test_thames_valley_flagged_for_unsafe_input_language():
    response = run_pipeline(_load_sample())
    tvl = next(l for l in response.leads if l.id == "L-2005")
    # Bad email so it should not produce a draft.
    assert tvl.email is None
    assert not tvl.validation.email_valid
    # And the prospect's "guaranteed within 24 hours" must surface as a flag.
    codes = {f.code for f in tvl.safety_flags}
    assert "prospect_guarantee_language" in codes
    assert "prospect_timeline_language" in codes


def test_startup_routed_low_or_manual():
    response = run_pipeline(_load_sample())
    sv = next(l for l in response.leads if l.id == "L-2008")
    assert sv.score.band == "low"
    # VC request triggers manual review per eligibility rules.
    assert sv.routing.owner in {"Triage", "Manual-Review"}


def test_high_value_lead_gets_priority():
    response = run_pipeline(_load_sample())
    nb = next(l for l in response.leads if l.id == "L-2002")
    assert nb.score.band in {"medium", "high"}
    assert nb.routing.owner == "Growth-Inbound"


def test_email_word_count_within_band_for_template():
    response = run_pipeline(_load_sample())
    drafts = [l.email for l in response.leads if l.email is not None]
    assert drafts, "expected at least one drafted email"
    for draft in drafts:
        assert 90 <= draft.word_count <= 200, (
            f"email out of expected band: {draft.word_count} words\n{draft.body}"
        )
        assert draft.cta_count == 1
