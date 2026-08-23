from backend.models.clinical_record import ClinicalRecord
from backend.repositories.base_repository import BaseRepository


class ClinicalRecordRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, ClinicalRecord)

    def by_patient(self, patient_id):
        return (
            self.db.query(ClinicalRecord)
            .filter(ClinicalRecord.patient_id == patient_id)
            .order_by(ClinicalRecord.appointment_date.desc())
            .all()
        )
