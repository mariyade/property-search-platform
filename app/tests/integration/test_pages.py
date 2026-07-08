from app.tests.utils import client


def test_ui_page_loads():
    response = client.get("/ui")

    assert response.status_code == 200
    assert "Search properties" in response.text
    assert "Property Deals Dashboard" in response.text


def test_login_page_loads():
    response = client.get("/login")

    assert response.status_code == 200
    assert "Login" in response.text


def test_register_page_loads():
    response = client.get("/register")

    assert response.status_code == 200
    assert "Register" in response.text
