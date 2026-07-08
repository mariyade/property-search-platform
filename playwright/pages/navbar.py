from playwright.sync_api import Page


class Navbar:
    def __init__(self, page: Page):
        self.page = page
        self.brand = page.get_by_role("link", name="Property Search")
        self.searches_link = page.get_by_role("link", name="Searches")
        self.login_link = page.get_by_role("link", name="Login")
        self.register_link = page.get_by_role("link", name="Register")
        self.logout_button = page.get_by_role("button", name="Logout")

    def logout(self):
        self.logout_button.click()
