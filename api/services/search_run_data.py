from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text

from app_config import DATABASE_URL

SEARCH_RUN_TABLES = {
    "search_run_sale_listings",
    "search_run_rent_listings",
    "clean_search_run_sale_listings",
    "clean_search_run_rent_listings",
    "search_run_yields",
}


def get_engine():
    return create_engine(DATABASE_URL)


def load_from_db(table_name: str):
    engine = get_engine()
    return pd.read_sql(f"SELECT * FROM {table_name}", engine)


def save_to_db(df, table_name: str, if_exists: str = "replace"):
    engine = get_engine()
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)


def load_search_run(search_run_id: int) -> dict:
    engine = get_engine()
    with engine.connect() as conn:
        result = (
            conn.execute(
                text("SELECT * FROM search_runs WHERE id = :id"),
                {"id": search_run_id},
            )
            .mappings()
            .first()
        )

    if result is None:
        raise ValueError(f"Search run {search_run_id} not found")

    return dict(result)


def update_search_run_status(
    search_run_id: int,
    status: str,
    error_message: str | None = None,
):
    now = datetime.utcnow()
    started_at = now if status == "running" else None
    finished_at = now if status in {"completed", "failed"} else None

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE search_runs
                SET status = :status,
                    error_message = :error_message,
                    started_at = COALESCE(:started_at, started_at),
                    finished_at = COALESCE(:finished_at, finished_at)
                WHERE id = :id
            """),
            {
                "id": search_run_id,
                "status": status,
                "error_message": error_message,
                "started_at": started_at,
                "finished_at": finished_at,
            },
        )


def clear_search_run_rows(table_name: str, search_run_id: int):
    if table_name not in SEARCH_RUN_TABLES:
        raise ValueError(f"Table is not allowed for search run cleanup: {table_name}")

    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(
                text(f"DELETE FROM {table_name} WHERE search_run_id = :search_run_id"),
                {"search_run_id": search_run_id},
            )
    except Exception as exc:
        print(f"Could not clear rows from {table_name}: {exc}")


def build_search_filters(search_run: dict, channel: str = "BUY") -> dict:
    channel = channel.upper()

    filters = {
        "searchLocation": search_run["search_location"],
        "useLocationIdentifier": "true",
        "locationIdentifier": search_run["location_identifier"],
        "radius": search_run["radius"],
        "sortType": search_run["sort_type"],
        "channel": channel,
        "transactionType": "BUY" if channel == "BUY" else "LETTING",
        "displayLocationIdentifier": search_run["display_location_identifier"],
        "index": search_run["result_index"],
    }

    optional_fields = {
        "minBedrooms": search_run.get("min_bedrooms"),
        "maxBedrooms": search_run.get("max_bedrooms"),
        "propertyTypes": search_run.get("property_types"),
    }

    if channel == "BUY":
        optional_fields.update(
            {
                "minPrice": search_run.get("min_price"),
                "maxPrice": search_run.get("max_price"),
            }
        )
        filters["_includeSSTC"] = search_run["include_sstc"]
    else:
        filters["includeLetAgreed"] = "on"

    for key, value in optional_fields.items():
        if value is not None:
            filters[key] = value

    return filters
