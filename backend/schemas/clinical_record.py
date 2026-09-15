from datetime import datetime
from pydantic import model_validator

from backend.schemas.common import ORMBase


class ClinicalRecordBase(ORMBase):
    patient_id: int
    psychologist_id: int
    appointment_id: int | None = None
    appointment_date: datetime
    main_complaint: str = ""
    session_goals: str = ""
    observed_mood: str = ""
    clinical_evolution: str = ""
    interventions: str = ""
    referrals: str = ""
    next_steps: str = ""
    private_notes: str = ""
    clinical_hypotheses: str = ""
    therapeutic_plan: str = ""
    future_attachments: str = ""


class ClinicalRecordCreate(ClinicalRecordBase):
    pass


class ClinicalRecordUpdate(ORMBase):
    appointment_date: datetime | None = None
    main_complaint: str | None = None
    session_goals: str | None = None
    observed_mood: str | None = None
    clinical_evolution: str | None = None
    interventions: str | None = None
    referrals: str | None = None
    next_steps: str | None = None
    private_notes: str | None = None
    clinical_hypotheses: str | None = None
    therapeutic_plan: str | None = None
    future_attachments: str | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_explicit_null(cls, data):
        if isinstance(data, dict) and any(value is None for value in data.values()):
            raise ValueError("NULL nao permitido em campos clinicos de atualizacao.")
        return data


class ClinicalRecordRead(ClinicalRecordBase):
    id: int
    author_user_id: int | None = None
    author_status: str
    status: str
    version: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    finalized_at: datetime | None = None


class ClinicalRecordRectify(ORMBase):
    reason: str
    main_complaint: str = ""
    session_goals: str = ""
    observed_mood: str = ""
    clinical_evolution: str = ""
    interventions: str = ""
    referrals: str = ""
    next_steps: str = ""
    private_notes: str = ""
    clinical_hypotheses: str = ""
    therapeutic_plan: str = ""
    future_attachments: str = ""


class ClinicalRecordRevisionRead(ORMBase):
    id: int
    clinical_record_id: int
    previous_revision_id: int | None = None
    author_user_id: int
    psychologist_id: int
    reason: str
    created_at: datetime
