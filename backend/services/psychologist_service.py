from fastapi import HTTPException, status

from backend.repositories.psychologist_repository import PsychologistRepository


class PsychologistService:
    def __init__(self, db):
        self.repository = PsychologistRepository(db)

    def list_psychologists(self, only_active=False):
        if only_active:
            return self.repository.active()
        return self.repository.list_all()

    def get_psychologist(self, psychologist_id):
        psychologist = self.repository.get(psychologist_id)
        if not psychologist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Psicologo nao encontrado.")
        return psychologist

    def create_psychologist(self, data):
        return self.repository.create(data)

    def update_psychologist(self, psychologist_id, data):
        psychologist = self.get_psychologist(psychologist_id)
        return self.repository.update(psychologist, data)
