from datetime import timedelta

import pytest
from fastapi import HTTPException, status
from jose import jwt

from app.models import Users
from app.routers.auth import (
    ALGORITHM,
    SECRET_KEY,
    authenticate_user,
    bcrypt_context,
    create_access_token,
    get_current_user,
)


class FakeQuery:
    def __init__(self, user):
        self.user = user

    def filter(self, *conditions):
        return self

    def first(self):
        return self.user


class FakeDb:
    def __init__(self, user=None):
        self.user = user

    def query(self, model):
        return FakeQuery(self.user)


def make_user(
    username="testuser",
    password="testpassword",
    is_active=True,
):
    return Users(
        username=username,
        email=f"{username}@example.com",
        hashed_password=bcrypt_context.hash(password),
        role="user",
        is_active=is_active,
    )


def test_authenticate_user_returns_user_for_valid_credentials():
    user = make_user()

    authenticated_user = authenticate_user(user.username, "testpassword", FakeDb(user))

    assert authenticated_user is not False
    assert authenticated_user.username == user.username


def test_authenticate_user_rejects_unknown_username():
    assert authenticate_user("missing", "testpassword", FakeDb()) is False


def test_authenticate_user_rejects_wrong_password():
    user = make_user()

    assert authenticate_user(user.username, "wrong", FakeDb(user)) is False


def test_authenticate_user_rejects_inactive_user():
    user = make_user(username="inactive", is_active=False)

    assert authenticate_user("inactive", "testpassword", FakeDb(user)) is False


def test_create_access_token_contains_user_claims():
    token = create_access_token("testuser", 1, "user", timedelta(minutes=20))
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert decoded_token["sub"] == "testuser"
    assert decoded_token["id"] == 1
    assert decoded_token["role"] == "user"


def test_create_access_token_contains_expiry():
    token = create_access_token("testuser", 1, "user", timedelta(minutes=20))
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert "exp" in decoded_token


@pytest.mark.asyncio
async def test_get_current_user_returns_claims_for_valid_token():
    token = jwt.encode({"sub": "testuser", "id": 1, "role": "user"}, SECRET_KEY, ALGORITHM)

    user = await get_current_user(token=token)

    assert user == {"username": "testuser", "id": 1, "user_role": "user"}


@pytest.mark.asyncio
async def test_get_current_user_rejects_token_without_subject():
    token = jwt.encode({"id": 1, "role": "user"}, SECRET_KEY, ALGORITHM)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_current_user_rejects_token_without_user_id():
    token = jwt.encode({"sub": "testuser", "role": "user"}, SECRET_KEY, ALGORITHM)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
