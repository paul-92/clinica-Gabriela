from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class ClinicalRecord(Base):
    __tablename__ = "clinical_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    psychologist_id: Mapped[int] = mapped_column(ForeignKey("psychologists.id"), nullable=False)
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

    patient = relationship("Patient", back_populates="clinical_records")
    psychologist = relationship("Psychologist", back_populates="clinical_records")
