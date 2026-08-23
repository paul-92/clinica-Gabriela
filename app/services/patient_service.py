from app.models.patient import Patient
from app.repositories.patient_repository import PatientRepository


class PatientService:
    def __init__(self, session):
        self.repository = PatientRepository(session)

    def list_patients(self, search=""):
        return self.repository.search(search)

    def create_patient(self, data):
        patient = Patient(**data)
        return self.repository.add(patient)
