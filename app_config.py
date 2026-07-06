import os

DEFAULT_DATABASE_URL = "postgresql+psycopg2://airflow:airflow@localhost:5432/airflow"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
