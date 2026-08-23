from datetime import datetime

from backend.schemas.common import ORMBase


class ClinicalRecordBase(ORMBase):
    patient_id: int
    psychologist_id: int
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


class ClinicalRecordRead(ClinicalRecordBase):
    id: int
    created_at: datetime | None = None
