from fastapi import status

from api.tests.utils import client


def test_get_user(test_user, auth_override):
    response = client.get("/user/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == test_user.username
    assert response.json()["email"] == test_user.email


def test_change_password_success(test_user, auth_override):
    response = client.put(
        "/user/password",
        json={"password": "testpassword", "new_password": "newpassword"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_change_password_invalid_current_password(test_user, auth_override):
    response = client.put(
        "/user/password",
        json={"password": "wrong", "new_password": "newpassword"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Current password is incorrect"}


def test_change_phone_number_success(test_user, auth_override):
    response = client.put("/user/phonenumber/07999999999")

    assert response.status_code == status.HTTP_204_NO_CONTENT
