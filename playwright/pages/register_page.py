from playwright.sync_api import Page


class RegisterPage:
    def __init__(self, page: Page):
        self.page = page
        self.first_name = page.locator("#first_name")
        self.last_name = page.locator("#last_name")
        self.username = page.locator("#username")
        self.email = page.locator("#email")
        self.phone_number = page.locator("#phone_number")
        self.password = page.locator("#password")
        self.confirm_password = page.locator("#password2")
        self.submit_button = page.get_by_role("button", name="Register")

    def open(self):
        self.page.goto("/register")

    def register(self, user, confirm_password: str | None = None):
        self.first_name.fill(user.first_name)
        self.last_name.fill(user.last_name)
        self.username.fill(user.username)
        self.email.fill(user.email)
        self.phone_number.fill(user.phone_number)
        self.password.fill(user.password)
        self.confirm_password.fill(confirm_password or user.password)
        self.submit_button.click()
