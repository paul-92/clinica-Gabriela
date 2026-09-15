from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schemas.psychologist import PsychologistCreate, PsychologistRead, PsychologistUpdate
from backend.services.psychologist_service import PsychologistService
from backend.api.routes.auth import get_current_user
from backend.api.dependencies import require_admin
from backend.api.versioning import parse_if_match


router = APIRouter(prefix="/psychologists", tags=["psychologists"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[PsychologistRead])
def list_psychologists(active: bool = False, db: Session = Depends(get_db)):
    return PsychologistService(db).list_psychologists(only_active=active)


@router.post("", response_model=PsychologistRead, status_code=201)
def create_psychologist(payload: PsychologistCreate, db: Session = Depends(get_db)):
    return PsychologistService(db).create_psychologist(payload.model_dump())


@router.get("/{psychologist_id}", response_model=PsychologistRead)
def get_psychologist(psychologist_id: int, response: Response, db: Session = Depends(get_db)):
    psychologist = PsychologistService(db).get_psychologist(psychologist_id)
    response.headers["ETag"] = f'"{psychologist.version}"'
    return psychologist


@router.put("/{psychologist_id}", response_model=PsychologistRead, deprecated=True)
def update_psychologist(psychologist_id: int, payload: PsychologistUpdate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    return PsychologistService(db).update_psychologist(psychologist_id, data)


@router.patch("/{psychologist_id}", response_model=PsychologistRead)
def patch_psychologist(psychologist_id: int, payload: PsychologistUpdate, if_match: str | None = Header(None), db: Session = Depends(get_db)):
    return PsychologistService(db).update_psychologist(psychologist_id, payload.model_dump(exclude_unset=True), parse_if_match(if_match))


@router.post("/{psychologist_id}/aptitude", response_model=PsychologistRead, dependencies=[Depends(require_admin)])
def set_aptitude(psychologist_id: int, apt: bool, db: Session = Depends(get_db)):
    return PsychologistService(db).set_aptitude(psychologist_id, apt)
