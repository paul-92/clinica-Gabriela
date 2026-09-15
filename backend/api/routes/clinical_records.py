from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schemas.clinical_record import ClinicalRecordCreate, ClinicalRecordRead, ClinicalRecordRevisionRead, ClinicalRecordRectify, ClinicalRecordUpdate
from backend.services.clinical_record_service import ClinicalRecordService
from backend.api.dependencies import require_psychologist
from backend.api.routes.auth import get_current_user
from backend.api.versioning import parse_if_match


router = APIRouter(prefix="/clinical-records", tags=["clinical-records"], dependencies=[Depends(require_psychologist)])


@router.get("", response_model=list[ClinicalRecordRead])
def list_records(patient_id: int | None = None, db: Session = Depends(get_db)):
    return ClinicalRecordService(db).list_records(patient_id)


@router.post("", response_model=ClinicalRecordRead, status_code=201)
def create_record(payload: ClinicalRecordCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return ClinicalRecordService(db).create_record(payload.model_dump(), current_user)


@router.get("/{record_id}", response_model=ClinicalRecordRead)
def get_record(record_id: int, response: Response, db: Session = Depends(get_db)):
    record = ClinicalRecordService(db).get_record(record_id)
    response.headers["ETag"] = f'"{record.version}"'
    return record


@router.put("/{record_id}", response_model=ClinicalRecordRead, deprecated=True)
def update_record(record_id: int, payload: ClinicalRecordUpdate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    return ClinicalRecordService(db).update_record(record_id, data, None)


@router.patch("/{record_id}", response_model=ClinicalRecordRead)
def patch_record(record_id: int, payload: ClinicalRecordUpdate, if_match: str | None = Header(None), db: Session = Depends(get_db)):
    return ClinicalRecordService(db).update_record(record_id, payload.model_dump(exclude_unset=True), parse_if_match(if_match))


@router.post("/{record_id}/finalize", response_model=ClinicalRecordRead)
def finalize_record(record_id: int, if_match: str | None = Header(None), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return ClinicalRecordService(db).finalize_record(record_id, parse_if_match(if_match), current_user)


@router.post("/{record_id}/rectifications", response_model=ClinicalRecordRevisionRead, status_code=201)
def rectify_record(record_id: int, payload: ClinicalRecordRectify, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return ClinicalRecordService(db).rectify_record(record_id, payload.model_dump(), current_user)


@router.delete("/{record_id}", status_code=204)
def delete_draft(record_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    ClinicalRecordService(db).delete_draft(record_id, current_user)
