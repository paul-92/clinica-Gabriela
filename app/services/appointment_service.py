from app.models.appointment import AppointmentStatus
from app.repositories.appointment_repository import AppointmentRepository


class AppointmentService:
    def __init__(self, session):
        self.repository = AppointmentRepository(session)

    def appointments_for_day(self, target_date=None, psychologist_id=None):
        return self.repository.by_day(target_date, psychologist_id)

    def change_status(self, appointment, status):
        if status not in {item.value for item in AppointmentStatus}:
            raise ValueError("Status de atendimento invalido.")
        appointment.status = status
        self.repository.session.commit()
        return appointment
