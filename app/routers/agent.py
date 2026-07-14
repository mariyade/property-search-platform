from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status

from app.database import get_db
from app.models import SearchRun
from app.schemas import DealAgentRequest, DealAgentResponse
from app.services.deal_agent import (
    DealAgentInputBlockedError,
    DealAgentUnavailableError,
    run_deal_agent,
)

from .auth import get_current_user

router = APIRouter(
    prefix="/search-runs",
    tags=["deal-agent"],
)

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.post(
    "/{run_id}/agent-summary",
    status_code=status.HTTP_200_OK,
    response_model=DealAgentResponse,
)
async def create_agent_summary(
    request: DealAgentRequest,
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
        return run_deal_agent(
            db=db,
            search_run_id=run_id,
            mortgage_rate=run_model.mortgage_rate,
            ltv=run_model.ltv,
            question=request.question,
            limit=request.limit,
            offset=request.offset,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search results are not available yet",
        ) from exc
    except DealAgentInputBlockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except DealAgentUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
