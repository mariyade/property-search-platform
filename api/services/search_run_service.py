from sqlalchemy.orm import Session

from api.models import SearchRun
from api.schemas import SearchRunCreate
from api.tasks.search_runs import process_search_run


def create_search_run_with_pipeline_trigger(
    db: Session,
    search_run_request: SearchRunCreate,
    owner_id: int,
) -> SearchRun:
    search_run = SearchRun(
        **search_run_request.model_dump(),
        owner_id=owner_id,
    )

    db.add(search_run)
    db.commit()
    db.refresh(search_run)

    process_search_run.delay(search_run.id)

    return search_run
