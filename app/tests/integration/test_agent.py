from fastapi import status
from sqlalchemy import text

from app.tests.utils import TestingSessionLocal, client


def test_agent_summary_returns_503_without_llm_config(search_run, auth_override, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    db = TestingSessionLocal()
    db.execute(
        text("""
            INSERT INTO search_run_yields (
                search_run_id,
                "Address",
                "Postcode",
                "Price",
                "Rooms",
                "Link",
                "EstimatedAnnualRent",
                "Gross_Yield_%",
                "Net_Yield_%"
            )
            VALUES
                (
                    1,
                    'Best Street',
                    'E1 1LF',
                    200000,
                    2,
                    'https://example.com/1',
                    24000,
                    12,
                    4.05
                ),
                (
                    1,
                    'Second Street',
                    'E1 1LF',
                    250000,
                    2,
                    'https://example.com/2',
                    18000,
                    7.2,
                    0.38
                )
        """)
    )
    db.commit()
    db.close()

    response = client.post(
        f"/search-runs/{search_run.id}/agent-summary",
        json={"limit": 20, "offset": 0},
    )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Deal agent LLM is not configured."}


def test_agent_summary_returns_202_when_search_run_not_complete(search_run, auth_override):
    db = TestingSessionLocal()
    search_run.status = "running"
    db.merge(search_run)
    db.commit()
    db.close()

    response = client.post(
        f"/search-runs/{search_run.id}/agent-summary",
        json={},
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"detail": "Search run is still running"}
