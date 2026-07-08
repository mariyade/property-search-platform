import requests
from config import TestUser

from app.database import SessionLocal
from app.models import SearchRun, Users


def delete_test_user(username: str):
    db = SessionLocal()
    try:
        user = db.query(Users).filter(Users.username == username).first()
        if user is None:
            return
        db.query(SearchRun).filter(SearchRun.owner_id == user.id).delete()
        db.delete(user)
        db.commit()
    finally:
        db.close()


def create_test_user(base_url: str):
    response = requests.post(
        f"{base_url}/auth/",
        json={
            "username": TestUser.username,
            "email": TestUser.email,
            "first_name": TestUser.first_name,
            "last_name": TestUser.last_name,
            "password": TestUser.password,
            "phone_number": TestUser.phone_number,
        },
        timeout=10,
    )
    if response.status_code not in {201, 400}:
        raise AssertionError(
            f"Could not create test user through API: {response.status_code} {response.text}"
        )
