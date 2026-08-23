from backend.schemas.common import ORMBase


class LicenseStatus(ORMBase):
    valid: bool
    reason: str
    message: str
    customer: str
    type: str
    expires_at: str
    days_left: int
