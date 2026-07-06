import pytest
from fastapi import HTTPException, status

from api.routers.admin import require_admin


def test_require_admin_returns_admin_user():
    user = {"id": 2, "username": "admin", "user_role": "admin"}

    assert require_admin(user) == user


def test_require_admin_rejects_normal_user():
    with pytest.raises(HTTPException) as exc:
        require_admin({"id": 1, "username": "testuser", "user_role": "user"})

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc.value.detail == "Admin access required"


def test_require_admin_rejects_missing_role():
    with pytest.raises(HTTPException) as exc:
        require_admin({"id": 1, "username": "testuser"})

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
