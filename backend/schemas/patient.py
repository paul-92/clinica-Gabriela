from datetime import date, datetime

from backend.schemas.common import ORMBase


class PatientBase(ORMBase):
    full_name: str
    cpf: str
    birth_date: date | None = None
    phone: str = ""
    email: str = ""
    address: str = ""
    emergency_contact: str = ""
    notes: str = ""
    active: bool = True


class PatientCreate(PatientBase):
    pass


class PatientUpdate(ORMBase):
    full_name: str | None = None
    cpf: str | None = None
    birth_date: date | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    notes: str | None = None
    active: bool | None = None


class PatientRead(PatientBase):
    id: int
    created_at: datetime | None = None
