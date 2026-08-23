from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    cpf: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    birth_date = mapped_column(Date, nullable=True)
    phone: Mapped[str] = mapped_column(String(30), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    address: Mapped[str] = mapped_column(String(255), default="")
    emergency_contact: Mapped[str] = mapped_column(String(160), default="")
    notes = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at = mapped_column(DateTime, server_default=func.now())

    appointments = relationship("Appointment", back_populates="patient")
    clinical_records = relationship("ClinicalRecord", back_populates="patient")
