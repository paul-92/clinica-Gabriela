from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schemas.patient import PatientCreate, PatientRead, PatientUpdate
from backend.services.patient_service import PatientService


router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=list[PatientRead])
def list_patients(search: str = "", db: Session = Depends(get_db)):
    return PatientService(db).list_patients(search)


@router.post("", response_model=PatientRead, status_code=201)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    return PatientService(db).create_patient(payload.model_dump())


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    return PatientService(db).get_patient(patient_id)


@router.put("/{patient_id}", response_model=PatientRead)
def update_patient(patient_id: int, payload: PatientUpdate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    return PatientService(db).update_patient(patient_id, data)
