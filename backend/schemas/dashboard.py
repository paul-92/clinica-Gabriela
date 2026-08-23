from datetime import datetime

from backend.schemas.common import ORMBase


class DashboardAppointment(ORMBase):
    id: int
    scheduled_at: datetime
    patient_name: str
    psychologist_name: str
    status: str


class DashboardSummary(ORMBase):
    active_patients: int
    active_psychologists: int
    appointments_today: int
    pending_payments: float
    paid_payments: float
    expenses: float
    balance: float
    recent_appointments: list[DashboardAppointment]
