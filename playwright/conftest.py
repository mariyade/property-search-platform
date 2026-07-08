from pathlib import Path

import pytest
import requests
from config import TestUser
from playwright.sync_api import sync_playwright
from utils.backend_cleanup import delete_test_user

REPORTS_DIR = Path(__file__).parent / "reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
VIDEOS_DIR = REPORTS_DIR / "videos"
TRACES_DIR = REPORTS_DIR / "traces"


def pytest_addoption(parser):
    parser.addoption("--app-base-url", default="http://127.0.0.1:8000", help="Application base URL")
    parser.addoption(
        "--app-video",
        default="retain-on-failure",
        choices=["on", "off", "retain-on-failure"],
        help="Record browser video",
    )
    parser.addoption(
        "--app-screenshot",
        default="only-on-failure",
        choices=["on", "off", "only-on-failure"],
        help="Capture screenshots",
    )
    parser.addoption(
        "--app-tracing",
        default="retain-on-failure",
        choices=["on", "off", "retain-on-failure"],
        help="Capture Playwright traces",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.fixture()
def app_base_url(request):
    return request.config.getoption("--app-base-url")


@pytest.fixture()
def browser_page(request, app_base_url):
    browser_option = request.config.getoption("--browser")
    browser_name = browser_option[0] if browser_option else "chromium"
    headed = request.config.getoption("--headed")
    video_option = request.config.getoption("--app-video")
    tracing_option = request.config.getoption("--app-tracing")
    screenshot_option = request.config.getoption("--app-screenshot")

    for directory in (SCREENSHOTS_DIR, VIDEOS_DIR, TRACES_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(f"{app_base_url}/health/", timeout=2)
        response.raise_for_status()
    except requests.RequestException:
        pytest.fail(
            f"Application is not reachable at {app_base_url}. "
            "Start the app before running E2E tests."
        )

    with sync_playwright() as playwright:
        browser_type = getattr(playwright, browser_name)
        browser = browser_type.launch(headless=not headed)
        context_kwargs = {"base_url": app_base_url}
        if video_option in {"on", "retain-on-failure"}:
            context_kwargs["record_video_dir"] = str(VIDEOS_DIR)

        context = browser.new_context(**context_kwargs)
        if tracing_option in {"on", "retain-on-failure"}:
            context.tracing.start(screenshots=True, snapshots=True, sources=True)

        page = context.new_page()
        page.dialog_messages = []
        page.on("dialog", lambda dialog: accept_dialog(dialog, page.dialog_messages))

        yield page

        test_name = request.node.name
        test_failed = getattr(request.node, "rep_call", None) and request.node.rep_call.failed

        if screenshot_option == "on" or (screenshot_option == "only-on-failure" and test_failed):
            page.screenshot(path=str(SCREENSHOTS_DIR / f"{test_name}.png"), full_page=True)

        if tracing_option in {"on", "retain-on-failure"}:
            trace_path = TRACES_DIR / f"{test_name}.zip"
            if tracing_option == "on" or test_failed:
                context.tracing.stop(path=str(trace_path))
            else:
                context.tracing.stop()

        video_path = page.video.path() if page.video else None
        context.close()
        if video_path and video_option == "retain-on-failure" and not test_failed:
            Path(video_path).unlink(missing_ok=True)
        browser.close()


@pytest.fixture()
def clean_test_user():
    delete_test_user(TestUser.username)
    yield
    delete_test_user(TestUser.username)


def accept_dialog(dialog, messages):
    messages.append(dialog.message)
    dialog.accept()
