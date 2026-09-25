from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.common import ORMBase


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=128)
    role: str
    active: bool = True

    model_config = ConfigDict(extra="forbid")


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    username: str | None = Field(default=None, min_length=1, max_length=80)
    role: str | None = None
    active: bool | None = None

    model_config = ConfigDict(extra="forbid")


class UserRead(ORMBase):
    id: int
    name: str
    username: str
    role: str
    psychologist_id: int | None = None
    active: bool
    password_reset_required: bool
    created_at: datetime | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
