from enum import Enum

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    PSYCHOLOGIST = "psychologist"
    RECEPTION = "reception"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default=UserRole.RECEPTION.value)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at = mapped_column(DateTime, server_default=func.now())
