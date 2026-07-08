from fastapi import status

from app.tests.utils import client


def test_admin_can_read_users(test_user, admin_user, admin_auth_override):
    response = client.get("/admin/users")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2


def test_normal_user_cannot_read_admin_users(test_user, auth_override):
    response = client.get("/admin/users")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Admin access required"}


def test_admin_can_deactivate_user(test_user, admin_user, admin_auth_override):
    response = client.put(f"/admin/users/{test_user.id}/deactivate")

    assert response.status_code == status.HTTP_204_NO_CONTENT
