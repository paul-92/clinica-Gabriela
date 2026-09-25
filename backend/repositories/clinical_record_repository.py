from backend.models.clinical_record import ClinicalRecord, ClinicalRecordRevision
from backend.repositories.base_repository import BaseRepository


class ClinicalRecordRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, ClinicalRecord)

    def by_patient(self, patient_id, psychologist_id=None):
        query = self.db.query(ClinicalRecord).filter(ClinicalRecord.patient_id == patient_id)
        if psychologist_id is not None:
            query = query.filter(ClinicalRecord.psychologist_id == psychologist_id)
        return query.order_by(ClinicalRecord.appointment_date.desc()).all()

    def list_for_psychologist(self, psychologist_id):
        return (
            self.db.query(ClinicalRecord)
            .filter(ClinicalRecord.psychologist_id == psychologist_id)
            .order_by(ClinicalRecord.appointment_date.desc())
            .all()
        )

    def latest_revision(self, record_id):
        return (
            self.db.query(ClinicalRecordRevision)
            .filter(ClinicalRecordRevision.clinical_record_id == record_id)
            .order_by(ClinicalRecordRevision.id.desc())
            .first()
        )
