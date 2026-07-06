from fastapi import status
from sqlalchemy import text

from api.tests.utils import TestingSessionLocal, client

SEARCH_RUN_PAYLOAD = {
    "search_location": "E1 1LF",
    "location_identifier": "POSTCODE^1327365",
    "radius": 0.25,
    "min_price": 120000,
    "max_price": 400000,
    "min_bedrooms": 1,
    "max_bedrooms": 2,
    "property_types": "flat",
    "include_sstc": "on",
    "sort_type": 6,
    "channel": "BUY",
    "transaction_type": "BUY",
    "display_location_identifier": "undefined",
    "result_index": 0,
    "max_pages": 1,
}


def test_read_search_runs_returns_only_current_user_runs(search_run, auth_override):
    response = client.get("/search-runs/")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == search_run.id


def test_create_search_run_sets_owner_id(monkeypatch, test_user, auth_override):
    def fake_trigger(search_run_id: int):
        return None

    monkeypatch.setattr(
        "api.services.search_run_service.trigger_airflow_filtered_search_dag",
        fake_trigger,
    )

    response = client.post("/search-runs/", json=SEARCH_RUN_PAYLOAD)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["owner_id"] == test_user.id


def test_results_return_202_when_search_run_not_complete(search_run, auth_override):
    db = TestingSessionLocal()
    search_run.status = "running"
    db.merge(search_run)
    db.commit()
    db.close()

    response = client.get(f"/search-runs/{search_run.id}/results")

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"detail": "Search run is still running"}


def test_results_are_paginated(search_run, auth_override):
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
                    1,
                    'https://example.com/1',
                    30000.888,
                    15.123,
                    8.456
                ),
                (
                    1,
                    'Second Street',
                    'E1 1LF',
                    250000,
                    1,
                    'https://example.com/2',
                    28000.111,
                    11.111,
                    5.222
                )
        """)
    )
    db.commit()
    db.close()

    response = client.get(f"/search-runs/{search_run.id}/results?limit=1&offset=0")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["address"] == "Best Street"
    assert body["items"][0]["estimated_annual_rent"] == 30000.89
    assert body["items"][0]["net_yield_percent"] == 8.46
