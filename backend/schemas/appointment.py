from datetime import datetime

from pydantic import Field

from backend.schemas.common import ORMBase


class AppointmentBase(ORMBase):
    patient_id: int
    psychologist_id: int
    scheduled_at: datetime
    duration_minutes: int = Field(default=50, gt=0)
    status: str = "scheduled"
    notes: str = ""
    timezone_name: str = "America/Sao_Paulo"


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(ORMBase):
    patient_id: int | None = None
    psychologist_id: int | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    status: str | None = None
    notes: str | None = None
    timezone_name: str | None = None


class AppointmentRead(AppointmentBase):
    id: int
    version: int
    updated_at: datetime | None = None
    original_appointment_id: int | None = None


class AppointmentAction(ORMBase):
    reason: str = ""


class AppointmentExceptionalCorrection(ORMBase):
    target_status: str
    reason: str = Field(min_length=1, max_length=500)


class AppointmentReschedule(AppointmentCreate):
    reason: str = Field(min_length=1, max_length=500)
