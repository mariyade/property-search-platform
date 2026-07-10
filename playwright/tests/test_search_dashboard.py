import pytest
from config import TestUser
from pages.login_page import LoginPage
from pages.search_page import SearchPage
from pages.search_results_page import SearchResultsPage
from playwright.sync_api import expect
from utils.backend_cleanup import create_test_user


def create_search_run_from_form(page, base_url):
    create_test_user(base_url)
    login_page = LoginPage(page)
    search_page = SearchPage(page)

    login_page.open()
    login_page.login(TestUser.username, TestUser.password)

    expect(search_page.heading).to_be_visible()
    search_page.fill_n1_search()
    search_page.create_search_run()

    expect(search_page.form_status).to_contain_text("Created run")

    run_id = search_page.created_run_id()
    expect(search_page.run_row(run_id)).to_contain_text("pending")
    expect(search_page.run_row(run_id)).to_contain_text("N1 6BU")
    expect(search_page.run_row(run_id)).to_contain_text("£1 - £300,000")

    return run_id, search_page


def stub_search_dashboard(page):
    run = {
        "id": 999,
        "status": "completed",
        "search_location": "N1 6BU",
        "location_identifier": "POSTCODE^544623",
        "radius": 0.5,
        "min_price": 1,
        "max_price": 300000,
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
        "owner_id": 1,
    }
    runs = []

    def handle_search_runs(route):
        request = route.request
        if request.method == "POST":
            runs.clear()
            runs.append(run)
            route.fulfill(status=201, json=run)
            return
        route.fulfill(status=200, json=runs)

    def handle_results(route):
        route.fulfill(
            status=200,
            json={
                "search_run_id": 999,
                "limit": 20,
                "offset": 0,
                "total": 1,
                "items": [
                    {
                        "address": "Stubbed Test Street, Islington",
                        "price": 265000,
                        "rooms": 2,
                        "estimated_annual_rent": 18020,
                        "gross_yield_percent": 6.8,
                        "net_yield_percent": 3.25,
                        "link": "https://www.rightmove.co.uk/properties/999",
                    }
                ],
            },
        )

    page.route("**/search-runs/", handle_search_runs)
    page.route("**/search-runs/999/results?*", handle_results)


@pytest.mark.e2e
def test_real_search_run_can_be_viewed(browser_page, app_base_url, clean_test_user):
    run_id, search_page = create_search_run_from_form(browser_page, app_base_url)

    search_page.view_run(run_id)
    expect(browser_page.locator("#resultsMeta")).to_contain_text("Search run is still")


@pytest.mark.e2e
def test_real_search_run_can_be_deleted(browser_page, app_base_url, clean_test_user):
    run_id, search_page = create_search_run_from_form(browser_page, app_base_url)

    search_page.delete_run(run_id)

    expect(search_page.run_row(run_id)).to_have_count(0)


@pytest.mark.e2e
def test_search_dashboard_uses_stubbed_results(browser_page, app_base_url, clean_test_user):
    create_test_user(app_base_url)
    stub_search_dashboard(browser_page)

    login_page = LoginPage(browser_page)
    search_page = SearchPage(browser_page)
    results_page = SearchResultsPage(browser_page)

    login_page.open()
    login_page.login(TestUser.username, TestUser.password)

    expect(search_page.heading).to_be_visible()

    search_page.fill_n1_search()
    search_page.create_search_run()

    expect(search_page.form_status).to_have_text("Created run 999")
    expect(browser_page.get_by_text("completed")).to_be_visible()

    search_page.view_run(999)

    expect(results_page.results_meta).to_have_text("Run 999: 1-1 of 1")
    expect(results_page.dashboard_postcode).to_have_text("N1 6BU")
    expect(results_page.dashboard_max_price).to_have_text("£300,000")
    expect(results_page.dashboard_max_bedrooms).to_have_text("2")
    expect(results_page.results_table).to_contain_text("Stubbed Test Street, Islington")
    expect(results_page.results_table).to_contain_text("6.80%")
    expect(results_page.results_table).to_contain_text("3.25%")
