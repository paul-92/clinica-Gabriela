from backend.schemas.common import ORMBase


class ClinicSettingsBase(ORMBase):
    clinic_name: str = "Marilia Gabriela Gaspar | Psicologa"
    phone: str = ""
    email: str = ""
    address: str = ""
    default_session_value: float = 0.0


class ClinicSettingsUpdate(ClinicSettingsBase):
    pass


class ClinicSettingsRead(ClinicSettingsBase):
    id: int
