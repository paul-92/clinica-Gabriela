from datetime import date, timedelta

from backend.models.patient import Patient
from backend.models.psychologist import Psychologist
from backend.services.appointment_service import AppointmentService
from backend.services.finance_service import FinanceService


class DashboardService:
    def __init__(self, db):
        self.db = db

    def summary(self, actor=None):
        today = date.today()
        appointments = AppointmentService(self.db).list_appointments(today, actor=actor)
        month_start = today.replace(day=1)
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        if actor is not None and actor.role == "psychologist":
            finance = {"receivable_cents": 0, "income_cents": 0, "expense_cents": 0, "balance_cents": 0}
        else:
            finance = FinanceService(self.db).summary(month_start, next_month, "cash", actor)
        active_patients = self.db.query(Patient).filter(Patient.active.is_(True)).count()
        active_psychologists = self.db.query(Psychologist).filter(Psychologist.active.is_(True)).count()

        return {
            "active_patients": active_patients,
            "active_psychologists": active_psychologists,
            "appointments_today": len(appointments),
            "finance_regime": "cash",
            "finance_start": month_start,
            "finance_end": next_month,
            "receivable_cents": finance["receivable_cents"],
            "received_cents": finance["income_cents"],
            "expense_cents": finance["expense_cents"],
            "balance_cents": finance["balance_cents"],
            "recent_appointments": [
                {
                    "id": item.id,
                    "scheduled_at": item.scheduled_at,
                    "patient_name": item.patient.full_name,
                    "psychologist_name": item.psychologist.full_name,
                    "status": item.status,
                }
                for item in appointments[:6]
            ],
        }
