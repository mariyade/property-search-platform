from fastapi import status

from app.tests.utils import client


def test_health_check():
    response = client.get("/health/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
