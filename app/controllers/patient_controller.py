from datetime import datetime

from app.database.session import get_session
from app.services.patient_service import PatientService


class PatientController:
    def list_patients(self, search=""):
        with get_session() as session:
            return PatientService(session).list_patients(search)

    def create_patient(self, data):
        if data.get("birth_date"):
            data["birth_date"] = datetime.strptime(data["birth_date"], "%Y-%m-%d").date()
        with get_session() as session:
            return PatientService(session).create_patient(data)
