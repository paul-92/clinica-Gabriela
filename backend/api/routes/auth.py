from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schemas.user import LoginRequest, LoginResponse
from backend.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = AuthService(db).authenticate(payload.username, payload.password)
    return {"authenticated": user is not None, "user": user}
