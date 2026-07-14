from app.services.search_cleaner import clean_data
from app.services.search_run_data import (
    build_search_filters,
    clear_search_run_rows,
    load_from_db,
    load_search_run,
    save_to_db,
    update_search_run_status,
)
from app.services.search_scraper import scrape_listings
from app.services.yield_calculator import calculate_gross_yield, calculate_net_yield


def scrape_sale_listings(search_run_id: int):
    search_run = load_search_run(search_run_id)
    filters = build_search_filters(search_run, channel="BUY")

    df = scrape_listings(
        filters=filters,
        max_pages=search_run["max_pages"],
        channel="BUY",
    )
    df["search_run_id"] = search_run_id

    clear_search_run_rows("search_run_sale_listings", search_run_id)
    save_to_db(df, table_name="search_run_sale_listings", if_exists="append")


def scrape_rent_listings(search_run_id: int):
    search_run = load_search_run(search_run_id)
    filters = build_search_filters(search_run, channel="RENT")

    df = scrape_listings(
        filters=filters,
        max_pages=search_run["max_pages"],
        channel="RENT",
    )
    df["search_run_id"] = search_run_id

    clear_search_run_rows("search_run_rent_listings", search_run_id)
    save_to_db(df, table_name="search_run_rent_listings", if_exists="append")


def clean_search_listings(search_run_id: int):
    sale_df = load_from_db("search_run_sale_listings")
    rent_df = load_from_db("search_run_rent_listings")

    sale_df = sale_df[sale_df["search_run_id"] == search_run_id]
    rent_df = rent_df[rent_df["search_run_id"] == search_run_id]

    clean_sale_df = clean_data(sale_df)
    clean_rent_df = clean_data(rent_df)

    clear_search_run_rows("clean_search_run_sale_listings", search_run_id)
    clear_search_run_rows("clean_search_run_rent_listings", search_run_id)

    if not clean_sale_df.empty:
        save_to_db(clean_sale_df, "clean_search_run_sale_listings", if_exists="append")
    if not clean_rent_df.empty:
        save_to_db(clean_rent_df, "clean_search_run_rent_listings", if_exists="append")


def calculate_search_yields(search_run_id: int):
    search_run = load_search_run(search_run_id)
    sale_df = load_from_db("clean_search_run_sale_listings")
    rent_df = load_from_db("clean_search_run_rent_listings")

    sale_df = sale_df[sale_df["search_run_id"] == search_run_id]
    rent_df = rent_df[rent_df["search_run_id"] == search_run_id]

    avg_rent_per_postcode_room = rent_df.groupby(["Postcode", "Rooms"])["Price"].mean().to_dict()
    result_df = calculate_gross_yield(sale_df, avg_rent_per_postcode_room)
    result_df = calculate_net_yield(
        result_df,
        mortgage_rate=search_run["mortgage_rate"],
        ltv=search_run["ltv"],
    )

    if "Gross_Yield_%" in result_df.columns:
        result_df["Gross_Yield_%"] = result_df["Gross_Yield_%"].round(2)
    if "Net_Yield_%" in result_df.columns:
        result_df["Net_Yield_%"] = result_df["Net_Yield_%"].round(2)

    clear_search_run_rows("search_run_yields", search_run_id)
    if not result_df.empty:
        save_to_db(result_df, "search_run_yields", if_exists="append")


def run_search_pipeline(search_run_id: int):
    update_search_run_status(search_run_id, "running")
    scrape_sale_listings(search_run_id)
    scrape_rent_listings(search_run_id)
    clean_search_listings(search_run_id)
    calculate_search_yields(search_run_id)
    update_search_run_status(search_run_id, "completed")
