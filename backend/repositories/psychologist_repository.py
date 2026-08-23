from backend.models.psychologist import Psychologist
from backend.repositories.base_repository import BaseRepository


class PsychologistRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Psychologist)

    def active(self):
        return self.db.query(Psychologist).filter(Psychologist.active.is_(True)).order_by(Psychologist.full_name).all()
