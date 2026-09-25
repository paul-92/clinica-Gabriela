from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.dependencies import require_admin
from backend.database.session import get_db
from backend.models.user import User
from backend.schemas.user import UserCreate, UserRead, UserUpdate
from backend.services.errors import ConflictError, NotFoundError
from backend.services.user_management_service import UserManagementService


router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_admin)])


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    return UserManagementService(db).list_users()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        return UserManagementService(db).create_user(payload.model_dump())
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return UserManagementService(db).update_user(user_id, payload.model_dump(exclude_unset=True), current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
