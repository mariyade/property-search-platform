import os

import requests

AIRFLOW_BASE_URL = os.getenv("AIRFLOW_BASE_URL", "http://airflow:8080")
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME", "admin")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD", "admin")

DAG_ID = "filtered_search_dag"


def trigger_airflow_filtered_search_dag(search_run_id: int) -> None:
    url = f"{AIRFLOW_BASE_URL}/api/v1/dags/{DAG_ID}/dagRuns"

    try:
        response = requests.post(
            url,
            auth=(AIRFLOW_USERNAME, AIRFLOW_PASSWORD),
            json={
                "conf": {
                    "search_run_id": search_run_id,
                }
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        detail = getattr(exc.response, "text", None)
        message = f"Failed to trigger Airflow DAG for search_run_id={search_run_id}"
        if detail:
            message = f"{message}: {detail}"
        raise RuntimeError(message) from exc
