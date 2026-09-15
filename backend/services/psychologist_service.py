from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from backend.repositories.psychologist_repository import PsychologistRepository
from backend.services.errors import translate_integrity_error


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
        data["crp_status"] = "provisional"
        if data.get("crp_region") and data.get("crp_number"):
            data["crp"] = f'{data["crp_region"]}/{data["crp_number"]}'
        try:
            return self.repository.create(data)
        except IntegrityError as exc:
            translate_integrity_error(self.repository.db, exc)

    def update_psychologist(self, psychologist_id, data, expected_version=None):
        psychologist = self.get_psychologist(psychologist_id)
        if expected_version is not None and expected_version != psychologist.version:
            raise HTTPException(status_code=412, detail="Versao do recurso desatualizada.")
        data.pop("crp_status", None)
        region = data.get("crp_region", psychologist.crp_region)
        number = data.get("crp_number", psychologist.crp_number)
        if (region is None) != (number is None):
            raise HTTPException(status_code=422, detail="Regional e numero do CRP devem ser informados juntos.")
        if "crp_region" in data or "crp_number" in data:
            data["crp"] = f"{region}/{number}" if region and number else None
            data["crp_status"] = "provisional"
        data["version"] = psychologist.version + 1
        try:
            return self.repository.update(psychologist, data)
        except IntegrityError as exc:
            translate_integrity_error(self.repository.db, exc)

    def set_aptitude(self, psychologist_id, apt):
        psychologist = self.get_psychologist(psychologist_id)
        if apt and (not psychologist.crp_region or not psychologist.crp_number):
            raise HTTPException(status_code=409, detail="CRP canonico obrigatorio para aptidao clinica.")
        return self.repository.update(psychologist, {
            "crp_status": "apt" if apt else "provisional",
            "version": psychologist.version + 1,
        })
