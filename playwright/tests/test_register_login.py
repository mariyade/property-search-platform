import re

import pytest
from config import TestUser
from pages.login_page import LoginPage
from pages.navbar import Navbar
from pages.register_page import RegisterPage
from pages.search_page import SearchPage
from playwright.sync_api import expect
from utils.backend_cleanup import create_test_user


@pytest.mark.e2e
def test_register_then_login_same_user(browser_page, clean_test_user):
    register_page = RegisterPage(browser_page)
    login_page = LoginPage(browser_page)
    navbar = Navbar(browser_page)
    search_page = SearchPage(browser_page)

    register_page.open()
    register_page.register(TestUser)

    expect(browser_page).to_have_url(re.compile(r".*/login$"))

    login_page.login(TestUser.username, TestUser.password)

    expect(browser_page).to_have_url(re.compile(r".*/ui$"))
    expect(search_page.heading).to_be_visible()
    expect(navbar.logout_button).to_be_visible()

    navbar.logout()

    expect(browser_page).to_have_url(re.compile(r".*/login$"))

    login_page.login(TestUser.username, TestUser.password)

    expect(browser_page).to_have_url(re.compile(r".*/ui$"))
    expect(search_page.heading).to_be_visible()


@pytest.mark.e2e
def test_invalid_login_shows_error(browser_page):
    login_page = LoginPage(browser_page)

    login_page.open()

    browser_page.dialog_messages.clear()
    login_page.login("invalid_user", "wrong_password")

    browser_page.wait_for_timeout(500)
    assert browser_page.dialog_messages == ["Incorrect username or password."]
    expect(browser_page).to_have_url(re.compile(r".*/login$"))


@pytest.mark.e2e
def test_register_with_mismatched_passwords_shows_error(browser_page, clean_test_user):
    register_page = RegisterPage(browser_page)

    register_page.open()

    browser_page.dialog_messages.clear()
    register_page.register(TestUser, confirm_password="Different123!")

    browser_page.wait_for_timeout(500)
    assert browser_page.dialog_messages == ["Passwords do not match"]
    expect(browser_page).to_have_url(re.compile(r".*/register$"))


@pytest.mark.e2e
def test_register_existing_user_shows_error(browser_page, app_base_url, clean_test_user):
    create_test_user(app_base_url)
    register_page = RegisterPage(browser_page)

    register_page.open()

    browser_page.dialog_messages.clear()
    register_page.register(TestUser)

    browser_page.wait_for_timeout(500)
    assert browser_page.dialog_messages == ["Username or email already exists"]
    expect(browser_page).to_have_url(re.compile(r".*/register$"))
