from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base


class Psychologist(Base):
    __tablename__ = "psychologists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    crp: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(30), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    specialty: Mapped[str] = mapped_column(String(120), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at = mapped_column(DateTime, server_default=func.now())

    appointments = relationship("Appointment", back_populates="psychologist")
    clinical_records = relationship("ClinicalRecord", back_populates="psychologist")
