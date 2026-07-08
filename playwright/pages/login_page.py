from playwright.sync_api import Page


class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username = page.locator("#username")
        self.password = page.locator("#password")
        self.submit_button = page.get_by_role("button", name="Login")

    def open(self):
        self.page.goto("/login")

    def login(self, username: str, password: str):
        self.username.fill(username)
        self.password.fill(password)
        self.submit_button.click()
