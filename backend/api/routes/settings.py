from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schemas.settings import ClinicSettingsRead, ClinicSettingsUpdate
from backend.services.settings_service import SettingsService
from backend.api.dependencies import require_admin


router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(require_admin)])


@router.get("", response_model=ClinicSettingsRead)
def get_settings(db: Session = Depends(get_db)):
    return SettingsService(db).get_settings()


@router.put("", response_model=ClinicSettingsRead)
def update_settings(payload: ClinicSettingsUpdate, db: Session = Depends(get_db)):
    return SettingsService(db).update_settings(payload.model_dump())
