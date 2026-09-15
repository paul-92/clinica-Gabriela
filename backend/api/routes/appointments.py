from datetime import date

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schemas.appointment import AppointmentCreate, AppointmentRead, AppointmentUpdate
from backend.services.appointment_integrity_service import AppointmentIntegrityService
from backend.api.routes.auth import get_current_user
from backend.api.versioning import parse_if_match


router = APIRouter(prefix="/appointments", tags=["appointments"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[AppointmentRead])
def list_appointments(
    target_date: date | None = None,
    psychologist_id: int | None = None,
    db: Session = Depends(get_db),
):
    return AppointmentIntegrityService(db).list_appointments(target_date, psychologist_id)


@router.post("", response_model=AppointmentRead, status_code=201)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    return AppointmentIntegrityService(db).create_appointment(payload.model_dump())


@router.get("/{appointment_id}", response_model=AppointmentRead)
def get_appointment(appointment_id: int, response: Response, db: Session = Depends(get_db)):
    appointment = AppointmentIntegrityService(db).get_appointment(appointment_id)
    response.headers["ETag"] = f'"{appointment.version}"'
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentRead, deprecated=True)
def update_appointment(appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    return AppointmentIntegrityService(db).update_appointment(appointment_id, data)


@router.patch("/{appointment_id}", response_model=AppointmentRead)
def patch_appointment(appointment_id: int, payload: AppointmentUpdate, if_match: str | None = Header(None), db: Session = Depends(get_db)):
    expected = parse_if_match(if_match)
    if expected is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=428, detail="If-Match obrigatorio.")
    return AppointmentIntegrityService(db).update_appointment(appointment_id, payload.model_dump(exclude_unset=True), expected)
