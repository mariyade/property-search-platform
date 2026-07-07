from api.celery_app import celery_app
from api.services.search_pipeline import run_search_pipeline
from api.services.search_run_data import update_search_run_status


@celery_app.task(name="search_runs.process_search_run")
def process_search_run(search_run_id: int):
    try:
        run_search_pipeline(search_run_id)
    except Exception as exc:
        update_search_run_status(search_run_id, "failed", str(exc))
        raise

    return {"search_run_id": search_run_id}
