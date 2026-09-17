from datetime import date

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schemas.appointment import AppointmentAction, AppointmentCreate, AppointmentExceptionalCorrection, AppointmentRead, AppointmentReschedule, AppointmentUpdate
from backend.services.appointment_integrity_service import AppointmentIntegrityService
from backend.api.routes.auth import get_current_user
from backend.api.versioning import parse_if_match


router = APIRouter(prefix="/appointments", tags=["appointments"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[AppointmentRead])
def list_appointments(
    target_date: date | None = None,
    psychologist_id: int | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return AppointmentIntegrityService(db).list_appointments(target_date, psychologist_id, current_user)


@router.post("", response_model=AppointmentRead, status_code=201)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return AppointmentIntegrityService(db).create_appointment(payload.model_dump(), current_user)


@router.get("/{appointment_id}", response_model=AppointmentRead)
def get_appointment(appointment_id: int, response: Response, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    appointment = AppointmentIntegrityService(db).get_appointment(appointment_id, current_user)
    response.headers["ETag"] = f'"{appointment.version}"'
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentRead, deprecated=True)
def update_appointment(appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    data = payload.model_dump(exclude_unset=True)
    current = AppointmentIntegrityService(db).get_appointment(appointment_id, current_user)
    return AppointmentIntegrityService(db).update_appointment(appointment_id, data, current_user, current.version)


@router.patch("/{appointment_id}", response_model=AppointmentRead)
def patch_appointment(appointment_id: int, payload: AppointmentUpdate, response: Response, if_match: str | None = Header(None), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    expected = parse_if_match(if_match)
    if expected is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=428, detail="If-Match obrigatorio.")
    item = AppointmentIntegrityService(db).update_appointment(appointment_id, payload.model_dump(exclude_unset=True), current_user, expected)
    response.headers["ETag"] = f'"{item.version}"'
    return item


def _action(appointment_id, target, payload, if_match, db, current_user):
    expected = parse_if_match(if_match)
    if expected is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=428, detail="If-Match obrigatorio.")
    return AppointmentIntegrityService(db).transition(appointment_id, target, current_user, expected, payload.reason)


@router.post("/{appointment_id}/cancel", response_model=AppointmentRead)
def cancel(appointment_id: int, payload: AppointmentAction, if_match: str | None = Header(None), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return _action(appointment_id, "canceled", payload, if_match, db, current_user)


@router.post("/{appointment_id}/done", response_model=AppointmentRead)
def done(appointment_id: int, payload: AppointmentAction, if_match: str | None = Header(None), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return _action(appointment_id, "done", payload, if_match, db, current_user)


@router.post("/{appointment_id}/no-show", response_model=AppointmentRead)
def no_show(appointment_id: int, payload: AppointmentAction, if_match: str | None = Header(None), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return _action(appointment_id, "no_show", payload, if_match, db, current_user)


@router.post("/{appointment_id}/reschedule", response_model=AppointmentRead, status_code=201)
def reschedule(appointment_id: int, payload: AppointmentReschedule, if_match: str | None = Header(None), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    expected = parse_if_match(if_match)
    if expected is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=428, detail="If-Match obrigatorio.")
    data = payload.model_dump(); reason = data.pop("reason")
    return AppointmentIntegrityService(db).reschedule(appointment_id, data, current_user, expected, reason)


@router.post("/{appointment_id}/exceptional-correction", response_model=AppointmentRead)
def exceptional_correction(appointment_id: int, payload: AppointmentExceptionalCorrection,
                           if_match: str | None = Header(None), db: Session = Depends(get_db),
                           current_user=Depends(get_current_user)):
    expected = parse_if_match(if_match)
    if expected is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=428, detail="If-Match obrigatorio.")
    return AppointmentIntegrityService(db).exceptional_correction(
        appointment_id, payload.target_status, current_user, expected, payload.reason
    )
