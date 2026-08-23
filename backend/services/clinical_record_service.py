from fastapi import HTTPException, status

from backend.repositories.clinical_record_repository import ClinicalRecordRepository


class ClinicalRecordService:
    def __init__(self, db):
        self.repository = ClinicalRecordRepository(db)

    def list_records(self, patient_id=None):
        if patient_id:
            return self.repository.by_patient(patient_id)
        return self.repository.list_all()

    def get_record(self, record_id):
        record = self.repository.get(record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prontuario nao encontrado.")
        return record

    def create_record(self, data):
        return self.repository.create(data)

    def update_record(self, record_id, data):
        record = self.get_record(record_id)
        return self.repository.update(record, data)
