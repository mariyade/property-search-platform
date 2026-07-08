from playwright.sync_api import Page


class SearchResultsPage:
    def __init__(self, page: Page):
        self.page = page
        self.results_meta = page.locator("#resultsMeta")
        self.results_table = page.locator("#resultsTable")
        self.dashboard_postcode = page.locator("#dashboardPostcode")
        self.dashboard_max_price = page.locator("#dashboardMaxPrice")
        self.dashboard_max_bedrooms = page.locator("#dashboardMaxBedrooms")

    def result_row(self, text: str):
        return self.results_table.get_by_text(text)
