from datetime import date

from app.database.session import get_session
from app.services.appointment_service import AppointmentService


class AppointmentController:
    def today(self):
        with get_session() as session:
            return AppointmentService(session).appointments_for_day(date.today())
