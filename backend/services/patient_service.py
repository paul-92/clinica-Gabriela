from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from backend.repositories.patient_repository import PatientRepository
from backend.services.errors import translate_integrity_error


class PatientService:
    def __init__(self, db):
        self.repository = PatientRepository(db)

    def list_patients(self, search=""):
        return self.repository.search(search)

    def get_patient(self, patient_id):
        patient = self.repository.get(patient_id)
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado.")
        return patient

    def create_patient(self, data):
        data["cpf_status"] = "verified" if data.get("cpf") else "not_provided"
        try:
            return self.repository.create(data)
        except IntegrityError as exc:
            translate_integrity_error(self.repository.db, exc)

    def update_patient(self, patient_id, data, expected_version=None):
        patient = self.get_patient(patient_id)
        self._check_version(patient, expected_version)
        data.pop("cpf_status", None)
        if "cpf" in data:
            data["cpf_status"] = "verified" if data["cpf"] else "not_provided"
        data["version"] = patient.version + 1
        try:
            return self.repository.update(patient, data)
        except IntegrityError as exc:
            translate_integrity_error(self.repository.db, exc)

    @staticmethod
    def _check_version(entity, expected):
        if expected is not None and expected != entity.version:
            raise HTTPException(status_code=412, detail="Versao do recurso desatualizada.")
