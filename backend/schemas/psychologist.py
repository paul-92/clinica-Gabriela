from datetime import datetime

from backend.schemas.common import ORMBase


class PsychologistBase(ORMBase):
    full_name: str
    crp: str
    phone: str = ""
    email: str = ""
    specialty: str = ""
    active: bool = True


class PsychologistCreate(PsychologistBase):
    pass


class PsychologistUpdate(ORMBase):
    full_name: str | None = None
    crp: str | None = None
    phone: str | None = None
    email: str | None = None
    specialty: str | None = None
    active: bool | None = None


class PsychologistRead(PsychologistBase):
    id: int
    created_at: datetime | None = None
