from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    RESCHEDULED = "rescheduled"
    CANCELED = "canceled"
    DONE = "done"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    psychologist_id: Mapped[int] = mapped_column(ForeignKey("psychologists.id"), nullable=False)
    scheduled_at = mapped_column(DateTime, nullable=False, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=50)
    status: Mapped[str] = mapped_column(String(30), default=AppointmentStatus.SCHEDULED.value)
    notes = mapped_column(Text, default="")

    patient = relationship("Patient", back_populates="appointments")
    psychologist = relationship("Psychologist", back_populates="appointments")
