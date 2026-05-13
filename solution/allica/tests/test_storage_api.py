"""Integration tests for the storage layer + new API endpoints."""

from __future__ import annotations


def test_run_persists_and_returns_run_id(client):
    response = client.post("/run", json={}).json()
    assert "meta" in response and "run_id" in response["meta"]
    assert response["meta"]["cached"] is False
    assert response["summary"]["received"] == 10


def test_idempotency_same_payload_returns_cached_run(client):
    first = client.post("/run", json={}).json()
    second = client.post("/run", json={}).json()
    assert first["meta"]["run_id"] == second["meta"]["run_id"]
    assert second["meta"]["cached"] is True


def test_different_payload_creates_new_run(client):
    first = client.post("/run", json={}).json()
    second = client.post(
        "/run",
        json={"leads": [{"id": "X-1", "company_name": "New Co", "email": "a@b.com"}]},
    ).json()
    assert first["meta"]["run_id"] != second["meta"]["run_id"]


def test_list_runs_in_recency_order(client):
    client.post("/run", json={}).json()
    client.post(
        "/run",
        json={"leads": [{"id": "X-1", "company_name": "New Co", "email": "a@b.com"}]},
    ).json()
    runs = client.get("/runs").json()["runs"]
    assert len(runs) == 2
    # Newest first.
    assert runs[0]["received_at"] >= runs[1]["received_at"]


def test_list_runs_offset_pagination(client):
    # Three distinct payloads — identical bodies are idempotent (one run).
    for i in range(3):
        client.post(
            "/run",
            json={
                "leads": [
                    {
                        "id": f"PAG-{i}",
                        "company_name": f"Pagination Test {i}",
                        "email": f"pag{i}@example.com",
                    }
                ]
            },
        ).json()
    full = client.get("/runs?limit=10&offset=0").json()
    assert len(full["runs"]) == 3
    assert full["has_more"] is False
    page = client.get("/runs?limit=2&offset=0").json()
    assert len(page["runs"]) == 2
    assert page["has_more"] is True
    page2 = client.get("/runs?limit=2&offset=2").json()
    assert len(page2["runs"]) == 1
    assert page2["has_more"] is False
    assert page["runs"][0]["run_id"] == full["runs"][0]["run_id"]
    assert page2["runs"][0]["run_id"] == full["runs"][2]["run_id"]


def test_get_run_includes_full_lead_details(client):
    run_id = client.post("/run", json={}).json()["meta"]["run_id"]
    detail = client.get(f"/runs/{run_id}").json()
    lead = detail["leads"][0]
    for key in ("validation", "enrichment", "score", "routing", "safety_flags"):
        assert key in lead


def test_get_unknown_run_returns_404(client):
    response = client.get("/runs/does-not-exist")
    assert response.status_code == 404


def test_lead_history_finds_persisted_lead(client):
    client.post("/run", json={}).json()
    history = client.get("/leads/history?external_id=L-2001").json()["results"]
    assert len(history) == 1
    assert history[0]["company_name"] == "Oxfordshire Bakery Ltd"


def test_lead_history_requires_a_filter(client):
    response = client.get("/leads/history")
    assert response.status_code == 400


def test_feedback_records_routing_override(client):
    run_id = client.post("/run", json={}).json()["meta"]["run_id"]
    detail = client.get(f"/runs/{run_id}").json()
    lr_id = detail["leads"][0]["lead_result_id"]
    body = {
        "corrected_owner": "Manual-Review",
        "operator_id": "op-42",
        "reason": "wanted to verify revenue band first",
    }
    response = client.post(f"/leads/{lr_id}/feedback", json=body).json()
    assert response["original_owner"] in {"Growth-Inbound", "Triage", "Manual-Review", "Decline"}
    assert response["corrected_owner"] == "Manual-Review"

    # Should now appear in subsequent reads.
    re_read = client.get(f"/runs/{run_id}").json()
    assert len(re_read["leads"][0]["overrides"]) == 1


def test_feedback_for_unknown_lead_returns_404(client):
    response = client.post(
        "/leads/does-not-exist/feedback",
        json={"corrected_owner": "Triage"},
    )
    assert response.status_code == 404


def test_email_pii_is_hashed_not_stored_raw(client):
    """The DB must never contain the raw email address."""
    run_id = client.post("/run", json={}).json()["meta"]["run_id"]
    detail = client.get(f"/runs/{run_id}").json()
    # The serialised lead should not include the raw email field; only the
    # validation status. We verify by looking at the DB directly.
    from allica.storage import session_scope
    from allica.storage.models import LeadResult

    with session_scope() as session:
        rows = session.query(LeadResult).all()
        assert rows
        for row in rows:
            if row.lead_external_id == "L-2001":
                # Email hash present, but raw email never stored anywhere.
                assert row.email_hash is not None and len(row.email_hash) == 64
                # Notes excerpt is allowed (truncated, sanitised), but full raw notes are not.
                assert row.notes_hash is not None
                assert row.notes_excerpt is not None
                assert "amelia.shaw@example.com" not in (row.notes_excerpt or "")
                break
        else:
            raise AssertionError("L-2001 not found in DB")


def test_pii_hash_is_stable_across_runs(client):
    """The same email in two runs should produce the same hash."""
    payload_a = {
        "leads": [
            {
                "id": "P-1",
                "company_name": "Acme",
                "email": "stable@example.com",
                "annual_revenue_gbp": 1000000,
            }
        ]
    }
    payload_b = {
        "leads": [
            {
                "id": "P-2",  # different external id, same email
                "company_name": "Acme",
                "email": "stable@example.com",
                "annual_revenue_gbp": 1000000,
            }
        ]
    }
    client.post("/run", json=payload_a).json()
    client.post("/run", json=payload_b).json()

    from allica.storage import session_scope
    from allica.storage.models import LeadResult

    with session_scope() as session:
        rows = (
            session.query(LeadResult)
            .filter(LeadResult.lead_external_id.in_(["P-1", "P-2"]))
            .all()
        )
        assert len(rows) == 2
        assert rows[0].email_hash == rows[1].email_hash
