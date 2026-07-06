from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from db import load_from_db, save_to_db
from tasks.scraping import scrape_listings
from tasks.cleaner import clean_data
from tasks.yield_calculator import calculate_gross_yield, calculate_net_yield
from tasks.search_runs import (
    build_search_filters,
    clear_search_run_rows,
    load_search_run,
    update_search_run_status,
)

def get_search_run_id(context):
    conf = context["dag_run"].conf or {}
    search_run_id = conf.get("search_run_id")

    if search_run_id is None:
        raise ValueError("Missing search_run_id in dag_run.conf")

    return search_run_id

def mark_search_failed(context):
    try:
        search_run_id = get_search_run_id(context)
        exception = context.get("exception")
        update_search_run_status(search_run_id, "failed", str(exception))
    except Exception as exc:
        print(f"Could not mark search run as failed: {exc}")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2026, 7, 4),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": mark_search_failed,
}

dag = DAG(
    'filtered_search_dag',
    default_args=default_args,
    description='DAG for scraping and analyzing property listings',
    schedule_interval=None,
    catchup=False,
)

def mark_search_running(**context):
    search_run_id = get_search_run_id(context)
    update_search_run_status(search_run_id, "running")

def scrape_sale_listings(**context):
    search_run_id = get_search_run_id(context)
    search_run = load_search_run(search_run_id)

    filters = build_search_filters(search_run, channel="BUY")

    df = scrape_listings(
        filters=filters,
        max_pages=search_run["max_pages"],
        channel="BUY",
    )

    df["search_run_id"] = search_run_id

    clear_search_run_rows("search_run_sale_listings", search_run_id)
    save_to_db(
        df,
        table_name="search_run_sale_listings",
        if_exists="append",
    )

def scrape_rent_listings(**context):
    search_run_id = get_search_run_id(context)
    search_run = load_search_run(search_run_id)

    filters = build_search_filters(search_run, channel="RENT")

    df = scrape_listings(
        filters=filters,
        max_pages=search_run["max_pages"],
        channel="RENT",
    )

    df["search_run_id"] = search_run_id

    clear_search_run_rows("search_run_rent_listings", search_run_id)
    save_to_db(
        df,
        table_name="search_run_rent_listings",
        if_exists="append",
    )

def clean_search_listings(**context):
    search_run_id = get_search_run_id(context)

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

def calculate_search_yields(**context):
    search_run_id = get_search_run_id(context)

    sale_df = load_from_db("clean_search_run_sale_listings")
    rent_df = load_from_db("clean_search_run_rent_listings")

    sale_df = sale_df[sale_df["search_run_id"] == search_run_id]
    rent_df = rent_df[rent_df["search_run_id"] == search_run_id]

    avg_rent_per_postcode_room = rent_df.groupby(["Postcode", "Rooms"])["Price"].mean().to_dict()
    result_df = calculate_gross_yield(sale_df, avg_rent_per_postcode_room)
    result_df = calculate_net_yield(result_df)

    if "Gross_Yield_%" in result_df.columns:
        result_df["Gross_Yield_%"] = result_df["Gross_Yield_%"].round(2)
    if "Net_Yield_%" in result_df.columns:
        result_df["Net_Yield_%"] = result_df["Net_Yield_%"].round(2)

    clear_search_run_rows("search_run_yields", search_run_id)
    if not result_df.empty:
        save_to_db(result_df, "search_run_yields", if_exists="append")

def mark_search_completed(**context):
    search_run_id = get_search_run_id(context)
    update_search_run_status(search_run_id, "completed")

mark_running_task = PythonOperator(
    task_id="mark_search_running",
    python_callable=mark_search_running,
    dag=dag,
)

scrape_sale_task = PythonOperator(
    task_id="scrape_sale_listings",
    python_callable=scrape_sale_listings,
    dag=dag,
)

scrape_rent_task = PythonOperator(
    task_id="scrape_rent_listings",
    python_callable=scrape_rent_listings,
    dag=dag,
)

clean_task = PythonOperator(
    task_id="clean_search_listings",
    python_callable=clean_search_listings,
    dag=dag,
)

calculate_yields_task = PythonOperator(
    task_id="calculate_search_yields",
    python_callable=calculate_search_yields,
    dag=dag,
)

mark_completed_task = PythonOperator(
    task_id="mark_search_completed",
    python_callable=mark_search_completed,
    dag=dag,
)


mark_running_task >> scrape_sale_task >> scrape_rent_task >> clean_task >> calculate_yields_task >> mark_completed_task
