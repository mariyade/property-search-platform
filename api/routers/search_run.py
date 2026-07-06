from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status

from api.services.search_run_service import create_search_run_with_pipeline_trigger

from ..database import get_db
from ..models import SearchRun
from ..schemas import PaginatedSearchRunResults, SearchRunCreate, SearchRunResponse
from .auth import get_current_user

router = APIRouter(
    prefix="/search-runs",
    tags=["search-runs"],
)

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


def round_value(value, digits=2):
    if value is None:
        return None
    return round(value, digits)


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[SearchRunResponse])
async def read_all(db: db_dependency, user: user_dependency):
    return db.query(SearchRun).filter(SearchRun.owner_id == user.get("id")).all()


@router.get("/{run_id}", status_code=status.HTTP_200_OK, response_model=SearchRunResponse)
async def read_search_run(
    db: db_dependency,
    user: user_dependency,
    run_id: int = Path(gt=0),
):

    run_model = (
        db.query(SearchRun)
        .filter(
            SearchRun.id == run_id,
            SearchRun.owner_id == user.get("id"),
        )
        .first()
    )
    if run_model is not None:
        return run_model
    raise HTTPException(status_code=404, detail="Search run not found")


@router.get(
    "/{run_id}/results",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedSearchRunResults,
)
async def read_search_run_results(
    db: db_dependency,
    user: user_dependency,
    run_id: int = Path(gt=0),
    limit: int = Query(default=20, gt=0, le=100),
    offset: int = Query(default=0, ge=0),
):
    run_model = (
        db.query(SearchRun)
        .filter(
            SearchRun.id == run_id,
            SearchRun.owner_id == user.get("id"),
        )
        .first()
    )
    if run_model is None:
        raise HTTPException(status_code=404, detail="Search run not found")
    if run_model.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=run_model.error_message or "Search run failed",
        )
    if run_model.status in {"pending", "running"}:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Search run is still {run_model.status}",
        )

    try:
        total = db.execute(
            text("""
                SELECT COUNT(*)
                FROM search_run_yields
                WHERE search_run_id = :run_id
            """),
            {"run_id": run_id},
        ).scalar_one()

        rows = (
            db.execute(
                text("""
                SELECT *
                FROM search_run_yields
                WHERE search_run_id = :run_id
                ORDER BY "Net_Yield_%" DESC NULLS LAST
                LIMIT :limit OFFSET :offset
            """),
                {
                    "run_id": run_id,
                    "limit": limit,
                    "offset": offset,
                },
            )
            .mappings()
            .all()
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search results are not available yet",
        ) from exc

    items = []
    for row in rows:
        items.append(
            {
                "search_run_id": row.get("search_run_id"),
                "address": row.get("Address"),
                "city": row.get("City"),
                "postcode": row.get("Postcode"),
                "price": round_value(row.get("Price")),
                "rooms": row.get("Rooms"),
                "link": row.get("Link"),
                "date_last_updated": row.get("DateLastUpdated"),
                "estimated_annual_rent": round_value(row.get("EstimatedAnnualRent")),
                "gross_yield_percent": round_value(row.get("Gross_Yield_%")),
                "net_yield_percent": round_value(row.get("Net_Yield_%")),
            }
        )

    return {
        "search_run_id": run_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SearchRunResponse)
async def create_search_run(
    db: db_dependency,
    user: user_dependency,
    search_run_request: SearchRunCreate,
):
    try:
        return create_search_run_with_pipeline_trigger(
            db,
            search_run_request,
            owner_id=user.get("id"),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_search_run(
    db: db_dependency,
    user: user_dependency,
    run_id: int = Path(gt=0),
):
    search_run_model = (
        db.query(SearchRun)
        .filter(
            SearchRun.id == run_id,
            SearchRun.owner_id == user.get("id"),
        )
        .first()
    )
    if search_run_model is None:
        raise HTTPException(status_code=404, detail="Search run not found")
    db.query(SearchRun).filter(
        SearchRun.id == run_id,
        SearchRun.owner_id == user.get("id"),
    ).delete()
    db.commit()
