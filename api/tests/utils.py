import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.database import Base, get_db
from api.main import app
from api.models import SearchRun, Users
from api.routers.auth import bcrypt_context, get_current_user

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

with engine.begin() as connection:
    connection.execute(
        text("""
            CREATE TABLE IF NOT EXISTS search_run_yields (
                search_run_id INTEGER,
                "Address" TEXT,
                "City" TEXT,
                "Postcode" TEXT,
                "Price" FLOAT,
                "Rooms" INTEGER,
                "Link" TEXT,
                "DateLastUpdated" TEXT,
                "EstimatedAnnualRent" FLOAT,
                "Gross_Yield_%" FLOAT,
                "Net_Yield_%" FLOAT
            )
        """)
    )


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    return {"username": "testuser", "id": 1, "user_role": "user"}


def override_get_admin_user():
    return {"username": "admin", "id": 2, "user_role": "admin"}


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_tables():
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM search_run_yields"))
        connection.execute(text("DELETE FROM search_runs"))
        connection.execute(text("DELETE FROM users"))
    yield
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM search_run_yields"))
        connection.execute(text("DELETE FROM search_runs"))
        connection.execute(text("DELETE FROM users"))


@pytest.fixture
def test_user():
    user = Users(
        id=1,
        username="testuser",
        email="testuser@example.com",
        first_name="Test",
        last_name="User",
        hashed_password=bcrypt_context.hash("testpassword"),
        role="user",
        is_active=True,
        phone_number="07111111111",
    )
    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def admin_user():
    user = Users(
        id=2,
        username="admin",
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        hashed_password=bcrypt_context.hash("adminpassword"),
        role="admin",
        is_active=True,
        phone_number="07222222222",
    )
    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def search_run(test_user):
    run = SearchRun(
        id=1,
        owner_id=test_user.id,
        status="completed",
        search_location="E1 1LF",
        location_identifier="POSTCODE^1327365",
        radius=0.25,
        min_price=120000,
        max_price=400000,
        min_bedrooms=1,
        max_bedrooms=2,
        property_types="flat",
        include_sstc="on",
        sort_type=6,
        channel="BUY",
        transaction_type="BUY",
        display_location_identifier="undefined",
        result_index=0,
        max_pages=1,
    )
    db = TestingSessionLocal()
    db.add(run)
    db.commit()
    db.refresh(run)
    db.close()
    return run


@pytest.fixture
def auth_override():
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def admin_auth_override():
    app.dependency_overrides[get_current_user] = override_get_admin_user
    yield
    app.dependency_overrides.pop(get_current_user, None)
