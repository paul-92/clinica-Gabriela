from datetime import date

from app.database.session import get_session
from app.models.patient import Patient
from app.services.appointment_service import AppointmentService
from app.services.finance_service import FinanceService


class DashboardController:
    def summary(self):
        with get_session() as session:
            patients_count = session.query(Patient).count()
            appointments = AppointmentService(session).appointments_for_day(date.today())
            finance = FinanceService(session).monthly_summary()
            return {
                "patients_count": patients_count,
                "today_appointments": len(appointments),
                "finance": finance,
            }
