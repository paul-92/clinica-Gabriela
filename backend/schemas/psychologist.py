from datetime import datetime
from pydantic import model_validator

from backend.domain.identifiers import normalize_crp
from backend.schemas.common import ORMBase


class PsychologistBase(ORMBase):
    full_name: str
    crp: str | None = None
    crp_region: str | None = None
    crp_number: str | None = None
    crp_status: str = "provisional"
    phone: str = ""
    email: str = ""
    specialty: str = ""
    active: bool = True

    @model_validator(mode="after")
    def validate_crp(self):
        self.crp_region, self.crp_number = normalize_crp(self.crp_region, self.crp_number)
        return self


class PsychologistCreate(PsychologistBase):
    pass


class PsychologistUpdate(ORMBase):
    full_name: str | None = None
    crp: str | None = None
    crp_region: str | None = None
    crp_number: str | None = None
    crp_status: str | None = None
    phone: str | None = None
    email: str | None = None
    specialty: str | None = None
    active: bool | None = None

    @model_validator(mode="after")
    def validate_crp(self):
        supplied = "crp_region" in self.model_fields_set or "crp_number" in self.model_fields_set
        if supplied:
            self.crp_region, self.crp_number = normalize_crp(self.crp_region, self.crp_number)
        return self

    @model_validator(mode="before")
    @classmethod
    def reject_null_for_non_nullable_fields(cls, data):
        if isinstance(data, dict):
            forbidden = {"full_name", "phone", "email", "specialty", "active"}
            if any(name in data and data[name] is None for name in forbidden):
                raise ValueError("NULL nao permitido para campo nao nullable.")
        return data


class PsychologistRead(PsychologistBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    version: int
