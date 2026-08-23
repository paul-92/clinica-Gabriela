from backend.models.patient import Patient
from backend.repositories.base_repository import BaseRepository


class PatientRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Patient)

    def search(self, text=""):
        query = self.db.query(Patient)
        if text:
            query = query.filter(Patient.full_name.ilike(f"%{text}%"))
        return query.order_by(Patient.full_name).all()
