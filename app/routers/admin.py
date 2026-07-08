from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from starlette import status

from ..database import get_db
from ..models import Users
from ..schemas import UserResponse
from .auth import get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


def require_admin(user: user_dependency):
    if user.get("user_role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


admin_dependency = Annotated[dict, Depends(require_admin)]


@router.get("/users", status_code=status.HTTP_200_OK, response_model=list[UserResponse])
async def read_users(admin_user: admin_dependency, db: db_dependency):
    return db.query(Users).all()


@router.put("/users/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    admin_user: admin_dependency,
    db: db_dependency,
    user_id: int = Path(gt=0),
):
    user_model = db.query(Users).filter(Users.id == user_id).first()
    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found")

    user_model.is_active = False
    db.add(user_model)
    db.commit()
