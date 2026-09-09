from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schemas.psychologist import PsychologistCreate, PsychologistRead, PsychologistUpdate
from backend.services.psychologist_service import PsychologistService
from backend.api.routes.auth import get_current_user


router = APIRouter(prefix="/psychologists", tags=["psychologists"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[PsychologistRead])
def list_psychologists(active: bool = False, db: Session = Depends(get_db)):
    return PsychologistService(db).list_psychologists(only_active=active)


@router.post("", response_model=PsychologistRead, status_code=201)
def create_psychologist(payload: PsychologistCreate, db: Session = Depends(get_db)):
    return PsychologistService(db).create_psychologist(payload.model_dump())


@router.get("/{psychologist_id}", response_model=PsychologistRead)
def get_psychologist(psychologist_id: int, db: Session = Depends(get_db)):
    return PsychologistService(db).get_psychologist(psychologist_id)


@router.put("/{psychologist_id}", response_model=PsychologistRead)
def update_psychologist(psychologist_id: int, payload: PsychologistUpdate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    return PsychologistService(db).update_psychologist(psychologist_id, data)
