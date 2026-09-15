from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from backend.models.patient import Patient
from backend.models.psychologist import Psychologist
from backend.services.appointment_service import AppointmentService
from backend.services.errors import translate_integrity_error


class AppointmentIntegrityService(AppointmentService):
    """Adiciona as garantias SPEC-003 sem acoplar regras de conflito de agenda."""

    def create_appointment(self, data):
        self._spec003_validate_relations(data)
        try:
            return super().create_appointment(data)
        except IntegrityError as exc:
            translate_integrity_error(self.repository.db, exc)

    def update_appointment(self, appointment_id, data, expected_version=None):
        appointment = self.get_appointment(appointment_id)
        if expected_version is not None and expected_version != appointment.version:
            raise HTTPException(status_code=412, detail="Versao do recurso desatualizada.")
        self._spec003_validate_relations({
            "patient_id": data.get("patient_id", appointment.patient_id),
            "psychologist_id": data.get("psychologist_id", appointment.psychologist_id),
        })
        data["version"] = appointment.version + 1
        try:
            return super().update_appointment(appointment_id, data)
        except IntegrityError as exc:
            translate_integrity_error(self.repository.db, exc)

    def _spec003_validate_relations(self, data):
        patient = self.repository.db.get(Patient, data["patient_id"])
        if patient is None:
            raise HTTPException(status_code=404, detail="Paciente nao encontrado.")
        psychologist = self.repository.db.get(Psychologist, data["psychologist_id"])
        if psychologist is None:
            raise HTTPException(status_code=404, detail="Psicologo nao encontrado.")
        if not patient.active:
            raise HTTPException(status_code=409, detail="Paciente inativo para novos atendimentos.")
        if not psychologist.active or psychologist.crp_status != "apt":
            raise HTTPException(status_code=409, detail="Psicologo nao esta apto para atuacao clinica.")
