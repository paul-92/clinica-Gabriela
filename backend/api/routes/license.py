from fastapi import APIRouter

from app.utils.license import license_status
from backend.schemas.license import LicenseStatus


router = APIRouter(prefix="/license", tags=["license"])


@router.get("/status", response_model=LicenseStatus)
def get_license_status():
    return license_status()
