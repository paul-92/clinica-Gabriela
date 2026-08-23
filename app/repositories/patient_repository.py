from app.models.patient import Patient
from app.repositories.base_repository import BaseRepository


class PatientRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session, Patient)

    def search(self, text=""):
        query = self.session.query(Patient)
        if text:
            query = query.filter(Patient.full_name.ilike(f"%{text}%"))
        return query.order_by(Patient.full_name).all()
