import pytest
from pydantic import ValidationError

from app.schemas import SearchRunCreate

VALID_SEARCH_RUN = {
    "search_location": "E1 1LF",
    "location_identifier": "POSTCODE^1327365",
    "radius": 0.25,
    "min_price": 120000,
    "max_price": 400000,
    "min_bedrooms": 1,
    "max_bedrooms": 2,
    "property_types": "flat",
    "include_sstc": "on",
    "channel": "BUY",
    "transaction_type": "BUY",
    "display_location_identifier": "undefined",
    "result_index": 0,
}


def test_search_run_create_defaults_sort_type():
    search_run = SearchRunCreate(**VALID_SEARCH_RUN)

    assert search_run.sort_type == 6


def test_search_run_create_defaults_max_pages():
    search_run = SearchRunCreate(**VALID_SEARCH_RUN)

    assert search_run.max_pages == 1


def test_search_run_create_defaults_mortgage_assumptions():
    search_run = SearchRunCreate(**VALID_SEARCH_RUN)

    assert search_run.mortgage_rate == 0.0515
    assert search_run.ltv == 0.75


def test_search_run_create_rejects_ltv_above_100_percent():
    payload = VALID_SEARCH_RUN | {"ltv": 1.1}

    with pytest.raises(ValidationError):
        SearchRunCreate(**payload)


def test_search_run_create_allows_missing_optional_price_bounds():
    payload = VALID_SEARCH_RUN | {"min_price": None, "max_price": None}

    search_run = SearchRunCreate(**payload)

    assert search_run.min_price is None
    assert search_run.max_price is None


def test_search_run_create_rejects_negative_min_price():
    payload = VALID_SEARCH_RUN | {"min_price": -1}

    with pytest.raises(ValidationError):
        SearchRunCreate(**payload)


def test_search_run_create_rejects_negative_result_index():
    payload = VALID_SEARCH_RUN | {"result_index": -1}

    with pytest.raises(ValidationError):
        SearchRunCreate(**payload)


def test_search_run_create_rejects_too_many_pages():
    payload = VALID_SEARCH_RUN | {"max_pages": 31}

    with pytest.raises(ValidationError):
        SearchRunCreate(**payload)
