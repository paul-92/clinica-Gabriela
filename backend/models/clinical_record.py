from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base


class ClinicalRecord(Base):
    __tablename__ = "clinical_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    psychologist_id: Mapped[int] = mapped_column(ForeignKey("psychologists.id"), nullable=False)
    author_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    author_status: Mapped[str] = mapped_column(String(30), nullable=False, default="identified", server_default="identified")
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id"), nullable=True)
    appointment_date = mapped_column(DateTime, nullable=False)
    main_complaint = mapped_column(Text, default="")
    session_goals = mapped_column(Text, default="")
    observed_mood = mapped_column(Text, default="")
    clinical_evolution = mapped_column(Text, default="")
    interventions = mapped_column(Text, default="")
    referrals = mapped_column(Text, default="")
    next_steps = mapped_column(Text, default="")
    private_notes = mapped_column(Text, default="")
    clinical_hypotheses = mapped_column(Text, default="")
    therapeutic_plan = mapped_column(Text, default="")
    future_attachments = mapped_column(Text, default="")
    created_at = mapped_column(DateTime, server_default=func.now())
    updated_at = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    finalized_at = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft", server_default="draft")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    patient = relationship("Patient", back_populates="clinical_records")
    psychologist = relationship("Psychologist", back_populates="clinical_records")


class ClinicalRecordRevision(Base):
    __tablename__ = "clinical_record_revisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clinical_record_id: Mapped[int] = mapped_column(ForeignKey("clinical_records.id"), nullable=False, index=True)
    previous_revision_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_record_revisions.id"), nullable=True)
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    psychologist_id: Mapped[int] = mapped_column(ForeignKey("psychologists.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    content_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    created_at = mapped_column(DateTime, nullable=False, server_default=func.now())


class ClinicalRecordAuditEvent(Base):
    __tablename__ = "clinical_record_audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    record_reference: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    occurred_at = mapped_column(DateTime, nullable=False, server_default=func.now())
