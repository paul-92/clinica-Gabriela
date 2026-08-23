from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.session import Base


class ClinicSettings(Base):
    __tablename__ = "clinic_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clinic_name: Mapped[str] = mapped_column(String(160), default="Marilia Gabriela Gaspar | Psicologa")
    phone: Mapped[str] = mapped_column(String(30), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    address: Mapped[str] = mapped_column(String(255), default="")
    default_session_value: Mapped[float] = mapped_column(Float, default=0.0)
