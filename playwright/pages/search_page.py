import re

from playwright.sync_api import Page


class SearchPage:
    def __init__(self, page: Page):
        self.page = page
        self.heading = page.get_by_role("heading", name="Search properties")
        self.postcode = page.locator("#search_location")
        self.location_identifier = page.locator("#location_identifier")
        self.radius = page.locator("#radius")
        self.min_price = page.locator("#min_price")
        self.max_price = page.locator("#max_price")
        self.min_bedrooms = page.locator("#min_bedrooms")
        self.max_bedrooms = page.locator("#max_bedrooms")
        self.sort_type = page.locator("#sort_type")
        self.max_pages = page.locator("#max_pages")
        self.create_button = page.get_by_role("button", name="Create search run")
        self.form_status = page.locator("#formStatus")

    def fill_n1_search(self):
        self.postcode.fill("N1 6BU")
        self.location_identifier.fill("POSTCODE^544623")
        self.radius.fill("0.5")
        self.min_price.fill("1")
        self.max_price.fill("300000")
        self.min_bedrooms.fill("1")
        self.max_bedrooms.fill("2")
        self.sort_type.fill("6")
        self.max_pages.fill("1")

    def create_search_run(self):
        self.create_button.click()

    def created_run_id(self) -> int:
        match = re.search(r"Created run (\d+)", self.form_status.text_content() or "")
        if match is None:
            raise AssertionError("Created run id was not found in form status")
        return int(match.group(1))

    def view_run(self, run_id: int):
        self.page.locator(f'.view-run-button[data-run-id="{run_id}"]').click()

    def delete_run(self, run_id: int):
        self.page.once("dialog", lambda dialog: dialog.accept())
        self.page.locator(f'.delete-run-button[data-run-id="{run_id}"]').click()

    def run_row(self, run_id: int):
        return self.page.locator("#searchRunsTable").locator("tr").filter(has_text=str(run_id))
