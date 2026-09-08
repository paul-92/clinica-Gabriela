from datetime import datetime

from pydantic import BaseModel

from backend.schemas.common import ORMBase


class LoginRequest(BaseModel):
    username: str
    password: str


class UserRead(ORMBase):
    id: int
    name: str
    username: str
    role: str
    active: bool
    created_at: datetime | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
