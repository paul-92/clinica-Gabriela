from datetime import timedelta

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
        self._validate_availability(data)
        return self.repository.create(data)

    def update_appointment(self, appointment_id, data):
        if "status" in data:
            self._validate_status(data["status"])
        appointment = self.get_appointment(appointment_id)
        merged = {
            "psychologist_id": data.get("psychologist_id", appointment.psychologist_id),
            "scheduled_at": data.get("scheduled_at", appointment.scheduled_at),
            "duration_minutes": data.get("duration_minutes", appointment.duration_minutes),
            "status": data.get("status", appointment.status),
        }
        self._validate_availability(merged, exclude_id=appointment_id)
        return self.repository.update(appointment, data)

    def _validate_status(self, status_value):
        allowed = {item.value for item in AppointmentStatus}
        if status_value not in allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status de atendimento invalido.")

    def _validate_availability(self, data, *, exclude_id=None):
        if data.get("status") == AppointmentStatus.CANCELED.value:
            return
        start = data["scheduled_at"]
        end = start + timedelta(minutes=data.get("duration_minutes", 50))
        for existing in self.repository.active_for_psychologist(
            data["psychologist_id"], exclude_id=exclude_id
        ):
            existing_end = existing.scheduled_at + timedelta(
                minutes=existing.duration_minutes
            )
            if start < existing_end and existing.scheduled_at < end:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Conflito de horario para o psicologo.",
                )
