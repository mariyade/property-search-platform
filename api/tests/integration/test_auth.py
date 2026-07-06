from fastapi import status

from api.tests.utils import client


def test_create_user_success():
    response = client.post(
        "/auth/",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "password123",
            "phone_number": "07000000000",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "User created successfully"}


def test_create_user_duplicate_returns_400(test_user):
    response = client.post(
        "/auth/",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "password123",
            "phone_number": "07000000000",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Username or email already exists"}
