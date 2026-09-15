from datetime import date, datetime
from pydantic import field_validator, model_validator

from backend.domain.identifiers import normalize_cpf
from backend.schemas.common import ORMBase


class PatientBase(ORMBase):
    full_name: str
    cpf: str | None = None
    cpf_status: str = "not_provided"
    birth_date: date | None = None
    phone: str = ""
    email: str = ""
    address: str = ""
    emergency_contact: str = ""
    notes: str = ""
    active: bool = True

class PatientCreate(PatientBase):
    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, value):
        return normalize_cpf(value)


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

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, value):
        return normalize_cpf(value)

    @model_validator(mode="before")
    @classmethod
    def reject_null_for_non_nullable_fields(cls, data):
        if isinstance(data, dict):
            forbidden = {"full_name", "phone", "email", "address", "emergency_contact", "active"}
            if any(name in data and data[name] is None for name in forbidden):
                raise ValueError("NULL nao permitido para campo nao nullable.")
        return data


class PatientRead(PatientBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    version: int
