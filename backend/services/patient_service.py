from fastapi import HTTPException, status

from backend.repositories.patient_repository import PatientRepository


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
        return self.repository.create(data)

    def update_patient(self, patient_id, data):
        patient = self.get_patient(patient_id)
        return self.repository.update(patient, data)
