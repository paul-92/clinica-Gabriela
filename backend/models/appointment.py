from enum import Enum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CANCELED = "canceled"
    DONE = "done"
    NO_SHOW = "no_show"


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="ck_appointments_duration_positive"),
        CheckConstraint("status IN ('scheduled','done','canceled','no_show')", name="ck_appointments_status"),
        Index("ix_appointments_psychologist_start_status", "psychologist_id", "scheduled_at", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    psychologist_id: Mapped[int] = mapped_column(ForeignKey("psychologists.id"), nullable=False)
    scheduled_at = mapped_column(DateTime, nullable=False, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=50)
    status: Mapped[str] = mapped_column(String(30), default=AppointmentStatus.SCHEDULED.value)
    notes = mapped_column(Text, default="")
    updated_at = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    original_appointment_id: Mapped[int | None] = mapped_column(
        ForeignKey("appointments.id", ondelete="NO ACTION"), nullable=True, unique=True
    )
    timezone_name: Mapped[str] = mapped_column(String(64), nullable=False, default="America/Sao_Paulo", server_default="America/Sao_Paulo")
    temporal_status: Mapped[str] = mapped_column(String(32), nullable=False, default="verified", server_default="verified")

    patient = relationship("Patient", back_populates="appointments")
    psychologist = relationship("Psychologist", back_populates="appointments")


class AppointmentEvent(Base):
    __tablename__ = "appointment_events"
    __table_args__ = (
        Index("ix_appointment_events_appointment_created", "appointment_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id", ondelete="NO ACTION"), nullable=False)
    successor_appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id", ondelete="NO ACTION"))
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="NO ACTION"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
