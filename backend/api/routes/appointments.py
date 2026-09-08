from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schemas.appointment import AppointmentCreate, AppointmentRead, AppointmentUpdate
from backend.services.appointment_service import AppointmentService
from backend.api.routes.auth import get_current_user


router = APIRouter(prefix="/appointments", tags=["appointments"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[AppointmentRead])
def list_appointments(
    target_date: date | None = None,
    psychologist_id: int | None = None,
    db: Session = Depends(get_db),
):
    return AppointmentService(db).list_appointments(target_date, psychologist_id)


@router.post("", response_model=AppointmentRead, status_code=201)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    return AppointmentService(db).create_appointment(payload.model_dump())


@router.get("/{appointment_id}", response_model=AppointmentRead)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    return AppointmentService(db).get_appointment(appointment_id)


@router.put("/{appointment_id}", response_model=AppointmentRead)
def update_appointment(appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    return AppointmentService(db).update_appointment(appointment_id, data)
