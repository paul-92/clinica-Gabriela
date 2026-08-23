from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schemas.clinical_record import ClinicalRecordCreate, ClinicalRecordRead, ClinicalRecordUpdate
from backend.services.clinical_record_service import ClinicalRecordService


router = APIRouter(prefix="/clinical-records", tags=["clinical-records"])


@router.get("", response_model=list[ClinicalRecordRead])
def list_records(patient_id: int | None = None, db: Session = Depends(get_db)):
    return ClinicalRecordService(db).list_records(patient_id)


@router.post("", response_model=ClinicalRecordRead, status_code=201)
def create_record(payload: ClinicalRecordCreate, db: Session = Depends(get_db)):
    return ClinicalRecordService(db).create_record(payload.model_dump())


@router.get("/{record_id}", response_model=ClinicalRecordRead)
def get_record(record_id: int, db: Session = Depends(get_db)):
    return ClinicalRecordService(db).get_record(record_id)


@router.put("/{record_id}", response_model=ClinicalRecordRead)
def update_record(record_id: int, payload: ClinicalRecordUpdate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    return ClinicalRecordService(db).update_record(record_id, data)
