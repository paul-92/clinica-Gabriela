from datetime import date

from app.database.session import get_session
from app.models.patient import Patient
from app.services.appointment_service import AppointmentService
from app.controllers.finance_controller import FinanceController


class DashboardController:
    def __init__(self, api_client, role):
        self.finance = FinanceController(api_client)
        self.role = role

    def summary(self):
        with get_session() as session:
            patients_count = session.query(Patient).count()
            appointments = AppointmentService(session).appointments_for_day(date.today())
            finance = self.finance.summary() if self.role != "psychologist" else None
            return {
                "patients_count": patients_count,
                "today_appointments": len(appointments),
                "finance": finance,
            }
