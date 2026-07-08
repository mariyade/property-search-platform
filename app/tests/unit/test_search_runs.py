from unittest.mock import Mock

from app.routers.search_run import round_value
from app.schemas import SearchRunCreate
from app.services.search_run_service import create_search_run_with_pipeline_trigger

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


def test_round_value_rounds_to_two_decimal_places_by_default():
    assert round_value(8.456) == 8.46


def test_round_value_uses_requested_digits():
    assert round_value(8.456, digits=1) == 8.5


def test_round_value_keeps_none_as_none():
    assert round_value(None) is None


def test_create_search_run_assigns_owner_id(monkeypatch):
    delay = Mock()
    monkeypatch.setattr("app.services.search_run_service.process_search_run.delay", delay)
    db = Mock()
    request = SearchRunCreate(**SEARCH_RUN_PAYLOAD)

    search_run = create_search_run_with_pipeline_trigger(db, request, owner_id=42)

    assert search_run.owner_id == 42


def test_create_search_run_persists_and_refreshes(monkeypatch):
    monkeypatch.setattr("app.services.search_run_service.process_search_run.delay", Mock())
    db = Mock()
    request = SearchRunCreate(**SEARCH_RUN_PAYLOAD)

    search_run = create_search_run_with_pipeline_trigger(db, request, owner_id=42)

    db.add.assert_called_once_with(search_run)
    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(search_run)


def test_create_search_run_triggers_pipeline_after_persisting(monkeypatch):
    delay = Mock()
    monkeypatch.setattr("app.services.search_run_service.process_search_run.delay", delay)
    db = Mock()
    db.refresh.side_effect = lambda search_run: setattr(search_run, "id", 99)
    request = SearchRunCreate(**SEARCH_RUN_PAYLOAD)

    search_run = create_search_run_with_pipeline_trigger(db, request, owner_id=42)

    delay.assert_called_once_with(search_run.id)
