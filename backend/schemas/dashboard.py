from datetime import date, datetime

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
    finance_regime: str
    finance_start: date
    finance_end: date
    receivable_cents: int
    received_cents: int
    expense_cents: int
    balance_cents: int
    recent_appointments: list[DashboardAppointment]
