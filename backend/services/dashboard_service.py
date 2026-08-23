from datetime import date

from backend.models.patient import Patient
from backend.models.psychologist import Psychologist
from backend.services.appointment_service import AppointmentService
from backend.services.finance_service import FinanceService


class DashboardService:
    def __init__(self, db):
        self.db = db

    def summary(self):
        appointments = AppointmentService(self.db).list_appointments(date.today())
        finance = FinanceService(self.db).summary()
        active_patients = self.db.query(Patient).filter(Patient.active.is_(True)).count()
        active_psychologists = self.db.query(Psychologist).filter(Psychologist.active.is_(True)).count()

        return {
            "active_patients": active_patients,
            "active_psychologists": active_psychologists,
            "appointments_today": len(appointments),
            "pending_payments": finance["pending"],
            "paid_payments": finance["paid"],
            "expenses": finance["expenses"],
            "balance": finance["balance"],
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
