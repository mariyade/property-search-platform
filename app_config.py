import os

DEFAULT_DATABASE_URL = (
    "postgresql+psycopg2://property_search:property_search@127.0.0.1:5433/property_search"
)

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
