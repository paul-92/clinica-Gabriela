from fastapi import HTTPException, status

from backend.models.appointment import AppointmentStatus
from backend.repositories.appointment_repository import AppointmentRepository


class AppointmentService:
    def __init__(self, db):
        self.repository = AppointmentRepository(db)

    def list_appointments(self, target_date=None, psychologist_id=None):
        return self.repository.list_filtered(target_date, psychologist_id)

    def get_appointment(self, appointment_id):
        appointment = self.repository.get(appointment_id)
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atendimento nao encontrado.")
        return appointment

    def create_appointment(self, data):
        self._validate_status(data.get("status", AppointmentStatus.SCHEDULED.value))
        return self.repository.create(data)

    def update_appointment(self, appointment_id, data):
        if "status" in data:
            self._validate_status(data["status"])
        appointment = self.get_appointment(appointment_id)
        return self.repository.update(appointment, data)

    def _validate_status(self, status_value):
        allowed = {item.value for item in AppointmentStatus}
        if status_value not in allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status de atendimento invalido.")
