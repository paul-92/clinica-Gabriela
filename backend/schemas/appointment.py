from datetime import datetime

from backend.schemas.common import ORMBase


class AppointmentBase(ORMBase):
    patient_id: int
    psychologist_id: int
    scheduled_at: datetime
    duration_minutes: int = 50
    status: str = "scheduled"
    notes: str = ""


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(ORMBase):
    patient_id: int | None = None
    psychologist_id: int | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = None
    status: str | None = None
    notes: str | None = None


class AppointmentRead(AppointmentBase):
    id: int
