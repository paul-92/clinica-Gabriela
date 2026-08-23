from app.models.psychologist import Psychologist
from app.repositories.base_repository import BaseRepository


class PsychologistRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session, Psychologist)

    def active(self):
        return self.session.query(Psychologist).filter(Psychologist.active.is_(True)).order_by(Psychologist.full_name).all()
